"""
job-tracker - search, save, and export remote job listings.

Data source: RemoteOK public API (https://remoteok.com/api)
No API key required. Uses Python stdlib only (urllib, sqlite3, csv, argparse).

Commands:
    search <keyword>  -- Pull live listings from RemoteOK matching a keyword
    save <id>         -- Bookmark a job to your local SQLite database
    list              -- Show all saved jobs
    remove <id>       -- Delete a saved job
    export            -- Write saved jobs to a CSV file
    stats             -- Show a summary of your saved jobs

Usage:
    python scraper.py search python --limit 15
    python scraper.py save 123456
    python scraper.py list
    python scraper.py remove 123456
    python scraper.py export --output results.csv
    python scraper.py stats
"""

import argparse
import csv
import json
import sys
import urllib.request
from db import JobDB

API_URL = "https://remoteok.com/api"
HEADERS = {"User-Agent": "job-tracker/1.0 (github.com/jonatakuzi/job-tracker)"}
SEPARATOR = "-" * 60


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def fetch_jobs(keyword: str = None) -> list[dict]:
    """
    Pull live listings from the RemoteOK public API and filter by keyword.

    RemoteOK returns a JSON array where the first element is metadata,
    so we skip it. We search across the job title, company name, tags,
    and description so that a search for 'python' catches both
    Python Engineer titles AND listings that list python as a required tag.
    """
    req = urllib.request.Request(API_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())

    jobs = [j for j in data if isinstance(j, dict) and "id" in j]

    if keyword:
        kw = keyword.lower()
        jobs = [
            j for j in jobs
            if kw in j.get("position", "").lower()
            or kw in j.get("company", "").lower()
            or kw in " ".join(j.get("tags", [])).lower()
            or kw in j.get("description", "").lower()
        ]

    return jobs


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------

def print_job(job: dict) -> None:
    """Print a single job listing in a readable card format."""
    print(SEPARATOR)
    print(f"ID:      {job.get('id', 'N/A')}")
    print(f"Title:   {job.get('position', 'N/A')}")
    print(f"Company: {job.get('company', 'N/A')}")
    tags = ", ".join(job.get("tags", [])) or "none"
    print(f"Tags:    {tags}")
    print(f"Date:    {job.get('date', 'N/A')[:10]}")
    print(f"URL:     {job.get('url', 'N/A')}")


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_search(args, db: JobDB) -> None:
    """
    Fetch live listings from RemoteOK and display matches for a keyword.
    Results are capped by --limit (default 10) to avoid flooding the terminal.
    Tip: copy an ID from the output and run 'save <id>' to bookmark it.
    """
    print(f'Searching remote jobs for "{args.keyword}"...\n')
    try:
        jobs = fetch_jobs(args.keyword)
    except Exception as e:
        print(f"Error fetching jobs: {e}", file=sys.stderr)
        sys.exit(1)

    jobs = jobs[: args.limit]

    if not jobs:
        print("No results found.")
        return

    for job in jobs:
        print_job(job)

    print(SEPARATOR)
    print(f"\n{len(jobs)} result(s). Use 'save <ID>' to bookmark one.")


def cmd_save(args, db: JobDB) -> None:
    """
    Look up a job by ID in the live API feed and save it to the local database.
    The database uses SQLite so your list persists between terminal sessions.
    If the job ID is already saved, nothing changes (no duplicates).
    """
    try:
        jobs = fetch_jobs()
    except Exception as e:
        print(f"Error fetching jobs: {e}", file=sys.stderr)
        sys.exit(1)

    job = next((j for j in jobs if str(j.get("id")) == str(args.id)), None)
    if not job:
        print(f"Job ID {args.id} not found in current listings.")
        return

    if db.save_job(job):
        print(f"Saved: {job.get('position')} @ {job.get('company')}")
    else:
        print(f"Already saved: {job.get('position')} @ {job.get('company')}")


def cmd_list(args, db: JobDB) -> None:
    """
    Display all jobs saved in the local database.
    Jobs are sorted newest-first by the time you saved them.
    """
    jobs = db.list_jobs()
    if not jobs:
        print("No saved jobs. Use 'search' to find listings, then 'save <id>'.")
        return

    print(f"\n{'ID':<12} {'Company':<20} {'Title':<40} {'Saved'}")
    print("-" * 90)
    for j in jobs:
        print(
            f"{j['id']:<12} {j['company'][:18]:<20} {j['title'][:38]:<40} {j['saved_at'][:16]}"
        )
    print(f"\n{len(jobs)} saved job(s).")


def cmd_remove(args, db: JobDB) -> None:
    """
    Remove a saved job from the local database by its RemoteOK ID.
    Only deletes from your local list; the live listing is unaffected.
    """
    if db.remove_job(args.id):
        print(f"Removed job {args.id}.")
    else:
        print(f"Job ID {args.id} not found in your saved list.")


def cmd_export(args, db: JobDB) -> None:
    """
    Export all saved jobs to a CSV file for tracking in Excel or Google Sheets.
    Default output is 'jobs_export.csv'. Pass --output to set a custom path.
    Columns: id, title, company, tags, url, date, saved_at.
    """
    jobs = db.list_jobs()
    if not jobs:
        print("Nothing to export - no saved jobs.")
        return

    output = args.output or "jobs_export.csv"
    fields = ["id", "title", "company", "tags", "url", "date", "saved_at"]

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(jobs)

    print(f"Exported {len(jobs)} job(s) to '{output}'.")


def cmd_stats(args, db: JobDB) -> None:
    """
    Show a summary of your saved jobs database.

    Prints:
      - Total number of bookmarked jobs
      - Top companies (how many listings per company you saved)
      - Top skill tags across all saved listings
      - Date range of your saves

    Great for spotting which tech skills appear most in roles you are
    interested in - useful for deciding what to study next or what to
    highlight on a resume.
    """
    stats = db.get_stats()

    if stats["total"] == 0:
        print("No saved jobs yet. Use 'search' and 'save' to get started.")
        return

    print("\n=== Job Tracker Stats ===\n")
    print(f"Total saved:  {stats['total']}")
    print(f"First saved:  {stats['oldest_save']}")
    print(f"Last saved:   {stats['newest_save']}")

    print("\nTop Companies:")
    for company, count in stats["top_companies"]:
        print(f"  {company:<30} {count} job(s)")

    print("\nTop Skill Tags:")
    for tag, count in stats["top_tags"]:
        print(f"  {tag:<25} {count}x")

    print()


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """
    Build the argument parser with subcommands.
    Each subcommand maps to one cmd_* function above.
    Using subcommands (add_subparsers) keeps each command isolated
    and makes it easy to add new ones without touching existing logic.
    """
    parser = argparse.ArgumentParser(
        prog="scraper",
        description="Search, save, and track remote job listings from RemoteOK.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Search live RemoteOK listings by keyword")
    p_search.add_argument("keyword", help="Keyword to search (title, company, tags, description)")
    p_search.add_argument("--limit", type=int, default=10, help="Max results to show (default 10)")

    p_save = sub.add_parser("save", help="Save a job to your local database by its ID")
    p_save.add_argument("id", help="RemoteOK job ID (shown in search results)")

    sub.add_parser("list", help="Show all saved jobs")

    p_remove = sub.add_parser("remove", help="Remove a saved job by its ID")
    p_remove.add_argument("id", help="RemoteOK job ID to remove")

    p_export = sub.add_parser("export", help="Export saved jobs to a CSV file")
    p_export.add_argument("--output", default="jobs_export.csv", help="Output filename")

    sub.add_parser("stats", help="Show a summary of your saved jobs (top companies, skills)")

    return parser


COMMANDS = {
    "search": cmd_search,
    "save": cmd_save,
    "list": cmd_list,
    "remove": cmd_remove,
    "export": cmd_export,
    "stats": cmd_stats,
}


def main():
    """Entry point - parse arguments and dispatch to the correct command handler."""
    parser = build_parser()
    args = parser.parse_args()
    db = JobDB()
    try:
        COMMANDS[args.command](args, db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
