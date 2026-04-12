#!/bin/bash
# Directly seed the database

echo "=== Direct Database Seeding ==="

cd /root/.openclaw/workspace/ohv-trail-dashboard

# Ensure data directory exists
mkdir -p data

# Check if we have the init script
if [ -f "init_db.py" ]; then
    echo "Found init_db.py"
else
    echo "ERROR: init_db.py not found!"
    exit 1
fi

# Run init_db.py directly to create the database locally
python init_db.py

echo ""
echo "Checking local database..."
ls -la data/

# Copy database to container
if [ -f data/trails.db ]; then
    echo "Database file exists, container should pick it up"
else
    echo "ERROR: Database file not created!"
    exit 1
fi

# Restart container to pick up the data
echo ""
echo "Restarting container to load data..."
docker compose restart ohv-trail-dashboard

sleep 5

echo ""
echo "Final check - database count in container:"
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db "SELECT COUNT(*) as count FROM trails;"

echo ""
echo "Dashboard URL: http://oc1:8000/"
