#!/bin/bash
# Quick dashboard fix script

echo "=== Fixing OHV Trail Dashboard ==="

cd /root/.openclaw/workspace/ohv-trail-dashboard

# Stop containers
echo "Stopping containers..."
docker compose down

# Remove old data to force re-initialization
echo "Clearing old data..."
rm -rf data/*

# Rebuild with updated code
echo "Rebuilding containers..."
docker compose build

# Start containers
echo "Starting containers..."
docker compose up -d

# Wait for startup
echo "Waiting for startup (10 seconds)..."
sleep 10

# Initialize database
echo "Initializing database..."
docker compose exec ohv-trail-dashboard python init_container_db.py

# Check container logs for errors
echo ""
echo "=== Container Logs (last 20 lines) ==="
docker compose logs --tail=20 ohv-trail-dashboard

echo ""
echo "=== Dashboard Status ==="
echo "Dashboard URL: http://oc1:8000"
echo "Debug URL: http://oc1:8000/debug"
echo "Test URL: http://oc1:8000/test"

echo ""
echo "=== What to do ==="
echo "1. Refresh http://oc1:8000/test"
echo "2. If that works, try http://oc1:8000/debug"
echo "3. If both work but main page fails, the issue is in the template"
echo "4. Check the logs above for specific errors"
