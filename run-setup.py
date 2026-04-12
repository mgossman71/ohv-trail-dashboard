#!/usr/bin/env python3
import json

CONFIG_PATH = '/root/.openclaw/openclaw.json'

with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

if 'secrets' not in config:
    config['secrets'] = {}

config['secrets']['GITHUB_TOKEN'] = {
    'value': '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',
    'description': 'GitHub Personal Access Token with full repo access',
    'scopes': ['repo', 'user', 'workflow'],
    'type': 'github',
    'created': '2026-04-12'
}

with open(CONFIG_PATH, 'w') as f:
    json.dump(config, f, indent=2)

print("GitHub integration configured!")
