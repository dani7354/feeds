from unittest.mock import MagicMock

import pytest

from feeds.email.client import EmailClient
from feeds.feed.web import ConfigKeys, UrlAvailabilityChecker
from feeds.http.client import HTTPClientBase


@pytest.fixture
def url_availability_checker(tmp_path) -> UrlAvailabilityChecker:
    email_client = MagicMock(EmailClient)
    http_client = MagicMock(HTTPClientBase)
    config = {
        ConfigKeys.NAME: "Test",
        ConfigKeys.URL: "http://test.com",
        ConfigKeys.DIR: tmp_path / "test",
        ConfigKeys.EXPECTED_STATUS_CODE: 200,
    }

    return UrlAvailabilityChecker(email_client, http_client, config)


def test_url_availability_checker_do_nothing_on_service_down(url_availability_checker) -> None:
    url_availability_checker.http_client.get_response_code.return_value = 500
    url_availability_checker.check()

    request_log_path = url_availability_checker.config[ConfigKeys.DIR] / url_availability_checker._request_log_filename
    assert url_availability_checker.get_last_request_status(request_log_path) == 500
    url_availability_checker.email_client.send_email.assert_not_called()


def test_url_availability_checker_send_email_on_service_up(url_availability_checker) -> None:
    url_availability_checker.http_client.get_response_code.return_value = 200
    url_availability_checker.check()

    request_log_path = url_availability_checker.config[ConfigKeys.DIR] / url_availability_checker._request_log_filename
    assert url_availability_checker.get_last_request_status(request_log_path) == 200
    url_availability_checker.email_client.send_email.assert_called_once()
