"""
Second scraper: pull every quote's text, author, and tags from
quotes.toscrape.com/js — a version of the practice site that renders its
content via JavaScript, so plain requests+BeautifulSoup won't see anything
(the initial HTML is empty; a script fills it in after load). That's why
this one uses Playwright to drive a real browser instead.
"""
import csv

from playwright.sync_api import sync_playwright

START_URL = "https://quotes.toscrape.com/js/"


def scrape_all_quotes():
    quotes = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(START_URL)

        while True:
            page.wait_for_selector("div.quote")  # wait for JS to render the quotes
            for quote_el in page.query_selector_all("div.quote"):
                text = quote_el.query_selector("span.text").inner_text()
                author = quote_el.query_selector("small.author").inner_text()
                tags = [
                    t.inner_text()
                    for t in quote_el.query_selector_all("div.tags a.tag")
                ]
                quotes.append({"text": text, "author": author, "tags": ", ".join(tags)})

            next_link = page.query_selector("li.next a")
            if next_link is None:
                break
            next_link.click()

        browser.close()
    return quotes


def save_csv(quotes, path="quotes.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "author", "tags"])
        writer.writeheader()
        writer.writerows(quotes)


if __name__ == "__main__":
    quotes = scrape_all_quotes()
    save_csv(quotes)
    print(f"Saved {len(quotes)} quotes to quotes.csv")
