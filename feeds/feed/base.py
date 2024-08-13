from feeds.email.client import EmailClient


class FeedCheckFailedError(Exception):
    pass


class FeedChecker:
    def __init__(self, config: dict):
        self.config = config

    def check(self) -> None:
        """ Should be overwritten by subclasses """
        raise NotImplementedError
