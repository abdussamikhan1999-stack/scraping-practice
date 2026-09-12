"""
Tenth script: tracks Hacker News front-page stories over time in SQLite,
instead of overwriting a snapshot on every run (which is what
scrape_books_db.py does — fine for a catalogue that barely changes, but
wrong for something like HN scores/comment counts that change by the
minute).

Two different tables for two different questions, on purpose:
  - `stories` — current known info per story (title, url, author). Each
    run UPSERTs into this: same id twice updates the row in place, never
    creates a duplicate. Answers "what do we know about this story right
    now."
  - `score_snapshots` — one new row per story PER RUN, with a timestamp.
    Never overwritten, only appended to. Answers "how has this story's
    score/comment count changed over time" — a question `stories` alone
    structurally cannot answer, since it only ever holds the latest value.

Run this script more than once (a few minutes apart) to see
score_snapshots actually accumulate history — see history_for_story() in
query_hackernews_history.py to look at it.
"""
import argparse
import asyncio
import sqlite3
from datetime import datetime, timezone

from scrape_hackernews import DEFAULT_STORY_LIMIT, scrape_top_stories

DB_PATH = "hackernews_history.db"


def create_schema(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stories (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT,
            author TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS score_snapshots (
            story_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            comments INTEGER NOT NULL,
            scraped_at TEXT NOT NULL,
            FOREIGN KEY (story_id) REFERENCES stories(id)
        )
        """
    )


def save_snapshot(stories, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    now = datetime.now(timezone.utc).isoformat()
    try:
        create_schema(conn)

        # UPSERT: insert if new, update in place if this id already exists —
        # never creates a second row for the same story.
        conn.executemany(
            """
            INSERT INTO stories (id, title, url, author) VALUES (:id, :title, :url, :author)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                url = excluded.url,
                author = excluded.author
            """,
            stories,
        )

        # APPEND, deliberately: every run adds new rows here, none are
        # ever updated or deleted, so history accumulates.
        conn.executemany(
            "INSERT INTO score_snapshots (story_id, score, comments, scraped_at) VALUES (?, ?, ?, ?)",
            [(s["id"], s["score"], s["comments"], now) for s in stories],
        )
        conn.commit()
    finally:
        conn.close()
    return now


def parse_args():
    parser = argparse.ArgumentParser(
        description="Record a timestamped snapshot of Hacker News' front page into SQLite."
    )
    parser.add_argument(
        "--limit", type=int, default=DEFAULT_STORY_LIMIT,
        help=f"how many top stories to track (default: {DEFAULT_STORY_LIMIT})",
    )
    parser.add_argument("--db", default=DB_PATH, help=f"SQLite db path (default: {DB_PATH})")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    stories = asyncio.run(scrape_top_stories(limit=args.limit))
    scraped_at = save_snapshot(stories, db_path=args.db)
    print(f"Recorded a snapshot of {len(stories)} stories at {scraped_at}")

    total_snapshots = sqlite3.connect(args.db).execute(
        "SELECT COUNT(*) FROM score_snapshots"
    ).fetchone()[0]
    print(f"score_snapshots now has {total_snapshots} rows total across all runs")
