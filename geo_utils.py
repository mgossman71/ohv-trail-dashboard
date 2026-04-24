"""
geo_utils.py — Shared geocoding utilities for the OHV Trail Dashboard.

Used by both scraper.py (inline geocoding during scrape runs) and
geocode_trails.py (one-shot backfill of existing trail records).
"""

import re
import time

import requests

DNR_DETAIL_BASE = 'https://www.dnr.state.mn.us/ohv/trail_detail.html?id='

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
NOMINATIM_HEADERS = {
    'User-Agent': 'OHV-Trail-Dashboard/1.0 (geocoding; personal use)',
}

# Minnesota bounding box — reject Nominatim results outside this range
MN_LAT_MIN, MN_LAT_MAX = 43.0, 49.5
MN_LON_MIN, MN_LON_MAX = -97.5, -89.0


def extract_location_info(soup):
    """
    Extract location text and facility cities from a parsed DNR detail page.

    Args:
        soup: BeautifulSoup object of the trail detail page.

    Returns:
        (location_text, facilities_cities) where location_text is the raw text
        from the 'Location' section and facilities_cities is a list of city
        names from the 'Facilities' section.
    """
    main = soup.find(id='main_page_content') or soup.find('main') or soup.body
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
    Build a Nominatim geocode query from the trail's DNR location info.

    Priority:
    1. Specific city/place mentioned in the location description
    2. First city from facilities list
    3. County name as fallback
    """
    # Remove contact info that can confuse the geocoder
    loc = re.sub(r'\d{3}-\d{3}-\d{4}', '', location_text)
    loc = re.sub(r'[\w.+-]+@[\w-]+\.[\w.]+', '', loc)

    city_patterns = [
        r'(?:In|From|in|from|Parking (?:is )?(?:available )?in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
        r'(?:at|near|outside of|west of|east of|north of|south of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',
    ]
    found_cities = []
    for pattern in city_patterns:
        found_cities.extend(re.findall(pattern, loc))

    skip_words = {'county', 'state', 'park', 'forest', 'area', 'trail', 'highway',
                  'intersection', 'mile', 'miles', 'turn', 'go', 'parking', 'available'}
    found_cities = [c for c in found_cities if c.lower() not in skip_words]

    community_match = re.search(
        r'(?:community|city|town)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', loc
    )
    if community_match:
        found_cities.insert(0, community_match.group(1))

    if not found_cities and facilities_cities:
        found_cities = [c.split(',')[0].strip() for c in facilities_cities[:1]]

    if found_cities:
        return f"{found_cities[0]}, {county} County, Minnesota"
    return f"{county} County, Minnesota"


def geocode(query, retries=2):
    """
    Geocode a query string using Nominatim (OpenStreetMap).

    Validates that the result falls within Minnesota's bounding box.
    Respects the Nominatim usage policy with a 1-second caller-side delay
    between requests (the caller is responsible for adding that delay).

    Returns (lat, lon) on success, or None if no valid result found.
    """
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
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                if MN_LAT_MIN <= lat <= MN_LAT_MAX and MN_LON_MIN <= lon <= MN_LON_MAX:
                    return lat, lon
                return None  # Valid response but outside Minnesota
            return None
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                print(f"      Geocode error: {e}")
                return None
    return None
