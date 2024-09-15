import dataclasses
import logging
import os
import time
import xml.etree.ElementTree as ET
from enum import IntEnum
from tempfile import TemporaryDirectory

from slugify import slugify


class HostStatus(IntEnum):
    DOWN = 0
    UP = 1
    UNKNOWN = 2


@dataclasses.dataclass
class HostScanResult:
    host: str
    status: HostStatus
    open_tcp_ports: list[int]
    filtered_ports: list[int]


class HostScanService:
    async def scan_host_tcp_ports(self, host: str) -> HostScanResult:
        """ Scan host for open and filtered TCP ports. """
        raise NotImplementedError


class NmapScanService(HostScanService):
    def __init__(self):
        self._logger = logging.getLogger("NmapScanService")
        self._cmd = "nmap -vv -Pn -sT -p0-65535 {host} -oX {xml_file}"

    async def scan_host_tcp_ports(self, host: str) -> HostScanResult:
        time_start = time.perf_counter()
        with TemporaryDirectory() as temp_dir:
            temp_scan_result_file = os.path.join(temp_dir, f"nmap_scan_result_{slugify(host)}_{time.time_ns()}.xml")
            cmd = self._cmd.format(host=host, xml_file=temp_scan_result_file)
            self._logger.info("Scanning host %s. Result will be saved to %s.", host, temp_scan_result_file)
            exit_code = os.system(cmd)
            if exit_code != 0:
                raise RuntimeError(
                    f"Failed to scan host {host} with nmap. Maybe nmap is missing Exit code: {exit_code}")

            self._logger.info("Scan finished")
            scan_result = await self._parse_scan_result(temp_scan_result_file, host)
            self._logger.info("Scan finished in %s seconds", time.perf_counter() - time_start)
            return scan_result[0]

    async def _parse_scan_result(self, scan_result_file: str, host: str) -> list[HostScanResult]:
        self._logger.info("Parsing scan result from %s", scan_result_file)
        with open(scan_result_file, "r", encoding="utf-8") as f:
            result_xml = ET.parse(f)
            host_results = []
            for host_node in result_xml.findall(".//host"):
                host_ip = await self._read_ip_address(host_node)
                if not host_ip:
                    self._logger.warning("Host without IP address found. Skipping")
                    host_results.append(
                        HostScanResult(
                            host=host,
                            status=HostStatus.UNKNOWN,
                            open_tcp_ports=[],
                            filtered_ports=[]))
                    continue

                open_ports, filtered_ports = await self._read_open_and_filtered_ports(host_node)
                host_status = HostStatus.UP if open_ports or filtered_ports else HostStatus.DOWN
                host_results.append(
                    HostScanResult(
                        host=host,
                        status=host_status,
                        open_tcp_ports=open_ports,
                        filtered_ports=filtered_ports))

        self._logger.info("Parsing finished. Found %s hosts", len(host_results))

        return host_results

    @staticmethod
    async def _read_ip_address(node: ET.Element) -> str | None:
        if (ip_node := node.find("address[@addrtype='ipv4']")) is None:
            return None

        return ip_node.attrib["addr"]

    @staticmethod
    async def _read_open_and_filtered_ports(node: ET.Element) -> tuple[list[int], list[int]]:
        open_ports, filtered_ports = [], []
        for port in node.findall(".//port"):
            port_number = int(port.attrib["portid"])
            state = port.find("state").attrib["state"]
            if state == "open":
                open_ports.append(port_number)
            elif state == "filtered":
                filtered_ports.append(port_number)

        return open_ports, filtered_ports
