#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
對比測試不同語句的時間解析
"""

import sys
import os

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ai_parser'))

from ai_parser.handle_time import parse_datetime_phrases

def compare_time_parsing():
    """對比測試不同語句的時間解析"""
    
    print("=== 對比測試時間解析 ===\n")
    
    test_cases = [
        "下午五點",  # 簡單版本，預期能正確解析
        "今天下午五點",  # 帶日期的版本
        "請問今天下午五點，有那些師傅可以?",  # 完整問句
        "請問下午五點可以嗎?",  # 簡化問句
        "下午5點",  # 數字版本
        "下午17點",  # 24小時制版本
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. 測試：'{test_case}'")
        print("-" * 40)
        
        result = parse_datetime_phrases(test_case)
        
        if result and isinstance(result, dict):
            time_str = result.get('時間', '未找到')
            print(f"解析時間：{time_str}")
            
            # 檢查是否正確解析為17:xx
            if time_str.startswith("17:"):
                print("✅ 正確解析為下午5點")
            elif time_str.startswith("14:") or time_str.startswith("15:"):
                print("❌ 返回當前時間，未解析語句中的時間")
            else:
                print(f"⚠️ 其他時間結果：{time_str}")
        else:
            print("❌ 無法解析")
            
        print()

if __name__ == "__main__":
    compare_time_parsing()
