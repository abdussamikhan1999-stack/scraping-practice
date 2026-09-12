"""
Ninth script: a genuinely authenticated real-login example, replacing the
fake login from scrape_quotes_login.py (where any password worked). Uses
the GitHub API with the token this environment's `gh` CLI is already
authenticated with, to fetch data only this account can see — including
private repos, which the API would refuse to return without real auth.

The token itself is never printed, logged, or written to any file here —
it's fetched fresh from `gh auth token` at runtime and used only in the
Authorization header for this one request.
"""
import csv
import subprocess

import requests

API_URL = "https://api.github.com/user/repos"


def get_github_token():
    result = subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def fetch_all_repos(token):
    repos = []
    page = 1
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    while True:
        response = requests.get(
            API_URL,
            headers=headers,
            params={"per_page": 100, "page": page, "affiliation": "owner"},
            timeout=10,
        )
        response.raise_for_status()
        page_repos = response.json()
        if not page_repos:
            break
        repos.extend(page_repos)
        page += 1
    return repos


def save_csv(repos, path="github_repos.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["name", "private", "language", "stargazers_count", "html_url"]
        )
        writer.writeheader()
        for r in repos:
            writer.writerow(
                {
                    "name": r["name"],
                    "private": r["private"],
                    "language": r["language"] or "",
                    "stargazers_count": r["stargazers_count"],
                    "html_url": r["html_url"],
                }
            )


if __name__ == "__main__":
    token = get_github_token()
    repos = fetch_all_repos(token)
    save_csv(repos)

    private_count = sum(1 for r in repos if r["private"])
    print(f"Saved {len(repos)} repos to github_repos.csv ({private_count} private)")
