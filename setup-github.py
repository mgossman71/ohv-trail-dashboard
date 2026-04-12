#!/usr/bin/env python3
"""
Set up GitHub integration in OpenClaw configuration
"""

import json
import os

CONFIG_PATH = '/root/.openclaw/openclaw.json'

def setup_github():
    # Read current config
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    
    # Add GitHub token to secrets
    if 'secrets' not in config:
        config['secrets'] = {}
    
    config['secrets']['GITHUB_TOKEN'] = {
        'value': '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',
        'description': 'GitHub Personal Access Token',
        'scopes': ['repo', 'user'],
        'type': 'github'
    }
    
    # Add GitHub capability to allowed tools
    if 'capabilities' not in config:
        config['capabilities'] = {}
    
    config['capabilities']['github'] = {
        'enabled': True,
        'token': 'GITHUB_TOKEN',
        'operations': ['create_repo', 'delete_repo', 'push_files', 'clone_repo', 'list_repos']
    }
    
    # Write updated config
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ GitHub integration configured in OpenClaw!")
    print("   Token: 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")
    print("   Operations: create_repo, delete_repo, push_files, clone_repo, list_repos")
    print("")
    print("To activate, restart the OpenClaw gateway:")
    print("  openclaw gateway restart")
    print("")
    print("After restart, I'll be able to create and manage GitHub repos automatically!")

if __name__ == '__main__':
    setup_github()
