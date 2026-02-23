#!/usr/bin/env python3
"""
測試 checkRoomCanBook 修復
"""
import requests
import sys
from datetime import datetime, timedelta

# API 基礎 URL
API_BASE_URL = "http://localhost:8000/api"

def test_checkroom():
    """測試 checkRoomCanBook API"""
    
    # 用明天的日期進行測試
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    test_cases = [
        {
            "name": "基本測試 - 下午 2:45，60 分鐘",
            "params": {
                "date": tomorrow,
                "time": "14:45",
                "guest": 1,
                "duration": 60,
                "storeid": "1",
                "lineid": "U1234567890abcdef"
            }
        },
        {
            "name": "邊界測試 - 接近營業結束",
            "params": {
                "date": tomorrow,
                "time": "23:30",
                "guest": 1,
                "duration": 60,
                "storeid": "1",
                "lineid": "U1234567890abcdef"
            }
        },
        {
            "name": "早上測試",
            "params": {
                "date": tomorrow,
                "time": "09:00",
                "guest": 1,
                "duration": 120,
                "storeid": "1",
                "lineid": "U1234567890abcdef"
            }
        },
    ]
    
    print(f"{'='*60}")
    print(f"checkRoomCanBook API 測試")
    print(f"{'='*60}\n")
    
    for test in test_cases:
        print(f"[測試] {test['name']}")
        print(f"參數: {test['params']}")
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/rooms/checkRoomCanBook",
                params=test['params'],
                timeout=10
            )
            
            print(f"狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"結果: {data}")
                if 'error' in data:
                    print(f"❌ 錯誤: {data['error']}")
                elif data.get('result'):
                    print(f"✅ 可以預約 (店家: {data.get('store_id')})")
                else:
                    print(f"❌ 無法預約")
            else:
                print(f"❌ API 錯誤: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"❌ 連接錯誤: {e}")
        
        print()

if __name__ == "__main__":
    test_checkroom()
