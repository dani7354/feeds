import logging
import os
from datetime import datetime


class RequestLogService:
    _request_log_base_filename: str = "requests"
    _log_encoding: str = "utf-8"
    _cell_delimiter: str = ";"

    def __init__(self, request_log_dir: str) -> None:
        self._request_log_dir = request_log_dir
        self._logger = logging.getLogger("RequestLogService")
        self.request_log = None
        self._rotate_log_file_if_needed()

    def log_request(self, *values) -> None:
        self._rotate_log_file_if_needed()
        with open(self.request_log, "a", encoding=self._log_encoding) as file:
            self._logger.debug("Writing to %s...", self.request_log)
            record = (f"{datetime.now().isoformat()}{self._cell_delimiter}"
                      f"{self._cell_delimiter.join(str(value) for value in values)}\n")
            file.write(record)

    def get_last_request_value(self, value_index: int = 0) -> str | None:
        if not self.request_log or not os.path.exists(self.request_log):
            self._logger.warning("Request log %s doesn't exist!", self.request_log)
            return None

        with open(self.request_log, "r", encoding=self._log_encoding) as file:
            if not (lines := file.readlines()):
                return None
            return lines[-1].split(self._cell_delimiter)[value_index]

    def _rotate_log_file_if_needed(self) -> None:
        date_str = datetime.now().strftime("%Y-%m")
        if self.request_log and date_str in os.path.basename(self.request_log):
            return

        new_log_filename = os.path.join(self._request_log_dir, f"{self._request_log_base_filename}_{date_str}.log")
        self._logger.debug("Rotating log file to %s...", new_log_filename)
        self.request_log = new_log_filename
