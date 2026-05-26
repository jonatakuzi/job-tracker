"""
job-tracker — search, save, and export remote job listings.

Data source: RemoteOK public API (https://remoteok.com/api)
No API key required. Uses Python stdlib only.

Usage:
    python scraper.py search python --limit 15
    python scraper.py save 123456
    python scraper.py list
    python scraper.py remove 123456
    python scraper.py export --output results.csv
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
    """Pull listings from RemoteOK and optionally filter by keyword."""
    req = urllib.request.Request(API_URL, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    # First element is a legal/info dict — skip it
    jobs = [j for j in data if isinstance(j, dict) and "id" in j]

    if keyword:
        kw = keyword.lower()
        jobs = [
            j for j in jobs
            if kw in j.get("position", "").lower()
            or kw in " ".join(j.get("tags", [])).lower()
            or kw in j.get("company", "").lower()
            or kw in j.get("description", "").lower()
        ]

    return jobs


def normalize(job: dict) -> dict:
    """Flatten a raw API job dict into a clean record."""
    return {
        "id":      str(job.get("id", "")),
        "title":   job.get("position", "N/A"),
        "company": job.get("company", "N/A"),
        "location": job.get("location", "Remote"),
        "tags":    ", ".join(job.get("tags", [])[:6]),
        "url":     job.get("url", ""),
        "date":    (job.get("date", "") or "")[:10],
    }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_search(db: JobDB, args: argparse.Namespace):
    print(f'Searching remote jobs for "{args.keyword}"...\n')
    try:
        jobs = fetch_jobs(keyword=args.keyword)
    except Exception as e:
        print(f"Error fetching jobs: {e}", file=sys.stderr)
        sys.exit(1)

    if not jobs:
        print("No matching jobs found.")
        return

    limit = args.limit or 10
    for job in jobs[:limit]:
        j = normalize(job)
        print(SEPARATOR)
        print(f"  ID:      {j['id']}")
        print(f"  Title:   {j['title']}")
        print(f"  Company: {j['company']}")
        print(f"  Tags:    {j['tags']}")
        print(f"  Date:    {j['date']}")
        print(f"  URL:     {j['url']}")

    print(SEPARATOR)
    print(f"\n{len(jobs[:limit])} result(s). Use 'save <ID>' to bookmark one.")


def cmd_save(db: JobDB, args: argparse.Namespace):
    print(f"Looking up job {args.id}...")
    try:
        jobs = fetch_jobs()
    except Exception as e:
        print(f"Error fetching jobs: {e}", file=sys.stderr)
        sys.exit(1)

    match = next((j for j in jobs if str(j.get("id", "")) == str(args.id)), None)
    if not match:
        print(f'Job ID "{args.id}" not found in current listings.')
        sys.exit(1)

    j = normalize(match)
    db.save_job(j)
    print(f"Saved: {j['title']} @ {j['company']}")


def cmd_list(db: JobDB, args: argparse.Namespace):
    rows = db.list_jobs()
    if not rows:
        print("No saved jobs. Run 'search <keyword>' then 'save <ID>'.")
        return

    print(f"\n{len(rows)} saved job(s):\n")
    for row in rows:
        print(SEPARATOR)
        print(f"  ID:      {row['remote_id']}")
        print(f"  Title:   {row['title']}")
        print(f"  Company: {row['company']}")
        print(f"  Tags:    {row['tags']}")
        print(f"  URL:     {row['url']}")
        print(f"  Saved:   {row['saved_at'][:10]}")
    print(SEPARATOR)


def cmd_remove(db: JobDB, args: argparse.Namespace):
    db.delete_job(str(args.id))
    print(f"Removed job {args.id} from your saved list.")


def cmd_export(db: JobDB, args: argparse.Namespace):
    rows = db.list_jobs()
    if not rows:
        print("No saved jobs to export.")
        return

    filename = args.output or "saved_jobs.csv"
    fields = ["id", "remote_id", "title", "company", "tags", "url", "saved_at"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows([dict(row) for row in rows])

    print(f"Exported {len(rows)} job(s) to {filename}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="scraper",
        description="job-tracker — search and save remote job listings (RemoteOK)",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # search
    p = sub.add_parser("search", help="Search remote job listings by keyword")
    p.add_argument("keyword", help="Keyword to search (e.g. 'python', 'devops')")
    p.add_argument("--limit", type=int, default=10, help="Max results to show (default: 10)")
    p.set_defaults(func=cmd_search)

    # save
    p = sub.add_parser("save", help="Save a job to your local list by ID")
    p.add_argument("id", help="Job ID shown in search results")
    p.set_defaults(func=cmd_save)

    # list
    p = sub.add_parser("list", help="Show all saved jobs")
    p.set_defaults(func=cmd_list)

    # remove
    p = sub.add_parser("remove", help="Remove a saved job by ID")
    p.add_argument("id", help="Job ID to remove")
    p.set_defaults(func=cmd_remove)

    # export
    p = sub.add_parser("export", help="Export saved jobs to CSV")
    p.add_argument("--output", metavar="FILE", help="Output filename (default: saved_jobs.csv)")
    p.set_defaults(func=cmd_export)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    db = JobDB()
    args.func(db, args)


if __name__ == "__main__":
    main()
