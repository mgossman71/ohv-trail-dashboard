#!/bin/bash
TOKEN="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"

echo "Creating private repository..."

RESPONSE=$(curl -s -X POST https://api.github.com/mgossman71/repos \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"name":"ohv-trail-dashboard","private":true,"description":"Personal web application for browsing Minnesota OHV trail statuses"}')

echo "$RESPONSE"

# Extract info
NAME=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('name','ERROR'))")
URL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('html_url','ERROR'))")
PRIVATE=$(echo "$RESPONSE" | python3 -c "import sys,json; print('PRIVATE' if json.load(sys.stdin).get('private') else 'PUBLIC')")

echo ""
echo "Repository created!"
echo "  Name: $NAME"
echo "  URL: $URL"
echo "  Type: $PRIVATE"
