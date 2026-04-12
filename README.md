# Minnesota OHV Trail Dashboard

A personal web application for browsing Minnesota OHV trail statuses. Shows which trails are open or closed, how far each one is from your location, links to each trail's DNR page, and one-click Google Maps directions.

---

## Features

- **Live trail status** — Open / Closed / Limited, sourced directly from the Minnesota DNR website
- **Your location** — Enter a zip code or use GPS; straight-line distances calculate automatically
- **DNR links** — Every trail name links to its official DNR detail page
- **Google Maps directions** — One click opens turn-by-turn directions from your location to the trail
- **Status notes** — Partial closures, seasonal restrictions, and route changes shown inline
- **Search & filter** — Filter by status or search by name and county
- **Status history** — Every status change is recorded in the database over time
- **CSV export** — Download the current trail list for offline use
- **Automatic updates** — A scraper runs on a schedule and updates the database in the background; the dashboard reflects changes immediately with no restart required
- **Portable** — Runs anywhere Docker is available; no external services or API keys required

---

## How Data Updates Work

```
Minnesota DNR website
        │
        ▼  (scraper.py — runs on schedule via scheduler.py)
  SQLite database  ◄──── written directly by scraper
        │
        ▼  (app.py reads DB on every page request)
   Dashboard  ◄──── always shows current data, no restart needed
```

1. On startup, `docker-compose up` launches two containers that share one database file on the host:
   - **ohv-dashboard** — the Flask web app, always running
   - **ohv-scraper** — runs `scheduler.py`, which calls `scraper.py` immediately and then again every N hours
2. `scraper.py` fetches the full trail list from the DNR A-Z page, then visits each trail's detail page for its current open/closed status.
3. Any status changes are written to the database and recorded in `status_history`. New trails are inserted automatically. Trails that no longer appear on the DNR listing are removed from the database.
4. Because Flask queries the database on every request, users see updated data the moment the next scraper run finishes — no app restart is needed.

---

## Scrape Interval

The scrape interval is set via the `SCRAPE_INTERVAL_HOURS` environment variable in `docker-compose.yml`:

```yaml
environment:
  - SCRAPE_INTERVAL_HOURS=12
```

**Minimum interval: 12 hours.** Values below 12 are silently raised to 12. This floor exists to avoid sending excessive automated traffic to the Minnesota DNR website. Please be a good citizen and do not lower `MIN_INTERVAL_HOURS` in `scheduler.py`.

Valid examples:

| Value | Behaviour |
|-------|-----------|
| `12`  | Scrape every 12 hours (default, recommended) |
| `24`  | Scrape once per day |
| `6`   | Ignored — 12 hours used instead |

To change the interval, edit `docker-compose.yml` and restart the scraper service:

```bash
docker-compose restart ohv-scraper
```

---

## Quick Start

### Docker (recommended)

```bash
git clone <repo-url>
cd ohv-trail-dashboard
docker-compose up --build -d

# View the dashboard
open http://localhost:8000

# Watch scraper logs
docker-compose logs -f ohv-scraper

# Run a manual scrape right now
docker-compose exec ohv-scraper python scraper.py

# Stop everything
docker-compose down
```

The database is stored at `./data/trails.db` on the host and persists across container restarts.

### Local (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Seed the database (one time)
python init_db.py

# Start the web server
python app.py          # http://localhost:8000

# Run scraper manually (separate terminal)
python scraper.py
```

To run the scraper on a schedule locally, add a crontab entry:

```
# Runs every 12 hours — do not set lower
0 */12 * * * cd /path/to/ohv-trail-dashboard && python scraper.py >> /var/log/ohv-scraper.log 2>&1
```

---

## Configuration

All configuration is done via environment variables. With Docker these are set in `docker-compose.yml`; locally you can export them in your shell or set them in a `.env` file.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_PATH` | `<app_dir>/data/trails.db` | Path to the SQLite database |
| `TEMPLATES_DIR` | `<app_dir>/templates` | Path to HTML templates |
| `SCRAPE_INTERVAL_HOURS` | `12` | Hours between scraper runs (minimum 12) |

---

## Architecture

```
ohv-trail-dashboard/
├── app.py                  Flask web app and REST API
├── scraper.py              DNR website scraper — updates the database
├── scheduler.py            Long-running loop that calls scraper.py on interval
├── init_db.py              One-time database seed (run before first start)
├── templates/
│   └── index.html          Single-page dashboard (HTML + vanilla JS)
├── data/
│   └── trails.db           SQLite database (created by init_db.py)
├── Dockerfile              Container image definition
└── docker-compose.yml      Two-service orchestration (app + scraper)
```

**Tech stack:** Python 3 · Flask · SQLite · BeautifulSoup4 · Vanilla HTML/CSS/JS · Docker

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard (server-rendered HTML) |
| GET | `/api/trails` | JSON list of all trails |
| GET | `/api/trails?status=open` | Filter by status: `open`, `closed`, `limited` |
| GET | `/api/stats` | Counts by status + `last_updated` date |
| GET | `/api/status-history/<trail_id>` | Status change history for one trail |
| GET | `/api/export?status=all` | Download trail data as CSV |

---

## Database Schema

```sql
-- Current trail data
CREATE TABLE trails (
    id              INTEGER PRIMARY KEY,
    trail_id        INTEGER UNIQUE,     -- DNR trail identifier
    name            TEXT NOT NULL,
    counties        TEXT,
    miles           INTEGER,            -- Total trail miles
    atv_miles       INTEGER,
    ohv_miles       INTEGER,
    ohm_miles       INTEGER,            -- Off-highway motorcycle
    morv_miles      INTEGER,            -- Multi-purpose off-road vehicle
    winter_miles    INTEGER,
    status          TEXT,               -- OPEN | Closed | Limited | Unknown
    status_notes    TEXT,
    last_updated    DATE,
    normal_season   TEXT,
    dnr_url         TEXT                -- Link to DNR trail detail page
);

-- Audit log of every status change
CREATE TABLE status_history (
    id          INTEGER PRIMARY KEY,
    trail_id    INTEGER,
    status      TEXT,
    status_notes TEXT,
    recorded_at TIMESTAMP,
    FOREIGN KEY (trail_id) REFERENCES trails(trail_id)
);
```

---

## Data Source & Responsible Use

Data is scraped from the [Minnesota DNR OHV Trails pages](https://www.dnr.state.mn.us/ohv/).

- This app is for **personal use only**
- The 12-hour minimum scrape interval is intentional — please respect it
- Always verify trail status with the [official DNR source](https://www.dnr.state.mn.us/ohv/az.html) before heading out

---

## Disclaimer

Trail status information may not always reflect the most current conditions. Check the official DNR website and posted signage before riding.
