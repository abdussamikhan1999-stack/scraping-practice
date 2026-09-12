"""
Sixth scraper: the same books.toscrape.com catalogue as scrape_books.py,
rebuilt as a proper Scrapy spider instead of a hand-rolled requests loop.

Run with:
    scrapy runspider books_spider.py -o books_scrapy.csv

Compare this to scrape_books.py's ~30 lines of manual pagination, error
handling, and CSV writing — Scrapy gives you all of that for free:
- `response.follow()` handles building the next-page URL and dispatching
  the request; you don't manually construct `page-{n}.html` URLs.
- `-o books_scrapy.csv` handles CSV writing entirely; no csv.DictWriter.
- Scrapy's default settings already respect robots.txt (see
  ROBOTSTXT_OBEY below) and auto-throttle request rate — both had to be
  built by hand for the other scripts in this repo (see the
  polite_requests.py utility).
- Retries on failed requests are built in and configurable, versus
  scrape_books.py having no retry logic at all.

The tradeoff: Scrapy has real setup/conceptual overhead (its own request/
response/callback model) that a 20-line requests script doesn't need for
something this small — worth it once a crawl gets big or needs Scrapy's
built-in retry/concurrency/pipeline machinery, overkill for a one-off.
"""
import scrapy

RATING_WORDS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class BooksSpider(scrapy.Spider):
    name = "books"
    start_urls = ["https://books.toscrape.com/catalogue/page-1.html"]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,  # Scrapy checks /robots.txt before crawling, on by default here
        "DOWNLOAD_DELAY": 0.5,  # be polite, same rate as scrape_books.py's manual time.sleep(0.5)
    }

    def parse(self, response):
        for book in response.css("article.product_pod"):
            rating_class = book.css("p.star-rating::attr(class)").get()
            rating_word = rating_class.replace("star-rating", "").strip()
            yield {
                "title": book.css("h3 a::attr(title)").get(),
                "price": book.css("p.price_color::text").get(),
                "rating": RATING_WORDS.get(rating_word, 0),
            }

        next_page = response.css("li.next a::attr(href)").get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)
