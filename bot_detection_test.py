"""
Eleventh script: measures what a default headless Playwright browser
reveals about itself, and whether playwright-stealth actually changes
that — against bot.sannysoft.com, a page built specifically for
developers to self-check their browser's bot-detection fingerprint.

This is NOT scraping a real site's protected data, and it's not trying to
get past anything a site owner doesn't want automated: bot.sannysoft.com
exists *for this exact purpose* (it's a public diagnostic tool, not a
production site with real content behind its checks) — the earlier
`/scrp/` notes' anti-bot/stealth-browser section was deliberately left
undone against a real target twice in this repo's TODO.md, and this is
the honest way to learn the same lesson without doing that: a sanctioned
target instead of an unwilling one.

Run twice — once with default Playwright, once with playwright-stealth
applied — and diffs the results, rather than assuming stealth "works."
"""
import csv

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

TARGET_URL = "https://bot.sannysoft.com"

# The specific rows on the page worth comparing before/after — there are
# more rows on the page (WebGL renderer strings, etc.) that are noisy/
# environment-specific rather than pass/fail signals, so this focuses on
# the ones that actually read as clear automation tells.
TRACKED_TESTS = [
    "WebDriver",
    "WebDriver Advanced",
    "Chrome",
    "Permissions",
    "Plugins Length",
    "Plugins is of type PluginArray",
]


def get_test_results(apply_stealth):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        if apply_stealth:
            Stealth().apply_stealth_sync(page)

        page.goto(TARGET_URL, wait_until="networkidle")
        page.wait_for_timeout(1000)

        results = {}
        for row in page.query_selector_all("table tr"):
            cells = row.query_selector_all("td")
            if len(cells) < 2:
                continue
            test_name = cells[0].inner_text().split("\n")[0].strip()
            if test_name in TRACKED_TESTS:
                results[test_name] = cells[1].inner_text().strip()

        user_agent = page.evaluate("() => navigator.userAgent")
        browser.close()

    results["User Agent"] = user_agent
    return results


def save_comparison_csv(before, after, path="bot_detection_comparison.csv"):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["test", "without_stealth", "with_stealth"])
        for test in sorted(set(before) | set(after)):
            writer.writerow([test, before.get(test, ""), after.get(test, "")])


if __name__ == "__main__":
    print("Running with default Playwright (no stealth)...")
    before = get_test_results(apply_stealth=False)

    print("Running with playwright-stealth applied...")
    after = get_test_results(apply_stealth=True)

    save_comparison_csv(before, after)

    print(f"\n{'Test':<35} {'Without stealth':<45} {'With stealth'}")
    print("-" * 110)
    for test in sorted(set(before) | set(after)):
        b = before.get(test, "(missing)")
        a = after.get(test, "(missing)")
        changed = " <-- changed" if b != a else ""
        print(f"{test:<35} {b:<45} {a}{changed}")
