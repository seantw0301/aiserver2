#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_parser'))

from handle_time import parse_datetime_phrases_multiline

def test_cases():
    """完整的優先邏輯測試用例"""
    test_data = [
        # 多日期測試
        ("預約 11/12 或 11/13 或 11/14", "2025-11-12", "null", "優先今天 (11/12)"),
        ("明天 11/13 或 11/14", "2025-11-13", "null", "優先最近未來 (11/13)"),
        ("11/20 和 11/15", "2025-11-15", "null", "優先最近未來 (11/15)"),
        
        # 多時間測試 (當前時間 14:18)
        ("今天 14:30 或 15:00 或 16:00", "2025-11-12", "14:30:00", "優先最近未來時間 (14:30)"),
        ("今天 10:00 或 16:00", "2025-11-12", "16:00:00", "避免過期時間，選 16:00"),
        ("今天 20:00 或 22:00", "2025-11-12", "20:00:00", "優先最近未來時間 (20:00)"),
        
        # 日期+時間綜合測試
        ("11/12 14:30 或 11/13 10:00", "2025-11-12", "14:30:00", "優先今天 11/12 + 14:30"),
        ("11/15 16:00 或 11/13 15:00 或 11/12 18:00", "2025-11-12", "18:00:00", "優先今天 11/12 + 18:00"),
        
        # 實際場景
        ("你好 想要預約今天11/12。 16：00雄師傅 西門 兩小時", "2025-11-12", "16:00:00", "實際場景測試"),
    ]
    
    print("="*90)
    print("日期時間優先邏輯完整測試")
    print("="*90)
    print(f"當前時間: 2025-11-12 14:18:08\n")
    
    passed = 0
    failed = 0
    
    for i, (text, expected_date, expected_time, description) in enumerate(test_data, 1):
        result = parse_datetime_phrases_multiline(text)
        actual_date = result.get("日期") if result else "null"
        actual_time = result.get("時間") if result else "null"
        
        date_match = actual_date == expected_date
        time_match = actual_time == expected_time
        passed_test = date_match and time_match
        
        status = "✅ PASS" if passed_test else "❌ FAIL"
        
        print(f"測試 {i}: {status}")
        print(f"  說明: {description}")
        print(f"  輸入: {text}")
        print(f"  預期: 日期={expected_date}, 時間={expected_time}")
        print(f"  實際: 日期={actual_date}, 時間={actual_time}")
        
        if passed_test:
            passed += 1
        else:
            failed += 1
        
        print()
    
    print("="*90)
    print(f"測試結果: 通過 {passed}/{len(test_data)}, 失敗 {failed}/{len(test_data)}")
    print("="*90)
    
    return failed == 0

if __name__ == "__main__":
    success = test_cases()
    sys.exit(0 if success else 1)
