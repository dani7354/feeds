from enum import Enum, StrEnum
from typing import Any
from feeds.feed.base import FeedChecker
from feeds.feed.rss import RSSFeedChecker
from feeds.email.client import EmailClient
from feeds.http.client import HTTPClientBase


class FeedFactoryError(Exception):
    pass


class FeedType(StrEnum):
    RSS = "rss"


def create_feed_checkers(
        feeds_by_type: dict[str, list[dict[str, Any]]],
        email_client: EmailClient,
        http_client: HTTPClientBase) -> list[FeedChecker]:
    feed_checkers = []
    for feed_type, feeds in feeds_by_type.items():
        if feed_type == FeedType.RSS:
            feed_checkers.extend(RSSFeedChecker(email_client, http_client, feed) for feed in feeds)
        else:
            raise FeedFactoryError(f"Unknown feed type: {feed_type}")

    return feed_checkers
