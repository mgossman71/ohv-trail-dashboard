#!/bin/bash
# Setup GitHub Integration for OpenClaw

echo "Setting up GitHub integration in OpenClaw..."

# Create the GitHub secret plan
cat > /tmp/github-secrets-plan.yaml << 'EOF'
secrets:
  GITHUB_TOKEN:
    provider: static
    value: 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
    description: GitHub Personal Access Token with repo scope
    scopes:
      - repo
      - user
EOF

echo "✅ Secret plan created at /tmp/github-secrets-plan.yaml"
echo ""
echo "Next step: Apply this plan to OpenClaw"
echo "  openclaw secrets apply /tmp/github-secrets-plan.yaml"
echo ""
echo "Then reload the secrets:"
echo "  openclaw secrets reload"
echo ""
echo "After that, I'll be able to create and manage GitHub repos automatically!"
