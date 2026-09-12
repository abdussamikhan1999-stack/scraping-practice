# Scraping Practice

Web scraping practice on the toscrape.com sandbox sites — built
specifically for practicing scraping, so there's no ToS concern. Four
scripts, covering the core decision tree for "how do I scrape this":

| Script | Target | Approach | Why |
|---|---|---|---|
| `scrape_books.py` | books.toscrape.com | `requests` + BeautifulSoup | Static HTML — content is already in the page source, no need for a browser |
| `scrape_quotes_js.py` | quotes.toscrape.com/js | Playwright | JS-rendered — the raw HTML is empty, content is filled in by a script after load, so a real browser is required |
| `discover_api.py` | quotes.toscrape.com/scroll | Playwright (network logging) | Not a scraper — opens the page and logs every XHR/fetch response, to find a hidden JSON API instead of guessing |
| `scrape_quotes_api.py` | quotes.toscrape.com/scroll | `requests` (hitting the API `discover_api.py` found) | Same data as the JS scraper, but no browser at all — see the comparison below |
| `scrape_quotes_login.py` | quotes.toscrape.com/login | `requests.Session()` | Login-gated — some content is only visible once authenticated |
| `scrape_quotes_concurrent.py` | quotes.toscrape.com/scroll | `httpx` + `asyncio` | Fetches pages in parallel batches instead of one at a time — see the timing comparison below |
| `books_spider.py` | books.toscrape.com | Scrapy | Same catalogue as `scrape_books.py`, rebuilt as a proper Scrapy spider instead of a hand-rolled loop |
| `polite_requests.py` | (utility, not a scraper) | `requests` + `urllib.robotparser` | Wraps `requests.get()` with a real robots.txt check and retry-with-backoff; used by `scrape_books.py` |
| `scrape_hackernews.py` | Hacker News (real site) | `httpx` + `asyncio` | The first non-sandbox target — Hacker News' own official public API, not scraped HTML |
| `scrape_books_db.py` + `query_books.py` | books.toscrape.com | `sqlite3` | Same books data as `scrape_books.py`, stored in SQLite instead of CSV, plus real SQL queries on top |
| `scrape_github.py` | GitHub API (your own account) | `requests` + real OAuth token | A genuinely authenticated login, replacing `scrape_quotes_login.py`'s fake one — fetches data only this account can see |

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Run

```
source .venv/bin/activate
python scrape_books.py       # -> books.csv (1000 books, title/price/rating)
python scrape_quotes_js.py   # -> quotes.csv (100 quotes, text/author/tags)
python discover_api.py       # -> prints the JSON API URL it finds, nothing saved
python scrape_quotes_api.py  # -> quotes_api.csv (same 100 quotes, no browser)
python scrape_quotes_login.py  # -> quotes_login.csv (same quotes + goodreads_link, only visible logged in)
python scrape_quotes_concurrent.py  # -> quotes_concurrent.csv (same quotes, ~9x faster)
scrapy runspider books_spider.py -o books_scrapy.csv  # -> same 1000 books, via Scrapy
python scrape_hackernews.py  # -> hackernews.csv (top 30 HN stories, real site)
python scrape_books_db.py    # -> books.db (same 1000 books, in SQLite)
python query_books.py        # -> runs real SQL queries against books.db
python scrape_github.py       # -> github_repos.csv (your own repos, via authenticated API)
```

## Lessons learned

- **`scrape_books.py`**: the server doesn't declare a charset in its
  response headers, so `requests`'s encoding auto-detection guessed wrong
  and mangled the `£` symbol into `Â£` in every price. Fix: explicitly set
  `response.encoding = "utf-8"` before reading `.text`. This kind of silent
  mis-decoding won't throw an error — it'll just quietly corrupt your data.
- **`scrape_quotes_js.py`**: confirms why the static approach doesn't work
  here — if you `requests.get()` this URL and look at the raw HTML, the
  quote content isn't there at all; it only appears after Playwright waits
  for `div.quote` to render. Pagination here is also different: instead of
  building a URL for each page number, you click the actual "Next" link
  and wait for the new content to load, the same way you'd navigate in a
  Selenium test.
- **`discover_api.py`**: first tried this against a different site
  (scrapingclub.com's infinite-scroll exercise) and got nothing useful —
  turned out that site sits behind Cloudflare and returns a flat 403 to
  `requests` entirely (a real anti-bot wall, not a code bug — this is
  exactly the TLS-fingerprinting problem `curl_cffi` exists to solve, per
  the `/scrp/` notes). Switched targets to `quotes.toscrape.com/scroll`,
  which has no such protection, and found a clean paginated JSON endpoint:
  `https://quotes.toscrape.com/api/quotes?page=N`, with a `has_next` flag
  telling you when to stop.
- **`scrape_quotes_api.py`**: same 100 quotes as `scrape_quotes_js.py`, but
  measure *CPU time*, not just wall-clock, to see the real cost difference:

  | | wall-clock | user CPU | sys CPU |
  |---|---|---|---|
  | `scrape_quotes_api.py` (requests) | 11.2s | 0.28s | 0.02s |
  | `scrape_quotes_js.py` (Playwright) | 16.9s | 5.74s | 1.49s |

  Wall-clock looks similar at this tiny scale (15 pages) because both are
  mostly waiting on the network either way. **CPU time is the real story**:
  over 20x more CPU spent per page just to launch and drive a browser vs.
  a plain HTTP GET. That gap is invisible on one small script running
  locally — it's the whole story once you're running hundreds of
  concurrent scrape jobs and paying for compute.
- **`scrape_quotes_login.py`**: fetch the login page, pull the
  `csrf_token` hidden input out of the form with BeautifulSoup, POST it
  back alongside `username`/`password` (any values work on this sandbox —
  it's not checking a real user database) on a `requests.Session()`, then
  reuse that *same* session for every later request — the session object
  carries the resulting auth cookie automatically, you never touch it by
  hand. To confirm logging in actually did something (rather than just
  logging in for its own sake), diffed the logged-in vs. logged-out HTML
  byte-for-byte: logged-out pages only link to each quote's `(about)`
  page, while logged-in pages add a second `(Goodreads page)` link per
  quote pointing at the real goodreads.com author page. The scraper
  captures that extra `goodreads_link` field — the concrete, checked
  reason this login step is worth doing at all, not an assumption.
- **`scrape_quotes_concurrent.py`**: same data as `scrape_quotes_api.py`,
  but fetches pages in concurrent batches of 5 with `httpx.AsyncClient` +
  `asyncio.gather` instead of one at a time. The catch: you don't know the
  total page count up front (it's discovered one `has_next` flag at a
  time), so this fetches a batch of page numbers speculatively and stops
  once a batch comes back with no more pages needed — checked first that
  requesting an out-of-range page number (e.g. page 100) returns a normal
  `200` with an empty quote list rather than an error, so slightly
  over-fetching past the real last page is harmless. The result, run
  back-to-back on the same machine:

  | | wall-clock | user CPU |
  |---|---|---|
  | `scrape_quotes_api.py` (sequential) | 14.9s | 0.32s |
  | `scrape_quotes_concurrent.py` (batches of 5) | 1.7s | 0.17s |

  **~8.8x faster wall-clock, for slightly *less* CPU** — concurrency here
  is close to a free win, because the bottleneck was never CPU, it was
  waiting on the network one request at a time. This is the clearest
  lesson in this repo so far: sequential I/O-bound loops waste almost all
  their wall-clock time doing nothing but waiting.
- **`books_spider.py`**: the same 1000 books as `scrape_books.py`, but
  what Scrapy gives you for free versus the hand-rolled version is the
  actual lesson here, not the data itself:
  - `ROBOTSTXT_OBEY = True` is the *default* — Scrapy checked
    `books.toscrape.com/robots.txt` on its own before crawling anything
    (visible in the run stats as `robotstxt/request_count: 1`); the
    `scrape_books.py`/`polite_requests.py` version had to be built by hand.
  - `response.follow(next_page)` replaces manually formatting a
    `page-{n}.html` URL string.
  - `-o books_scrapy.csv` replaces the entire `csv.DictWriter` block.
  - The `£` encoding bug from `scrape_books.py` **did not happen here** —
    Scrapy's response decoding handled it correctly with zero extra code,
    unlike plain `requests` which needed an explicit `response.encoding =
    "utf-8"` fix.
  The honest tradeoff: Scrapy has real conceptual overhead (its own spider/
  callback/settings model) that isn't worth it for a 20-line one-off script
  — it earns its keep once a crawl is big enough, or long-lived enough,
  that retries/concurrency/robots.txt/encoding-correctness being handled
  for you actually matters.
- **`polite_requests.py`**: a small wrapper adding what `books_spider.py`
  gets for free from Scrapy, to the plain-`requests` scripts instead.
  Verified both pieces actually work rather than trusting the code by
  inspection alone:
  - `is_allowed()` correctly returned `False` for `google.com/search`
    (Google's robots.txt disallows that path for most agents) and `True`
    for `google.com/` — proof it's a real check, not a function that
    always returns `True`.
  - `get_with_retry()` against a reliable always-500 test endpoint
    (`httpbin.org/status/500`) retried twice with correctly-doubling
    backoff (0.3s → 0.6s) before raising, confirming the exponential
    backoff math and the attempt-count limit both work as written.
  - Deliberately does *not* raise on a 404 — `scrape_books.py` relies on
    getting a plain 404 response back (not an exception) to detect "past
    the last page," so only 429/5xx/connection errors trigger a retry.
- **`scrape_hackernews.py`**: the first real (non-sandbox) target,
  checked against the `/scrp/` notes' legal-risk factors *before* writing
  any code, not after:
  - Public data, no login wall.
  - Not scraping HTML at all — Hacker News' own GitHub
    (`github.com/HackerNews/API`) documents and endorses this exact API
    specifically so third parties don't have to scrape their pages. This
    is the sanctioned access method, not a workaround.
  - `hacker-news.firebaseio.com/robots.txt` is a 404 (checked directly) —
    nothing to violate, and no rate limit is published, so this
    self-imposes one anyway (`STORY_LIMIT = 30`, not the full ~500-story
    list) rather than assuming unlimited access is fine just because
    nothing stops it technically.
  - Reuses the concurrency pattern from `scrape_quotes_concurrent.py`:
    fetching each of the 30 stories' details one at a time would be the
    same slow, network-idle pattern that script measured — so this
    fetches them concurrently with `httpx` + `asyncio.gather` from the
    start, rather than writing the slow version first.
  - Handles two edge cases the toscrape.com sandbox never has: a story
    can be `None` if it was deleted between the two API calls (filtered
    out), and text/"Ask HN" posts have no `url` field at all (`.get(...,
    "")` instead of `s["url"]`, which would `KeyError`). Worth being
    honest that this particular run's top 30 didn't happen to include a
    text post, so that specific branch is defensively correct by
    inspection, not something this run actually exercised.
- **`scrape_books_db.py` / `query_books.py`**: reuses
  `scrape_books.py`'s own `scrape_all_books()` instead of duplicating the
  fetch/parse logic — the only new thing here is *where the data ends
  up*. Price is converted from `"£51.77"` (a string) to `51.77` (a real
  `REAL` column) at write time — the schema enforces this once, instead
  of every reader having to re-parse the currency string themselves.
  Re-running the script `DELETE`s and re-inserts rather than appending, so
  it's safe to run repeatedly without accumulating duplicates. Verified
  `query_books.py`'s "top 5 most expensive" result against an independent
  sort of `books.csv` in plain Python — identical top 5, in the same
  order, confirming the SQL result is actually correct and not just
  plausible-looking.
- **`scrape_github.py`**: `scrape_quotes_login.py`'s login is fake — any
  password works, so it never actually proves auth is doing anything.
  This one is real: fetches the token this environment's `gh` CLI is
  already authenticated with (`gh auth token`, never printed/logged/
  written to any file — checked with `grep` for the token prefix across
  every file in the repo afterward, found nothing) and requests
  `/user/repos`. Concrete proof the auth is real and not a no-op: the
  response included **1 private repo** — something GitHub's API would
  simply omit for an unauthenticated request. That's the actual point of
  this script; the CSV of repo names is secondary to that.
