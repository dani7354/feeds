import logging
import os
from typing import ClassVar
from venv import logger

from bs4 import BeautifulSoup
from slugify import slugify

from feeds.email.client import EmailClient, EmailMessage
from feeds.email.html import create_heading_one, create_pre
from feeds.feed.base import FeedChecker, FeedCheckFailedError
from feeds.http.client import HTTPClientBase, HTTPClientDynamicBase
from feeds.http.log import RequestLogService
from feeds.service.content import HtmlContentFileService
from feeds.shared.config import ConfigKeys
from feeds.shared.helper import hash_equals


class WebCheckerBase(FeedChecker):
    """Base class for simple web checkers"""

    def __init__(
            self,
            email_client: EmailClient,
            request_log_service: RequestLogService,
            config: dict,
    ) -> None:
        super().__init__(config)
        self.email_client = email_client
        self.request_log_service = request_log_service

    @property
    def url(self) -> str:
        return self.config[ConfigKeys.URL]

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
            config: dict,
    ) -> None:
        super().__init__(email_client, request_log_service, config)
        self._http_client = http_client
        self._logger = logging.getLogger("UrlAvailabilityChecker")
        self.expected_status_code = self.config[ConfigKeys.EXPECTED_STATUS_CODE]
        self.data_dir = self.config[ConfigKeys.DIR]

    def check(self) -> None:
        try:
            if not os.path.exists(self.data_dir):
                logger.info("Creating directory %s...", self.data_dir)
                os.makedirs(self.data_dir)
            last_status_code = self.request_log_service.get_last_request_value(value_index=1)
            logger.debug("Last status code: %s", last_status_code)
            if last_status_code and int(last_status_code) == self.expected_status_code:
                self._logger.info(
                    "Service is available (status code %s). Check is skipped!",
                    last_status_code,
                )
                return

            logger.debug("Checking availability of web service at %s...", self.url)
            status_code = self._http_client.get_response_code(self.url)
            self.request_log_service.log_request(status_code)
            if status_code == self.expected_status_code:
                self.send_email(
                    subject=f"Web service {self.name} returns status code {status_code}",
                    body=f"Web service at {self.url} is returning status code {status_code}",
                )
        except Exception as ex:
            self._logger.error(ex)
            raise FeedCheckFailedError from ex


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
            config: dict,
    ):
        super().__init__(email_client, request_log_service, config)
        self._logger = logging.getLogger("PageContentChecker")
        self._http_client = http_client
        self.content_file_service = HtmlContentFileService(
            os.path.join(self.config[ConfigKeys.DIR], "content"), slugify(self.name)
        )
        self.css_selector = self.config[ConfigKeys.CSS_SELECTOR]

    def check(self) -> None:
        try:
            logger.debug("Checking content of web service at %s...", self.url)
            if not (response := self._http_client.get_response_string(self.url)):
                self._logger.error("%s: Failed to get response from %s", self.name, self.url)
                self.request_log_service.log_request(self.check_failed)
                return

            response_content_bs = BeautifulSoup(response, "html.parser")
            html_node = response_content_bs.select_one(self.css_selector)
            is_content_updated = self._is_content_updated(str(html_node))
            self.request_log_service.log_request(int(is_content_updated))
            html_node_str = str(html_node)
            self.content_file_service.save_content(html_node_str.encode(encoding=self._content_encoding))
            if is_content_updated:
                self._logger.info("Content updated. Saving content...")
                message_body = (f"{create_heading_one(f"Content of {self.name} at {self.url} has been updated.")}\n"
                                f"{create_pre(self.content_file_service.get_diff(html_node_str))}")
                self.send_email(
                    subject=f"{self.name}: content updated!",
                    body=message_body,
                )
            else:
                self._logger.info("Content not updated.")
            self.content_file_service.clean_up_content_dir()
        except Exception as ex:
            self._logger.error(ex)
            raise FeedCheckFailedError from ex

    def _is_content_updated(self, content: str) -> bool:
        if not (saved_content := self.content_file_service.read_latest_content()):
            return False

        return not hash_equals(content.encode(encoding=self._content_encoding), saved_content)


class PageContentCheckerDynamic(WebCheckerBase):
    check_success: ClassVar[int] = int(True)
    check_failed: ClassVar[int] = int(False)
    saved_content_count: ClassVar[int] = 50
    _content_encoding: ClassVar[str] = "utf-8"

    def __init__(
            self,
            email_client: EmailClient,
            http_client: HTTPClientDynamicBase,
            request_log_service: RequestLogService,
            config: dict,
    ):
        super().__init__(email_client, request_log_service, config)
        self._logger = logging.getLogger("PageContentCheckerDynamic")
        self._http_client = http_client
        self.content_file_service = HtmlContentFileService(
            os.path.join(self.config[ConfigKeys.DIR], "content"), slugify(self.name)
        )
        self.css_selector_loaded = self.config[ConfigKeys.CSS_SELECTOR_LOADED]
        self.css_selector_content = self.config[ConfigKeys.CSS_SELECTOR_CONTENT]

    def check(self) -> None:
        try:
            logger.debug("Checking content of web service at %s...", self.url)
            if not (
                    response := self._http_client.get_content_by_css_selector(
                        self.url, self.css_selector_loaded, self.css_selector_content
                    )
            ):
                self._logger.error("%s: Failed to get response from %s", self.name, self.url)
                self.request_log_service.log_request(self.check_failed)
                return
            response_str = str(response)
            is_content_updated = self._is_content_updated(response_str)
            self.request_log_service.log_request(int(is_content_updated))
            self.content_file_service.save_content(response_str.encode(encoding=self._content_encoding))
            if is_content_updated:
                self._logger.info("Content updated. Saving content...")
                self.send_email(
                    subject=f"{self.name}: content updated!",
                    body=f"{create_heading_one(f"Content of {self.name} at {self.url} has been updated.")}\n"
                         f"{create_pre(self.content_file_service.get_diff(response_str))}",
                )
            else:
                self._logger.info("Content not updated.")
            self.content_file_service.clean_up_content_dir()
        except Exception as ex:
            self._logger.error(ex)
            raise FeedCheckFailedError from ex

    def _is_content_updated(self, content: str) -> bool:
        if not (saved_content := self.content_file_service.read_latest_content()):
            return False

        return not hash_equals(content.encode(encoding=self._content_encoding), saved_content)
