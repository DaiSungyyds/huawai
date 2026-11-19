#!/usr/bin/env python3
"""Create 8 pairs of parent-child test accounts"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import secrets
import hashlib
import sqlite3

def password(p, s):
    return hashlib.scrypt(p.encode(), salt=bytes.fromhex(s), n=16384, r=8, p=1).hex()

conn = sqlite3.connect("huawai.sqlite3")

# 8 pairs of accounts
pairs = []
for i in range(1, 9):
    pair_id = f"{i:02d}"
    # Child account
    child_account = f"child{pair_id}"
    child_salt = secrets.token_hex(16)
    child_pwd = "test12345678"  # 12 chars
    child_hash = password(child_pwd, child_salt)
    child_id = secrets.token_hex(16)

    # Parent account
    parent_account = f"parent{pair_id}"
    parent_salt = secrets.token_hex(16)
    parent_pwd = "test12345678"
    parent_hash = password(parent_pwd, parent_salt)
    parent_id = secrets.token_hex(16)

    pairs.append({
        'child': {'id': child_id, 'account': child_account, 'name': f'孩子{pair_id}', 'role': 'child', 'salt': child_salt, 'password': child_hash},
        'parent': {'id': parent_id, 'account': parent_account, 'name': f'家长{pair_id}', 'role': 'parent', 'salt': parent_salt, 'password': parent_hash},
    })

try:
    for pair in pairs:
        for user in [pair['child'], pair['parent']]:
            # Delete existing if any
            conn.execute("DELETE FROM users WHERE account=?", (user['account'],))
            # Insert new
            conn.execute(
                "INSERT INTO users(id, account, name, role, salt, password) VALUES(?,?,?,?,?,?)",
                (user['id'], user['account'], user['name'], user['role'], user['salt'], user['password'])
            )
    conn.commit()
    print(f"Created {len(pairs)} pairs of accounts successfully!\n")
    print("=" * 60)
    print(f"{'Pair':<6} {'Child Account':<15} {'Parent Account':<15} {'Password':<15}")
    print("=" * 60)
    for i, pair in enumerate(pairs, 1):
        print(f"{i:<6} {pair['child']['account']:<15} {pair['parent']['account']:<15} test12345678")
    print("=" * 60)
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
