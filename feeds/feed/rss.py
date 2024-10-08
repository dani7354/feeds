import logging
import os
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from datetime import datetime
from typing import NamedTuple, ClassVar

from feeds.email.client import EmailClient, EmailMessage
from feeds.email.html import create_table, create_heading_two, create_link
from feeds.feed.base import FeedChecker, FeedCheckFailedError
from feeds.http.client import HTTPClientBase
from feeds.shared.config import ConfigKeys
from feeds.shared.helper import hash_equals


class RssItem(NamedTuple):
    title: str
    link: str
    published_date: str


class RSSFeedChecker(FeedChecker):
    _channel_items_path: ClassVar[str] = "channel/item"
    _title_element: ClassVar[str] = "title"
    _link_element: ClassVar[str] = "link"
    _published_date_element: ClassVar[str] = "pubDate"

    def __init__(self, email_client: EmailClient, http_client: HTTPClientBase, config: dict):
        super().__init__(config)
        self._http_client = http_client
        self._email_client = email_client
        self._logger = logging.getLogger("RSSFeedChecker")
        self.data_dir_path = self.config[ConfigKeys.DIR]
        self.saved_feeds_count = self.config[ConfigKeys.SAVED_FEEDS_COUNT]
        self.url = self.config[ConfigKeys.URL]

    def check(self) -> None:
        try:
            if not os.path.exists(self.data_dir_path):
                os.mkdir(self.data_dir_path)

            if not (feed := self._http_client.get_response_string(self.url)):
                raise FeedCheckFailedError(f"Failed to download feed at {self.url}")

            rss_tree = ET.ElementTree(ET.fromstring(feed))
            if self._feed_content_updated(rss_tree):
                self._logger.debug("Feed %s updated. Saving feed...", self.name)
                self._save_feed(rss_tree)
                self._send_notification_email(self._parse_feed_items(rss_tree))
                self._remove_old_feeds()
        except Exception as ex:
            raise FeedCheckFailedError(f"Error checking RSS feed {self.name}: {ex}") from ex

    def _parse_feed_items(self, tree: ET.ElementTree) -> list[RssItem]:
        rss_items = []
        for item in tree.findall(self._channel_items_path):
            title = item.find(self._title_element).text
            link = item.find(self._link_element).text
            published_date = item.find(self._published_date_element).text
            rss_items.append(RssItem(title, link, published_date))

        return rss_items

    def _feed_content_updated(self, new_feed_tree: ET.ElementTree) -> bool:
        if not (saved_feeds := self._list_data_dir(descending=True)):
            return True

        latest_feed = saved_feeds[0]
        latest_saved_feed_path = os.path.join(self.data_dir_path, latest_feed)
        latest_saved_feed_tree = ET.parse(latest_saved_feed_path)

        channel_old_feed_bytes = b"".join(
            ET.tostring(x) for x in latest_saved_feed_tree.findall(self._channel_items_path)
        )
        channel_new_feed_bytes = b"".join(ET.tostring(x) for x in new_feed_tree.findall(self._channel_items_path))
        if not channel_new_feed_bytes or not channel_old_feed_bytes:
            raise FeedCheckFailedError("Failed to find RSS feed items. Check if the RSS feed is alright.")

        return not hash_equals(channel_old_feed_bytes, channel_new_feed_bytes)

    def _save_feed(self, feed: ET.ElementTree) -> None:
        feed_name = f"{self.name}_{datetime.now().strftime('%Y-%m-%d_%H_%M')}.xml"
        self._logger.debug("Writing feed %s", feed_name)
        feed.write(os.path.join(self.data_dir_path, feed_name))

    def _send_notification_email(self, rss_items: Sequence[RssItem]) -> None:
        subject = f"RSS-feed {self.name} opdateret"
        rss_items_formatted = [(x.published_date, create_link(x.link, x.title)) for x in rss_items]

        html_heading = create_heading_two(self.name)
        html_table = create_table(["Oprettet", "Link"], rss_items_formatted)

        body = f"{html_heading}\n{html_table}"
        message = EmailMessage(subject=subject, body=body)
        self._email_client.send_email(message)

    def _remove_old_feeds(self) -> None:
        saved_feeds = self._list_data_dir(descending=True)
        if len(saved_feeds) > self.saved_feeds_count:
            for feed in saved_feeds[self.saved_feeds_count:]:
                self._logger.debug("Removing old feed %s...", feed)
                os.remove(os.path.join(self.data_dir_path, feed))

    def _list_data_dir(self, descending: bool) -> list[str]:
        return sorted(os.listdir(self.data_dir_path), reverse=descending)
