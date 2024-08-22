import logging
import os
from datetime import datetime
from enum import StrEnum
from typing import ClassVar
from venv import logger

from feeds.email.client import EmailClient, EmailMessage
from feeds.feed.base import FeedChecker
from feeds.http.client import HTTPClientBase


class ConfigKeys(StrEnum):
    URL = "url"
    DIR = "data_dir"
    NAME = "name"
    EXPECTED_STATUS_CODE = "expected_status_code"


class WebServiceAvailabilityChecker(FeedChecker):
    _request_log_filename: ClassVar[str] = "requests.log"
    _request_log_encoding: ClassVar[str] = "utf-8"
    _record_cell_delimiter: ClassVar[str] = ";"

    def __init__(
            self, email_client: EmailClient, http_client: HTTPClientBase, config: dict
    ) -> None:
        super().__init__(config)
        self._email_client = email_client
        self._http_client = http_client
        self.logger = logging.getLogger("WebServiceAvailabilityChecker")

    def check(self) -> None:
        data_dir = self.config[ConfigKeys.DIR]
        if not os.path.exists(data_dir):
            logger.info("Creating directory %s...", data_dir)
            os.makedirs(data_dir)
        requests_log = os.path.join(
            data_dir, self._request_log_filename
        )
        last_status_code = self._get_latest_status_code(requests_log)
        expected_status_code = self.config[ConfigKeys.EXPECTED_STATUS_CODE]
        logger.debug("Last status code: %s", last_status_code)
        if last_status_code == expected_status_code:
            self.logger.info(
                "Service is available (status code %s). Check is skipped!",
                last_status_code,
            )
            return

        url = self.config[ConfigKeys.URL]
        name = self.config[ConfigKeys.NAME]
        logger.debug("Checking availability of web service at %s...", url)
        status_code = self._http_client.get_response_code(url)
        if status_code == expected_status_code:
            subject = f"Web service {name} returns status code {status_code}"
            body = f"Web service at {url} is returning status code {status_code}"
            message = EmailMessage(subject=subject, body=body)
            self._log_status_code(requests_log, status_code)
            self._email_client.send_email(message)

    def _get_latest_status_code(self, request_log_path: str) -> int | None:
        if not os.path.exists(request_log_path):
            logger.warning("Request log %s doesn't exist!", request_log_path)
            return None

        with open(request_log_path, "r", encoding=self._request_log_encoding) as file:
            lines = file.readlines()
            if not lines:
                return None
            return int(lines[-1].split(self._record_cell_delimiter)[1])

    def _log_status_code(self, request_log_path: str, status_code: int) -> None:
        with open(request_log_path, "a", encoding=self._request_log_encoding) as file:
            logger.debug("Writing status code to %s...", request_log_path)
            file.write(
                f"{datetime.now().isoformat()}{self._record_cell_delimiter}{status_code}\n"
            )
