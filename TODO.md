# TODO

Next steps for this scraping-practice project, roughly in order.

## Next up

- [ ] **A real (not sandbox) target** — pick one real site and actually
  apply the `/scrp/` notes' legal-risk checklist (public data, no login,
  no hammering the server) before scraping it for real. This is the last
  item — everything else on this list is done.

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
