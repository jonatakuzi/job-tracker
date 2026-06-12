# Job Tracker

A command-line tool for searching and saving remote job listings. Pulls live data from the [RemoteOK](https://remoteok.com) public API — no API key required, no external libraries needed.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **Search** live remote jobs by keyword — matches against title, company, tags, and description
- **Save** listings to a local SQLite database for later review
- **List** all saved jobs with company, title, and URL
- **Remove** jobs you're no longer interested in
- **Export** your saved list to CSV for application tracking
- No API key, no sign-up — uses RemoteOK's public endpoint
- No external dependencies — uses only Python's `urllib`, `sqlite3`, `csv`, `argparse`

## Requirements

- Python 3.10+
- No `pip install` needed

## Installation

```bash
git clone https://github.com/jonatakuzi/job-tracker.git
cd job-tracker
```

## Usage

### Search for jobs
```bash
python scraper.py search python
python scraper.py search "security engineer" --limit 20
python scraper.py search devops
```
```
Searching remote jobs for "python"...

──────────────────────────────────────────────────────
  ID:      120483
  Title:   Senior Python Developer
  Company: Acme Corp
  Tags:    python, django, postgresql
  URL:     https://remoteok.com/jobs/120483
──────────────────────────────────────────────────────
```

### Save a job
```bash
python scraper.py save 120483
```

### List saved jobs
```bash
python scraper.py list
```

### Export saved jobs to CSV
```bash
python scraper.py export saved_jobs.csv
```

### Remove a saved job
```bash
python scraper.py remove 120483
```

## Tech Stack

- Python 3.10+
- RemoteOK public API (no key required)
- Standard library: `urllib`, `sqlite3`, `csv`, `json`, `argparse`
