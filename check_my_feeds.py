#!/usr/bin/env python3
from feeds.http.client import HTTPClientBase, HTTPClient
from feeds.settings import MAX_THREAD_COUNT, CONFIG_PATH
from feeds.feed.factory import create_feed_checkers
from feeds.email.client import StandardSMTP, Configuration, EmailClient
from feeds.feed.base import FeedChecker
import os
import json


class CheckMyFeedsJob:
    def __init__(self, config: dict):
        self.config = config

    def get_feed_checkers(self) -> list[FeedChecker]:
        email_client = self._get_email_client()
        http_client = self._get_http_client()
        feed_checkers = create_feed_checkers(
            email_client=email_client,
            http_client=http_client,
            feeds_by_type=self.config["feeds_by_type"])

        return feed_checkers

    def _get_email_client(self) -> EmailClient:
        email_client_config = Configuration(
            smtp_host=self.config["email"]["smtp_server"],
            smtp_port=self.config["email"]["smtp_port"],
            smtp_user=self.config["email"]["smtp_user"],
            smtp_password=self.config["email"]["smtp_password"],
            sender=self.config["email"]["sender"],
            recipients=self.config["email"]["recipients"])
        email_client = StandardSMTP(email_client_config)

        return email_client

    @staticmethod
    def _get_http_client() -> HTTPClientBase:
        return HTTPClient({})

    def run(self):
        for feed_checker in self.get_feed_checkers():
            feed_checker.check()


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as config_file:
        return json.load(config_file)


def main():
    config = load_config()
    job = CheckMyFeedsJob(config)
    job.run()


if __name__ == "__main__":
    main()
