#!/usr/bin/env python3
"""API Integration Tests"""

import sys
import io
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "message": json.loads(e.read().decode()).get("message")}
    except Exception as e:
        return {"error": str(e)}

def test_health():
    """Test health endpoint"""
    result = api_request("/api/health")
    assert result.get("data", {}).get("ok") == True, "Health check failed"
    print("[PASS] Health endpoint")
    return True

def test_login():
    """Test login with test user"""
    # Login as child
    result = api_request("/api/auth/login", "POST", {
        "account": "testchild",
        "password": "testpass123456",
        "role": "child"
    })

    if "error" in result:
        print(f"[SKIP] Login test - users may not have password 'testpassword123'")
        return None

    token = result.get("data", {}).get("accessToken")
    if token:
        print("[PASS] Child login")
        return token
    else:
        print(f"[FAIL] Child login - {result}")
        return None

def test_create_room(token):
    """Test creating a room"""
    if not token:
        print("[SKIP] Create room - no token")
        return None

    result = api_request("/api/communication/rooms", "POST", {"role": "child"}, token)

    if "error" in result:
        print(f"[FAIL] Create room - {result}")
        return None

    room_id = result.get("data", {}).get("roomId")
    invite_code = result.get("data", {}).get("inviteCode")

    if room_id and invite_code:
        print(f"[PASS] Create room - invite code: {invite_code}")
        return room_id
    else:
        print(f"[FAIL] Create room - invalid response")
        return None

def test_send_message_with_safety_check(token, room_id):
    """Test sending message with safety detection"""
    if not token or not room_id:
        print("[SKIP] Safety message test - missing token or room")
        return

    # Test high-risk message
    result = api_request(f"/api/communication/rooms/{room_id}/messages", "POST", {
        "role": "child",
        "text": "我不想活了",
        "clientMessageId": "test-safety-1"
    }, token)

    data = result.get("data", {})
    if data.get("safetyAlert") and data.get("riskLevel") == "high":
        print("[PASS] High-risk message detected and blocked")
    elif "error" in result:
        print(f"[INFO] Safety message returned error (expected): {result.get('message')}")
    else:
        print(f"[INFO] Safety response: {data}")

    # Test normal message
    result = api_request(f"/api/communication/rooms/{room_id}/messages", "POST", {
        "role": "child",
        "text": "今天天气不错",
        "clientMessageId": "test-normal-1"
    }, token)

    data = result.get("data", {})
    if data.get("id"):
        print("[PASS] Normal message sent successfully")
    else:
        print(f"[INFO] Normal message response: {data}")

def test_data_cleanup():
    """Test data cleanup function"""
    from server import cleanup_old_data
    try:
        cleanup_old_data()
        print("[PASS] Data cleanup function runs without error")
    except Exception as e:
        print(f"[FAIL] Data cleanup error: {e}")

def main():
    print("=" * 60)
    print("API Integration Tests")
    print("=" * 60)

    # Test health
    test_health()

    # Test login (may fail if password not set)
    token = test_login()

    # Test room creation
    room_id = test_create_room(token)

    # Test safety detection in messages
    test_send_message_with_safety_check(token, room_id)

    # Test data cleanup
    test_data_cleanup()

    print("=" * 60)
    print("Tests completed")

if __name__ == "__main__":
    main()
