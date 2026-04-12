#!/bin/bash
# Create new private GitHub repository

GITHUB_TOKEN="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"
USERNAME="mgossman71"
REPO_NAME="ohv-trail-dashboard"

echo "Creating private repository: ${USERNAME}/${REPO_NAME}..."
echo ""

# Create the repository
RESPONSE=$(curl -s -X POST https://api.github.com/${USERNAME}/repos \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  -d "{
    \"name\": \"${REPO_NAME}\",
    \"private\": true,
    \"description\": \"Personal web application for browsing Minnesota OHV trail statuses\",
    \"homepage\": \"http://oc1:8000\"
  }")

# Parse the response
echo "$RESPONSE" | python3 -c "
import sys, json

data = json.load(sys.stdin)

if 'id' in data:
    print('✅ SUCCESS! Repository created:')
    print(f'   Name: {data[\"name\"]}')
    print(f'   URL: {data[\"html_url\"]}')
    print(f'   Private: {data[\"private\"]}')
    print(f'   Description: {data.get(\"description\", \"N/A\")}')
    print(f'   ID: {data[\"id\"]}')
    print(f'   Clone URL: {data[\"clone_url\"]}')
    
    # Set up git remote
    import subprocess
    subprocess.run([
        'git', 'remote', 'add', 'origin', data['clone_url'],
        cwd='/root/.openclaw/workspace/ohv-trail-dashboard'
    ])
    
    print()
    print('📦 Next steps to push your code:')
    print('   git add .')
    print('   git commit -m "Initial commit: OHV Trail Dashboard"')
    print('   git push -u origin main')
    
else:
    print('❌ ERROR creating repository:')
    print(data)
"
