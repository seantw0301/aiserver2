#!/usr/bin/env python3
"""
測試腳本：驗證 checkRoomCanBook 和 checkStaffCanBook API 的黑名單功能
"""

import requests
import json
import sys

# API 端點
BASE_URL = "http://localhost:8000/api/rooms"

# 測試參數
NORMAL_USER_LINEID = "U1234567890abcdef"  # 正常用戶（假設不在黑名單中）
BLACKLIST_LINEID = "U9999999999999999"    # 假設為超級黑名單用戶

def test_check_room_can_book(lineid, test_name):
    """測試 checkRoomCanBook 端點"""
    print(f"\n{'='*60}")
    print(f"測試：{test_name}")
    print(f"{'='*60}")
    
    params = {
        'date': '2025-12-20',
        'time': '14:00',
        'guest': 2,
        'duration': 90,
        'storeid': '1',
        'lineid': lineid
    }
    
    try:
        response = requests.get(f"{BASE_URL}/checkRoomCanBook", params=params)
        print(f"✓ 狀態碼: {response.status_code}")
        result = response.json()
        print(f"✓ 響應內容:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 驗證響應
        if 'result' in result:
            if lineid == BLACKLIST_LINEID and not result['result']:
                print("✅ 超級黑名單檢查正確：拒絕了黑名單用戶")
                return True
            elif lineid == NORMAL_USER_LINEID:
                print("✅ 正常用戶檢查通過")
                return True
        return False
        
    except requests.exceptions.ConnectionError:
        print("✗ 連接失敗：API 服務器未運行")
        return False
    except Exception as e:
        print(f"✗ 錯誤: {e}")
        return False

def test_check_staff_can_book(lineid, test_name):
    """測試 checkStaffCanBook 端點"""
    print(f"\n{'='*60}")
    print(f"測試：{test_name}")
    print(f"{'='*60}")
    
    params = {
        'date': '2025-12-20',
        'time': '14:00',
        'guest': 1,
        'duration': 90,
        'storeid': '1',
        'lineid': lineid
    }
    
    try:
        response = requests.get(f"{BASE_URL}/checkStaffCanBook", params=params)
        print(f"✓ 狀態碼: {response.status_code}")
        result = response.json()
        print(f"✓ 響應內容:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # 驗證響應
        if 'result' in result and 'available_staffs' in result:
            if lineid == BLACKLIST_LINEID and not result['result']:
                print("✅ 超級黑名單檢查正確：拒絕了黑名單用戶")
                return True
            elif lineid == NORMAL_USER_LINEID:
                print("✅ 正常用戶檢查通過")
                return True
        return False
        
    except requests.exceptions.ConnectionError:
        print("✗ 連接失敗：API 服務器未運行")
        return False
    except Exception as e:
        print(f"✗ 錯誤: {e}")
        return False

def test_missing_lineid():
    """測試缺少 lineid 參數"""
    print(f"\n{'='*60}")
    print("測試：缺少 lineid 參數")
    print(f"{'='*60}")
    
    params = {
        'date': '2025-12-20',
        'time': '14:00',
        'guest': 2,
        'duration': 90,
        'storeid': '1'
        # 注意：沒有 lineid
    }
    
    try:
        response = requests.get(f"{BASE_URL}/checkRoomCanBook", params=params)
        print(f"✓ 狀態碼: {response.status_code}")
        
        if response.status_code == 400:
            print("✅ 正確拒絕了缺少必需參數的請求")
            return True
        else:
            print(f"✗ 預期狀態碼 400，但得到 {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ 錯誤: {e}")
        return False

def main():
    """執行所有測試"""
    print("\n" + "="*60)
    print("API 黑名單功能測試套件")
    print("="*60)
    
    print("\n⚠️  確保 API 服務器已在 http://localhost:8000 上運行")
    print("⚠️  如果使用假的 blacklist_lineid，測試可能不會顯示預期結果")
    
    results = []
    
    # 測試 1：checkRoomCanBook - 正常用戶
    results.append(("checkRoomCanBook - 正常用戶", 
                   test_check_room_can_book(NORMAL_USER_LINEID, "checkRoomCanBook - 正常用戶")))
    
    # 測試 2：checkRoomCanBook - 超級黑名單用戶
    results.append(("checkRoomCanBook - 超級黑名單用戶", 
                   test_check_room_can_book(BLACKLIST_LINEID, "checkRoomCanBook - 超級黑名單用戶")))
    
    # 測試 3：checkStaffCanBook - 正常用戶
    results.append(("checkStaffCanBook - 正常用戶", 
                   test_check_staff_can_book(NORMAL_USER_LINEID, "checkStaffCanBook - 正常用戶")))
    
    # 測試 4：checkStaffCanBook - 超級黑名單用戶
    results.append(("checkStaffCanBook - 超級黑名單用戶", 
                   test_check_staff_can_book(BLACKLIST_LINEID, "checkStaffCanBook - 超級黑名單用戶")))
    
    # 測試 5：缺少 lineid 參數
    results.append(("缺少 lineid 參數", test_missing_lineid()))
    
    # 打印總結
    print(f"\n{'='*60}")
    print("測試結果總結")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status}: {test_name}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試都通過了！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 個測試失敗")
        return 1

if __name__ == "__main__":
    sys.exit(main())
