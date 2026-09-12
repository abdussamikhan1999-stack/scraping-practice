# TODO

Next steps for this scraping-practice project, roughly in order.

## Next up

- [ ] **Pin dependencies** — add a `requirements.txt` so the environment
  is reproducible instead of "whatever was installed in this session."
- [ ] **SQLite storage** — refactor at least one scraper to write into a
  local SQLite database instead of a CSV, plus a small script that runs
  an actual SQL query against the result (e.g. "top 5 most expensive
  books"), to see what a real query engine gives you over grepping a CSV.
- [ ] **A real, genuinely authenticated real-login target** — the
  `scrape_quotes_login.py` login is fake (any password works). Use the
  GitHub API with the `gh` CLI's already-configured auth token to fetch
  real, private-to-this-account data (e.g. your own repo list) — a
  genuinely authenticated request against a real service, with zero
  legal/ethical ambiguity since it's your own account's own data via the
  official API.
- [ ] **Automated tests for the scrapers** — write pytest tests for the
  parsing logic specifically (not hitting the network on every test run —
  test against saved fixture HTML/JSON instead), since verifying
  extraction logic without depending on a live site staying unchanged is
  the actual QA-relevant skill here.

## Deliberately not doing this round

- Anti-bot/stealth-browser tricks (`curl_cffi`, `camoufox`, etc.) against
  a real protected site — riskier to demonstrate responsibly than the
  items above, and `discover_api.py` already showed the alternative
  (detect the wall, retarget) rather than trying to push through one.

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
