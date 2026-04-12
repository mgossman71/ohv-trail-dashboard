#!/bin/bash
# Test GitHub connection

echo "Testing GitHub connection..."

# Test if we can reach the GitHub API
GITHUB_TOKEN="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"

echo "Checking GitHub user..."
curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ GitHub user: {data[\"login\"]}')
print(f'   Full name: {data.get(\"name\", \"N/A\")}')
print(f'   Repos: {data.get(\"public_repos\", 0)}')
"
