#!/bin/bash
# Restart and initialize OHV Trail Dashboard

echo "=== Restarting OHV Trail Dashboard ==="

cd /root/.openclaw/workspace/ohv-trail-dashboard

# Stop and remove containers
docker compose down

# Restart containers (will trigger DB initialization)
docker compose up -d

echo ""
echo "Waiting for container to start..."
sleep 5

echo ""
echo "Container status:"
docker compose ps

echo ""
echo "View logs:"
echo "  docker compose logs -f ohv-trail-dashboard"

echo ""
echo "Dashboard URL: http://oc1:8000/"
