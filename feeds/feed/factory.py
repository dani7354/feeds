from enum import StrEnum
from typing import Any

from feeds.email.client import EmailClient
from feeds.feed.base import FeedChecker
from feeds.feed.host import HostAvailabilityCheck
from feeds.feed.rss import RSSFeedChecker
from feeds.feed.web import (
    UrlAvailabilityChecker,
    PageContentChecker,
    PageContentCheckerDynamic,
)
from feeds.http.client import HTTPClientBase, HTTPClientDynamicBase
from feeds.http.log import RequestLogService
from feeds.service.host_scan import HostScanService
from feeds.shared.config import ConfigKeys


class FeedFactoryError(Exception):
    pass


class FeedType(StrEnum):
    RSS = "rss"
    WEB_AVAILABILITY = "web_availability"
    WEB_CONTENT = "web_content"
    WEB_CONTENT_DYNAMIC = "web_content_dynamic"
    HOST_AVAILABILITY = "host_availability"


def create_feed_checkers(
        feeds_by_type: dict[str, list[dict[str, Any]]],
        email_client: EmailClient,
        http_client: HTTPClientBase,
        http_client_dynamic: HTTPClientDynamicBase,
        host_scan_service: HostScanService,
) -> list[FeedChecker]:
    feed_checkers = []
    for feed_type, feeds in feeds_by_type.items():
        if feed_type == FeedType.RSS:
            feed_checkers.extend(RSSFeedChecker(email_client, http_client, feed) for feed in feeds)
        elif feed_type == FeedType.WEB_AVAILABILITY:
            feed_checkers.extend(
                UrlAvailabilityChecker(
                    email_client,
                    http_client,
                    RequestLogService(feed[ConfigKeys.DIR]),
                    feed,
                )
                for feed in feeds
            )
        elif feed_type == FeedType.WEB_CONTENT:
            feed_checkers.extend(
                PageContentChecker(
                    email_client,
                    http_client,
                    RequestLogService(feed[ConfigKeys.DIR]),
                    feed,
                )
                for feed in feeds
            )
        elif feed_type == FeedType.WEB_CONTENT_DYNAMIC:
            feed_checkers.extend(
                PageContentCheckerDynamic(
                    email_client,
                    http_client_dynamic,
                    RequestLogService(feed[ConfigKeys.DIR]),
                    feed,
                )
                for feed in feeds
            )
        elif feed_type == FeedType.HOST_AVAILABILITY:
            feed_checkers.extend(HostAvailabilityCheck(host_scan_service, email_client, feed) for feed in feeds)
        else:
            raise FeedFactoryError(f"Unknown feed type: {feed_type}")

    return feed_checkers
