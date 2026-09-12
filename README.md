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

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install requests beautifulsoup4 lxml playwright
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
