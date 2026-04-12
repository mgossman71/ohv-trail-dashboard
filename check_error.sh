#!/bin/bash
# Check for errors in OHV Trail Dashboard

cd /root/.openclaw/workspace/ohv-trail-dashboard

echo "=== Container Status ==="
docker compose ps

echo ""
echo "=== App Logs (Last 50 lines) ==="
docker compose logs --tail=50 ohv-trail-dashboard

echo ""
echo "=== App Directory ==="
docker compose exec ohv-trail-dashboard ls -la /app/

echo ""
echo "=== Templates Check ==="
if docker compose exec ohv-trail-dashboard ls /app/templates/index.html > /dev/null 2>&1; then
    echo "Templates directory exists and contains index.html"
    docker compose exec ohv-trail-dashboard ls -la /app/templates/
else
    echo "Templates directory or index.html NOT FOUND!"
    docker compose exec ohv-trail-dashboard ls -la /app/
fi

echo ""
echo "=== Database Check ==="
if docker compose exec ohv-trail-dashboard ls /app/data/trails.db > /dev/null 2>&1; then
    echo "Database exists"
    docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db "SELECT COUNT(*) as count FROM trails;"
else
    echo "Database NOT FOUND!"
fi

echo ""
echo "=== Python Path ==="
docker compose exec ohv-trail-dashboard which python
docker compose exec ohv-trail-dashboard python --version
