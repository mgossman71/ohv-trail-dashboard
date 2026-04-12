#!/bin/bash
# Initialize the database with trail data

echo "=== Initializing OHV Trail Dashboard Database ==="

cd /root/.openclaw/workspace/ohv-trail-dashboard

# Ensure data directory exists
mkdir -p data

echo "Running init_db.py in the container..."
docker compose exec ohv-trail-dashboard python init_db.py

echo ""
echo "Verifying database..."
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db "SELECT COUNT(*) as trail_count FROM trails;"

echo ""
echo "Dashboard should now show data at http://oc1:8000/"
