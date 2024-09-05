import logging
import os
import time
from typing import ClassVar
from venv import logger

from bs4 import BeautifulSoup

from feeds.email.client import EmailClient, EmailMessage
from feeds.feed.base import FeedChecker
from feeds.http.client import HTTPClientBase
from feeds.http.log import RequestLogService
from feeds.shared.config import ConfigKeys
from feeds.shared.helper import hash_equals


class WebCheckerBase(FeedChecker):
    """Base class for simple web checkers"""

    def __init__(
            self,
            http_client: HTTPClientBase,
            email_client: EmailClient,
            request_log_service: RequestLogService,
            config: dict) -> None:
        super().__init__(config)
        self.http_client = http_client
        self.email_client = email_client
        self.request_log_service = request_log_service

    def check(self) -> None:
        """Should be overwritten by subclasses"""
        raise NotImplementedError

    def send_email(self, subject: str, body: str) -> None:
        message = EmailMessage(subject=subject, body=body)
        self.email_client.send_email(message)


class UrlAvailabilityChecker(WebCheckerBase):

    def __init__(
            self,
            email_client: EmailClient,
            http_client: HTTPClientBase,
            request_log_service: RequestLogService,
            config: dict) -> None:
        super().__init__(http_client, email_client, request_log_service, config)
        self.logger = logging.getLogger("UrlAvailabilityChecker")

    def check(self) -> None:
        data_dir = self.config[ConfigKeys.DIR]
        if not os.path.exists(data_dir):
            logger.info("Creating directory %s...", data_dir)
            os.makedirs(data_dir)
        last_status_code = self.request_log_service.get_last_request_value(value_index=1)
        expected_status_code = self.config[ConfigKeys.EXPECTED_STATUS_CODE]
        logger.debug("Last status code: %s", last_status_code)
        if last_status_code and int(last_status_code) == expected_status_code:
            self.logger.info(
                "Service is available (status code %s). Check is skipped!",
                last_status_code,
            )
            return

        url = self.config[ConfigKeys.URL]
        name = self.config[ConfigKeys.NAME]
        logger.debug("Checking availability of web service at %s...", url)
        status_code = self.http_client.get_response_code(url)
        self.request_log_service.log_request(status_code)
        if status_code == expected_status_code:
            self.send_email(
                subject=f"Web service {name} returns status code {status_code}",
                body=f"Web service at {url} is returning status code {status_code}")


class PageContentChecker(WebCheckerBase):
    check_success: ClassVar[int] = int(True)
    check_failed: ClassVar[int] = int(False)
    saved_content_count: ClassVar[int] = 50
    _content_encoding: ClassVar[str] = "utf-8"

    def __init__(
            self,
            email_client: EmailClient,
            http_client: HTTPClientBase,
            request_log_service: RequestLogService,
            config: dict):
        super().__init__(http_client, email_client, request_log_service, config)
        self.logger = logging.getLogger("PageContentChecker")
        self._data_dir = self.config[ConfigKeys.DIR]
        self._content_dir_path = os.path.join(self.config[ConfigKeys.DIR], "content")

    def check(self) -> None:
        if not os.path.exists(self._data_dir):
            logger.info("Creating directory %s...", self._data_dir)
            os.makedirs(self._data_dir)
        last_check = self.request_log_service.get_last_request_value(value_index=1)
        if last_check and int(last_check) == self.check_success:
            self.logger.info("Check is skipped!")
            return

        if not os.path.exists(self._content_dir_path):
            logger.info("Creating directory %s...", self._content_dir_path)
            os.makedirs(self._content_dir_path)

        url = self.config[ConfigKeys.URL]
        name = self.config[ConfigKeys.NAME]
        logger.debug("Checking content of web service at %s...", url)
        if not (response := self.http_client.get_response_string(url)):
            self.logger.error("%s: Failed to get response from %s", name, url)
            self.request_log_service.log_request(self.check_failed)
            return

        response_content_bs = BeautifulSoup(response, "html.parser")
        html_node = response_content_bs.select_one(self.config[ConfigKeys.CSS_SELECTOR])
        is_content_updated = self._is_content_updated(str(html_node))
        self.request_log_service.log_request(int(is_content_updated))
        self._write_page_content(str(html_node))
        if is_content_updated:
            self.logger.info("Content updated. Saving content...")
            self.request_log_service.log_request(self.check_success)
            self.send_email(
                subject=f"{name}: content updated!",
                body=f"Content of {name} at {url} has been updated.")
        else:
            self.logger.info("Content not updated.")
        self._clean_up_content_dir()

    def _write_page_content(self, page_content: str) -> None:
        file_path = os.path.join(self._content_dir_path, f"page_content{time.time_ns()}.html")
        with open(file_path, "w", encoding=self._content_encoding) as file:
            logger.debug("Writing page content to file %s...", file_path)
            file.write(page_content)

    def _is_content_updated(self, content: str) -> bool:
        saved_content = self._list_content_dir()
        if not saved_content:
            return False

        latest_content_file_path = saved_content[0]
        latest_saved_content_path = os.path.join(self._content_dir_path, latest_content_file_path)
        with open(latest_saved_content_path, "r", encoding=self._content_encoding) as file:
            return not hash_equals(content.encode(), file.read().encode())

    def _list_content_dir(self) -> list[str]:
        return sorted(os.listdir(self._content_dir_path), reverse=True)

    def _clean_up_content_dir(self) -> None:
        saved_content = self._list_content_dir()
        if len(saved_content) > self.saved_content_count:
            for file in saved_content[self.saved_content_count:]:
                file_path = os.path.join(self._content_dir_path, file)
                logger.debug("Removing file %s...", file_path)
                os.remove(file_path)
