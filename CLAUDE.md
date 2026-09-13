# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A collection of standalone Python scripts, each demonstrating one scraping
technique/decision against a real target — mostly the toscrape.com sandbox
sites (built for scraping practice, so no ToS concern), plus Hacker News'
official public API, GitHub's API, and a bot-detection diagnostic site. It is
not a package or an app; there's no shared entrypoint. Each script is a
self-contained lesson, listed with its target/approach/rationale in the table
in `README.md`. `TODO.md` tracks what's done and what's deliberately out of
scope — check it before assuming a technique (e.g. TLS-fingerprint spoofing,
stealth tricks against a real protected production site) is missing rather
than intentionally excluded.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Running scripts

Always `source .venv/bin/activate` first. Each script is run directly and
writes its own output file (CSV or SQLite db) — see the table in
`README.md` for the exact target/output of each one. Two scripts take CLI
args instead of hardcoded constants:

```
python scrape_hackernews.py --limit 100 --out top100.csv
python track_hackernews.py --limit 50 --db custom.db
```

`scrape_github.py` requires `gh auth token` to already be authenticated in
this environment (it reads the token via `gh`, never hardcodes or logs it).

## Tests

```
pytest -v
```

Tests (`test_parsing.py`) run only against saved fixtures in `fixtures/`
(`books_page1.html`, `hn_sample.json`) — no network access, so they're safe
to run anytime. To run a single test: `pytest -v test_parsing.py::test_name`.

## Architecture notes

- **Parsing is separated from fetching wherever it's tested.** `scrape_books.py`
  exposes `parse_books(html)` as a pure function independent of the network
  call; `scrape_hackernews.py` exposes `stories_to_rows(raw_stories)` the
  same way. This split was a deliberate refactor (pulling transformation
  logic out of an async fetch function) specifically so `test_parsing.py`
  could test it without mocking the network — follow the same pattern for
  any new scraper: keep "parse this HTML/JSON I already have" separable
  from "go get it over the network."
- **Scripts reuse each other rather than duplicating fetch/parse logic.**
  `scrape_books_db.py` imports `scrape_all_books()` from `scrape_books.py`;
  `track_hackernews.py` shares `DEFAULT_STORY_LIMIT` and
  `stories_to_rows()` with `scrape_hackernews.py`. When adding a new
  storage backend or variant for an existing target, import the existing
  fetch/parse function rather than rewriting it.
- **`polite_requests.py` is the shared politeness layer for plain-`requests`
  scripts** — robots.txt checking (`is_allowed()`) and retry-with-backoff
  (`get_with_retry()`). It deliberately does *not* retry/raise on a plain
  404, since `scrape_books.py` relies on a 404 response (not an exception)
  to detect "past the last page." Scrapy-based scripts (`books_spider.py`)
  get robots.txt handling and encoding-correct decoding for free from the
  framework instead and don't need this wrapper.
- **Storage pattern depends on whether the data changes over time.**
  One-shot/catalogue data (books, GitHub repos) uses a
  DELETE-then-reinsert-on-each-run SQLite table or plain CSV.
  `track_hackernews.py` is the exception: it's built for data that changes
  between runs, using two tables with different write semantics —
  `stories` (UPSERT, keyed on HN's story id, never duplicates) and
  `score_snapshots` (plain APPEND, one row per run, so history
  accumulates). Use the UPSERT+APPEND pattern for any future target whose
  values change over time; use DELETE+reinsert for static catalogues.
- **Encoding correctness is a known gotcha with plain `requests`.**
  `books.toscrape.com` doesn't declare a charset in its response headers,
  so `requests`'s auto-detection mis-guesses and silently corrupts `£`
  into `Â£` with no error. Fix is explicit: `response.encoding = "utf-8"`
  before reading `.text`. Scrapy does not have this problem (handles it
  correctly by default) — worth remembering when choosing between the two
  approaches for a new static-HTML target.
- **Before scraping a new real (non-sandbox) target**, this repo's own
  precedent (`scrape_hackernews.py`) checks, in order, before writing any
  code: is the data public / no login wall; is there a sanctioned API
  instead of raw HTML scraping; does `robots.txt` forbid it; is there a
  published rate limit (self-impose one if not). Follow the same sequence
  rather than writing the scraper first.
- **Anti-bot/stealth techniques are scoped to sanctioned diagnostic
  targets only.** `bot_detection_test.py` measures headless-browser
  fingerprinting and `playwright-stealth`'s effect against
  `bot.sannysoft.com`, a site built for exactly this self-check.
  Deliberately out of scope (per `TODO.md`, twice): pointing
  stealth/fingerprint-spoofing techniques (e.g. `curl_cffi`) at an actual
  real site that put up protection on purpose. Don't extend this repo's
  techniques toward a real protected production target.
