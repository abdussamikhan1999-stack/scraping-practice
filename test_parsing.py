"""
Tests for the parsing/transformation logic in this repo — deliberately
NOT hitting the network. Real scraping tests belong at two different
levels:
  1. "Does my parsing logic correctly extract fields from HTML/JSON I
     already have?" — testable against a saved fixture, fast, and won't
     break just because a live site went down or changed unrelated to
     what you're testing.
  2. "Is the live site still shaped the way I expect?" — a genuinely
     different concern (this repo doesn't have that layer; it would need
     to hit the network on purpose, on some slower schedule, not on every
     test run).
This file is entirely level 1.

Run with: pytest -v
"""
from scrape_books import parse_books
from scrape_books_db import price_to_float
from scrape_hackernews import stories_to_rows

import json


def test_parse_books_extracts_expected_fields():
    with open("fixtures/books_page1.html", encoding="utf-8") as f:
        html = f.read()

    books = parse_books(html)

    assert len(books) == 20  # books.toscrape.com shows 20 per page
    first = books[0]
    assert first["title"] == "A Light in the Attic"
    assert first["price"] == "£51.77"
    assert first["rating"] == 3


def test_parse_books_all_ratings_are_valid():
    with open("fixtures/books_page1.html", encoding="utf-8") as f:
        html = f.read()

    books = parse_books(html)

    # every rating should have matched a known word (One..Five), not
    # silently fallen back to the "unrecognized" default of 0
    assert all(1 <= b["rating"] <= 5 for b in books)


def test_price_to_float_strips_currency_symbol():
    assert price_to_float("£51.77") == 51.77
    assert price_to_float("£9.00") == 9.00


def test_stories_to_rows_extracts_known_story():
    with open("fixtures/hn_sample.json", encoding="utf-8") as f:
        raw_stories = json.load(f)

    rows = stories_to_rows(raw_stories)

    yc_story = next(r for r in rows if r["title"] == "Y Combinator")
    assert yc_story["author"] == "pg"
    assert yc_story["score"] == 57
    assert yc_story["url"] == "http://ycombinator.com"


def test_stories_to_rows_handles_missing_url():
    """Text/'Ask HN' posts have no url field at all — must not KeyError."""
    with open("fixtures/hn_sample.json", encoding="utf-8") as f:
        raw_stories = json.load(f)

    rows = stories_to_rows(raw_stories)

    ask_hn = next(r for r in rows if "Ask HN" in r["title"])
    assert ask_hn["url"] == ""


def test_stories_to_rows_filters_out_deleted_stories():
    """A deleted story comes back as JSON null, not a dict — must be dropped, not crash."""
    with open("fixtures/hn_sample.json", encoding="utf-8") as f:
        raw_stories = json.load(f)

    assert None in raw_stories  # confirms the fixture actually exercises this case
    rows = stories_to_rows(raw_stories)

    assert len(rows) == 2  # the two real stories, not the null
