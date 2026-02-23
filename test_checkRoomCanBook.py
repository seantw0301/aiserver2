#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 checkRoomCanBook 和 checkStaffCanBook API 端點
"""

import requests
import json
from datetime import datetime, timedelta

# API 基礎 URL
API_BASE_URL = "http://localhost:5001"

def test_checkRoomCanBook():
    """測試 checkRoomCanBook API"""
    
    # 取得明天的日期
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 測試用例
    test_cases = [
        {
            "name": "正常預約 - 1人，30分鐘（不指定店家）",
            "params": {
                "date": tomorrow,
                "time": "14:00",
                "guest": 1,
                "duration": 30
            }
        },
        {
            "name": "正常預約 - 3人，60分鐘（不指定店家）",
            "params": {
                "date": tomorrow,
                "time": "15:00",
                "guest": 3,
                "duration": 60
            }
        },
        {
            "name": "指定店家 - 店家ID 1，1人，30分鐘",
            "params": {
                "date": tomorrow,
                "time": "14:00",
                "guest": 1,
                "duration": 30,
                "storeid": "1"
            }
        },
        {
            "name": "指定店家 - 店家ID 2，3人，60分鐘",
            "params": {
                "date": tomorrow,
                "time": "15:00",
                "guest": 3,
                "duration": 60,
                "storeid": "2"
            }
        },
        {
            "name": "邊界測試 - 超過 24 小時",
            "params": {
                "date": tomorrow,
                "time": "23:30",
                "guest": 1,
                "duration": 60
            }
        },
        {
            "name": "錯誤的日期格式 - YYYY/MM/DD",
            "params": {
                "date": tomorrow.replace('-', '/'),
                "time": "14:00",
                "guest": 1,
                "duration": 30
            }
        },
        {
            "name": "錯誤的日期",
            "params": {
                "date": "2025-13-45",
                "time": "14:00",
                "guest": 1,
                "duration": 30
            }
        },
        {
            "name": "錯誤的時間格式",
            "params": {
                "date": tomorrow,
                "time": "25:70",
                "guest": 1,
                "duration": 30
            }
        },
        {
            "name": "無效的店家ID",
            "params": {
                "date": tomorrow,
                "time": "14:00",
                "guest": 1,
                "duration": 30,
                "storeid": "999"
            }
        }
    ]
    
    print("=" * 80)
    print("checkRoomCanBook API 測試")
    print("=" * 80)
    
    for test_case in test_cases:
        print(f"\n📝 測試: {test_case['name']}")
        print(f"   參數: {test_case['params']}")
        
        try:
            # 發送 GET 請求
            response = requests.get(
                f"{API_BASE_URL}/rooms/checkRoomCanBook",
                params=test_case['params'],
                timeout=10
            )
            
            # 檢查回應狀態
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 狀態碼: {response.status_code}")
                print(f"   📊 回應: {json.dumps(result, ensure_ascii=False, indent=6)}")
            else:
                print(f"   ❌ 狀態碼: {response.status_code}")
                print(f"   📊 回應: {response.text}")
        
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 連線失敗 - 請確保 API 服務器正在運行 (http://localhost:5001)")
        except Exception as e:
            print(f"   ❌ 錯誤: {str(e)}")

def test_checkStaffCanBook():
    """測試 checkStaffCanBook API"""
    
    # 取得明天的日期
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # 測試用例
    test_cases = [
        {
            "name": "檢查師傅 - 1人，30分鐘",
            "params": {
                "date": tomorrow,
                "time": "14:00",
                "guest": 1,
                "duration": 30
            }
        },
        {
            "name": "檢查師傅 - 3人，60分鐘",
            "params": {
                "date": tomorrow,
                "time": "15:00",
                "guest": 3,
                "duration": 60
            }
        },
        {
            "name": "檢查師傅 - 指定店家ID（不使用）",
            "params": {
                "date": tomorrow,
                "time": "14:00",
                "guest": 1,
                "duration": 30,
                "storeid": "1"
            }
        },
        {
            "name": "邊界測試 - 超過 24 小時",
            "params": {
                "date": tomorrow,
                "time": "23:30",
                "guest": 1,
                "duration": 60
            }
        },
        {
            "name": "錯誤的日期格式",
            "params": {
                "date": "2025/12/16",
                "time": "14:00",
                "guest": 1,
                "duration": 30
            }
        },
        {
            "name": "錯誤的時間格式",
            "params": {
                "date": tomorrow,
                "time": "25:70",
                "guest": 1,
                "duration": 30
            }
        }
    ]
    
    print("\n\n" + "=" * 80)
    print("checkStaffCanBook API 測試")
    print("=" * 80)
    
    for test_case in test_cases:
        print(f"\n📝 測試: {test_case['name']}")
        print(f"   參數: {test_case['params']}")
        
        try:
            # 發送 GET 請求
            response = requests.get(
                f"{API_BASE_URL}/rooms/checkStaffCanBook",
                params=test_case['params'],
                timeout=10
            )
            
            # 檢查回應狀態
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ 狀態碼: {response.status_code}")
                print(f"   📊 回應: {json.dumps(result, ensure_ascii=False, indent=6)}")
            else:
                print(f"   ❌ 狀態碼: {response.status_code}")
                print(f"   📊 回應: {response.text}")
        
        except requests.exceptions.ConnectionError:
            print(f"   ❌ 連線失敗 - 請確保 API 服務器正在運行 (http://localhost:5001)")
        except Exception as e:
            print(f"   ❌ 錯誤: {str(e)}")

if __name__ == '__main__':
    test_checkRoomCanBook()
    test_checkStaffCanBook()
    print("\n" + "=" * 80)
    print("測試完成")
    print("=" * 80)
