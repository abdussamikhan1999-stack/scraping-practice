"""
Fifth scraper: same data as scrape_quotes_api.py, but fetching all pages
concurrently with httpx + asyncio instead of one request at a time.

scrape_quotes_api.py has to fetch page 1, wait for the response, THEN
fetch page 2, because it doesn't know how many pages exist until it reads
each page's "has_next" flag. Here we sidestep that: fetch page 1 first to
read the total page count isn't available either, so instead we probe
pages concurrently in a batch and stop once a batch comes back with no
more "has_next" pages. This trades a little wasted work (typically one
batch's worth of requests past the real end) for a lot of parallelism.
"""
import asyncio
import csv
import time

import httpx

API_URL = "https://quotes.toscrape.com/api/quotes"
BATCH_SIZE = 5  # how many pages to fetch concurrently per round


async def fetch_page(client, page_num):
    response = await client.get(API_URL, params={"page": page_num}, timeout=10)
    response.raise_for_status()
    return page_num, response.json()


async def scrape_all_quotes():
    quotes = []
    async with httpx.AsyncClient() as client:
        page_num = 1
        keep_going = True
        while keep_going:
            batch = range(page_num, page_num + BATCH_SIZE)
            results = await asyncio.gather(*(fetch_page(client, p) for p in batch))
            results.sort(key=lambda r: r[0])  # asyncio.gather doesn't guarantee order

            for _, data in results:
                for q in data["quotes"]:
                    quotes.append(
                        {
                            "text": q["text"],
                            "author": q["author"]["name"],
                            "tags": ", ".join(q["tags"]),
                        }
                    )
                if not data["has_next"]:
                    keep_going = False

            page_num += BATCH_SIZE
    return quotes


def save_csv(quotes, path="quotes_concurrent.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "author", "tags"])
        writer.writeheader()
        writer.writerows(quotes)


if __name__ == "__main__":
    start = time.time()
    quotes = asyncio.run(scrape_all_quotes())
    elapsed = time.time() - start

    # dedupe, since fetching a batch past the real last page can pull in
    # nothing new but "has_next: false" repeats are harmless; real dupes
    # would only happen if the site itself repeated data, which it doesn't
    save_csv(quotes)
    print(f"Saved {len(quotes)} quotes to quotes_concurrent.csv in {elapsed:.2f}s")
