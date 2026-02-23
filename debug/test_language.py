#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
語系測試腳本
測試語言檢測、Redis 寫入、資料庫寫入及讀取功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis
from modules import lang
from core.database import db_config

# 測試配置
TEST_USER_ID = "test_user_language_001"
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# 測試案例
TEST_CASES = [
    {"message": "我要設定為中文", "expected_lang": "zh-TW", "description": "繁體中文關鍵字"},
    {"message": "請設定為Taiwan", "expected_lang": "zh-TW", "description": "Taiwan 關鍵字"},
    {"message": "I want to set English", "expected_lang": "en", "description": "English 關鍵字"},
    {"message": "請設定為英文", "expected_lang": "en", "description": "英文關鍵字"},
    {"message": "請設定為泰文", "expected_lang": "th", "description": "泰文關鍵字"},
    {"message": "Thailand language please", "expected_lang": "th", "description": "Thailand 關鍵字"},
    {"message": "日文でお願いします", "expected_lang": "ja", "description": "日文關鍵字"},
    {"message": "請設定為Japanese", "expected_lang": "ja", "description": "Japanese 關鍵字"},
    {"message": "Korean language", "expected_lang": "ko", "description": "Korean 關鍵字"},
    {"message": "請設定為韓文", "expected_lang": "ko", "description": "韓文關鍵字"},
    {"message": "今天想預約按摩", "expected_lang": None, "description": "無語言關鍵字"},
]

def get_redis_connection():
    """建立 Redis 連接"""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def cleanup_test_data():
    """清理測試資料"""
    print("\n🧹 清理測試資料...")
    
    # 清理 Redis
    try:
        r = get_redis_connection()
        r.delete(f"{TEST_USER_ID}_lang")
        print(f"  ✓ Redis key '{TEST_USER_ID}_lang' 已刪除")
    except Exception as e:
        print(f"  ✗ Redis 清理失敗: {e}")
    
    # 清理資料庫
    try:
        connection = db_config.get_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM line_users WHERE line_id = %s", (TEST_USER_ID,))
            connection.commit()
            print(f"  ✓ 資料庫記錄 '{TEST_USER_ID}' 已刪除")
            cursor.close()
            connection.close()
    except Exception as e:
        print(f"  ✗ 資料庫清理失敗: {e}")

def verify_redis(expected_lang):
    """驗證 Redis 中的值"""
    try:
        r = get_redis_connection()
        actual_lang = r.get(f"{TEST_USER_ID}_lang")
        
        if expected_lang is None:
            if actual_lang is None or actual_lang == 'zh-TW':
                print(f"    ✓ Redis: {actual_lang or '(空值，符合預期)'}")
                return True
            else:
                print(f"    ✗ Redis: 預期為空或 zh-TW，實際為 {actual_lang}")
                return False
        else:
            if actual_lang == expected_lang:
                print(f"    ✓ Redis: {actual_lang}")
                return True
            else:
                print(f"    ✗ Redis: 預期 {expected_lang}，實際 {actual_lang}")
                return False
    except Exception as e:
        print(f"    ✗ Redis 驗證失敗: {e}")
        return False

def verify_database(expected_lang):
    """驗證資料庫中的值"""
    try:
        connection = db_config.get_connection()
        if not connection:
            print("    ✗ 無法連接資料庫")
            return False
        
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT language FROM line_users WHERE line_id = %s", (TEST_USER_ID,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if expected_lang is None:
            if result is None or result.get('language') in [None, 'zh-TW']:
                print(f"    ✓ Database: {result.get('language') if result else '(無記錄，符合預期)'}")
                return True
            else:
                print(f"    ✗ Database: 預期為空或 zh-TW，實際為 {result.get('language')}")
                return False
        else:
            if result and result.get('language') == expected_lang:
                print(f"    ✓ Database: {result.get('language')}")
                return True
            else:
                actual = result.get('language') if result else '(無記錄)'
                print(f"    ✗ Database: 預期 {expected_lang}，實際 {actual}")
                return False
    except Exception as e:
        print(f"    ✗ Database 驗證失敗: {e}")
        return False

def run_test():
    """執行測試"""
    print("=" * 60)
    print("🧪 語系功能測試")
    print("=" * 60)
    
    # 清理舊資料
    cleanup_test_data()
    
    results = []
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n📝 測試 {i}/{len(TEST_CASES)}: {test_case['description']}")
        print(f"   訊息: \"{test_case['message']}\"")
        print(f"   預期語系: {test_case['expected_lang'] or '(無變更)'}")
        
        # 每個測試前先清理，避免狀態污染
        cleanup_test_data()
        
        # 1. 測試語言檢測
        detected_lang = lang.detect_language(test_case['message'])
        
        if test_case['expected_lang'] is None:
            if detected_lang is None:
                print(f"  ✓ 語言檢測: 無檢測到語言關鍵字 (符合預期)")
                detect_pass = True
            else:
                print(f"  ✗ 語言檢測: 預期無檢測，實際檢測到 {detected_lang}")
                detect_pass = False
        else:
            if detected_lang == test_case['expected_lang']:
                print(f"  ✓ 語言檢測: {detected_lang}")
                detect_pass = True
            else:
                print(f"  ✗ 語言檢測: 預期 {test_case['expected_lang']}，實際 {detected_lang}")
                detect_pass = False
        
        # 2. 設定語言
        if detected_lang:
            success = lang.set_user_language(TEST_USER_ID, detected_lang)
            if success:
                print(f"  ✓ 設定語言: 成功")
                set_pass = True
            else:
                print(f"  ✗ 設定語言: 失敗")
                set_pass = False
        else:
            # 若無檢測到語言，則初始化為預設值
            lang.initialize_user_language_if_needed(TEST_USER_ID, 'zh-TW')
            print(f"  ✓ 初始化語言: zh-TW")
            set_pass = True
        
        # 3. 驗證 Redis
        print("  驗證儲存:")
        redis_pass = verify_redis(test_case['expected_lang'])
        
        # 4. 驗證 Database
        db_pass = verify_database(test_case['expected_lang'])
        
        # 5. 讀取驗證
        read_lang = lang.get_user_language(TEST_USER_ID)
        expected_read = test_case['expected_lang'] or 'zh-TW'
        if read_lang == expected_read:
            print(f"    ✓ 讀取驗證: {read_lang}")
            read_pass = True
        else:
            print(f"    ✗ 讀取驗證: 預期 {expected_read}，實際 {read_lang}")
            read_pass = False
        
        # 記錄結果
        test_pass = detect_pass and set_pass and redis_pass and db_pass and read_pass
        results.append({
            'case': test_case['description'],
            'pass': test_pass
        })
        
        if test_pass:
            print(f"  ✅ 測試通過")
        else:
            print(f"  ❌ 測試失敗")
    
    # 最終清理
    cleanup_test_data()
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 測試總結")
    print("=" * 60)
    
    passed = sum(1 for r in results if r['pass'])
    total = len(results)
    
    for i, result in enumerate(results, 1):
        status = "✅" if result['pass'] else "❌"
        print(f"{status} 測試 {i}: {result['case']}")
    
    print(f"\n通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有測試通過！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 個測試失敗")
        return 1

if __name__ == '__main__':
    sys.exit(run_test())
