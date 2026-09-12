"""
Small utility module, not a scraper itself: wraps requests.get() with two
things every scraper in this repo (except books_spider.py, where Scrapy
does both by default) was missing so far — checking robots.txt before
fetching, and retrying on a failed/rate-limited request with backoff.

Deliberately hand-rolled instead of pulling in a library (e.g. `tenacity`
for retries) — both of these are genuinely small enough to write directly,
and it's worth understanding what they actually do rather than treating
them as a decorator you trust blindly.
"""
import time
import urllib.robotparser
from urllib.parse import urlparse

import requests

_robot_parsers = {}  # one urllib.robotparser per domain, cached so we don't refetch robots.txt every call


def is_allowed(url, user_agent="*"):
    """Check the target site's robots.txt before fetching a URL."""
    domain = urlparse(url)._replace(path="", params="", query="", fragment="").geturl()
    if domain not in _robot_parsers:
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(domain + "/robots.txt")
        try:
            parser.read()
        except OSError:
            # no robots.txt, or couldn't fetch it — treat as "allowed"
            # rather than blocking on a network hiccup fetching the rules
            parser = None
        _robot_parsers[domain] = parser

    parser = _robot_parsers[domain]
    return parser.can_fetch(user_agent, url) if parser else True


def get_with_retry(url, max_attempts=3, backoff_seconds=1, **kwargs):
    """
    requests.get(), but retries with exponential backoff on connection
    errors, timeouts, 429 (rate-limited), and 5xx (server error).

    Deliberately does NOT raise on other non-2xx statuses like 404 — those
    are usually a meaningful, expected response (e.g. "you've paginated
    past the last page"), not a transient failure worth retrying. Callers
    check response.status_code themselves, same as plain requests.get().
    """
    if not is_allowed(url):
        raise PermissionError(f"robots.txt disallows fetching: {url}")

    last_exception = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url, **kwargs)
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(f"got {response.status_code}", response=response)
            return response
        except (requests.RequestException,) as exc:
            last_exception = exc
            if attempt < max_attempts:
                wait = backoff_seconds * (2 ** (attempt - 1))
                print(f"  request failed ({exc}), retrying in {wait}s (attempt {attempt}/{max_attempts})")
                time.sleep(wait)
    raise last_exception
