#!/bin/bash
# GitHub Authentication Setup Script

echo "Setting up GitHub authentication..."

# Store the token in a temporary file (will be used by scripts)
TOKEN="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"

# Option 1: Set as environment variable for current session
export GITHUB_TOKEN="$TOKEN"
echo "✅ Token set as GITHUB_TOKEN environment variable"

# Option 2: Store in git config for cloning repos
git config --global user.name "Mark Gossman"
git config --global user.email "your_email@example.com"

echo "
To use this token with git, run one of these commands:

1. For HTTPS URLs:
   git clone https://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@github.com/username/repo.git

2. Or configure git to use the token automatically:
   git config --global credential.helper store
   # Then when you clone, it will prompt for credentials and save them

3. Or use it directly in your scripts:
   export GITHUB_TOKEN='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'
   curl -H "Authorization: token $TOKEN" https://api.github.com/user

Important: This token has full repository access (repo scope).
Keep it secret and do not share it!
"
