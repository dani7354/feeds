#!/usr/bin/env python3
import json
import logging
import os
import time
from datetime import date
from typing import Any

import schedule

from feeds.email.client import StandardSMTP, Configuration, EmailClient
from feeds.feed.base import FeedCheckFailedError, FeedSchedule
from feeds.feed.base import FeedChecker
from feeds.feed.factory import create_feed_checkers
from feeds.http.client import (
    HTTPClientBase,
    HTTPClient,
    HTTPClientDynamicBase,
    HTTPClientDynamic,
)
from feeds.service.host_scan import NmapScanService
from feeds.settings import CONFIG_PATH


class CheckMyFeedsJob:
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger("CheckMyFeeds")

    def get_feed_checkers(self) -> list[FeedChecker]:
        email_client = self._get_email_client()
        http_client = self._get_http_client()
        http_client_dynamic = self._get_http_client_dynamic()
        feed_checkers = create_feed_checkers(
            email_client=email_client,
            http_client=http_client,
            http_client_dynamic=http_client_dynamic,
            feeds_by_type=self.config["feeds_by_type"],
            host_scan_service=NmapScanService(),
        )

        return feed_checkers

    def _get_email_client(self) -> EmailClient:
        email_client_config = Configuration(
            smtp_host=self.config["email"]["smtp_server"],
            smtp_port=self.config["email"]["smtp_port"],
            smtp_user=self.config["email"]["smtp_user"],
            smtp_password=self.config["email"]["smtp_password"],
            sender=self.config["email"]["sender"],
            recipients=self.config["email"]["recipients"],
        )
        email_client = StandardSMTP(email_client_config)

        return email_client

    @staticmethod
    def _schedule_check(feed_checker: FeedChecker) -> None:
        logging.info("%s will run %s.", feed_checker.name, feed_checker.schedule)
        if feed_checker.schedule == FeedSchedule.HOURLY:
            schedule.every().hour.do(feed_checker.check)
        elif feed_checker.schedule == FeedSchedule.DAILY:
            schedule.every().day.do(feed_checker.check)
        elif feed_checker.schedule == FeedSchedule.WEEKLY:
            schedule.every().week.do(feed_checker.check)
        else:
            raise ValueError(f"Invalid schedule: {feed_checker.schedule}")

    @staticmethod
    def _get_http_client() -> HTTPClientBase:
        return HTTPClient({})

    @staticmethod
    def _get_http_client_dynamic() -> HTTPClientDynamicBase:
        return HTTPClientDynamic({})

    def run(self) -> None:
        try:
            for feed_checker in self.get_feed_checkers():
                self.logger.info("Running feed checker %s...", feed_checker.name)
                feed_checker.check()
                self.logger.info("Finished running %s.", feed_checker.name)

                self.logger.debug("Setting up scheduling for feed %s...", feed_checker.name)
                self._schedule_check(feed_checker)
        except FeedCheckFailedError as ex:
            self.logger.error("Error running scheduled jobs: %s", ex)

        self.logger.info("Feed checkers set up successfully! Running scheduled jobs...")
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except FeedCheckFailedError as ex:
                self.logger.error("Error running scheduled jobs: %s", ex)


def _load_config() -> dict[str, Any]:
    with open(CONFIG_PATH, "r", encoding="utf-8") as config_file:
        return json.load(config_file)


def _setup_logging(config: dict[str, Any]) -> None:
    conf_section = config["logging"]
    loglevel = conf_section["level"]
    directory = conf_section["dir"]
    filename_base = f"CheckMyFeedsJob_{date.today().month:02d}-{date.today().year}.log"
    logfile = os.path.join(directory, filename_base)
    logging.basicConfig(
        filename=logfile,
        filemode="a",
        format="%(asctime)s - %(levelname)s: %(message)s",
        level=loglevel,
    )
    logging.getLogger().addHandler(logging.StreamHandler())


def main():
    config = _load_config()
    _setup_logging(config)
    job = CheckMyFeedsJob(config)
    job.run()


if __name__ == "__main__":
    main()
