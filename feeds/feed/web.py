import logging
import os
from datetime import datetime
from enum import StrEnum
from typing import ClassVar
from venv import logger

from bs4 import BeautifulSoup

from feeds.email.client import EmailClient, EmailMessage
from feeds.feed.base import FeedChecker
from feeds.http.client import HTTPClientBase
from feeds.shared.helper import hash_equals


class ConfigKeys(StrEnum):
    URL = "url"
    DIR = "data_dir"
    NAME = "name"
    EXPECTED_STATUS_CODE = "expected_status_code"
    CSS_SELECTOR = "css_selector"


class WebCheckerBase(FeedChecker):
    """Base class for simple web checkers"""
    _request_log_filename: ClassVar[str] = "requests.log"
    _request_log_encoding: ClassVar[str] = "utf-8"
    _record_cell_delimiter: ClassVar[str] = ";"

    def __init__(self, http_client: HTTPClientBase, email_client: EmailClient, config: dict) -> None:
        super().__init__(config)
        self.http_client = http_client
        self.email_client = email_client

    def check(self) -> None:
        """Should be overwritten by subclasses"""
        raise NotImplementedError

    def get_last_request_status(self, request_log_path: str) -> int | None:
        if not os.path.exists(request_log_path):
            logger.warning("Request log %s doesn't exist!", request_log_path)
            return None

        with open(request_log_path, "r", encoding=self._request_log_encoding) as file:
            lines = file.readlines()
            if not lines:
                return None
            return int(lines[-1].split(self._record_cell_delimiter)[1])

    def log_request_status(self, request_log_path: str, status: int) -> None:
        with open(request_log_path, "a", encoding=self._request_log_encoding) as file:
            logger.debug("Writing status code to %s...", request_log_path)
            file.write(f"{datetime.now().isoformat()}{self._record_cell_delimiter}{status}\n")


class UrlAvailabilityChecker(WebCheckerBase):

    def __init__(self, email_client: EmailClient, http_client: HTTPClientBase, config: dict) -> None:
        super().__init__(http_client, email_client, config)
        self.logger = logging.getLogger("WebServiceAvailabilityChecker")

    def check(self) -> None:
        data_dir = self.config[ConfigKeys.DIR]
        if not os.path.exists(data_dir):
            logger.info("Creating directory %s...", data_dir)
            os.makedirs(data_dir)
        requests_log = os.path.join(
            data_dir, self._request_log_filename
        )
        last_status_code = self.get_last_request_status(requests_log)
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
        status_code = self.http_client.get_response_code(url)
        if status_code == expected_status_code:
            subject = f"Web service {name} returns status code {status_code}"
            body = f"Web service at {url} is returning status code {status_code}"
            message = EmailMessage(subject=subject, body=body)
            self.log_request_status(requests_log, status_code)
            self.email_client.send_email(message)


class PageContentChecker(WebCheckerBase):
    _check_success: ClassVar[int] = 0
    _check_failed: ClassVar[int] = 1
    _content_encoding: ClassVar[str] = "utf-8"

    def __init__(self, email_client: EmailClient, http_client: HTTPClientBase, config: dict):
        super().__init__(http_client, email_client, config)
        self.logger = logging.getLogger("WebServiceContentChecker")
        self._data_dir = self.config[ConfigKeys.DIR]
        self._content_dir_path = os.path.join(self.config[ConfigKeys.DIR], "content")

    def check(self) -> None:
        if not os.path.exists(self._data_dir):
            logger.info("Creating directory %s...", self._data_dir)
            os.makedirs(self._data_dir)
        requests_log = os.path.join(
            self._data_dir, self._request_log_filename
        )
        last_check = self.get_last_request_status(requests_log)
        if last_check == self._check_success:
            self.logger.info("Check is skipped!")
            return

        if not os.path.exists(self._content_dir_path):
            logger.info("Creating directory %s...", self._content_dir_path)
            os.makedirs(self._content_dir_path)

        url = self.config[ConfigKeys.URL]
        name = self.config[ConfigKeys.NAME]
        logger.debug("Checking content of web service at %s...", url)
        response = self.http_client.get_response_string(url)
        if not response:
            self.logger.error("%s: Failed to get response from %s", name, url)
            self.log_request_status(requests_log, self._check_failed)
            return

        response_content_bs = BeautifulSoup(response, "html.parser")
        html_node = response_content_bs.select_one(self.config[ConfigKeys.CSS_SELECTOR])
        if self._is_content_updated(str(html_node)):
            self.logger.info("Content updated. Saving content...")
            self._write_page_content(str(html_node))
            self.log_request_status(requests_log, self._check_success)

    def _write_page_content(self, page_content: str) -> None:
        file_path = os.path.join(self._content_dir_path, f"{datetime.now().isoformat()}.html")
        with open(file_path, "w", encoding=self._content_encoding) as file:
            logger.debug("Writing page content to file %s...", file_path)
            file.write(page_content)

    def _is_content_updated(self, content: str) -> bool:
        saved_content = self._list_content_dir()
        if not saved_content:
            return True

        latest_content_file_path = saved_content[0]
        latest_saved_content_path = os.path.join(self._content_dir_path, latest_content_file_path)
        with open(latest_saved_content_path, "r", encoding=self._content_encoding) as file:
            return hash_equals(content.encode(), file.read().encode())

    def _list_content_dir(self) -> list[str]:
        return sorted(os.listdir(self._content_dir_path), reverse=True)
