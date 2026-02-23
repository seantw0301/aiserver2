#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime

# Add the ai_parser directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_parser'))

from handle_time import parse_datetime_phrases_multiline

def print_test_header(title):
    print("\n" + "="*80)
    print(f"測試: {title}")
    print("="*80)

def test_multiple_dates():
    """測試多日期優先邏輯：優先今天，其次未來最近的"""
    print_test_header("多日期優先邏輯")
    
    # 模擬當前時間為 2025-11-12 14:18
    # 測試文本包含多個日期
    test_cases = [
        # 優先: 今天 (11/12)
        ("預約 11/12 或 11/13 或 11/14", "應該選擇 11/12 (今天)"),
        ("明天 11/13 或 11/14", "應該選擇 11/13 (最近的未來)"),
        ("11/20 和 11/15", "應該選擇 11/15 (最近的未來)"),
    ]
    
    for text, description in test_cases:
        result = parse_datetime_phrases_multiline(text)
        print(f"\n輸入: {text}")
        print(f"說明: {description}")
        if result:
            print(f"日期: {result.get('日期', 'null')} ({result.get('星期', 'null')})")
            print(f"時間: {result.get('時間', 'null')}")
        else:
            print("未解析")
        print("-" * 80)

def test_multiple_times():
    """測試多時間優先邏輯：優先未過期且最近當前時間的"""
    print_test_header("多時間優先邏輯")
    
    # 模擬當前時間為 2025-11-12 14:18
    test_cases = [
        # 優先: 14:30 (最近未來)
        ("今天 14:30 或 15:00 或 16:00", "應該選擇 14:30 (最近的未來時間)"),
        # 優先: 16:00 (避免過期時間)
        ("今天 10:00 或 16:00", "應該選擇 16:00 (10:00已過期)"),
        # 優先: 20:00 (最近未來)
        ("今天 20:00 或 22:00", "應該選擇 20:00 (最近未來時間)"),
    ]
    
    for text, description in test_cases:
        result = parse_datetime_phrases_multiline(text)
        print(f"\n輸入: {text}")
        print(f"說明: {description}")
        if result:
            print(f"日期: {result.get('日期', 'null')} ({result.get('星期', 'null')})")
            print(f"時間: {result.get('時間', 'null')}")
        else:
            print("未解析")
        print("-" * 80)

def test_combined_priority():
    """測試日期和時間綜合優先邏輯"""
    print_test_header("日期+時間綜合優先邏輯")
    
    # 模擬當前時間為 2025-11-12 14:18
    test_cases = [
        # 優先: 今天 (11/12) + 未來時間
        ("11/12 14:30 或 11/13 10:00", "應該選擇 11/12 (今天優先) + 14:30 (未來)"),
        # 優先: 未來最近日期 + 最近未來時間
        ("11/14 20:00 或 11/13 10:00", "應該選擇 11/13 (最近未來日期)"),
        # 複雜情況
        ("11/15 16:00 或 11/13 15:00 或 11/12 18:00", "應該選擇 11/12 18:00 (今天優先)"),
    ]
    
    for text, description in test_cases:
        result = parse_datetime_phrases_multiline(text)
        print(f"\n輸入: {text}")
        print(f"說明: {description}")
        if result:
            print(f"日期: {result.get('日期', 'null')} ({result.get('星期', 'null')})")
            print(f"時間: {result.get('時間', 'null')}")
        else:
            print("未解析")
        print("-" * 80)

if __name__ == "__main__":
    print("日期時間解析 - 優先邏輯測試")
    print("當前時間: 2025-11-12 14:18:08")
    
    test_multiple_dates()
    test_multiple_times()
    test_combined_priority()
    
    print("\n" + "="*80)
    print("測試完成")
    print("="*80)
