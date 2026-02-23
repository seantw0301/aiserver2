#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試日期比較邏輯，確保能正確處理包含時間戳記的 visitdate
"""

from datetime import datetime

def test_date_comparison():
    """測試日期比較邏輯"""
    print("=" * 60)
    print("測試日期比較邏輯（處理時間戳記格式）")
    print("=" * 60)
    
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n今日日期: {today}\n")
    
    # 測試用例
    test_cases = [
        {
            "name": "時間戳記格式 - 兩天前",
            "visitdate": "2025-11-19T00:00:00",
            "should_show": True
        },
        {
            "name": "時間戳記格式 - 一天前",
            "visitdate": "2025-11-20T14:30:45",
            "should_show": True
        },
        {
            "name": "時間戳記格式 - 今天",
            "visitdate": today + "T10:00:00",
            "should_show": False
        },
        {
            "name": "純日期格式 - 昨天",
            "visitdate": "2025-11-20",
            "should_show": True
        },
        {
            "name": "純日期格式 - 今天",
            "visitdate": today,
            "should_show": False
        },
        {
            "name": "null 值",
            "visitdate": None,
            "should_show": True
        },
    ]
    
    print("測試用例:\n")
    
    for test_case in test_cases:
        old_visitdate = test_case["visitdate"]
        should_show = test_case["should_show"]
        
        # 模擬 app.py 中的日期比較邏輯
        visitdate_date_str = None
        if old_visitdate:
            # 只取日期部分（前 10 個字符）
            visitdate_date_str = old_visitdate[:10] if len(old_visitdate) >= 10 else old_visitdate
        
        # 判斷是否應該顯示問侯語
        should_show_greeting = old_visitdate is None or visitdate_date_str != today
        
        # 驗證結果
        status = "✓ PASS" if should_show_greeting == should_show else "✗ FAIL"
        
        print(f"{status}: {test_case['name']}")
        print(f"    - visitdate: {old_visitdate}")
        print(f"    - 提取的日期: {visitdate_date_str}")
        print(f"    - 應顯示問侯語: {should_show_greeting}")
        print(f"    - 預期結果: {should_show}")
        
        if should_show_greeting != should_show:
            print(f"    ✗ 邏輯錯誤！")
        print()

if __name__ == "__main__":
    print("\n開始測試日期比較邏輯\n")
    
    try:
        test_date_comparison()
        print("=" * 60)
        print("✓ 測試完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 測試過程中出現錯誤: {e}")
        import traceback
        traceback.print_exc()
