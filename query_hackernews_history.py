"""
Queries hackernews_history.db (built by track_hackernews.py) for the thing
a single-snapshot scraper structurally can't answer: how has a story's
score changed across multiple runs.
"""
import sqlite3

DB_PATH = "hackernews_history.db"


def stories_with_growth(conn):
    """
    For each story with more than one snapshot, compare its first and
    most recent recorded score. Stories with only one snapshot (only
    scraped once so far) are excluded — there's nothing to compare yet.
    """
    return conn.execute(
        """
        SELECT
            s.title,
            MIN(sn.score) AS first_seen_score,
            MAX(sn.score) AS latest_score,
            COUNT(*) AS num_snapshots
        FROM stories s
        JOIN score_snapshots sn ON sn.story_id = s.id
        GROUP BY s.id
        HAVING COUNT(*) > 1
        ORDER BY (MAX(sn.score) - MIN(sn.score)) DESC
        """
    ).fetchall()


def history_for_story(conn, story_id):
    return conn.execute(
        "SELECT score, comments, scraped_at FROM score_snapshots WHERE story_id = ? ORDER BY scraped_at",
        (story_id,),
    ).fetchall()


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)

    rows = stories_with_growth(conn)
    if not rows:
        print("No stories have more than one snapshot yet — run track_hackernews.py again first.")
    else:
        print("Stories tracked across multiple runs, by score growth:")
        for title, first, latest, n in rows:
            delta = latest - first
            sign = "+" if delta >= 0 else ""
            print(f"  {sign}{delta:>4} ({n} snapshots)  {title}")

    conn.close()
