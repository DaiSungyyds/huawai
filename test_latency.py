#!/usr/bin/env python3
"""Test message translation latency"""

import sys
import io
import time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def api_request(path, method="GET", data=None, token=None):
    """Make API request"""
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "message": json.loads(e.read().decode()).get("message")}
    except Exception as e:
        return {"error": str(e)}

def test_translation_latency():
    """Test message translation latency"""
    print("=" * 60)
    print("Message Translation Latency Test")
    print("=" * 60)

    # Login
    result = api_request("/api/auth/login", "POST", {
        "account": "testchild",
        "password": "testpass123456",
        "role": "child"
    })

    if "error" in result:
        print(f"[FAIL] Login failed: {result}")
        return

    token = result.get("data", {}).get("accessToken")
    print(f"[OK] Login successful")

    # Create room
    result = api_request("/api/communication/rooms", "POST", {"role": "child"}, token)
    if "error" in result:
        print(f"[FAIL] Create room failed: {result}")
        return

    room_id = result.get("data", {}).get("roomId")
    print(f"[OK] Room created: {room_id}")

    # Test messages
    test_cases = [
        "你们总是很忙，都不听我说话。",
        "我想和你们聊聊学校的事情。",
        "我今天在学校很开心。",
    ]

    print("\n" + "-" * 60)
    print("Testing translation latency...")
    print("-" * 60)

    total_time = 0
    success_count = 0

    for i, text in enumerate(test_cases):
        print(f"\n[{i+1}] Original: {text}")
        start = time.time()

        result = api_request(f"/api/communication/rooms/{room_id}/messages", "POST", {
            "role": "child",
            "text": text,
            "clientMessageId": f"latency-test-{i}"
        }, token)

        elapsed = time.time() - start
        total_time += elapsed
        success_count += 1

        if "error" in result:
            print(f"    [ERROR] {result.get('message', 'Unknown error')}")
        else:
            data = result.get("data", {})
            translated = data.get("translated", "")
            print(f"    Translated: {translated[:80]}...")
            print(f"    Time: {elapsed:.2f}s")

    print("\n" + "=" * 60)
    print(f"Results:")
    print(f"  Total requests: {success_count}")
    print(f"  Average latency: {total_time/success_count:.2f}s")
    print(f"  Total time: {total_time:.2f}s")
    print("=" * 60)

if __name__ == "__main__":
    test_translation_latency()
