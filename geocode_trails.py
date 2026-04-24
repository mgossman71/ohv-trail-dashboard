#!/usr/bin/env python3
"""
geocode_trails.py — Standalone script for one-off trail geocoding.

Reads the Location section from each trail's DNR detail page, extracts
city names and place references, geocodes them via Nominatim (OpenStreetMap),
and updates the latitude/longitude and location_text in the database.

Writing location_text is important: scraper.py uses it to detect when a
trail's location info has changed and needs re-geocoding. Without it, the
next scraper run would re-geocode every trail unnecessarily.

Note: The scraper (scraper.py) handles geocoding automatically during each
scrape cycle, only re-geocoding when location text changes. You only need
this script to force a full re-geocode outside the normal scrape schedule.

Usage:
    python geocode_trails.py

Uses a 1-second delay between Nominatim requests per their usage policy.
"""

import os
import sys
import time

import requests
from bs4 import BeautifulSoup

from geo_utils import extract_location_info, build_geocode_query, geocode

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'data', 'trails.db'))
DNR_DETAIL_BASE = 'https://www.dnr.state.mn.us/ohv/trail_detail.html?id='

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; OHV-Trail-Dashboard/1.0; personal use)',
}
# Nominatim usage policy requires at least 1 second between requests
GEOCODE_DELAY = 1.0


def get_db():
    import sqlite3
    if not os.path.exists(DATABASE):
        print(f"ERROR: Database not found at {DATABASE}")
        sys.exit(1)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_page(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, 'lxml')
        except requests.RequestException as e:
            wait = 2 ** attempt
            print(f"  Request failed ({e}), retrying in {wait}s...")
            time.sleep(wait)
    return None


def run():
    conn = get_db()
    trails = conn.execute(
        'SELECT trail_id, name, counties, latitude, longitude FROM trails ORDER BY trail_id'
    ).fetchall()

    print(f"Geocoding {len(trails)} trails from DNR detail pages...")
    print()

    updated = 0
    fallback_count = 0
    failed = 0

    for i, trail in enumerate(trails, 1):
        tid = trail['trail_id']
        name = trail['name']
        county = trail['counties'].split(',')[0].strip() if trail['counties'] else ''

        print(f"[{i}/{len(trails)}] {name} (ID={tid})")

        # Fetch location info from the DNR detail page
        soup = fetch_page(f"{DNR_DETAIL_BASE}{tid}")
        time.sleep(0.4)

        if not soup:
            print(f"  Could not fetch detail page, skipping")
            continue

        location_text, facilities_cities = extract_location_info(soup)

        if not location_text:
            print(f"  No location info on detail page, skipping")
            continue

        query = build_geocode_query(name, location_text, facilities_cities, county)
        print(f"  Query: {query}")

        result = geocode(query)
        time.sleep(GEOCODE_DELAY)

        if not result and facilities_cities:
            # Retry with a simpler city-only query
            simple_query = f"{facilities_cities[0].split(',')[0].strip()}, Minnesota"
            print(f"  Retrying with: {simple_query}")
            result = geocode(simple_query)
            time.sleep(GEOCODE_DELAY)

        if result:
            lat, lon = result
            # Write coordinates AND location_text so the scraper's change-detection
            # doesn't re-geocode this trail on the very next run.
            conn.execute(
                'UPDATE trails SET latitude = ?, longitude = ?, location_text = ? WHERE trail_id = ?',
                (lat, lon, location_text, tid)
            )
            print(f"  → ({lat:.4f}, {lon:.4f})")
            updated += 1
        else:
            # Still write location_text even when geocoding fails — the scraper
            # will skip re-geocoding unchanged text, and will try again if the
            # DNR updates the location description.
            conn.execute(
                'UPDATE trails SET location_text = ? WHERE trail_id = ?',
                (location_text, tid)
            )
            print(f"  Geocode failed, keeping existing coords")
            failed += 1

    conn.commit()
    conn.close()

    print(f"\nDone: {updated} updated, {failed} failed")


if __name__ == '__main__':
    run()
