#!/bin/bash
# Fix data directory permissions and initialization

echo "=== Fixing OHV Trail Dashboard Data ==="

cd /root/.openclaw/workspace/ohv-trail-dashboard

# Create data directory with proper permissions
mkdir -p data
chmod 755 data

# Check what's in the data directory
echo "Checking data directory..."
ls -la data/

# Check if database exists locally
if [ ! -f data/trails.db ]; then
    echo "Creating local database..."
    # Initialize locally first
    python init_db.py
    ls -la data/
fi

echo ""
echo "Stopping containers..."
docker compose down

echo ""
echo "Starting containers with fresh data..."
docker compose up -d

echo ""
echo "Waiting for container to initialize..."
sleep 10

echo ""
echo "Container status:"
docker compose ps

echo ""
echo "Checking if data is in container..."
docker compose exec ohv-trail-dashboard ls -la /app/data/

echo ""
echo "Checking database count:"
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db "SELECT COUNT(*) as count FROM trails;"

echo ""
echo "View container logs:"
docker compose logs ohv-trail-dashboard

echo ""
echo "Dashboard URL: http://oc1:8000/"
