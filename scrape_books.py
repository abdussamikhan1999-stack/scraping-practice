"""
First scraper: pull every book's title, price, and rating from
books.toscrape.com (a sandbox site built specifically for practicing
scraping), across all pages, and save to a CSV.

Uses polite_requests.get_with_retry() instead of a plain requests.get() —
checks robots.txt before fetching (books.toscrape.com doesn't have one, so
this is a no-op here, but it's a real check, not a formality — see
polite_requests.py) and retries with backoff on connection errors/5xx/429.
"""
import csv
import time

from bs4 import BeautifulSoup

from polite_requests import get_with_retry

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"
RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def fetch_page(page_num):
    url = BASE_URL.format(page_num)
    response = get_with_retry(url, timeout=10)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    response.encoding = "utf-8"  # server doesn't declare charset; requests guesses wrong otherwise
    return response.text


def parse_books(html):
    soup = BeautifulSoup(html, "lxml")
    books = []
    for article in soup.select("article.product_pod"):
        title = article.h3.a["title"]
        price = article.select_one("p.price_color").text.strip()
        rating_class = article.select_one("p.star-rating")["class"]
        rating_word = [c for c in rating_class if c != "star-rating"][0]
        books.append(
            {
                "title": title,
                "price": price,
                "rating": RATING_WORDS.get(rating_word, 0),
            }
        )
    return books


def scrape_all_books():
    all_books = []
    page_num = 1
    while True:
        html = fetch_page(page_num)
        if html is None:
            break
        page_books = parse_books(html)
        all_books.extend(page_books)
        print(f"page {page_num}: {len(page_books)} books")
        page_num += 1
        time.sleep(0.5)  # be polite even to a sandbox site
    return all_books


def save_csv(books, path="books.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "price", "rating"])
        writer.writeheader()
        writer.writerows(books)


if __name__ == "__main__":
    books = scrape_all_books()
    save_csv(books)
    print(f"\nSaved {len(books)} books to books.csv")
