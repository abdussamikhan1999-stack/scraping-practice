# TODO

Next steps for this scraping-practice project, roughly in order.

## Next up

- [ ] **Concurrency** — right now every scraper fetches pages one at a
  time. Try `httpx` with `asyncio` (or a thread pool) to fetch multiple
  pages in parallel and measure the real speedup, now that the CPU-cost
  comparison from `scrape_quotes_api.py` already shows why this matters.
- [ ] **Scrapy** — rebuild one of the existing scrapers (probably the
  books one) as a proper Scrapy spider instead of a hand-rolled loop, to
  see what a real framework gives you for free (retries, concurrency,
  item pipelines) vs. doing it manually.

## Later / lower priority

- [ ] **Respect `robots.txt` deliberately** — add a check (or use a
  library) that reads and respects the target site's `robots.txt` before
  scraping, as a matter of habit rather than an afterthought.
- [ ] **Error handling / retries** — none of the current scripts retry on
  a failed request or handle a site being temporarily down; add basic
  retry-with-backoff.
- [ ] **A real (not sandbox) target** — once comfortable with the above,
  pick one real site and actually apply the `/scrp/` notes' legal-risk
  checklist (public data, no login, no hammering the server) before
  scraping it for real.

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
