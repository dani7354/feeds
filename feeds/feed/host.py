import asyncio
import logging

from feeds.email.client import EmailClient, EmailMessage
from feeds.email.html import create_paragraph, create_heading_two
from feeds.feed.base import FeedChecker, FeedCheckFailedError
from feeds.service.host_scan import HostScanService
from feeds.shared.config import ConfigKeys


class HostAvailabilityCheck(FeedChecker):

    def __init__(self, host_scan_service: HostScanService, email_client: EmailClient, config: dict):
        super().__init__(config)
        self._host_scan_service = host_scan_service
        self._email_client = email_client
        self._logger = logging.getLogger("HostCheck")
        self.host = self.config[ConfigKeys.HOST]
        self.expected_open_ports = set(self.config[ConfigKeys.EXPECTED_OPEN_PORTS])

    def check(self) -> None:
        try:
            port_scan_result = asyncio.run(self._host_scan_service.scan_host_tcp_ports(self.host))
            open_ports = set(port_scan_result.open_tcp_ports)

            if open_ports == self.expected_open_ports:
                self._logger.info(
                    "Host %s has all expected ports open: %s",
                    self.host,
                    ",".join(self.expected_open_ports))
                return

            message_subject = f"Host availability check {self.name}: Unexpected scan results"
            message_str = create_heading_two(f"Unexpected scan results for host {self.name}")
            missing_open_ports = self.expected_open_ports - open_ports
            if missing_open_ports:
                self._logger.info("Host %s is missing expected TCP ports: %s", self.host, missing_open_ports)
                message_str += create_paragraph(f"{self.host}: Missing open TCP ports: {missing_open_ports}")

            unexpected_open_ports = open_ports - self.expected_open_ports
            if unexpected_open_ports:
                self._logger.info("Host %s has unexpected open TCP ports: %s", self.host, unexpected_open_ports)
                message_str += create_paragraph(f"{self.host}: Unexpected open TCP ports: {unexpected_open_ports}")

            self._email_client.send_email(EmailMessage(subject=message_subject, body=message_str))
        except Exception as ex:
            raise FeedCheckFailedError(
                f"Error checking host {self.host}: {ex}"
            ) from ex
