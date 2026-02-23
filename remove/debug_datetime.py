#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
debug_datetime.py
讀取 datetime_test.txt 文件，逐行解析日期時間語句
使用 ai_parser/handle_time.py 作為解析工具
"""

import os
import sys
from datetime import datetime

# 添加 ai_parser 模組路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'ai_parser'))

# 導入時間解析函數
from handle_time import parse_datetime_phrases, parse_datetime_phrases_multiline

def main():
    """主函數：讀取測試文件並解析每一行"""
    
    # 設定文件路徑
    test_file_path = os.path.join(os.path.dirname(__file__), 'ai_parser', 'datetime_test.txt')
    
    # 檢查文件是否存在
    if not os.path.exists(test_file_path):
        print(f"錯誤：找不到測試文件 {test_file_path}")
        return
    
    print("=" * 80)
    print("日期時間解析測試")
    print("=" * 80)
    print(f"測試文件：{test_file_path}")
    print(f"當前時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 讀取並處理每一行
    line_number = 0
    success_count = 0
    total_count = 0
    
    try:
        with open(test_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                line_number += 1
                line = line.strip()
                
                # 跳過空行
                if not line:
                    continue
                
                total_count += 1
                
                print(f"\n第 {line_number} 行：")
                print(f"原始語句：{line}")
                print("-" * 40)
                
                # 使用 handle_time.py 解析
                try:
                    result = parse_datetime_phrases(line)
                    
                    if result:
                        success_count += 1
                        print("解析結果：")
                        for key, value in result.items():
                            print(f"  {key}：{value}")
                        print("✅ 解析成功")
                    else:
                        print("❌ 解析失敗：無法識別日期時間信息")
                        
                except Exception as e:
                    print(f"❌ 解析錯誤：{str(e)}")
                
                print("-" * 40)
    
    except FileNotFoundError:
        print(f"錯誤：無法打開文件 {test_file_path}")
        return
    except Exception as e:
        print(f"讀取文件時發生錯誤：{str(e)}")
        return
    
    # 顯示統計結果
    print("\n" + "=" * 80)
    print("解析統計")
    print("=" * 80)
    print(f"總行數（含空行）：{line_number}")
    print(f"有效語句：{total_count}")
    print(f"成功解析：{success_count}")
    print(f"失敗數量：{total_count - success_count}")
    if total_count > 0:
        success_rate = (success_count / total_count) * 100
        print(f"成功率：{success_rate:.1f}%")
    print("=" * 80)

def test_single_sentence(sentence):
    """測試單個語句的解析功能"""
    print(f"測試語句：{sentence}")
    print("-" * 40)
    
    try:
        result = parse_datetime_phrases(sentence)
        
        if result:
            print("解析結果：")
            for key, value in result.items():
                print(f"  {key}：{value}")
            print("✅ 解析成功")
        else:
            print("❌ 解析失敗：無法識別日期時間信息")
            
    except Exception as e:
        print(f"❌ 解析錯誤：{str(e)}")
    
    print("-" * 40)


def test_multiline_sentence(sentence):
    """測試多句語句的解析功能 - 自動分割並選擇最優結果"""
    print(f"測試多句語句：{sentence}")
    print("-" * 40)
    
    try:
        result = parse_datetime_phrases_multiline(sentence)
        
        if result:
            print("解析結果：")
            for key, value in result.items():
                print(f"  {key}：{value}")
            print("✅ 解析成功")
        else:
            print("❌ 解析失敗：無法識別日期時間信息")
            
    except Exception as e:
        print(f"❌ 解析錯誤：{str(e)}")
    
    print("-" * 40)


if __name__ == "__main__":
    # 如果有命令行參數，則測試單個語句
    if len(sys.argv) > 1:
        test_sentence = " ".join(sys.argv[1:])
        test_single_sentence(test_sentence)
    else:
        # 否則執行批量測試
        main()