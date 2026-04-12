#!/bin/bash
# Initialize the database inside the Docker container

echo "=== Initializing OHV Trail Dashboard Database ==="

cd /root/.openclaw/workspace/ohv-trail-dashboard

# Copy the init script into the container
echo "Copying init script to container..."

# Run the initialization script inside the container
echo "Running database initialization..."
docker compose exec ohv-trail-dashboard python init_container_db.py

echo ""
echo "Verifying database..."
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db "SELECT COUNT(*) as trail_count FROM trails;"

echo ""
echo "Dashboard should now show data at http://oc1:8000/"
