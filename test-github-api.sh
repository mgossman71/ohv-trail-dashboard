#!/bin/bash
# Test GitHub API connection

GITHUB_TOKEN="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"

echo "Testing GitHub API connection..."
echo "Token: ${GITHUB_TOKEN:0:20}... (truncated)"
echo ""

# Test 1: Get user info
echo "1. Getting user info..."
USER_INFO=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user)

if echo "$USER_INFO" | grep -q "login"; then
    echo "✅ Successfully connected to GitHub!"
    echo "$USER_INFO" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'   Username: {data[\"login\"]}')
print(f'   Name: {data.get(\"name\", \"N/A\")}')
print(f'   Public repos: {data.get(\"public_repos\", 0)}')
print(f'   Private repos: {data.get(\"total_private_repos\", 0)}')
print(f'   URL: {data[\"html_url\"]}')
"
else
    echo "❌ Failed to get user info"
    echo "Response: $USER_INFO"
    exit 1
fi

echo ""
echo "2. Listing repositories..."
REPOS=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user/repos?per_page=5)

echo "$REPOS" | python3 -c "
import sys, json
repos = json.load(sys.stdin)
for repo in repos[:5]:
    private = '[PRIVATE]' if repo.get('private', False) else '[PUBLIC]'
    print(f'   {private} {repo[\"name\"]}')
    print(f'      URL: {repo[\"html_url\"]}')
    print(f'      Stars: {repo.get(\"stargazers_count\", 0)}')
"

echo ""
echo "✅ GitHub API is working! You have {len(repos)} repositories."
