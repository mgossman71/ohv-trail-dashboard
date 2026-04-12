"""
OHV Trail Dashboard - Web Application
A personal tool to browse Minnesota OHV trail statuses
"""

import os
import sqlite3
from flask import Flask, render_template, request, jsonify, abort

app = Flask(__name__, template_folder='/app/templates')
DATABASE = '/app/data/trails.db'

# Ensure templates directory exists
templates_dir = '/app/templates'
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

# Ensure data directory exists
data_dir = '/app/data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

print(f"App started. Templates: {templates_dir}, Data: {data_dir}, Database: {DATABASE}")

def get_db():
    """Get database connection"""
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

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database"""
    os.makedirs('/app/data', exist_ok=True)
    conn = get_db()
    
    # Trails table
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
            normal_season TEXT
        )
    ''')
    
    # Status history for tracking changes over time
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
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Main dashboard page"""
    conn = get_db()
    if not conn:
        print("ERROR: Database connection failed")
        return "Database connection failed", 500
    
    try:
        # DEBUG: Print to console
        print(f"Request received: {request.url}")
        
        trail_count = conn.execute('SELECT COUNT(*) FROM trails').fetchone()[0]
        print(f"Trails count in DB: {trail_count}")
        
        # Get all trails with current status
        query = request.args.get('query', '').lower()
        status_filter = request.args.get('status', 'all')
        
        sql = 'SELECT trail_id, name, counties, miles, atv_miles, ohv_miles, ohm_miles, morv_miles, winter_miles, status, status_notes, last_updated, normal_season FROM trails WHERE 1=1'
        params = []
        
        if query:
            sql += ' AND (LOWER(name) LIKE ? OR LOWER(counties) LIKE ?)'
            search_term = f'%{query}%'
            params.extend([search_term, search_term])
        
        if status_filter != 'all':
            if status_filter == 'open':
                sql += ' AND status LIKE "%OPEN%"'
            elif status_filter == 'closed':
                sql += ' AND (status LIKE "%Closed%" OR status LIKE "%CLOSED%")'
            elif status_filter == 'limited':
                sql += ' AND status LIKE "%Limited%"'
        
        sql += ' ORDER BY name ASC'
        
        trails = conn.execute(sql, params).fetchall()
        conn.close()
        
        # Calculate distances
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
            'Lake': '170-235 miles', 'Multiple': 'Varies', 'Wabasha': '110-120 miles',
            'Winona': '115-125 miles', 'Grant': '255-265 miles', 'Lyon': '180-190 miles',
            'Meeker': '185-195 miles', 'Wadena': '170-180 miles', 'Polk': '160-170 miles',
            'Clay': '155-165 miles'
        }
        
        # Convert sqlite3.Row to dict and add distance
        trails_list = []
        for trail in trails:
            trail_dict = dict(trail)  # Convert to regular dict
            trail_dict['distance'] = distances.get(trail_dict['counties'], 'Unknown')
            trails_list.append(trail_dict)
        
        print(f"Rendering template with {len(trails_list)} trails")
        
        return render_template('index.html', trails=trails_list, status_filter=status_filter)
        
    except Exception as e:
        print(f"ERROR in index route: {e}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}\n\nStack trace:\n{traceback.format_exc()}", 500

@app.route('/debug')
def debug():
    """Debug endpoint to check app status"""
    try:
        conn = get_db()
        if not conn:
            return "Database not available", 500
        
        trail_count = conn.execute('SELECT COUNT(*) FROM trails').fetchone()[0]
        open_count = conn.execute('SELECT COUNT(*) FROM trails WHERE status LIKE "%OPEN%"').fetchone()[0]
        
        return f"""
            <html>
            <body>
                <h1>Debug Info</h1>
                <p>✅ App is running!</p>
                <p>📊 Total trails: {trail_count}</p>
                <p>✅ Open trails: {open_count}</p>
                <p><a href="/">Back to Dashboard</a></p>
            </body>
            </html>
        """
    except Exception as e:
        return f"Debug error: {e}", 500

@app.route('/test')
def test():
    """Simple test page"""
    return "✅ Flask is working! The app is running correctly.", 200

@app.route('/api/trails', methods=['GET'])
def api_trails():
    """API endpoint to get all trails"""
    conn = get_db()
    status_filter = request.args.get('status', 'all')
    
    sql = '''
        SELECT trail_id, name, counties, miles, atv_miles, ohv_miles, 
               ohm_miles, morv_miles, winter_miles, status, status_notes, 
               last_updated, normal_season
        FROM trails
        WHERE 1=1
    '''
    params = []
    
    if status_filter != 'all':
        if status_filter == 'open':
            sql += ' AND status LIKE "%OPEN%"'
        elif status_filter == 'closed':
            sql += ' AND (status LIKE "%Closed%" OR status LIKE "%CLOSED%")'
        elif status_filter == 'limited':
            sql += ' AND (status LIKE "%Limited%" OR (status LIKE "%Open%" AND status != "%OPEN%"))'
    
    sql += ' ORDER BY name ASC'
    
    trails = conn.execute(sql, params).fetchall()
    conn.close()
    
    # Convert to list of dicts
    trails_list = [dict(trail) for trail in trails]
    
    # Add distances
    distances = get_estimated_distances()
    for trail in trails_list:
        trail['distance'] = distances.get(trail['counties'], 'Unknown')
    
    return jsonify(trails_list)

@app.route('/api/status-history/<int:trail_id>', methods=['GET'])
def status_history(trail_id):
    """Get status history for a specific trail"""
    conn = get_db()
    history = conn.execute(
        'SELECT status, status_notes, recorded_at FROM status_history WHERE trail_id = ? ORDER BY recorded_at DESC',
        (trail_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(h) for h in history])

@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Get overall statistics"""
    conn = get_db()
    
    # Count by status
    open_count = conn.execute(
        'SELECT COUNT(*) as count FROM trails WHERE status LIKE "%OPEN%"'
    ).fetchone()['count']
    
    closed_count = conn.execute(
        'SELECT COUNT(*) as count FROM trails WHERE status LIKE "%Closed%" OR status LIKE "%CLOSED%"'
    ).fetchone()['count']
    
    limited_count = conn.execute(
        'SELECT COUNT(*) as count FROM trails WHERE status LIKE "%Limited%" OR (status LIKE "%Open%" AND status != "%OPEN%")'
    ).fetchone()['count']
    
    total = conn.execute('SELECT COUNT(*) as count FROM trails').fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'total': total,
        'open': open_count,
        'closed': closed_count,
        'limited': limited_count
    })

def get_estimated_distances():
    """
    Get estimated driving distances from Andover, MN (55304)
    These are approximations based on county locations
    """
    return {
        'Mille Lacs': '45-50 miles',
        'Crow Wing': '55-65 miles',
        'Cass': '65-75 miles',
        'Swift': '90-100 miles',
        'Fillmore': '105-115 miles',
        'Wabasha': '110-120 miles',
        'Winona': '115-125 miles',
        'St. Louis': '120-135 miles',
        'Pine': '140-150 miles',
        'Hubbard': '125-135 miles',
        'Becker': '135-145 miles',
        'Roseau': '140-180 miles',
        'Norman': '150-160 miles',
        'Clay': '155-165 miles',
        'Polk': '160-170 miles',
        'Itasca': '160-220 miles',
        'Koochiching': '165-175 miles',
        'Beltrami': '170-250 miles',
        'Marshall': '170-260 miles',
        'Carlton': '165-180 miles',
        'Aitkin': '205-225 miles',
        'Morrison': '215-230 miles',
        'Cook': '225-235 miles',
        'Lake': '170-235 miles',
        'Wadena': '170-180 miles',
        'Grant': '255-265 miles',
        'Lyon': '180-190 miles',
        'Meeker': '185-195 miles',
        'Mille Lacs County': '175 miles',
        'Multiple': 'Varies',
    }

@app.route('/api/export', methods=['GET'])
def api_export():
    """Export trails data to CSV"""
    conn = get_db()
    status_filter = request.args.get('status', 'all')
    
    sql = '''
        SELECT trail_id, name, counties, miles, atv_miles, ohv_miles, 
               ohm_miles, morv_miles, winter_miles, status, status_notes, 
               last_updated, normal_season
        FROM trails
        WHERE 1=1
    '''
    params = []
    
    if status_filter != 'all':
        if status_filter == 'open':
            sql += ' AND status LIKE "%OPEN%"'
        elif status_filter == 'closed':
            sql += ' AND (status LIKE "%Closed%" OR status LIKE "%CLOSED%")'
        elif status_filter == 'limited':
            sql += ' AND (status LIKE "%Limited%" OR (status LIKE "%Open%" AND status != "%OPEN%"))'
    
    sql += ' ORDER BY name ASC'
    
    trails = conn.execute(sql, params).fetchall()
    conn.close()
    
    # Generate CSV
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Trail ID', 'Name', 'Counties', 'Total Miles', 'ATV', 'OHV', 'OHM', 'MORV', 'Winter', 'Status', 'Status Notes', 'Last Updated', 'Normal Season'])
    
    # Data rows
    for trail in trails:
        writer.writerow([
            trail['trail_id'],
            trail['name'],
            trail['counties'],
            trail['miles'],
            trail['atv_miles'],
            trail['ohv_miles'],
            trail['ohm_miles'],
            trail['morv_miles'],
            trail['winter_miles'],
            trail['status'],
            trail['status_notes'],
            trail['last_updated'],
            trail['normal_season']
        ])
    
    output.seek(0)
    
    return output.getvalue(), 200, {
        'Content-Type': 'text/csv',
        'Content-Disposition': f'attachment; filename=trails_{status_filter or "all"}.csv'
    }

if __name__ == '__main__':
    # Initialize database tables if they don't exist
    init_db()
    
    app.run(host='0.0.0.0', port=8000, debug=False)
