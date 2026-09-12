# Scraping Practice

First web scraping project, practicing on
[books.toscrape.com](https://books.toscrape.com) — a site built specifically
for scraping practice, so there's no ToS concern.

## Setup

```
python3 -m venv .venv
source .venv/bin/activate
pip install requests beautifulsoup4 lxml
```

## Run

```
source .venv/bin/activate
python scrape_books.py
```

Paginates through all 50 pages of the catalogue, extracts each book's
title, price, and star rating, and writes them to `books.csv`.

## Lesson learned

The server doesn't declare a charset in its response headers, so
`requests`'s encoding auto-detection guessed wrong and mangled the `£`
symbol into `Â£` in every price. Fix: explicitly set
`response.encoding = "utf-8"` before reading `.text`. Worth remembering —
this kind of silent mis-decoding is a very common scraping gotcha and won't
throw an error, it'll just quietly corrupt your data.

## Stack

Plain `requests` + `BeautifulSoup` (with the `lxml` parser) — no browser
automation needed here since this site's content is static HTML, no
JavaScript rendering required.
