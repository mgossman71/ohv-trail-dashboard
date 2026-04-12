#!/bin/bash
# Check if OpenClaw gateway is running

echo "Checking OpenClaw gateway status..."

# Check if the gateway process is running
if pgrep -f "openclaw gateway" > /dev/null; then
    echo "✅ Gateway process is running!"
else
    echo "❌ Gateway process not found"
    echo "Try starting it with: nohup openclaw gateway run > /tmp/gateway.log 2>&1 &"
    exit 1
fi

# Check if we can connect to the gateway
if curl -s http://127.0.0.1:18789/health > /dev/null 2>&1; then
    echo "✅ Gateway is responding on port 18789!"
else
    echo "❌ Gateway not responding on port 18789"
    exit 1
fi

echo ""
echo "Gateway is ready!"
