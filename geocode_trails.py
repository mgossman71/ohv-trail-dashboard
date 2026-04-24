#!/usr/bin/env python3
"""
geocode_trails.py — Geocode OHV trail locations using Nominatim (OpenStreetMap).

Searches for each trail name + "Minnesota" and stores the best-match coordinates
in the trails database. Falls back to county center coordinates when geocoding
fails or returns low-confidence results.

Run once (or re-run when trails are added):
    python3 geocode_trails.py

Rate-limited to 1 request/second per Nominatim usage policy.
"""

import sqlite3
import time
import json
import urllib.request
import urllib.parse
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'data', 'trails.db'))

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
USER_AGENT = 'OHVTrailDashboard/1.0 (mgossman71@github)'
REQUEST_DELAY = 1.1  # seconds between requests (Nominatim policy: max 1/sec)


def geocode_search(query):
    """Search Nominatim and return list of results."""
    params = urllib.parse.urlencode({
        'q': query,
        'format': 'json',
        'limit': 5,
        'countrycodes': 'us',
        'addressdetails': 1,
    })
    url = f'{NOMINATIM_URL}?{params}'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f'  Geocoding error: {e}')
        return []


def get_county_coords():
    """Same county center coords used by app.py for fallback."""
    return {
        'Aitkin':       (46.60, -93.41),
        'Becker':       (46.93, -95.66),
        'Beltrami':     (47.97, -94.90),
        'Carlton':      (46.59, -92.68),
        'Cass':         (46.95, -94.33),
        'Clay':         (46.89, -96.50),
        'Cook':         (47.87, -90.55),
        'Crow Wing':    (46.50, -94.07),
        'Fillmore':     (43.67, -92.09),
        'Grant':        (45.93, -96.02),
        'Hubbard':      (47.10, -94.92),
        'Itasca':       (47.50, -93.62),
        'Koochiching':  (48.22, -93.78),
        'Lake':         (47.38, -91.39),
        'Lyon':         (44.41, -95.83),
        'Marshall':     (48.35, -96.37),
        'Meeker':       (45.12, -94.52),
        'Mille Lacs':   (46.11, -93.64),
        'Morrison':     (46.02, -94.26),
        'Norman':       (47.33, -96.46),
        'Pine':         (46.12, -92.72),
        'Polk':         (47.77, -96.41),
        'Roseau':       (48.73, -95.85),
        'St. Louis':    (47.57, -92.49),
        'Swift':        (45.29, -95.84),
        'Wabasha':      (44.27, -92.03),
        'Wadena':       (46.58, -95.00),
        'Winona':       (43.90, -91.66),
        'Beltrami, Marshall': (48.10, -95.60),
        'Clay, Norman, Polk': (47.30, -96.45),
        'Crow Wing, Aitkin':  (46.55, -93.70),
        'Lake, St. Louis':    (47.47, -91.94),
    }


def best_result_for_trail(trail_name, counties, results):
    """
    Pick the best geocoding result for a trail.

    Prioritizes results that:
    1. Are in Minnesota
    2. Match the trail's county
    3. Have a higher importance/relevance score
    """
    if not results:
        return None

    # Try to match county name in the result address
    county_list = [c.strip() for c in counties.split(',')] if counties else []

    for r in results:
        addr = r.get('address', {})
        state = addr.get('state', '')
        result_county = addr.get('county', '')
        # Prefer results in Minnesota and in the right county
        if state == 'Minnesota':
            for c in county_list:
                if c.lower() in result_county.lower():
                    return r
            # If no county match, still accept MN results
            if len(results) == 1:
                return r

    # Fall back to first result in Minnesota
    for r in results:
        if r.get('address', {}).get('state') == 'Minnesota':
            return r

    # Fall back to any result in the US
    return results[0] if results else None


def main():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row

    # Add lat/lng columns if they don't exist
    try:
        conn.execute('ALTER TABLE trails ADD COLUMN latitude REAL')
    except Exception:
        pass
    try:
        conn.execute('ALTER TABLE trails ADD COLUMN longitude REAL')
    except Exception:
        pass
    conn.commit()

    rows = conn.execute('SELECT trail_id, name, counties FROM trails ORDER BY trail_id').fetchall()
    county_coords = get_county_coords()

    geocoded = 0
    fallback = 0
    failed = 0

    print(f'Geocoding {len(rows)} trails...\n')

    for i, row in enumerate(rows):
        trail_id = row['trail_id']
        name = row['name']
        counties = row['counties'] or ''

        # Try multiple search queries, most specific first
        queries = [
            f'{name}, Minnesota',
            f'{name} trail, Minnesota',
        ]

        # If multi-county, try just the first county
        first_county = counties.split(',')[0].strip() if counties else ''
        if first_county:
            queries.append(f'{name}, {first_county} County, Minnesota')

        best = None
        for q in queries:
            print(f'  [{i+1}/{len(rows)}] Searching: {q}')
            results = geocode_search(q)
            time.sleep(REQUEST_DELAY)
            candidate = best_result_for_trail(name, counties, results)
            if candidate:
                # Check that it's actually in Minnesota
                addr = candidate.get('address', {})
                state = addr.get('state', '')
                if state == 'Minnesota' or not state:
                    best = candidate
                    break

        if best:
            lat = float(best['lat'])
            lng = float(best['lon'])
            conn.execute('UPDATE trails SET latitude = ?, longitude = ? WHERE trail_id = ?',
                          (lat, lng, trail_id))
            geocoded += 1
            print(f'    ✓ {name} → ({lat:.4f}, {lng:.4f}) — {best.get("display_name", "")[:60]}')
        else:
            # Fall back to county center
            coords = county_coords.get(counties)
            if not coords and first_county:
                coords = county_coords.get(first_county)
            if coords:
                conn.execute('UPDATE trails SET latitude = ?, longitude = ? WHERE trail_id = ?',
                              (coords[0], coords[1], trail_id))
                fallback += 1
                print(f'    ⚠ {name} → county fallback ({coords[0]:.4f}, {coords[1]:.4f})')
            else:
                failed += 1
                print(f'    ✗ {name} — no geocode result and no county fallback!')

        # Commit every 10 trails
        if (i + 1) % 10 == 0:
            conn.commit()

    conn.commit()
    conn.close()

    print(f'\nDone!')
    print(f'  Geocoded: {geocoded}')
    print(f'  County fallback: {fallback}')
    print(f'  Failed: {failed}')


if __name__ == '__main__':
    main()