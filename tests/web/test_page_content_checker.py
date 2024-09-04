from unittest.mock import MagicMock

import pytest

from feeds.email.client import EmailClient
from feeds.feed.web import PageContentChecker, ConfigKeys
from feeds.http.client import HTTPClientBase


def _get_html_content(text: str):
    return f"<html><body><div class='content'>{text}</div></body></html>"


@pytest.fixture
def page_content_checker(tmp_path):
    email_client = MagicMock(EmailClient)
    http_client = MagicMock(HTTPClientBase)
    config = {
        ConfigKeys.NAME: "Test",
        ConfigKeys.URL: "http://test.com",
        ConfigKeys.DIR: tmp_path / "test",
        ConfigKeys.CSS_SELECTOR: ".content",
    }
    http_client.get_response_string.return_value = _get_html_content("Original content")
    return PageContentChecker(email_client, http_client, config)


def test_page_content_checker_detect_content_changed(page_content_checker):
    page_content_checker.check()

    page_content_checker.http_client.get_response_string.return_value = _get_html_content("Changed content")
    page_content_checker.check()

    request_log_path = page_content_checker.config[ConfigKeys.DIR] / page_content_checker._request_log_filename
    assert page_content_checker.get_last_request_status(request_log_path) == int(True)
    page_content_checker.email_client.send_email.assert_called_once()


def test_page_content_checker_ignore_on_no_change(page_content_checker):
    page_content_checker.check()

    # Content not changed since last check
    page_content_checker.check()

    request_log_path = page_content_checker.config[ConfigKeys.DIR] / page_content_checker._request_log_filename
    assert page_content_checker.get_last_request_status(request_log_path) == int(False)
    page_content_checker.email_client.send_email.assert_not_called()
