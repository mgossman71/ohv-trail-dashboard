# Minnesota OHV Trail Dashboard

A personal web application for browsing Minnesota OHV trail statuses. Shows which trails are open or closed, how far each one is from your location, links to each trail's DNR page, one-click Google Maps directions, and an interactive map view with real trail locations.

---

## Features

- **Live trail status** — Open / Closed / Limited, sourced directly from the Minnesota DNR website
- **Your location** — Enter a zip code or use GPS; straight-line distances calculate automatically
- **Interactive map view** — Full-screen map with colored markers (green=open, red=closed, amber=limited), marker clustering, and popup info with directions
- **Real trail locations** — Trail coordinates are geocoded from DNR location descriptions, not just county centers
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

1. On startup, `docker compose up` launches two containers that share one database file on the host:
   - **ohv-dashboard** — the Flask web app, always running
   - **ohv-scraper** — runs `scheduler.py`, which calls `scraper.py` immediately and then again every N hours
2. `scraper.py` fetches the full trail list from the DNR A-Z page, then visits each trail's detail page for its current open/closed status.
3. Any status changes are written to the database and recorded in `status_history`. New trails are inserted automatically. Trails that no longer appear on the DNR listing are removed from the database.
4. Because Flask queries the database on every request, users see updated data the moment the next scraper run finishes — no app restart is needed.

### Trail Locations (Geocoding)

The scraper also extracts location text from each DNR detail page and geocodes it via Nominatim (OpenStreetMap) to get real trailhead coordinates. This only happens when the DNR location text has changed — not on every scrape cycle. On first run, all trails are geocoded. On subsequent runs, typically zero geocoding requests are made.

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
docker compose restart ohv-scraper
```

---

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/mgossman71/ohv-trail-dashboard.git
cd ohv-trail-dashboard
docker compose up --build -d

# View the dashboard
open http://localhost:8000

# Watch scraper logs
docker compose logs -f ohv-scraper

# Run a manual scrape right now
docker compose exec ohv-scraper python scraper.py

# Stop everything
docker compose down
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
├── app.py                  Flask web app, REST API, and map endpoints
├── scraper.py              DNR website scraper — status + location geocoding
├── scheduler.py            Long-running loop that calls scraper.py on interval
├── geocode_trails.py       Standalone script for one-off re-geocoding
├── init_db.py              One-time database seed (run before first start)
├── templates/
│   ├── index.html          Table view — stats, filters, trail list
│   └── map.html            Interactive Leaflet map view
├── data/
│   └── trails.db           SQLite database (created by init_db.py)
├── Dockerfile              Container image definition
├── docker-compose.yml      Two-service orchestration (app + scraper)
└── requirements.txt        Python dependencies
```

**Tech stack:** Python 3 · Flask · SQLite · BeautifulSoup4 · Leaflet.js · Nominatim · Docker

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Table view dashboard |
| GET | `/map` | Interactive map view |
| GET | `/api/trails` | JSON list of all trails |
| GET | `/api/trails?status=open` | Filter by status: `open`, `closed`, `limited` |
| GET | `/api/trails/geo` | GeoJSON FeatureCollection for map markers |
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
    dnr_url         TEXT,               -- Link to DNR trail detail page
    latitude        REAL,               -- Geocoded trail location
    longitude       REAL,               -- Geocoded trail location
    location_text   TEXT                -- Raw DNR location text (for change detection)
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

## Troubleshooting

### Dashboard shows "Database not found"

Run `python init_db.py` to create the database with seed data. If using Docker, restart the containers:

```bash
docker compose restart
```

### Map doesn't show trail locations correctly

The first scrape after pulling new code will geocode all trails (takes ~3-4 minutes). Check progress with:

```bash
docker compose logs -f ohv-scraper
```

If locations are still wrong after a complete scrape:

1. Check the scraper logs for geocoding failures
2. Force a full re-geocode: `docker compose exec ohv-scraper python geocode_trails.py --force`
3. Check the database directly:
   ```bash
   sqlite3 data/trails.db "SELECT name, latitude, longitude FROM trails LIMIT 5;"
   ```

### Data seems stale

Check the "Last updated" timestamp on the dashboard. The scraper runs every 12 hours by default. You can run a manual update with:

```bash
docker compose exec ohv-scraper python scraper.py
```

### Distance calculations don't work

The dashboard uses browser-side JavaScript with GeoJS API to convert zip codes to coordinates. If this is blocked by a firewall, zip-to-location won't work, but manual GPS entry will.

---

## Data Source & Responsible Use

Data is scraped from the [Minnesota DNR OHV Trails pages](https://www.dnr.state.mn.us/ohv/).

- This app is for **personal use only**
- The 12-hour minimum scrape interval is intentional — please respect it
- Trail coordinates are geocoded from DNR location descriptions via Nominatim (OpenStreetMap) — they are approximate, not exact trailhead GPS coordinates
- Always verify trail status with the [official DNR source](https://www.dnr.state.mn.us/ohv/az.html) before heading out

---

## License

MIT — do what you want with it. Consider this a template for building dashboards for other states' trail systems.