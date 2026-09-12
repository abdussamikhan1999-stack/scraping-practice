# Scraping Practice

Web scraping practice on the toscrape.com sandbox sites — built
specifically for practicing scraping, so there's no ToS concern. Two
scripts, deliberately covering the two branches of "how do I scrape this":

| Script | Target | Approach | Why |
|---|---|---|---|
| `scrape_books.py` | books.toscrape.com | `requests` + BeautifulSoup | Static HTML — content is already in the page source, no need for a browser |
| `scrape_quotes_js.py` | quotes.toscrape.com/js | Playwright | JS-rendered — the raw HTML is empty, content is filled in by a script after load, so a real browser is required |

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
