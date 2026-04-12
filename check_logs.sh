#!/bin/bash
# Diagnostic script to check OHV Trail Dashboard

echo "=== OHV Trail Dashboard Diagnostic ==="
echo ""
echo "1. Container status:"
docker compose ps
echo ""

echo "2. Recent logs:"
docker compose logs --tail=30 ohv-trail-dashboard
echo ""

echo "3. Directory structure in container:"
docker compose exec ohv-trail-dashboard ls -la /app/
echo ""

echo "4. Templates directory:"
docker compose exec ohv-trail-dashboard ls -la /app/templates/ 2>&1 || echo "Templates directory does not exist"
echo ""

echo "5. Data directory:"
docker compose exec ohv-trail-dashboard ls -la /app/data/
echo ""

echo "6. Database file:"
docker compose exec ohv-trail-dashboard ls -la /app/data/trails.db 2>&1 || echo "Database file not found"
echo ""

echo "7. Database contents (trail count):"
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db "SELECT COUNT(*) as count FROM trails;"
echo ""

echo "8. Database tables:"
docker compose exec ohv-trail-dashboard sqlite3 /app/data/trails.db ".tables"
echo ""

echo "9. App file contents:"
docker compose exec ohv-trail-dashboard head -20 /app/app.py
echo ""

echo "=== End Diagnostic ==="
