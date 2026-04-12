"""
Directly seed the database for the Docker container
This script should be run inside the container or by copying the database
"""

import sqlite3
import os
import sys

# Always use the Docker path
DATABASE = '/app/data/trails.db'

def main():
    print(f"Seeding database at {DATABASE}...")
    
    # Create directory if it doesn't exist
    os.makedirs('/app/data', exist_ok=True)
    
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
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
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY,
            trail_id INTEGER,
            status TEXT,
            status_notes TEXT,
            recorded_at TIMESTAMP,
            FOREIGN KEY (trail_id) REFERENCES trails(trail_id)
        )
    ''')
    
    # Sample trail data (you'd want all 95 trails here)
    trails = [
        (132, 'Agassiz Central Trail', 'Norman', 17, 17, 0, 0, 0, 0, 'Closed', '', '2026-04-11', 'April 1 to November 30'),
        (2, 'Agassiz Recreational Trail', 'Clay, Norman, Polk', 52, 52, 0, 0, 0, 0, 'OPEN', '', '2026-04-11', 'Year round'),
        # Add all other trails here...
    ]
    
    for trail in trails:
        cursor.execute('''
            INSERT OR REPLACE INTO trails 
            (trail_id, name, counties, miles, atv_miles, ohv_miles, ohm_miles, morv_miles, winter_miles, status, status_notes, last_updated, normal_season)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', trail)
    
    conn.commit()
    conn.close()
    
    # Verify
    conn = sqlite3.connect(DATABASE)
    count = conn.execute('SELECT COUNT(*) FROM trails').fetchone()[0]
    conn.close()
    
    print(f"Database seeded with {count} trails!")

if __name__ == '__main__':
    main()
