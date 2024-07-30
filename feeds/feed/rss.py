from feeds.feed.base import FeedChecker
from enum import StrEnum
from feeds.http.client import HTTPClientBase
from datetime import datetime
from feeds.email.client import EmailClient, EmailMessage
from feeds.shared.helper import hash_equals
import xml.etree.ElementTree as ET
import os


class ConfigKeys(StrEnum):
    URL = "url"
    DIR = "data_dir"
    SAVED_FEEDS_COUNT = "saved_feeds_count"
    NAME = "name"


class RSSFeedChecker(FeedChecker):
    CHANNEL = "channel"

    def __init__(self, email_client: EmailClient, http_client: HTTPClientBase, config: dict):
        super().__init__(config)
        self._http_client = http_client
        self._email_client = email_client

    def check(self) -> None:
        feed_dir = self.config[ConfigKeys.DIR]
        if not os.path.exists(feed_dir):
            os.mkdir(feed_dir)

        url = self.config[ConfigKeys.URL]
        feed = self._http_client.get_response_string(url)
        rss_tree = ET.ElementTree(ET.fromstring(feed))
        if self._feed_content_updated(rss_tree):
            self._save_feed(rss_tree)
            self._send_notification_email()
            self._remove_old_feeds()

    def _feed_content_updated(self, new_feed: ET.ElementTree) -> bool:
        saved_feeds = self._list_data_dir(descending=True)
        if not saved_feeds:
            return True

        latest_feed = saved_feeds[0]
        feed_path = os.path.join(self.config[ConfigKeys.DIR], latest_feed)
        tree = ET.parse(feed_path)

        channel_new_feed = new_feed.find(self.CHANNEL)
        channel_old_feed = tree.find(self.CHANNEL)

        return not hash_equals(ET.tostring(channel_old_feed), ET.tostring(channel_new_feed))

    def _save_feed(self, feed: ET.ElementTree) -> None:
        feed_name = f"{self.config[ConfigKeys.NAME]}_{datetime.now().strftime('%Y-%m-%d_%H_%M')}.xml"
        feed.write(os.path.join(self.config[ConfigKeys.DIR], feed_name))

    def _send_notification_email(self) -> None:
        subject = f"RSS feed {self.config[ConfigKeys.NAME]} updated!"
        body = (f"RSS feed {self.config[ConfigKeys.NAME]} has been updated. See {self.config[ConfigKeys.URL]} "
                f"or downloaded file in {self.config[ConfigKeys.DIR]}.")
        message = EmailMessage(subject=subject, body=body)
        self._email_client.send_email(message)

    def _remove_old_feeds(self) -> None:
        saved_feeds = self._list_data_dir(descending=False)
        if len(saved_feeds) > self.config[ConfigKeys.SAVED_FEEDS_COUNT]:
            for feed in saved_feeds[self.config[ConfigKeys.SAVED_FEEDS_COUNT]:]:
                os.remove(os.path.join(self.config[ConfigKeys.DIR], feed))

    def _list_data_dir(self, descending: bool) -> list[str]:
        return sorted(os.listdir(self.config[ConfigKeys.DIR]), reverse=descending)
