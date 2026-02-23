#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime

# Add the ai_parser directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ai_parser'))

from handle_time import parse_datetime_phrases_multiline

def debug_priority():
    """調試優先邏輯 - 看看解析的中間結果"""
    
    text = "11/15 16:00 或 11/13 15:00 或 11/12 18:00"
    print(f"輸入文本: {text}")
    print(f"當前時間: 2025-11-12 14:18:08")
    print("="*80)
    
    # 直接調用 parse_datetime_phrases 看看多行拆分
    from handle_time import split_into_lines, parse_datetime_phrases
    
    lines = split_into_lines(text)
    print(f"拆分後的行數: {len(lines)}")
    for i, line in enumerate(lines):
        print(f"  行 {i+1}: '{line}'")
    
    print("\n" + "="*80)
    print("逐行解析結果：")
    print("="*80)
    
    results = []
    for i, line in enumerate(lines):
        result = parse_datetime_phrases(line)
        results.append(result)
        print(f"\n行 {i+1}: '{line}'")
        if result:
            print(f"  日期: {result.get('日期')} ({result.get('星期')})")
            print(f"  時間: {result.get('時間')}")
        else:
            print("  未解析")
    
    print("\n" + "="*80)
    print("多行綜合選擇：")
    print("="*80)
    
    from handle_time import select_best_result
    from datetime import datetime as dt
    
    now = dt.now()
    final_result = select_best_result(results, now)
    
    if final_result:
        print(f"最終日期: {final_result.get('日期')} ({final_result.get('星期')})")
        print(f"最終時間: {final_result.get('時間')}")
    else:
        print("未選擇結果")

if __name__ == "__main__":
    debug_priority()
