from unittest.mock import MagicMock

import pytest

from feeds.email.client import EmailClient
from feeds.feed.web import PageContentChecker
from feeds.http.client import HTTPClientBase
from feeds.http.log import RequestLogService
from feeds.shared.config import ConfigKeys


def _get_html_content(text: str) -> str:
    return f"<html><body><div class='content'>{text}</div></body></html>"


@pytest.fixture
def page_content_checker(tmp_path):
    email_client = MagicMock(EmailClient)
    http_client = MagicMock(HTTPClientBase)

    dir_path = tmp_path / "test"
    request_log_service = RequestLogService(str(dir_path))

    config = {
        ConfigKeys.NAME: "Test",
        ConfigKeys.URL: "http://test.com",
        ConfigKeys.DIR: dir_path,
        ConfigKeys.CSS_SELECTOR: ".content",
    }
    http_client.get_response_string.return_value = _get_html_content("Original content")
    return PageContentChecker(email_client, http_client, request_log_service, config)


def test_page_content_checker_detect_content_changed(page_content_checker):
    page_content_checker.check()

    page_content_checker._http_client.get_response_string.return_value = _get_html_content("Changed content")
    page_content_checker.check()

    assert int(page_content_checker.request_log_service.get_last_request_value(value_index=1)) == int(True)
    page_content_checker.email_client.send_email.assert_called_once()


def test_page_content_checker_ignore_on_no_change(page_content_checker):
    page_content_checker.check()

    # Content not changed since last check
    page_content_checker.check()

    assert int(page_content_checker.request_log_service.get_last_request_value(value_index=1)) == int(False)
    page_content_checker.email_client.send_email.assert_not_called()
