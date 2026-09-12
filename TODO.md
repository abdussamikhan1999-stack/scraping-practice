# TODO

Next steps for this scraping-practice project, roughly in order.

## Next up

Nothing queued — this (fourth) round is complete too. One good candidate
for a future round: actually scheduling `track_hackernews.py` (cron or
similar) to run periodically and build up real multi-day history instead
of the two-runs-12-seconds-apart demo this round produced.

## Deliberately still not doing

- `curl_cffi`/TLS-fingerprint spoofing, or stealth tricks aimed at an
  actual real protected production site — `bot_detection_test.py`
  covered the *underlying mechanism* (what a headless browser reveals,
  and what stealth patching changes) against a sanctioned diagnostic
  target instead. Actually pointing that at a real site whose owner put
  up protection on purpose is still a different, more deliberately
  adversarial thing than anything else in this repo, and stays out of
  scope here.

## Done

- [x] Static-site scraping with `requests` + BeautifulSoup
  (`scrape_books.py`) — hit and fixed a charset-detection bug.
- [x] JS-rendered scraping with Playwright (`scrape_quotes_js.py`).
- [x] Finding a hidden JSON API via network-response logging
  (`discover_api.py`) instead of guessing — including a real detour
  around a Cloudflare-protected site that flat-out 403s plain `requests`.
- [x] Hitting that API directly (`scrape_quotes_api.py`) and measuring
  the real CPU-cost difference vs. driving a browser.
- [x] Login-gated scraping (`scrape_quotes_login.py`) — CSRF token
  handling, `requests.Session()`, and confirming (by diffing HTML) that
  logging in actually unlocks a real extra field before assuming it does.
- [x] Concurrency (`scrape_quotes_concurrent.py`) — `httpx` + `asyncio`,
  ~8.8x faster wall-clock than the sequential version for less CPU.
- [x] Scrapy (`books_spider.py`) — rebuilt the books scraper as a proper
  spider; robots.txt handling and correct encoding came for free, which
  the hand-rolled version had to build/fix manually.
- [x] robots.txt handling + retry-with-backoff (`polite_requests.py`) —
  wrapped into `scrape_books.py`; both pieces verified against real
  endpoints (a known robots.txt-disallowed Google path, and a reliable
  always-500 test endpoint), not just trusted by inspection.
- [x] A real (non-sandbox) target (`scrape_hackernews.py`) — Hacker
  News' official public API, checked against the legal-risk checklist
  first (public, no login, sanctioned access method, no robots.txt to
  violate, self-imposed a request cap since HN doesn't publish one).
  Reused the concurrency pattern from `scrape_quotes_concurrent.py`
  rather than writing a slow version first.
- [x] Pin dependencies (`requirements.txt`) — verified reproducible in a
  completely fresh venv, not just the one already set up.
- [x] SQLite storage (`scrape_books_db.py` + `query_books.py`) — reused
  `scrape_books.py`'s own parsing logic; verified the SQL "top 5 most
  expensive" result against an independent Python sort of `books.csv`.
- [x] A real, genuinely authenticated target (`scrape_github.py`) — the
  GitHub API via the `gh` CLI's existing token; found 1 private repo,
  proving the auth is real and not a no-op like the sandbox's fake login.
  Confirmed the token itself never got printed/logged/written anywhere.
- [x] Automated tests (`test_parsing.py`) — pytest against fixtures
  (`fixtures/`), no network required. Required pulling
  `scrape_hackernews.py`'s row-transformation logic out into a separate
  pure function first so it was testable at all. Verified the tests
  actually catch a regression, not just that they pass: deliberately
  broke `parse_books()`, watched 2/6 tests fail correctly, restored it.
- [x] Incremental/upsert database updates (`track_hackernews.py` +
  `query_hackernews_history.py`) — `stories` table UPSERTs (never
  duplicates), `score_snapshots` table APPENDs (never overwrites, so
  history actually accumulates). Verified by running it twice: `stories`
  stayed at exactly 30 rows both times, `score_snapshots` grew 30 → 60.
- [x] Proper CLI (`--limit`/`--out`/`--db` via `argparse`) on
  `scrape_hackernews.py` and `track_hackernews.py`, replacing the
  hardcoded `STORY_LIMIT` constant. Verified the existing test suite
  still passes, a custom `--limit 5` produced exactly 5 rows, and
  `--help` prints correctly.
- [x] The bot-detection/stealth-browser lesson (`bot_detection_test.py`)
  — reframed onto `bot.sannysoft.com` (a sanctioned diagnostic site) since
  a real protected site was deliberately out of scope twice already.
  Measured, not assumed: 6 of 7 tracked signals changed between default
  headless Playwright and `playwright-stealth` applied, reproduced by
  running it twice with identical results. Reported honestly that one
  changed value (`Permissions: prompt -> denied`) isn't an obvious
  improvement, unlike the other five.
