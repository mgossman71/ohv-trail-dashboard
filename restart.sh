#!/bin/bash
# Script to restart the OHV Trail Dashboard Docker containers

echo "=== OHV Trail Dashboard - Restart Script ==="

# Navigate to the project directory
cd /root/.openclaw/workspace/ohv-trail-dashboard

echo "Step 1: Stopping existing containers..."
docker compose down

echo "Step 2: Building new Docker image..."
docker compose build

echo "Step 3: Starting containers..."
docker compose up -d

echo "Step 4: Checking container status..."
docker compose ps

echo ""
echo "=== Dashboard should be available at ==="
echo "http://localhost:8000"
echo ""
echo "To view logs:"
echo "  docker compose logs -f ohv-trail-dashboard"
echo ""
echo "To stop:"
echo "  docker compose down"
