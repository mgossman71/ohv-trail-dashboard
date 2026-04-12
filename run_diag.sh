#!/bin/bash
# Run diagnostic

echo "Running diagnostic..."
cd /root/.openclaw/workspace/ohv-trail-dashboard

echo "=== Container Status ==="
docker compose ps

echo ""
echo "=== Recent Logs ==="
docker compose logs --tail=30 ohv-trail-dashboard

echo ""
echo "=== App Directory ==="
docker compose exec ohv-trail-dashboard ls -la /app/

echo ""
echo "=== Templates Directory ==="
docker compose exec ohv-trail-dashboard ls -la /app/templates/

echo ""
echo "=== Data Directory ==="
docker compose exec ohv-trail-dashboard ls -la /app/data/

echo ""
echo "=== Database Info ==="
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db "SELECT COUNT(*) as trail_count FROM trails;"

echo ""
echo "=== Database Tables ==="
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db ".tables"

echo ""
echo "=== App.py First 20 Lines ==="
docker compose exec ohv-trail-dashboard head -20 /app/app.py
