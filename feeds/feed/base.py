from enum import StrEnum


class FeedCheckFailedError(Exception):
    pass


class FeedSchedule(StrEnum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class FeedChecker:
    def __init__(self, config: dict):
        self.config = config

    @property
    def name(self) -> str:
        return self.config["name"]

    @property
    def schedule(self) -> FeedSchedule:
        return FeedSchedule(self.config["schedule"])

    def check(self) -> None:
        """Should be overwritten by subclasses"""
        raise NotImplementedError
