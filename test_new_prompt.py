#!/usr/bin/env python3
"""Test new translation prompt"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
import urllib.request

# Login
login_data = json.dumps({'account': 'child01', 'password': 'test12345678', 'role': 'child'}).encode('utf-8')
req = urllib.request.Request('http://127.0.0.1:8000/api/auth/login', data=login_data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req)
token = json.loads(resp.read())['data']['accessToken']

# Test cases
test_cases = [
    '你们从来不听我说话',
    '我讨厌你们',
    '你们总是很忙，都不关心我',
    '我想和你们聊聊',
]

print("=" * 60)
print("Testing new translation prompt")
print("=" * 60)

for text in test_cases:
    translate_data = json.dumps({'text': text}).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:8000/api/translate', data=translate_data, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'})
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        print(f"\n原文: {text}")
        print(f"转译: {result['data']['translated']}")
    except Exception as e:
        print(f"\n原文: {text}")
        print(f"错误: {e}")

print("\n" + "=" * 60)
