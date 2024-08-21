import logging
import os
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from datetime import datetime
from enum import StrEnum
from typing import NamedTuple

from feeds.email.client import EmailClient, EmailMessage
from feeds.email.html import create_table, create_heading_two
from feeds.feed.base import FeedChecker, FeedCheckFailedError
from feeds.http.client import HTTPClientBase
from feeds.shared.helper import hash_equals


class ConfigKeys(StrEnum):
    URL = "url"
    DIR = "data_dir"
    SAVED_FEEDS_COUNT = "saved_feeds_count"
    NAME = "name"


class RssItem(NamedTuple):
    title: str
    link: str
    published_date: str



class RSSFeedChecker(FeedChecker):
    CHANNEL_ITEMS = "channel/item"

    def __init__(self, email_client: EmailClient, http_client: HTTPClientBase, config: dict):
        super().__init__(config)
        self._http_client = http_client
        self._email_client = email_client
        self._logger = logging.getLogger("RSSFeedChecker")

    def check(self) -> None:
        try:
            feed_dir = self.config[ConfigKeys.DIR]
            if not os.path.exists(feed_dir):
                os.mkdir(feed_dir)

            url = self.config[ConfigKeys.URL]
            feed = self._http_client.get_response_string(url)
            if not feed:
                raise FeedCheckFailedError(f"Failed to download feed at {url}")

            rss_tree = ET.ElementTree(ET.fromstring(feed))
            if self._feed_content_updated(rss_tree):
                self._logger.debug("Feed %s updated. Saving feed...", self.config[ConfigKeys.NAME])
                self._save_feed(rss_tree)
                rss_items = self._parse_feed_items(rss_tree)
                self._send_notification_email(rss_items)
                self._remove_old_feeds()
        except Exception as ex:
            raise FeedCheckFailedError(f"Error checking RSS feed {self.config[ConfigKeys.NAME]}: {ex}") from ex

    def _parse_feed_items(self, tree: ET.ElementTree) -> list[RssItem]:
        rss_items = []
        for item in tree.findall(self.CHANNEL_ITEMS):
            self._logger.debug("Parsing item %s", ET.tostring(item))
            title = item.find("title").text
            link = item.find("link").text
            published_date = item.find("pubDate").text
            rss_items.append(RssItem(title, link, published_date))

        return rss_items

    def _feed_content_updated(self, new_feed_tree: ET.ElementTree) -> bool:
        saved_feeds = self._list_data_dir(descending=True)
        if not saved_feeds:
            return True

        latest_feed = saved_feeds[0]
        latest_saved_feed_path = os.path.join(self.config[ConfigKeys.DIR], latest_feed)
        latest_saved_feed_tree = ET.parse(latest_saved_feed_path)

        channel_old_feed_bytes = b"".join(ET.tostring(x) for x in latest_saved_feed_tree.findall(self.CHANNEL_ITEMS))
        channel_new_feed_bytes = b"".join(ET.tostring(x) for x in new_feed_tree.findall(self.CHANNEL_ITEMS))
        if not channel_new_feed_bytes or not channel_old_feed_bytes:
            raise FeedCheckFailedError("Failed to find RSS feed items. Check if the RSS feed is alright.")

        return not hash_equals(channel_old_feed_bytes, channel_new_feed_bytes)

    def _save_feed(self, feed: ET.ElementTree) -> None:
        feed_name = f"{self.config[ConfigKeys.NAME]}_{datetime.now().strftime('%Y-%m-%d_%H_%M')}.xml"
        self._logger.debug("Writing feed %s", feed_name)
        feed.write(os.path.join(self.config[ConfigKeys.DIR], feed_name))

    def _send_notification_email(self, rss_items: Sequence[RssItem]) -> None:
        subject = f"RSS feed {self.config[ConfigKeys.NAME]} updated!"
        rss_items_formatted = [f"{x.published_date}: <a href=\"{x.link}\">{x.title}</a>" for x in rss_items]

        html_heading = create_heading_two(self.config[ConfigKeys.NAME])
        html_table = create_table(rss_items_formatted)

        body = f"{html_heading}\n{html_table}"
        message = EmailMessage(subject=subject, body=body)
        self._email_client.send_email(message)

    def _remove_old_feeds(self) -> None:
        saved_feeds = self._list_data_dir(descending=True)
        if len(saved_feeds) > self.config[ConfigKeys.SAVED_FEEDS_COUNT]:
            for feed in saved_feeds[self.config[ConfigKeys.SAVED_FEEDS_COUNT]:]:
                self._logger.debug("Removing old feed %s...", feed)
                os.remove(os.path.join(self.config[ConfigKeys.DIR], feed))

    def _list_data_dir(self, descending: bool) -> list[str]:
        return sorted(os.listdir(self.config[ConfigKeys.DIR]), reverse=descending)
