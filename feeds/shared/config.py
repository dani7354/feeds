from enum import StrEnum


class ConfigKeys(StrEnum):
    URL = "url"
    DIR = "data_dir"
    NAME = "name"
    EXPECTED_STATUS_CODE = "expected_status_code"
    CSS_SELECTOR = "css_selector"
    CSS_SELECTOR_LOADED = "css_selector_loaded"
    CSS_SELECTOR_CONTENT = "css_selector_content"
    SAVED_FEEDS_COUNT = "saved_feeds_count"
    HOST = "host"
    EXPECTED_OPEN_PORTS = "expected_open_ports"
