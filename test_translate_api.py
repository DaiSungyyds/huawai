#!/usr/bin/env python3
"""Test the new translate API"""

import sys
import io
import time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:8000"

def api_request(path, method="GET", data=None, token=None):
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

def test_translate_api():
    print("=" * 60)
    print("Test Translate API")
    print("=" * 60)

    # Login
    result = api_request("/api/auth/login", "POST", {
        "account": "testchild",
        "password": "testpass123456",
        "role": "child"
    })
    if "error" in result:
        print(f"[FAIL] Login: {result}")
        return
    token = result.get("data", {}).get("accessToken")
    print("[OK] Login successful")

    # Test translate API
    test_text = "你们总是很忙，都不听我说话。"
    print(f"\nOriginal: {test_text}")
    print("Calling /api/translate...")

    start = time.time()
    result = api_request("/api/translate", "POST", {"text": test_text}, token)
    elapsed = time.time() - start

    if "error" in result:
        print(f"[FAIL] Translate: {result}")
        return

    data = result.get("data", {})
    translated = data.get("translated", "")
    print(f"Translated: {translated}")
    print(f"Time: {elapsed:.2f}s")
    print(f"Safety: {data.get('riskLevel', 'none')}")

    # Test send with custom translated
    print("\n" + "-" * 60)
    print("Test send with custom translated text")

    # Create room
    result = api_request("/api/communication/rooms", "POST", {"role": "child"}, token)
    room_id = result.get("data", {}).get("roomId")
    print(f"[OK] Room created: {room_id}")

    # Send with custom translated
    custom_translated = "我希望你们能抽出时间听我说话，这让我感觉被重视。"
    result = api_request(f"/api/communication/rooms/{room_id}/messages", "POST", {
        "role": "child",
        "text": test_text,
        "translated": custom_translated,
        "clientMessageId": "custom-test-1"
    }, token)

    data = result.get("data", {})
    if data.get("translated") == custom_translated:
        print(f"[PASS] Custom translated text was used: {data.get('translated')}")
    else:
        print(f"[FAIL] Expected custom text, got: {data.get('translated')}")

    print("=" * 60)
    print("Test completed!")

if __name__ == "__main__":
    test_translate_api()
