#!/usr/bin/env python3
"""Create test user with known password"""

import sys
import secrets
import hashlib
import sqlite3

def password(p, s):
    return hashlib.scrypt(p.encode(), salt=bytes.fromhex(s), n=16384, r=8, p=1).hex()

# Create test user with known password
account = "testchild"
password_text = "testpass123456"  # At least 12 chars
role = "child"
name = "Test Child"

salt = secrets.token_hex(16)
pwd_hash = password(password_text, salt)
user_id = secrets.token_hex(16)

conn = sqlite3.connect("huawai.sqlite3")
try:
    # Delete existing test user if any
    conn.execute("DELETE FROM users WHERE account=?", (account,))
    # Insert new test user
    conn.execute(
        "INSERT INTO users(id, account, name, role, salt, password) VALUES(?,?,?,?,?,?)",
        (user_id, account, name, role, salt, pwd_hash)
    )
    conn.commit()
    print(f"Test user created: {account} / {password_text}")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
