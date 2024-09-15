from unittest.mock import MagicMock

import pytest

from feeds.email.client import EmailClient
from feeds.feed.web import UrlAvailabilityChecker
from feeds.http.client import HTTPClientBase
from feeds.http.log import RequestLogService
from feeds.shared.config import ConfigKeys


@pytest.fixture
def url_availability_checker(tmp_path) -> UrlAvailabilityChecker:
    email_client = MagicMock(EmailClient)
    http_client = MagicMock(HTTPClientBase)

    dir_path = tmp_path / "test"
    request_log_service = RequestLogService(str(dir_path))
    config = {
        ConfigKeys.NAME: "Test",
        ConfigKeys.URL: "http://test.com",
        ConfigKeys.DIR: dir_path,
        ConfigKeys.EXPECTED_STATUS_CODE: 200,
    }

    return UrlAvailabilityChecker(email_client, http_client, request_log_service, config)


def test_url_availability_checker_do_nothing_on_service_down(
        url_availability_checker,
) -> None:
    url_availability_checker._http_client.get_response_code.return_value = 500
    url_availability_checker.check()

    assert int(url_availability_checker.request_log_service.get_last_request_value(value_index=1)) == 500
    url_availability_checker.email_client.send_email.assert_not_called()


def test_url_availability_checker_send_email_on_service_up(
        url_availability_checker,
) -> None:
    url_availability_checker._http_client.get_response_code.return_value = 200
    url_availability_checker.check()

    assert int(url_availability_checker.request_log_service.get_last_request_value(value_index=1)) == 200
    url_availability_checker.email_client.send_email.assert_called_once()
