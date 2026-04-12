#!/bin/bash
# Script to initialize the OHV Trail Dashboard

echo "=== OHV Trail Dashboard - Initial Setup ==="

# Navigate to the project directory
cd /root/.openclaw/workspace/ohv-trail-dashboard

echo "Step 1: Creating data directory..."
mkdir -p data

echo "Step 2: Building Docker image..."
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
echo "To check container health:"
echo "  docker compose exec ohv-trail-dashboard curl http://localhost:8000"
