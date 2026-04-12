#!/bin/bash
# Quick database initialization script

echo "Initializing database..."
cd /root/.openclaw/workspace/ohv-trail-dashboard

# Copy the init script to the container and run it
docker compose exec ohv-trail-dashboard python init_container_db.py

echo ""
echo "Database initialized!"
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db "SELECT COUNT(*) as count FROM trails;"

echo ""
echo "Dashboard URL: http://oc1:8000/"
