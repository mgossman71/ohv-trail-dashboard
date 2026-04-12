#!/bin/bash
# Check if database and data exist

echo "=== Checking OHV Trail Dashboard Data ==="

cd /root/.openclaw/workspace/ohv-trail-dashboard

echo ""
echo "1. Checking Docker containers:"
docker compose ps

echo ""
echo "2. Checking if data directory exists on host:"
ls -la data/ 2>/dev/null || echo "Data directory does not exist or is empty"

echo ""
echo "3. Checking if database file exists on host:"
if [ -f data/trails.db ]; then
    echo "Database file exists!"
    sqlite3 data/trails.db "SELECT COUNT(*) as trail_count FROM trails;" 2>/dev/null || echo "Could not query database"
else
    echo "No database file found in data/ directory"
fi

echo ""
echo "4. Checking container's /app/data directory:"
docker compose exec ohv-trail-dashboard ls -la /app/data/ 2>/dev/null || echo "Could not access container"

echo ""
echo "5. Checking container's database:"
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db "SELECT COUNT(*) as trail_count FROM trails;" 2>/dev/null || echo "Could not query container database"

echo ""
echo "6. If no data, you need to initialize it:"
echo "   docker compose exec ohv-trail-dashboard python init_db.py"
echo "   or"
echo "   docker compose run --rm ohv-trail-dashboard python init_db.py"
