"""
app.py — OHV Trail Dashboard web application

A Flask application that serves the Minnesota OHV trail status dashboard.
Trail data lives in a SQLite database that is updated by scraper.py running
on a schedule via scheduler.py.  Because Flask queries the database on every
request, scraper updates are visible to the user immediately — no app restart
is ever required.

Routes:
    GET /                           Main dashboard (server-rendered HTML)
    GET /api/trails                 JSON list of trails, optional ?status= filter
    GET /api/stats                  JSON summary counts + last_updated date
    GET /api/status-history/<id>    JSON status change history for one trail
    GET /api/export                 CSV download, optional ?status= filter

Configuration (environment variables):
    DATABASE_PATH   Path to the SQLite database file.
                    Default: <app_dir>/data/trails.db
    TEMPLATES_DIR   Path to the Jinja2 templates directory.
                    Default: <app_dir>/templates
"""

import os
import csv
import io
import sqlite3
from flask import Flask, render_template, request, jsonify

# Portable paths — override DATABASE_PATH env var when running outside Docker
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'data', 'trails.db'))
TEMPLATES_DIR = os.environ.get('TEMPLATES_DIR', os.path.join(BASE_DIR, 'templates'))

app = Flask(__name__, template_folder=TEMPLATES_DIR)

os.makedirs(os.path.dirname(DATABASE), exist_ok=True)


def get_db():
    """Get database connection. Returns None if DB not found."""
    if not os.path.exists(DATABASE):
        print(f"Database not found at {DATABASE}")
        return None
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def init_db():
    """Create database tables if they don't exist. Safe to call on every startup."""
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trails (
            id INTEGER PRIMARY KEY,
            trail_id INTEGER UNIQUE,
            name TEXT NOT NULL,
            counties TEXT,
            miles INTEGER,
            atv_miles INTEGER,
            ohv_miles INTEGER,
            ohm_miles INTEGER,
            morv_miles INTEGER,
            winter_miles INTEGER,
            status TEXT,
            status_notes TEXT,
            last_updated DATE,
            normal_season TEXT,
            dnr_url TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY,
            trail_id INTEGER,
            status TEXT,
            status_notes TEXT,
            recorded_at TIMESTAMP,
            FOREIGN KEY (trail_id) REFERENCES trails(trail_id)
        )
    ''')
    # Add dnr_url column to existing databases that don't have it
    try:
        conn.execute('ALTER TABLE trails ADD COLUMN dnr_url TEXT')
    except Exception:
        pass  # Column already exists
    conn.commit()
    conn.close()


def normalize_status(raw):
    """
    Return a canonical status string for display and SQL filtering.
    Maps any raw DNR status text to one of: OPEN, Closed, Limited, Unknown.
    Must stay in sync with the LOWER(status) comparisons in trails_query().
    """
    if not raw:
        return 'Unknown'
    s = raw.strip().lower()
    if s == 'open' or s == 'open':
        return 'OPEN'
    if 'open' in s and 'limited' not in s:
        return 'OPEN'
    if 'limited' in s:
        return 'Limited'
    if 'closed' in s:
        return 'Closed'
    return raw.strip()


def get_county_coords():
    """
    Approximate geographic center coordinates (lat, lng) for Minnesota counties
    that contain OHV trails.

    These are used by the dashboard's client-side JavaScript to calculate
    straight-line distance from the user's location to each trail.  They are
    county-center estimates, not exact trailhead coordinates, so distances are
    approximate — useful for a rough "how far away is this?" gauge.
    """
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
        # Multi-county trails: use geographic midpoint of the listed counties
        'Beltrami, Marshall': (48.10, -95.60),
        'Clay, Norman, Polk': (47.30, -96.45),
        'Crow Wing, Aitkin':  (46.55, -93.70),
        'Lake, St. Louis':    (47.47, -91.94),
    }


def build_trail_dict(row):
    """
    Convert a sqlite3.Row into a plain dict and attach computed fields:
        dnr_url         Full URL to the trail's DNR detail page.
        trail_lat/lng   Approximate coordinates from get_county_coords(),
                        used by the frontend for distance calculation.
        status_display  Canonical status string from normalize_status().
    """
    d = dict(row)
    if not d.get('dnr_url') and d.get('trail_id'):
        d['dnr_url'] = f"https://www.dnr.state.mn.us/ohv/trail_detail.html?id={d['trail_id']}"
    # Coordinates for client-side distance calculation
    county_coords = get_county_coords()
    coords = county_coords.get(d.get('counties', ''))
    d['trail_lat'] = coords[0] if coords else None
    d['trail_lng'] = coords[1] if coords else None
    d['status_display'] = normalize_status(d.get('status', ''))
    return d


def trails_query(status_filter='all', query=''):
    """
    Query the trails table and return a list of trail dicts.

    Args:
        status_filter   'all' | 'open' | 'closed' | 'limited'
        query           Free-text search against trail name and counties.
    """
    conn = get_db()
    if not conn:
        return []

    sql = '''
        SELECT trail_id, name, counties, miles, atv_miles, ohv_miles,
               ohm_miles, morv_miles, winter_miles, status, status_notes,
               last_updated, normal_season, dnr_url
        FROM trails WHERE 1=1
    '''
    params = []

    if query:
        sql += ' AND (LOWER(name) LIKE ? OR LOWER(counties) LIKE ?)'
        params.extend([f'%{query.lower()}%', f'%{query.lower()}%'])

    if status_filter == 'open':
        sql += " AND LOWER(status) = 'open'"
    elif status_filter == 'closed':
        sql += " AND LOWER(status) = 'closed'"
    elif status_filter == 'limited':
        sql += " AND LOWER(status) = 'limited'"

    sql += ' ORDER BY name ASC'
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [build_trail_dict(r) for r in rows]


@app.route('/')
def index():
    query = request.args.get('query', '')
    status_filter = request.args.get('status', 'all')
    trails = trails_query(status_filter=status_filter, query=query)
    return render_template('index.html', trails=trails, status_filter=status_filter)


@app.route('/api/trails')
def api_trails():
    status_filter = request.args.get('status', 'all')
    return jsonify(trails_query(status_filter=status_filter))


@app.route('/api/stats')
def api_stats():
    conn = get_db()
    if not conn:
        return jsonify({'total': 0, 'open': 0, 'closed': 0, 'limited': 0})

    total = conn.execute('SELECT COUNT(*) FROM trails').fetchone()[0]
    open_count = conn.execute("SELECT COUNT(*) FROM trails WHERE LOWER(status) = 'open'").fetchone()[0]
    closed_count = conn.execute("SELECT COUNT(*) FROM trails WHERE LOWER(status) = 'closed'").fetchone()[0]
    limited_count = conn.execute("SELECT COUNT(*) FROM trails WHERE LOWER(status) = 'limited'").fetchone()[0]
    last_updated = conn.execute("SELECT MAX(last_updated) FROM trails").fetchone()[0]
    conn.close()

    return jsonify({
        'total': total,
        'open': open_count,
        'closed': closed_count,
        'limited': limited_count,
        'last_updated': last_updated,
    })


@app.route('/api/status-history/<int:trail_id>')
def status_history(trail_id):
    conn = get_db()
    if not conn:
        return jsonify([])
    rows = conn.execute(
        'SELECT status, status_notes, recorded_at FROM status_history WHERE trail_id = ? ORDER BY recorded_at DESC',
        (trail_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/export')
def api_export():
    status_filter = request.args.get('status', 'all')
    trails = trails_query(status_filter=status_filter)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Trail ID', 'Name', 'Counties', 'Total Miles', 'ATV', 'OHV', 'OHM', 'MORV',
                     'Winter', 'Status', 'Status Notes', 'Last Updated', 'Normal Season', 'DNR URL'])
    for t in trails:
        writer.writerow([
            t.get('trail_id'), t.get('name'), t.get('counties'), t.get('miles'),
            t.get('atv_miles'), t.get('ohv_miles'), t.get('ohm_miles'), t.get('morv_miles'),
            t.get('winter_miles'), t.get('status'), t.get('status_notes'),
            t.get('last_updated'), t.get('normal_season'), t.get('dnr_url'),
        ])
    output.seek(0)
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=trails_{status_filter}.csv',
    }


if __name__ == '__main__':
    init_db()
    print(f"Database: {DATABASE}")
    app.run(host='0.0.0.0', port=8000, debug=False)
