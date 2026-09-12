"""
Fourth scraper: log in first, then scrape — using quotes.toscrape.com's
login-gated demo. Any username/password works here (it's a scraping
sandbox, not a real auth system), but the mechanics are the same as a real
login: fetch a CSRF token from the login form, POST it back alongside
credentials, then reuse the resulting session cookie for every later
request.

New concept vs. the earlier scripts: a `requests.Session()` persists
cookies across requests automatically, so once login_session() succeeds,
every subsequent .get()/.post() on that same session carries the logged-in
cookie without you handling it manually.
"""
import csv

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://quotes.toscrape.com"


def login_session(username="anyname", password="anypassword"):
    session = requests.Session()

    login_page = session.get(f"{BASE_URL}/login", timeout=10)
    soup = BeautifulSoup(login_page.text, "lxml")
    csrf_token = soup.find("input", {"name": "csrf_token"})["value"]

    session.post(
        f"{BASE_URL}/login",
        data={"csrf_token": csrf_token, "username": username, "password": password},
        timeout=10,
    )
    return session


def is_logged_in(session):
    home = session.get(f"{BASE_URL}/", timeout=10)
    return "Logout" in home.text


def scrape_all_quotes(session):
    quotes = []
    page_num = 1
    while True:
        url = BASE_URL if page_num == 1 else f"{BASE_URL}/page/{page_num}/"
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "lxml")

        quote_divs = soup.select("div.quote")
        if not quote_divs:
            break

        for div in quote_divs:
            text = div.select_one("span.text").get_text(strip=True)
            author = div.select_one("small.author").get_text(strip=True)
            tags = [t.get_text(strip=True) for t in div.select("div.tags a.tag")]

            # Only present when logged in — a real, concrete reason to
            # bother authenticating rather than just logging in for its
            # own sake. See README for how this was discovered (a plain
            # diff of the logged-in vs. logged-out HTML). Scoped to this
            # div specifically (not find_all_next) so it can't pick up a
            # link belonging to a different quote.
            goodreads_a = div.find("a", href=lambda h: h and "goodreads.com" in h)
            goodreads_link = goodreads_a["href"] if goodreads_a else ""

            quotes.append(
                {
                    "text": text,
                    "author": author,
                    "tags": ", ".join(tags),
                    "goodreads_link": goodreads_link,
                }
            )

        page_num += 1
    return quotes


def save_csv(quotes, path="quotes_login.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "author", "tags", "goodreads_link"])
        writer.writeheader()
        writer.writerows(quotes)


if __name__ == "__main__":
    session = login_session()
    if not is_logged_in(session):
        raise SystemExit("Login failed — check credentials/CSRF handling")
    print("Logged in successfully.")

    quotes = scrape_all_quotes(session)
    save_csv(quotes)
    print(f"Saved {len(quotes)} quotes to quotes_login.csv")
