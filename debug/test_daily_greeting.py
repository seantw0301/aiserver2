#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試每日問侯語功能的腳本
"""

import json
import sys
import os
from datetime import datetime, timedelta

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 導入必要的模塊
from core.database import db_config
from core.common import update_user_visitdate, get_user_info

def test_visitdate_logic():
    """測試 visitdate 邏輯判斷"""
    print("=" * 60)
    print("測試 visitdate 邏輯判斷")
    print("=" * 60)
    
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    test_cases = [
        ("None", None, True, "新用戶（visitdate 為 null）"),
        ("yesterday", yesterday, True, "昨天訪問"),
        ("today", today, False, "今天已訪問"),
    ]
    
    print(f"\n今日日期: {today}")
    print(f"\n測試用例:")
    
    for case_name, visitdate, should_show, description in test_cases:
        # 模擬邏輯
        should_show_greeting = visitdate is None or visitdate != today
        
        status = "✓" if should_show_greeting == should_show else "✗"
        print(f"\n  {status} {description}")
        print(f"     - visitdate: {visitdate}")
        print(f"     - 應顯示問侯語: {should_show_greeting}")
        print(f"     - 預期結果: {should_show}")
        
        if should_show_greeting == should_show:
            print(f"     ✓ 邏輯正確")
        else:
            print(f"     ✗ 邏輯錯誤")

def test_greeting_generation():
    """測試問侯語生成"""
    print("\n" + "=" * 60)
    print("測試問侯語生成")
    print("=" * 60)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 模擬用戶信息
    user_info_test_cases = [
        {
            "name": "完整用戶信息",
            "data": {
                "id": 123,
                "line_id": "U12345678901234567890",
                "display_name": "小王",
                "visitdate": "2025-11-20"
            }
        },
        {
            "name": "新用戶（visitdate 為 null）",
            "data": {
                "id": 456,
                "line_id": "U98765432109876543210",
                "display_name": "小李",
                "visitdate": None
            }
        },
        {
            "name": "今天已訪問",
            "data": {
                "id": 789,
                "line_id": "U11111111111111111111",
                "display_name": "小張",
                "visitdate": today
            }
        },
    ]
    
    print(f"\n今日日期: {today}\n")
    
    for test_case in user_info_test_cases:
        user_info = test_case["data"]
        print(f"  測試: {test_case['name']}")
        
        old_visitdate = user_info.get('visitdate')
        display_name = user_info.get('display_name', '尊敬的會員')
        user_id = user_info.get('id')
        
        # 判斷是否需要顯示問侯語
        if old_visitdate is None or old_visitdate != today:
            greeting_message = f"親愛的會員{display_name}({user_id})您好!"
            print(f"    ✓ 應顯示問侯語:")
            print(f"      {greeting_message}")
        else:
            print(f"    ✗ 不顯示問侯語（已在今天訪問過）")
        print()

def test_natural_language_parser():
    """測試自然語言解析器返回用戶信息"""
    print("\n" + "=" * 60)
    print("測試自然語言解析器")
    print("=" * 60)
    
    from ai_parser.natural_language_parser import parse_natural_language
    
    test_cases = [
        {
            "name": "預約相關的訊息",
            "line_id": "U_test_001",
            "message": "我想要明天下午2點在西門預約按摩，1人"
        },
        {
            "name": "非預約相關的訊息",
            "line_id": "U_test_002",
            "message": "你好，今天天氣怎麼樣？"
        },
    ]
    
    print()
    
    for test_case in test_cases:
        print(f"  測試: {test_case['name']}")
        print(f"    訊息: {test_case['message']}")
        
        # 構建輸入 JSON
        input_data = {
            "key": test_case['line_id'],
            "message": test_case['message']
        }
        input_json = json.dumps(input_data, ensure_ascii=False)
        
        try:
            result = parse_natural_language(input_json)
            
            # 檢查關鍵字段
            is_reservation = result.get('isReservation')
            user_info = result.get('user_info')
            
            print(f"    isReservation: {is_reservation}")
            
            if user_info:
                print(f"    用戶信息:")
                print(f"      - id: {user_info.get('id')}")
                print(f"      - display_name: {user_info.get('display_name')}")
                print(f"      - visitdate: {user_info.get('visitdate')}")
            else:
                print(f"    用戶信息: 無")
                
        except Exception as e:
            print(f"    ✗ 解析失敗: {e}")
        
        print()

def test_complete_flow():
    """測試完整流程（模擬 app.py 中的邏輯）"""
    print("\n" + "=" * 60)
    print("測試完整流程（模擬 app.py 邏輯）")
    print("=" * 60)
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 模擬 parse_natural_language 返回的數據
    parsed_data_scenarios = [
        {
            "name": "預約相關（新用戶）",
            "parsed_data": {
                "isReservation": True,
                "branch": "西門",
                "user_info": {
                    "id": 100,
                    "line_id": "U_new_user",
                    "display_name": "新客戶",
                    "visitdate": None
                }
            }
        },
        {
            "name": "預約相關（舊訪問）",
            "parsed_data": {
                "isReservation": True,
                "branch": "延吉",
                "user_info": {
                    "id": 101,
                    "line_id": "U_old_user",
                    "display_name": "老客戶",
                    "visitdate": "2025-11-19"
                }
            }
        },
        {
            "name": "非預約相關（新用戶）",
            "parsed_data": {
                "isReservation": False,
                "response_message": "你好！",
                "user_info": {
                    "id": 102,
                    "line_id": "U_new_inquiry",
                    "display_name": "詢問客",
                    "visitdate": None
                }
            }
        },
        {
            "name": "非預約相關（已訪問）",
            "parsed_data": {
                "isReservation": False,
                "response_message": "已回覆",
                "user_info": {
                    "id": 103,
                    "line_id": "U_visited",
                    "display_name": "回訪客",
                    "visitdate": today
                }
            }
        },
    ]
    
    print(f"\n今日日期: {today}\n")
    
    for scenario in parsed_data_scenarios:
        print(f"  場景: {scenario['name']}")
        
        parsed_data = scenario['parsed_data'].copy()
        user_info = parsed_data.get('user_info')
        
        # 模擬 app.py 中的邏輯
        greeting_message = None
        if user_info:
            old_visitdate = user_info.get('visitdate')
            display_name = user_info.get('display_name', '尊敬的會員')
            user_id = user_info.get('id')
            
            if old_visitdate is None or old_visitdate != today:
                greeting_message = f"親愛的會員{display_name}({user_id})您好!"
        
        # 添加問侯語到結果
        if greeting_message:
            parsed_data['greeting_message'] = greeting_message
            if 'response_message' in parsed_data and parsed_data['response_message']:
                parsed_data['response_message'] = parsed_data['response_message'] + "\n" + greeting_message
        
        # 顯示結果
        print(f"    isReservation: {parsed_data.get('isReservation')}")
        print(f"    greeting_message: {parsed_data.get('greeting_message', '無')}")
        if 'response_message' in parsed_data:
            print(f"    response_message: {parsed_data.get('response_message')}")
        print()

if __name__ == "__main__":
    print("\n開始測試每日問侯語功能\n")
    
    try:
        # 測試邏輯判斷
        test_visitdate_logic()
        
        # 測試問侯語生成
        test_greeting_generation()
        
        # 測試自然語言解析器
        test_natural_language_parser()
        
        # 測試完整流程
        test_complete_flow()
        
        print("=" * 60)
        print("✓ 所有測試完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 測試過程中出現錯誤: {e}")
        import traceback
        traceback.print_exc()

