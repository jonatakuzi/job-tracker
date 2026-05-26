# Job Tracker

A command-line tool for searching and saving remote job listings. Pulls live data from the [RemoteOK](https://remoteok.com) public API — no API key required, no external libraries needed.

## Features

- **Search** remote jobs by keyword (title, company, tags, description)
- **Save** interesting listings to a local SQLite database
- **List** your saved jobs at any time
- **Remove** jobs you're no longer interested in
- **Export** your saved list to CSV for tracking applications

## Installation

```bash
git clone https://github.com/jonatakuzi/job-tracker.git
cd job-tracker
python scraper.py --help
```

Requires Python 3.10+ — no `pip install` needed. Uses only the standard library (`urllib`, `sqlite3`, `csv`, `argparse`).

## Usage

### Search for jobs

```bash
python scraper.py search python
python scraper.py search devops --limit 20
```

Example output:
```
Searching remote jobs for "python"...

------------------------------------------------------------
  ID:      123456
  Title:   Backend Python Engineer
  Company: Acme Corp
  Tags:    python, django, postgresql, aws, backend
  Date:    2026-05-20
  URL:     https://remoteok.com/l/123456
------------------------------------------------------------

10 result(s). Use 'save <ID>' to bookmark one.
```

### Save a job

```bash
python scraper.py save 123456
# Saved: Backend Python Engineer @ Acme Corp
```

### View saved jobs

```bash
python scraper.py list
```

### Remove a saved job

```bash
python scraper.py remove 123456
```

### Export to CSV

```bash
python scraper.py export
python scraper.py export --output my_applications.csv
```

## Project Structure

```
job-tracker/
├── scraper.py   # CLI entry point and RemoteOK API scraping logic
├── db.py        # SQLite storage layer (save/list/delete jobs)
├── jobs.db      # Created automatically on first run
└── README.md
```

## Why I Built This

Tracking job applications across browser tabs and sticky notes is a mess. This tool centralizes the search-and-save workflow in the terminal, keeps a persistent local record, and exports clean CSV data for further analysis or sharing. It also demonstrates practical use of Python's `urllib` for HTTP, JSON parsing, and `sqlite3` for lightweight persistence — all without external dependencies.
