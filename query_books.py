"""
Runs a couple of real SQL queries against books.db (built by
scrape_books_db.py), to show what a query engine gives you for free over
grepping/sorting a CSV by hand in Python.
"""
import sqlite3

DB_PATH = "books.db"


def top_n_most_expensive(conn, n=5):
    return conn.execute(
        "SELECT title, price_gbp FROM books ORDER BY price_gbp DESC LIMIT ?", (n,)
    ).fetchall()


def average_price_by_rating(conn):
    return conn.execute(
        """
        SELECT rating, ROUND(AVG(price_gbp), 2) AS avg_price, COUNT(*) AS num_books
        FROM books
        GROUP BY rating
        ORDER BY rating
        """
    ).fetchall()


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)

    print("Top 5 most expensive books:")
    for title, price in top_n_most_expensive(conn):
        print(f"  £{price:>6.2f}  {title}")

    print("\nAverage price by star rating:")
    for rating, avg_price, count in average_price_by_rating(conn):
        print(f"  {rating} stars: £{avg_price:>6.2f} avg, across {count} books")

    conn.close()
