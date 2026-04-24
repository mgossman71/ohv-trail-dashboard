"""
scraper.py — OHV Trail Dashboard data scraper

Fetches current trail status and location info from the Minnesota DNR OHV
website and writes updates directly to the SQLite database. The Flask app
reads the database on every request, so changes are visible immediately after
each scrape with no application restart required.

Data sources:
    Trail listing:  https://www.dnr.state.mn.us/ohv/az.html
                    Table of all trails with IDs, mileage, and county.
    Trail status:   https://www.dnr.state.mn.us/ohv/trail_detail.html?id=<ID>
                    Individual detail page scraped for current open/closed status
                    and the Location section (trailhead directions, city names).

Scraping behaviour:
    - Fetches the full trail list first, then visits each detail page.
    - REQUEST_DELAY (0.5 s) is applied between each detail page request to
      avoid hammering the DNR server.
    - Each request retries up to 3 times with exponential back-off before
      giving up on that trail.
    - Status changes are recorded in the status_history table.
    - Trail names from the listing are never allowed to overwrite a longer,
      more descriptive name already in the database (guards against the DNR
      abbreviated link text for Soo Line trails).

Geocoding behaviour:
    - Extracts city names and trailhead directions from the Location section
      of each DNR detail page.
    - Geocodes via Nominatim (OpenStreetMap) at 1 request/second.
    - Stores coordinates in the trails table for use by the map view and
      distance calculations.
    - Only re-geocodes if the location text from DNR has changed. On first run,
      all trails are geocoded. On subsequent runs, typically 0 geocoding
      requests are made unless the DNR updated a trail's location info.

Run manually:
    python scraper.py

Scheduled automatically:
    scheduler.py calls this script on the configured SCRAPE_INTERVAL_HOURS.
    Minimum interval is 12 hours — see scheduler.py for details.
"""

import os
import sqlite3
import sys
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from geo_utils import extract_location_info, build_geocode_query, geocode

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'data', 'trails.db'))

DNR_AZ_URL = 'https://www.dnr.state.mn.us/ohv/az.html'
DNR_DETAIL_BASE = 'https://www.dnr.state.mn.us/ohv/trail_detail.html?id='

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; OHV-Trail-Dashboard/1.0; personal use)',
}

# How long to wait between individual trail detail page requests (seconds)
REQUEST_DELAY = 0.5
# How long to wait between Nominatim geocoding requests (usage policy requires >=1s)
GEOCODE_DELAY = 1.0


def get_db():
    """Return a sqlite3 connection, exiting with an error if the database is missing."""
    if not os.path.exists(DATABASE):
        print(f"ERROR: Database not found at {DATABASE}. Run init_db.py first.")
        sys.exit(1)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn



def normalize_status(raw):
    """Normalize raw DNR status text to one of: OPEN, Closed, Limited, Unknown."""
    if not raw:
        return 'Unknown', ''
    text = raw.strip()
    lower = text.lower()

    if lower == 'open':
        return 'OPEN', ''
    if lower.startswith('open') and 'limited' not in lower:
        return 'OPEN', text
    if 'limited' in lower:
        return 'Limited', text
    if 'closed' in lower:
        return 'Closed', text
    # Edge cases seen in the data
    if 'route change' in lower:
        return 'Closed', text
    if 'atv' in lower and 'not allowed' in lower:
        return 'Closed', text
    if 'see individual' in lower:
        return 'Closed', text

    return 'Closed', text  # Default closed — safer than assuming open


def fetch_page(url, retries=3):
    """Fetch a URL and return a BeautifulSoup object, or None after all retries fail."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, 'lxml')
        except requests.RequestException as e:
            wait = 2 ** attempt
            print(f"  Request failed ({e}), retrying in {wait}s...")
            time.sleep(wait)
    print(f"  ERROR: Failed to fetch {url} after {retries} attempts.")
    return None


def scrape_trail_detail_name(trail_id):
    """
    Fetch the trail detail page and extract the real trail name from the
    page heading. The A-Z listing sometimes abbreviates names (e.g. showing
    "Aitkin County" instead of "Soo Line North Trail: Aitkin County").

    Returns the full trail name string, or None if the page can't be fetched.
    """
    url = f"{DNR_DETAIL_BASE}{trail_id}"
    soup = fetch_page(url)
    if not soup:
        return None
    main = soup.find(id='main_page_content') or soup.find('main') or soup.body
    if main:
        for heading in main.find_all(['h1', 'h2', 'h3']):
            text = heading.get_text(strip=True)
            # Skip generic headings like "OHV Trail Detail"
            if text and text.lower() not in ('ohv trail detail', 'ohv trails'):
                return text
    return None


def _safe_int(cells, cell_index):
    """Extract an integer from a table cell, returning 0 for missing or non-numeric values."""
    if cell_index >= len(cells):
        return 0
    val = cells[cell_index].get_text(strip=True).replace(',', '')
    try:
        return int(val) if val and val.isdigit() else 0
    except Exception:
        return 0


def scrape_trail_list():
    """
    Scrape the DNR A-Z trail listing page (az.html).

    Returns a list of dicts, one per trail:
        trail_id    int     DNR numeric trail identifier
        name        str     Trail name (from link text)
        counties    str     County or counties the trail is in
        miles       int     Total trail miles
        atv_miles   int     Miles designated for ATVs
        ohv_miles   int     Miles designated for OHVs
        ohm_miles   int     Miles designated for off-highway motorcycles
        morv_miles  int     Miles designated for MORVs (always 0 from listing)
        winter_miles int    Miles open in winter
        dnr_url     str     Full URL to the trail's detail page
    """
    print(f"Fetching trail list from {DNR_AZ_URL}")
    soup = fetch_page(DNR_AZ_URL)
    if not soup:
        return []

    table = soup.find('table', id='ohv_trails')
    if not table:
        # Fallback: look for any table with trail links
        table = soup.find('table')
    if not table:
        print("  ERROR: Could not find trails table on az.html")
        return []

    trails = []
    rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 2:
            continue

        # First cell: trail name with link to detail page
        link_tag = cells[0].find('a', href=True)
        if not link_tag:
            continue

        href = link_tag['href']
        name = link_tag.get_text(strip=True)

        # Extract trail_id from URL like /ohv/trail_detail.html?id=33
        trail_id = None
        if 'id=' in href:
            try:
                trail_id = int(href.split('id=')[-1].split('&')[0])
            except ValueError:
                pass
        if not trail_id:
            continue

        # If the listing shows just a bare county name (e.g. "Aitkin County",
        # "Mille Lacs County") the DNR abbreviated a multi-section trail.
        # Fetch the real name from the detail page instead.
        # Exception list guards against county-named trails that ARE the real name
        # (Grant County Trail, Meeker County Trail, Soo Line trails).
        if (name.endswith(' County') and
                'Soo' not in name and 'Grant' not in name and 'Meeker' not in name):
            print(f"    Fetching real name for trail {trail_id} (listed as \"{name}\")...")
            real_name = scrape_trail_detail_name(trail_id)
            if real_name:
                print(f"    → {real_name}")
                name = real_name
                time.sleep(REQUEST_DELAY)

        # Column order from DNR az.html: Name, Miles, ATV 1/2, OHM, ORV/OHV, Winter, County, Map
        total_miles  = _safe_int(cells, 1)
        atv_miles    = _safe_int(cells, 2)
        ohm_miles    = _safe_int(cells, 3)
        ohv_miles    = _safe_int(cells, 4)
        winter_miles = _safe_int(cells, 5)
        counties = cells[6].get_text(strip=True) if len(cells) > 6 else ''

        trails.append({
            'trail_id': trail_id,
            'name': name,
            'counties': counties,
            'miles': total_miles,
            'atv_miles': atv_miles,
            'ohv_miles': ohv_miles,
            'ohm_miles': ohm_miles,
            'morv_miles': 0,
            'winter_miles': winter_miles,
            'dnr_url': f"{DNR_DETAIL_BASE}{trail_id}",
        })

    print(f"  Found {len(trails)} trails in listing")
    return trails


def scrape_trail_status(trail_id):
    """
    Scrape a single trail detail page for its current open/closed status
    and location info.

    Tries three strategies in order:
        1. Look for a heading labelled 'closure', 'status', or 'current' and
           read the adjacent content.
        2. Look for a table with a 'status' or 'closure' column header.
        3. Full-text scan of the page body for the first occurrence of
           'closed for season', 'closed', 'open', or 'limited'.

    Returns (status, status_notes, normal_season, location_text, facilities_cities)
    on success, or None if the page could not be fetched or no status text
    was found.
    """
    url = f"{DNR_DETAIL_BASE}{trail_id}"
    soup = fetch_page(url)
    if not soup:
        return None

    status_text = ''
    notes_text = ''
    normal_season = ''

    main = soup.find(id='main_page_content') or soup.find('main') or soup.body

    if not main:
        return None

    # Strategy 1: Look for a closure/status table or labeled section
    for heading in main.find_all(['h2', 'h3', 'h4', 'strong', 'dt']):
        text = heading.get_text(strip=True).lower()
        if any(kw in text for kw in ('closure', 'status', 'current')):
            sibling = heading.find_next_sibling()
            if sibling:
                status_text = sibling.get_text(separator=' ', strip=True)
            else:
                parent_next = heading.parent.find_next_sibling()
                if parent_next:
                    status_text = parent_next.get_text(separator=' ', strip=True)
            break

    # Strategy 2: Look for tables with status columns
    if not status_text:
        for tbl in main.find_all('table'):
            headers = [th.get_text(strip=True).lower() for th in tbl.find_all('th')]
            if any('status' in h or 'closure' in h for h in headers):
                rows = tbl.find_all('tr')[1:]
                if rows:
                    cells = rows[0].find_all('td')
                    if cells:
                        status_text = cells[0].get_text(strip=True)
                break

    # Strategy 3: Search for "open" or "closed" keywords
    if not status_text:
        body_text = main.get_text(separator=' ', strip=True)
        lower_body = body_text.lower()
        for kw in ('closed for season', 'closed', 'open', 'limited'):
            idx = lower_body.find(kw)
            if idx != -1:
                snippet = body_text[max(0, idx - 20):idx + 80].strip()
                status_text = snippet
                break

    # Look for normal season info
    for tag in main.find_all(['p', 'li', 'dd']):
        t = tag.get_text(strip=True).lower()
        if 'season' in t or 'open from' in t or 'open april' in t or 'year round' in t:
            normal_season = tag.get_text(strip=True)
            break

    if not status_text:
        return None

    norm_status, notes = normalize_status(status_text)

    # Extract location info from the same page
    location_text, facilities_cities = extract_location_info(soup)

    return norm_status, notes or notes_text, normal_season, location_text, facilities_cities


def update_database(trails_from_listing, status_map, location_map=None):
    """
    Write scraped trail data, statuses, and geocoded coordinates to the database.

    - Trails already in the database are updated in-place.
    - New trails (not previously seeded) are inserted.
    - Trails in the database that are NOT in the current scrape are deleted —
      this keeps the database in sync when the DNR retires a trail system.
    - A row is added to status_history whenever a trail's status changes.
    - Trail names from the scrape are never allowed to overwrite a longer
      existing name (protects against DNR abbreviated link text).
    - If location_map contains geocoded coords for a trail, those are written
      to latitude/longitude columns, and location_text is stored for
      change detection (avoids re-geocoding unchanged data).

    location_map values are dicts with keys: loc_text, fac_cities, lat, lon.
    lat/lon are None when geocoding was skipped or failed.
    """
    if location_map is None:
        location_map = {}
    conn = get_db()
    updated = 0
    inserted = 0
    status_changes = 0

    for trail in trails_from_listing:
        tid = trail['trail_id']
        status_info = status_map.get(tid)

        if status_info:
            status, notes, season = status_info
        else:
            status, notes, season = 'Closed', '', ''

        existing = conn.execute(
            'SELECT status, name FROM trails WHERE trail_id = ?', (tid,)
        ).fetchone()

        loc_info = location_map.get(tid, {})
        loc_text = loc_info.get('loc_text')
        geo_lat  = loc_info.get('lat')
        geo_lon  = loc_info.get('lon')

        if existing:
            old_status = existing['status']
            # Don't overwrite a descriptive name with a bare county name from the listing.
            # The DNR az.html abbreviates some Soo Line trail links to just "Aitkin County" etc.
            scraped_name  = trail['name']
            existing_name = existing['name']
            use_name = scraped_name if len(scraped_name) > len(existing_name) or not existing_name else existing_name

            set_parts = [
                'name = ?', 'counties = ?', 'miles = ?', 'atv_miles = ?',
                'ohv_miles = ?', 'ohm_miles = ?', 'morv_miles = ?',
                'winter_miles = ?', 'status = ?', 'status_notes = ?',
                'last_updated = ?', 'dnr_url = ?',
            ]
            params = [
                use_name, trail['counties'], trail['miles'], trail['atv_miles'],
                trail['ohv_miles'], trail['ohm_miles'], trail['morv_miles'],
                trail['winter_miles'], status, notes,
                datetime.now().date(), trail['dnr_url'],
            ]
            if geo_lat is not None and geo_lon is not None:
                set_parts += ['latitude = ?', 'longitude = ?']
                params += [geo_lat, geo_lon]
            if loc_text is not None:
                set_parts.append('location_text = ?')
                params.append(loc_text)
            if season:
                set_parts.append('normal_season = ?')
                params.append(season)
            params.append(tid)
            conn.execute(
                f"UPDATE trails SET {', '.join(set_parts)} WHERE trail_id = ?",
                params,
            )
            updated += 1
            if old_status != status:
                conn.execute(
                    'INSERT INTO status_history (trail_id, status, status_notes, recorded_at) VALUES (?, ?, ?, ?)',
                    (tid, status, notes, datetime.now())
                )
                status_changes += 1
                print(f"  STATUS CHANGE: {use_name} — {old_status} → {status}")
        else:
            columns = [
                'trail_id', 'name', 'counties', 'miles', 'atv_miles', 'ohv_miles',
                'ohm_miles', 'morv_miles', 'winter_miles', 'status', 'status_notes',
                'last_updated', 'normal_season', 'dnr_url',
            ]
            values = [
                tid, trail['name'], trail['counties'], trail['miles'],
                trail['atv_miles'], trail['ohv_miles'], trail['ohm_miles'],
                trail['morv_miles'], trail['winter_miles'],
                status, notes, datetime.now().date(),
                season, trail['dnr_url'],
            ]
            if geo_lat is not None and geo_lon is not None:
                columns += ['latitude', 'longitude']
                values += [geo_lat, geo_lon]
            if loc_text is not None:
                columns.append('location_text')
                values.append(loc_text)
            placeholders = ', '.join('?' * len(columns))
            conn.execute(
                f"INSERT INTO trails ({', '.join(columns)}) VALUES ({placeholders})",
                values,
            )
            inserted += 1

    # Remove trails that no longer appear on the DNR listing.
    # This keeps the database in sync if the DNR retires a trail system.
    scraped_ids = [t['trail_id'] for t in trails_from_listing]
    placeholders = ','.join('?' * len(scraped_ids))
    removed_rows = conn.execute(
        f'SELECT trail_id, name FROM trails WHERE trail_id NOT IN ({placeholders})',
        scraped_ids
    ).fetchall()
    if removed_rows:
        conn.execute(f'DELETE FROM trails WHERE trail_id NOT IN ({placeholders})', scraped_ids)
        for row in removed_rows:
            print(f"  REMOVED: {row['name']} (trail_id={row['trail_id']}) — no longer on DNR listing")
    removed = len(removed_rows)

    conn.commit()
    conn.close()
    print(f"  DB update: {updated} updated, {inserted} inserted, {removed} removed, {status_changes} status changes")


def run_scraper():
    print(f"\n{'='*60}")
    print(f"OHV Trail Scraper — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {DATABASE}")
    print('='*60)

    # Step 1: Get the full trail list (names, IDs, mileage, counties)
    trails = scrape_trail_list()
    if not trails:
        print("No trails found from listing — aborting.")
        sys.exit(1)

    # Step 2: For each trail, fetch its detail page for current status + location
    print(f"\nFetching status and location for {len(trails)} trails (this takes a minute)...")
    status_map = {}
    # location_map: trail_id -> {'loc_text': str, 'fac_cities': list, 'lat': float|None, 'lon': float|None}
    location_map = {}
    for i, trail in enumerate(trails, 1):
        tid = trail['trail_id']
        print(f"  [{i}/{len(trails)}] {trail['name']}", end='... ')
        result = scrape_trail_status(tid)
        if result:
            status, notes, season, loc_text, fac_cities = result
            status_map[tid] = (status, notes, season)
            if loc_text or fac_cities:
                location_map[tid] = {'loc_text': loc_text, 'fac_cities': fac_cities, 'lat': None, 'lon': None}
            print(status)
        else:
            print("(no status found, keeping existing)")
        time.sleep(REQUEST_DELAY)

    # Step 3: Geocode only trails whose location text has changed
    conn = get_db()

    # Load stored location text for change detection
    stored_locations = {}
    for row in conn.execute('SELECT trail_id, location_text FROM trails'):
        stored_locations[row['trail_id']] = row['location_text'] or ''

    geocoded = 0
    geocode_skipped = 0
    geocode_failed = 0

    needs_geocode = {
        tid: info for tid, info in location_map.items()
        if info['loc_text'] and info['loc_text'].strip() != stored_locations.get(tid, '').strip()
    }
    geocode_skipped = len(location_map) - len(needs_geocode)

    if needs_geocode:
        print(f"\nGeocoding {len(needs_geocode)} trails with changed location info (skipping {geocode_skipped} unchanged)...")
        for tid, info in needs_geocode.items():
            loc_text = info['loc_text']
            fac_cities = info['fac_cities']
            trail_info = next((t for t in trails if t['trail_id'] == tid), None)
            if not trail_info:
                continue
            county = trail_info['counties'].split(',')[0].strip() if trail_info['counties'] else ''
            query = build_geocode_query(trail_info['name'], loc_text, fac_cities, county)
            result = geocode(query)
            time.sleep(GEOCODE_DELAY)
            if not result and fac_cities:
                simple_query = f"{fac_cities[0].split(',')[0].strip()}, Minnesota"
                result = geocode(simple_query)
                time.sleep(GEOCODE_DELAY)
            if result:
                info['lat'], info['lon'] = result
                geocoded += 1
            else:
                geocode_failed += 1
    else:
        print(f"\nAll {geocode_skipped} trail locations unchanged — skipping geocoding entirely.")

    print(f"  Geocoded: {geocoded} updated, {geocode_failed} failed, {geocode_skipped} unchanged")

    conn.close()

    # Step 4: Write to database (including geocoded coordinates)
    print(f"\nUpdating database...")
    update_database(trails, status_map, location_map)

    print(f"\nScrape complete — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    run_scraper()
