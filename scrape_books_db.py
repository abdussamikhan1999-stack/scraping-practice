"""
Eighth script: the same books.toscrape.com catalogue as scrape_books.py,
but stored in a local SQLite database instead of a CSV. Reuses
fetch_page/parse_books from scrape_books.py rather than duplicating them.

Why this over a CSV: querying "give me the 5 most expensive books" from a
CSV means loading it and sorting in Python; from SQLite it's one line of
SQL, and the schema (a real numeric price column, not a "£51.77" string)
is enforced at write time instead of hoped for at read time.
"""
import re
import sqlite3

from scrape_books import scrape_all_books

DB_PATH = "books.db"


def price_to_float(price_str):
    """'£51.77' -> 51.77 — strip the currency symbol so the column is a
    real number, sortable/comparable in SQL, not a string."""
    return float(re.sub(r"[^\d.]", "", price_str))


def create_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price_gbp REAL NOT NULL,
            rating INTEGER NOT NULL
        )
        """
    )


def save_to_db(books, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    try:
        create_schema(conn)
        conn.execute("DELETE FROM books")  # re-running this script replaces old data, doesn't duplicate it
        conn.executemany(
            "INSERT INTO books (title, price_gbp, rating) VALUES (?, ?, ?)",
            [(b["title"], price_to_float(b["price"]), b["rating"]) for b in books],
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    books = scrape_all_books()
    save_to_db(books)
    print(f"Saved {len(books)} books to {DB_PATH}")
