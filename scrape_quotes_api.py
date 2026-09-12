"""
Third scraper: same data as scrape_quotes_js.py (quotes from the
toscrape.com "scroll" page), but hitting the JSON API directly instead of
driving a browser.

/scroll's HTML is empty on load; the page's own JavaScript fetches
https://quotes.toscrape.com/api/quotes?page=N and renders the results as
you scroll. Found that endpoint using discover_api.py (Playwright, logging
every XHR response) instead of guessing.

This is the "check if there's a JSON API before reaching for a browser"
lesson: no browser, no waiting for renders, no clicking "Next" — just a
plain HTTP GET per page, which is why this is dramatically faster than
scrape_quotes_js.py for the exact same data.
"""
import csv

import requests

API_URL = "https://quotes.toscrape.com/api/quotes"


def scrape_all_quotes():
    quotes = []
    page = 1
    while True:
        response = requests.get(API_URL, params={"page": page}, timeout=10)
        response.raise_for_status()
        data = response.json()

        for q in data["quotes"]:
            quotes.append(
                {
                    "text": q["text"],
                    "author": q["author"]["name"],
                    "tags": ", ".join(q["tags"]),
                }
            )

        if not data["has_next"]:
            break
        page += 1
    return quotes


def save_csv(quotes, path="quotes_api.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "author", "tags"])
        writer.writeheader()
        writer.writerows(quotes)


if __name__ == "__main__":
    quotes = scrape_all_quotes()
    save_csv(quotes)
    print(f"Saved {len(quotes)} quotes to quotes_api.csv")
