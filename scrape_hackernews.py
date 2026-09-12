"""
Seventh script, and the first real (non-sandbox) target in this repo:
Hacker News' front page, via their official public API
(https://github.com/HackerNews/API) — not scraping HTML at all.

Why this is a genuinely low-risk real target, checked against the
/scrp/ notes' legal-risk factors before writing anything:
  - Public data, no login required.
  - This IS the sanctioned access method — HN's own GitHub documents this
    API specifically so third parties don't have to scrape their HTML.
  - api.firebaseio.com has no robots.txt (404) — nothing to violate.
  - Read-only, GET-only, no attempt to exceed any stated rate limit
    (HN doesn't publish one for this API, so this script self-limits by
    only fetching the top N stories, not the full ~500-story firehose).

Applies the concurrency lesson from scrape_quotes_concurrent.py: the
front page is a two-step fetch (get story IDs, then get each story's
details), and fetching those details one at a time would be exactly the
slow, mostly-idle pattern that script demonstrated — so this uses the
same httpx + asyncio.gather approach.
"""
import asyncio
import csv

import httpx

TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
STORY_LIMIT = 30  # self-imposed cap, not the full ~500-story list


async def fetch_story(client, story_id):
    response = await client.get(ITEM_URL.format(story_id), timeout=10)
    response.raise_for_status()
    return response.json()


def stories_to_rows(stories):
    """
    Pure transformation, deliberately separated from the network-fetching
    code above it so it can be unit tested against fixture data (see
    test_parsing.py) without hitting the network on every test run.
    """
    return [
        {
            "title": s.get("title", ""),
            "url": s.get("url", ""),  # missing for text/"Ask HN" posts
            "score": s.get("score", 0),
            "author": s.get("by", ""),
            "comments": s.get("descendants", 0),
        }
        for s in stories
        if s is not None  # a story can be None if deleted between the two requests
    ]


async def scrape_top_stories():
    async with httpx.AsyncClient() as client:
        ids_response = await client.get(TOP_STORIES_URL, timeout=10)
        ids_response.raise_for_status()
        story_ids = ids_response.json()[:STORY_LIMIT]

        stories = await asyncio.gather(*(fetch_story(client, sid) for sid in story_ids))

    return stories_to_rows(stories)


def save_csv(stories, path="hackernews.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "url", "score", "author", "comments"])
        writer.writeheader()
        writer.writerows(stories)


if __name__ == "__main__":
    stories = asyncio.run(scrape_top_stories())
    stories.sort(key=lambda s: s["score"], reverse=True)
    save_csv(stories)
    print(f"Saved {len(stories)} stories to hackernews.csv")
    print(f"Top story: \"{stories[0]['title']}\" ({stories[0]['score']} points)")
