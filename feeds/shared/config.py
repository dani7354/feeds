from enum import StrEnum


class ConfigKeys(StrEnum):
    URL = "url"
    DIR = "data_dir"
    NAME = "name"
    EXPECTED_STATUS_CODE = "expected_status_code"
    CSS_SELECTOR = "css_selector"
    SAVED_FEEDS_COUNT = "saved_feeds_count"
