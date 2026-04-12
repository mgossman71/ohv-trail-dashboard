"""
OHV Trail Scraper
Scrapes Minnesota DNR OHV trail data and updates the database
"""

import json
import sqlite3
import os
import time
from datetime import datetime
import re

DATABASE = '/app/data/trails.db'

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def parse_status(status_text):
    """Parse status from HTML text"""
    if not status_text:
        return "Unknown", ""
    
    status_text = status_text.strip()
    
    # Check for OPEN status
    if status_text.upper() == "OPEN" or "open" in status_text.lower():
        return "OPEN", ""
    
    # Check for CLOSED status (but not "Open" with notes)
    if (status_text.upper().startswith("CLOSED") or 
        status_text.upper() == "CLOSED" or
        "closed" in status_text.lower() or
        status_text.upper() == "CLOSED FOR SEASON"):
        return "Closed", ""
    
    # Check for LIMITED status
    if "limited" in status_text.lower():
        return "Limited", status_text
    
    # Default to CLOSED if no explicit OPEN
    if "closed" in status_text.lower() or "closed for" in status_text.lower():
        return "Closed", ""
    
    return status_text, ""

def scrape_closures_page():
    """
    Scrape the main closures page
    Returns list of trail data from the table
    """
    # This would normally use web scraping, but for now we'll use pre-fetched data
    # In production, you'd use requests + BeautifulSoup or similar
    
    # For this demo, we'll return sample data
    # In production, fetch from https://www.dnr.state.mn.us/ohv/closures.html
    pass

def fetch_trail_data():
    """
    Fetch all trail data from DNR website
    Returns list of trail dictionaries
    """
    # This is where you'd implement the actual scraping
    # For now, return empty list - you'll need to populate this
    
    # Example structure:
    # trails = [
    #     {
    #         'trail_id': 132,
    #         'name': 'Agassiz Central Trail',
    #         'counties': 'Norman',
    #         'miles': 17,
    #         'atv_miles': 17,
    #         'ohv_miles': 0,
    #         'ohm_miles': 0,
    #         'morv_miles': 0,
    #         'winter_miles': 0,
    #         'status': 'Closed',
    #         'status_notes': '',
    #         'normal_season': 'April 1 to November 30'
    #     },
    #     # ... more trails
    # ]
    
    return []

def store_trail_data(trails):
    """Store trail data in database"""
    conn = get_db()
    
    for trail in trails:
        # Check if trail exists
        existing = conn.execute(
            'SELECT id FROM trails WHERE trail_id = ?',
            (trail['trail_id'],)
        ).fetchone()
        
        if existing:
            # Update existing trail
            conn.execute('''
                UPDATE trails SET
                    name = ?,
                    counties = ?,
                    miles = ?,
                    atv_miles = ?,
                    ohv_miles = ?,
                    ohm_miles = ?,
                    morv_miles = ?,
                    winter_miles = ?,
                    status = ?,
                    status_notes = ?,
                    last_updated = ?,
                    normal_season = ?
                WHERE trail_id = ?
            ''', (
                trail['name'],
                trail['counties'],
                trail['miles'],
                trail.get('atv_miles', 0),
                trail.get('ohv_miles', 0),
                trail.get('ohm_miles', 0),
                trail.get('morv_miles', 0),
                trail.get('winter_miles', 0),
                trail['status'],
                trail.get('status_notes', ''),
                datetime.now().date(),
                trail.get('normal_season', ''),
                trail['trail_id']
            ))
            
            # Record status change in history
            existing_status = conn.execute(
                'SELECT status FROM trails WHERE trail_id = ?',
                (trail['trail_id'],)
            ).fetchone()['status']
            
            if existing_status != trail['status']:
                conn.execute('''
                    INSERT INTO status_history (trail_id, status, status_notes, recorded_at)
                    VALUES (?, ?, ?, ?)
                ''', (
                    trail['trail_id'],
                    trail['status'],
                    trail.get('status_notes', ''),
                    datetime.now()
                ))
        else:
            # Insert new trail
            conn.execute('''
                INSERT INTO trails (
                    trail_id, name, counties, miles,
                    atv_miles, ohv_miles, ohm_miles, morv_miles, winter_miles,
                    status, status_notes, last_updated, normal_season
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trail['trail_id'],
                trail['name'],
                trail['counties'],
                trail['miles'],
                trail.get('atv_miles', 0),
                trail.get('ohv_miles', 0),
                trail.get('ohm_miles', 0),
                trail.get('morv_miles', 0),
                trail.get('winter_miles', 0),
                trail['status'],
                trail.get('status_notes', ''),
                datetime.now().date(),
                trail.get('normal_season', '')
            ))
    
    conn.commit()
    conn.close()
    print(f"Stored {len(trails)} trails")

def run_scraper():
    """Main scraper function"""
    print("Starting OHV trail scraper...")
    
    # Fetch data from DNR website
    trails = fetch_trail_data()
    
    if not trails:
        print("No trails found. Make sure to implement the scraping logic.")
        return
    
    # Store in database
    store_trail_data(trails)
    
    print("Scrape completed successfully!")

if __name__ == '__main__':
    run_scraper()
