"""
One-off discovery script, not a scraper itself: opens a page with an
infinite-scroll product list, watches every network request the page makes
while scrolling, and prints any that look like a JSON API call underneath
the UI. This is the "check the Network tab" step from the /scrp/ notes,
done programmatically instead of by hand in devtools.
"""
from playwright.sync_api import sync_playwright

TARGET_URL = "https://quotes.toscrape.com/scroll"


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        api_calls = []

        def log_response(response):
            api_calls.append(
                (response.request.resource_type, response.url, response.headers.get("content-type", ""))
            )

        page.on("response", log_response)
        page.goto(TARGET_URL)

        # scroll down a few times to trigger the infinite-scroll requests
        for _ in range(5):
            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(500)

        browser.close()

    print("All responses seen while loading/scrolling this page:")
    for resource_type, url, content_type in api_calls:
        print(" ", resource_type, "-", content_type, "-", url)


if __name__ == "__main__":
    main()
