from feeds.feed.base import FeedChecker
from enum import StrEnum
from feeds.http.client import HTTPClientBase
from datetime import datetime
from feeds.email.client import EmailClient, EmailMessage
import xml.etree.ElementTree as ET
import os


class ConfigKeys(StrEnum):
    URL = "url"
    DIR = "dir"
    NAME = "name"


class RSSFeedChecker(FeedChecker):
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
        rss_tree = ET.parse(feed)
        if self._feed_updated(rss_tree):
            self._save_feed(rss_tree)
            self._send_notification_email()

    def _feed_updated(self, new_feed: ET.ElementTree) -> bool:
        latest_feed, = sorted(os.listdir(self.config[ConfigKeys.DIR]), reverse=True)
        if not latest_feed:
            return True

        feed_path = os.path.join(self.config[ConfigKeys.DIR], latest_feed)
        tree = ET.parse(feed_path)
        if str(tree) != str(new_feed):
            return True
        return False

    def _save_feed(self, feed: ET.ElementTree) -> None:
        feed_name = f"{self.config[ConfigKeys.NAME]}_{datetime.now().strftime('%Y-%m-%d_%H_%m')}.xml"
        feed.write(os.path.join(self.config[ConfigKeys.DIR], feed_name))

    def _send_notification_email(self) -> None:
        subject = f"RSS feed {self.config[ConfigKeys.NAME]} updated!"
        body = (f"RSS feed {self.config[ConfigKeys.NAME]} has been updated. See {self.config[ConfigKeys.URL]} "
                f"or downloaded file in {self.config[ConfigKeys.DIR]}.")
        message = EmailMessage(subject=subject, body=body)
        self._email_client.send_email(message)
