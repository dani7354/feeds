class FeedCheckFailedError(Exception):
    pass


class FeedChecker:
    def __init__(self, config: dict):
        self.config = config

    @property
    def name(self) -> str:
        return self.config["name"]

    def check(self) -> None:
        """Should be overwritten by subclasses"""
        raise NotImplementedError
