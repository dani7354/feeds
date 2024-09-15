import asyncio
import logging

from feeds.email.client import EmailClient
from feeds.feed.base import FeedChecker, FeedCheckFailedError
from feeds.service.portscan import HostScanService
from feeds.shared.config import ConfigKeys


class HostAvailabilityCheck(FeedChecker):

    def __init__(self, host_scan_service: HostScanService, email_client: EmailClient, config: dict):
        super().__init__(config)
        self._host_scan_service = host_scan_service
        self._email_client = email_client
        self._logger = logging.getLogger("HostCheck")
        self.host = self.config[ConfigKeys.HOST]
        self.expected_open_port = self.config[ConfigKeys.EXPECTED_OPEN_PORTS]

    def check(self) -> None:
        try:
            result = asyncio.run(self._host_scan_service.scan_host_tcp_ports(self.host))
            expected_ports_are_open = all(port in result.open_tcp_ports for port in self.expected_open_port)
            if not expected_ports_are_open:
                self._logger.error(
                    "Host %s does not have all expected ports open. Expected: %s, Open: %s",
                    self.host,
                    self.expected_open_port,
                    result.open_tcp_ports)
        except Exception as ex:
            raise FeedCheckFailedError(
                f"Error checking host {self.host}: {ex}"
            ) from ex
