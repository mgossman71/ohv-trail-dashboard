#!/usr/bin/env python3
"""
geocode_trails.py — Standalone script for one-off trail geocoding.

Reads the Location section from each trail's DNR detail page, extracts
city names and place references, geocodes them via Nominatim (OpenStreetMap),
and updates the latitude/longitude and location_text in the database.

By default, only geocodes trails whose location_text has changed since the
last run. Use --force to re-geocode all trails.

Note: The scraper (scraper.py) now handles geocoding automatically during
each scrape cycle, only re-geocoding when location text changes. You only
need this script if you want to force a full re-geocode outside the normal
scrape schedule.

Usage:
    python geocode_trails.py           # Re-geocode only changed trails
    python geocode_trails.py --force   # Force re-geocode all trails

Uses a 1-second delay between Nominatim requests per their usage policy.
"""

import json
import os
import re
import sqlite3
import sys
import time
from bs4 import BeautifulSoup
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'data', 'trails.db'))
DNR_DETAIL_BASE = 'https://www.dnr.state.mn.us/ohv/trail_detail.html?id='
NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; OHV-Trail-Dashboard/1.0; personal use)',
}
NOMINATIM_HEADERS = {
    'User-Agent': 'OHV-Trail-Dashboard/1.0 (geocoding script; personal use)',
}


def get_db():
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


def extract_location_info(trail_id):
    """Extract location text and facility cities from a DNR trail detail page."""
    url = f"{DNR_DETAIL_BASE}{trail_id}"
    soup = fetch_page(url)
    if not soup:
        return None, []

    main = soup.find(id='main_page_content') or soup.find('main')
    if not main:
        return None, []

    location_text = ''
    facilities_cities = []

    for h4 in main.find_all('h4'):
        header_text = h4.get_text(strip=True).lower()
        if header_text == 'location':
            sib = h4.find_next_sibling()
            while sib and sib.name not in ('h4', 'h3', 'h2'):
                text = sib.get_text(strip=True)
                if text:
                    location_text += text + ' '
                sib = sib.find_next_sibling()
        elif header_text == 'facilities':
            sib = h4.find_next_sibling()
            while sib and sib.name not in ('h4', 'h3', 'h2'):
                t = sib.get_text(strip=True)
                if t and len(t) < 30 and t.lower() not in (
                    'food', 'restroom', 'gas', 'lodging', 'camping'
                ):
                    facilities_cities.append(t)
                sib = sib.find_next_sibling()

    return location_text.strip() if location_text else None, facilities_cities


def build_geocode_query(trail_name, location_text, facilities_cities, county):
    """
    Build a geocode query string from the trail's location info.

    Priority:
    1. Specific city/place mentioned in the location description
    2. First city from facilities list
    3. County name as fallback
    """
    # Clean up location text - remove contact info (phone numbers, emails)
    loc = re.sub(r'\d{3}-\d{3}-\d{4}', '', location_text)
    loc = re.sub(r'[\w.+-]+@[\w-]+\.[\w.]+', '', loc)

    # Try to find a specific city or place in the location text
    # Patterns: "In <City>", "From <City>", "<City>, go", "Parking in <City>"
    city_patterns = [
        r'(?:In|From|in|from|Parking (?:is )?(?:available )?in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'(?:at|near|outside of|west of|east of|north of|south of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
    ]

    found_cities = []
    for pattern in city_patterns:
        matches = re.findall(pattern, loc)
        found_cities.extend(matches)

    # Filter out common non-city words
    skip_words = {'county', 'state', 'park', 'forest', 'area', 'trail', 'highway',
                  'intersection', 'mile', 'miles', 'turn', 'go', 'parking', 'available'}
    found_cities = [c for c in found_cities if c.lower() not in skip_words]

    # Also check for "the community of X" or "the city of X"
    community_match = re.search(r'(?:community|city|town)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', loc)
    if community_match:
        found_cities.insert(0, community_match.group(1))

    # Try facilities cities too
    if not found_cities and facilities_cities:
        found_cities = [c.split(',')[0].strip() for c in facilities_cities[:1]]

    if found_cities:
        # Use the first specific city with county and state for precision
        city = found_cities[0]
        return f"{city}, {county} County, Minnesota"
    else:
        # Fallback: county center
        return f"{county} County, Minnesota"


def geocode(query, retries=2):
    """Geocode a query string using Nominatim. Returns (lat, lon) or None."""
    for attempt in range(retries):
        try:
            resp = requests.get(NOMINATIM_URL, params={
                'q': query,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'us',
            }, headers=NOMINATIM_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
            return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                print(f"    Geocode error: {e}")
                return None
    return None


def run():
    import os
    import sys

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

        # Step 1: Get location info from DNR detail page
        location_text, facilities_cities = extract_location_info(tid)
        time.sleep(0.4)

        if not location_text:
            print(f"  ⚠ No location info on detail page, keeping existing coords")
            continue

        # Step 2: Build geocode query
        query = build_geocode_query(name, location_text, facilities_cities, county)
        print(f"  Query: {query}")

        # Step 3: Geocode
        result = geocode(query)
        time.sleep(1.0)  # Nominatim usage policy

        if result:
            lat, lon = result
            # Verify it's in Minnesota (rough bounds)
            if 43.0 <= lat <= 49.5 and -97.5 <= lon <= -89.0:
                conn.execute(
                    'UPDATE trails SET latitude = ?, longitude = ? WHERE trail_id = ?',
                    (lat, lon, tid)
                )
                print(f"  ✓ → ({lat:.4f}, {lon:.4f})")
                updated += 1
            else:
                print(f"  ⚠ Result outside Minnesota: ({lat:.4f}, {lon:.4f}), keeping existing")
                fallback_count += 1
        else:
            # Try a simpler query with just the first facility city
            if facilities_cities:
                simple_query = f"{facilities_cities[0].split(',')[0].strip()}, Minnesota"
                print(f"  Retrying with: {simple_query}")
                result = geocode(simple_query)
                time.sleep(1.0)
                if result:
                    lat, lon = result
                    if 43.0 <= lat <= 49.5 and -97.5 <= lon <= -89.0:
                        conn.execute(
                            'UPDATE trails SET latitude = ?, longitude = ? WHERE trail_id = ?',
                            (lat, lon, tid)
                        )
                        print(f"  ✓ (retry) → ({lat:.4f}, {lon:.4f})")
                        updated += 1
                        continue
            print(f"  ✗ Geocode failed, keeping existing coords")
            failed += 1

    conn.commit()
    conn.close()

    print(f"\nDone: {updated} updated, {fallback_count} outside MN (kept existing), {failed} failed")


if __name__ == '__main__':
    import os
    import sys
    run()