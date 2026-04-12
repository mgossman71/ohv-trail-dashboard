"""
OHV Trail Dashboard - Simple version
"""

import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder='/app/templates')
DATABASE = '/app/data/trails.db'

def get_db():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database error: {e}")
        return None

@app.route('/')
def index():
    try:
        conn = get_db()
        if not conn:
            return "Database connection failed", 500
        
        # Get all trails
        cursor = conn.execute('SELECT * FROM trails ORDER BY name ASC')
        trails = cursor.fetchall()
        
        # Convert to list of dicts
        trails_list = []
        for trail in trails:
            trails_list.append(dict(trail))
        
        # Get distances
        distances = {
            'Mille Lacs': '45-50 miles', 'Crow Wing': '55-65 miles',
            'Cass': '65-75 miles', 'Swift': '90-100 miles',
            'Fillmore': '105-115 miles', 'St. Louis': '120-135 miles',
            'Pine': '140-150 miles', 'Hubbard': '125-135 miles',
            'Becker': '135-145 miles', 'Roseau': '140-180 miles',
            'Norman': '150-160 miles', 'Itasca': '160-220 miles',
            'Koochiching': '165-175 miles', 'Beltrami': '170-250 miles',
            'Marshall': '170-260 miles', 'Carlton': '165-180 miles',
            'Aitkin': '205-225 miles', 'Cook': '225-235 miles',
            'Lake': '170-235 miles', 'Multiple': 'Varies',
        }
        
        # Add distance to each trail
        for trail in trails_list:
            trail['distance'] = distances.get(trail['counties'], 'Unknown')
        
        return render_template('index.html', trails=trails_list)
        
    except Exception as e:
        print(f"Error in index: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@app.route('/api/stats')
def api_stats():
    try:
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database error'}), 500
        
        open_count = conn.execute('SELECT COUNT(*) FROM trails WHERE status LIKE "%OPEN%"').fetchone()[0]
        closed_count = conn.execute('SELECT COUNT(*) FROM trails WHERE status LIKE "%Closed%" OR status LIKE "%CLOSED%"').fetchone()[0]
        total = conn.execute('SELECT COUNT(*) FROM trails').fetchone()[0]
        
        return jsonify({'open': open_count, 'closed': closed_count, 'total': total})
        
    except Exception as e:
        print(f"Error in stats: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print(f"Starting app with database: {DATABASE}")
    import os
    if not os.path.exists(DATABASE):
        print(f"Warning: Database not found at {DATABASE}")
    app.run(host='0.0.0.0', port=8000, debug=True)
