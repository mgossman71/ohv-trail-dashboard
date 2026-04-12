#!/bin/bash
echo "=== Container Status ==="
docker compose ps

echo -e "\n=== Recent Logs ==="
docker compose logs --tail=30 ohv-trail-dashboard

echo -e "\n=== App Directory ==="
docker compose exec ohv-trail-dashboard ls -la /app/

echo -e "\n=== Templates ==="
docker compose exec ohv-trail-dashboard ls -la /app/templates/

echo -e "\n=== Data ==="
docker compose exec ohv-trail-dashboard ls -la /app/data/

echo -e "\n=== Database Count ==="
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db "SELECT COUNT(*) FROM trails;"

echo -e "\n=== Tables ==="
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db ".tables"
