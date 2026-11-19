#!/usr/bin/env python3
"""Test safety risk detection"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, '.')

from server import check_safety_risk, SAFETY_KEYWORDS

def test_safety_detection():
    """Test various risk levels"""
    test_cases = [
        # High risk - Chinese keywords
        ("不想活了", "high"),
        ("自杀", "high"),
        ("割腕", "high"),
        ("跳楼", "high"),
        ("烧炭", "high"),

        # Medium risk
        ("抑郁", "medium"),
        ("焦虑", "medium"),
        ("绝望", "medium"),
        ("崩溃", "medium"),

        # No risk
        ("天气不错", "none"),
        ("聊聊", "none"),
        ("开心", "none"),
    ]

    print("=" * 60)
    print("Safety Risk Detection Test")
    print("=" * 60)

    all_passed = True
    for text, expected in test_cases:
        result = check_safety_risk(text)
        status = "PASS" if result['risk'] == expected else "FAIL"
        if result['risk'] != expected:
            all_passed = False
        # Use repr to avoid encoding issues
        print(f"[{status}] {repr(text)} -> {result['risk']} (expected: {expected})")

    print("=" * 60)
    if all_passed:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED!")

    return all_passed

if __name__ == '__main__':
    success = test_safety_detection()
    sys.exit(0 if success else 1)
