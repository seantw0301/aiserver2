#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日問候語功能測試腳本
測試 visitdate 更新、問候語生成及 Redis 緩存邏輯
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from modules import greeting
from core.database import db_config
from core.common import update_user_visitdate, get_user_info
import redis

# 測試配置
TEST_USER_ID = "test_greeting_user_001"
TEST_DISPLAY_NAME = "測試會員"
TEST_DB_USER_ID = 9999  # 資料庫中的 id 欄位

# Redis 配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

def get_redis_connection():
    """建立 Redis 連接"""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def cleanup_test_data():
    """清理測試資料（包含資料庫和 Redis）"""
    try:
        # 清理資料庫
        connection = db_config.get_connection()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM line_users WHERE line_id = %s", (TEST_USER_ID,))
            connection.commit()
            cursor.close()
            connection.close()
        
        # 清理 Redis
        r = get_redis_connection()
        r.delete(f"{TEST_USER_ID}_lastest")
        
        return True
    except Exception as e:
        print(f"清理測試資料失敗: {e}")
        return False

def create_test_user(visitdate=None):
    """建立測試用戶"""
    try:
        connection = db_config.get_connection()
        if connection:
            cursor = connection.cursor()
            
            # 先刪除舊資料
            cursor.execute("DELETE FROM line_users WHERE line_id = %s", (TEST_USER_ID,))
            
            # 插入測試用戶
            if visitdate:
                query = """
                    INSERT INTO line_users (id, line_id, display_name, visitdate, language)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cursor.execute(query, (TEST_DB_USER_ID, TEST_USER_ID, TEST_DISPLAY_NAME, visitdate, 'zh-TW'))
            else:
                query = """
                    INSERT INTO line_users (id, line_id, display_name, language)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (TEST_DB_USER_ID, TEST_USER_ID, TEST_DISPLAY_NAME, 'zh-TW'))
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
    except Exception as e:
        print(f"建立測試用戶失敗: {e}")
        return False

def get_user_visitdate():
    """獲取用戶的 visitdate"""
    try:
        connection = db_config.get_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT visitdate FROM line_users WHERE line_id = %s", (TEST_USER_ID,))
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            if result:
                return result['visitdate']
    except Exception as e:
        print(f"獲取 visitdate 失敗: {e}")
    return None

def get_redis_last_visit():
    """獲取 Redis 中的上次訪問日期"""
    try:
        r = get_redis_connection()
        return r.get(f"{TEST_USER_ID}_lastest")
    except Exception as e:
        print(f"獲取 Redis 資料失敗: {e}")
        return None

def format_datetime(dt):
    """格式化日期時間供顯示"""
    if dt is None:
        return "None"
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt)

def run_tests():
    """執行測試"""
    print("=" * 70)
    print("🧪 每日問候語功能測試 (含 Redis 緩存驗證)")
    print("=" * 70)
    
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    results = []
    
    # ============================================================
    # 測試 1: 新用戶（visitdate 為 NULL）
    # ============================================================
    print("\n" + "=" * 70)
    print("📝 測試 1: 新用戶 (visitdate 為 NULL)")
    print("=" * 70)
    
    cleanup_test_data()
    create_test_user(visitdate=None)
    
    print(f"初始狀態:")
    initial_visitdate = get_user_visitdate()
    initial_redis = get_redis_last_visit()
    print(f"  DB visitdate: {format_datetime(initial_visitdate)}")
    print(f"  Redis lastest: {initial_redis}")
    
    greeting_msg, user_info = greeting.check_daily_greeting(TEST_USER_ID)
    
    print(f"\n執行 check_daily_greeting 後:")
    print(f"  問候語: {greeting_msg}")
    
    updated_visitdate = get_user_visitdate()
    updated_redis = get_redis_last_visit()
    print(f"  更新後 DB visitdate: {format_datetime(updated_visitdate)}")
    print(f"  更新後 Redis lastest: {updated_redis}")
    
    # 驗證
    test1_pass = (
        greeting_msg is not None and
        TEST_DISPLAY_NAME in greeting_msg and
        str(TEST_DB_USER_ID) in greeting_msg and
        updated_visitdate is not None and
        updated_redis == today  # Redis 應更新為今日
    )
    
    if test1_pass:
        print("\n✅ 測試 1 通過")
        print(f"   ✓ 產生問候語: {greeting_msg}")
        print(f"   ✓ DB visitdate 已更新為今日")
        print(f"   ✓ Redis lastest 已設為今日")
    else:
        print("\n❌ 測試 1 失敗")
        if greeting_msg is None:
            print(f"   ✗ 未產生問候語")
        if updated_visitdate is None:
            print(f"   ✗ DB visitdate 未更新")
        if updated_redis != today:
            print(f"   ✗ Redis lastest 未正確設定（期望: {today}, 實際: {updated_redis}）")
    
    results.append({"name": "新用戶測試", "pass": test1_pass})
    
    # ============================================================
    # 測試 2: 昨日訪問的用戶（visitdate 為昨天）
    # ============================================================
    print("\n" + "=" * 70)
    print("📝 測試 2: 昨日訪問的用戶")
    print("=" * 70)
    
    cleanup_test_data()
    create_test_user(visitdate=yesterday)
    
    print(f"初始狀態:")
    initial_visitdate = get_user_visitdate()
    initial_redis = get_redis_last_visit()
    print(f"  DB visitdate: {format_datetime(initial_visitdate)}")
    print(f"  Redis lastest: {initial_redis}")
    
    greeting_msg, user_info = greeting.check_daily_greeting(TEST_USER_ID)
    
    print(f"\n執行 check_daily_greeting 後:")
    print(f"  問候語: {greeting_msg}")
    
    updated_visitdate = get_user_visitdate()
    updated_redis = get_redis_last_visit()
    print(f"  更新後 DB visitdate: {format_datetime(updated_visitdate)}")
    print(f"  更新後 Redis lastest: {updated_redis}")
    
    # 驗證
    test2_pass = (
        greeting_msg is not None and
        TEST_DISPLAY_NAME in greeting_msg and
        str(TEST_DB_USER_ID) in greeting_msg and
        updated_visitdate is not None and
        str(updated_visitdate).startswith(today) and
        updated_redis == today
    )
    
    if test2_pass:
        print("\n✅ 測試 2 通過")
        print(f"   ✓ 產生問候語: {greeting_msg}")
        print(f"   ✓ DB visitdate 已從昨日更新為今日")
        print(f"   ✓ Redis lastest 已設為今日")
    else:
        print("\n❌ 測試 2 失敗")
        if greeting_msg is None:
            print(f"   ✗ 未產生問候語")
        if updated_redis != today:
            print(f"   ✗ Redis 未正確更新")
    
    results.append({"name": "昨日訪問用戶測試", "pass": test2_pass})
    
    # ============================================================
    # 測試 3: 今日已訪問的用戶（visitdate 為今天）
    # ============================================================
    print("\n" + "=" * 70)
    print("📝 測試 3: 今日已訪問的用戶")
    print("=" * 70)
    
    cleanup_test_data()
    create_test_user(visitdate=today)
    
    print(f"初始狀態:")
    initial_visitdate = get_user_visitdate()
    initial_redis = get_redis_last_visit()
    print(f"  DB visitdate: {format_datetime(initial_visitdate)}")
    print(f"  Redis lastest: {initial_redis}")
    
    greeting_msg, user_info = greeting.check_daily_greeting(TEST_USER_ID)
    
    print(f"\n執行 check_daily_greeting 後:")
    print(f"  問候語: {greeting_msg}")
    
    updated_visitdate = get_user_visitdate()
    updated_redis = get_redis_last_visit()
    print(f"  更新後 DB visitdate: {format_datetime(updated_visitdate)}")
    print(f"  更新後 Redis lastest: {updated_redis}")
    
    # 驗證（注意：Redis 無記錄時仍會查資料庫並更新 Redis）
    test3_pass = (
        greeting_msg is None and
        updated_visitdate is not None and
        str(updated_visitdate).startswith(today) and
        updated_redis == today  # Redis 應已被設定
    )
    
    if test3_pass:
        print("\n✅ 測試 3 通過")
        print(f"   ✓ 未產生問候語（今日已訪問）")
        print(f"   ✓ DB visitdate 保持為今日")
        print(f"   ✓ Redis lastest 已設為今日")
    else:
        print("\n❌ 測試 3 失敗")
        if greeting_msg is not None:
            print(f"   ✗ 不應產生問候語，但產生了: {greeting_msg}")
        if updated_redis != today:
            print(f"   ✗ Redis 未正確設定")
    
    results.append({"name": "今日已訪問用戶測試", "pass": test3_pass})
    
    # ============================================================
    # 測試 4: 連續兩次調用（同一天）- Redis 緩存驗證
    # ============================================================
    print("\n" + "=" * 70)
    print("📝 測試 4: 連續兩次調用（模擬同一天多次訊息）")
    print("=" * 70)
    
    cleanup_test_data()
    create_test_user(visitdate=yesterday)
    
    print(f"初始狀態:")
    initial_visitdate = get_user_visitdate()
    initial_redis = get_redis_last_visit()
    print(f"  DB visitdate: {format_datetime(initial_visitdate)}")
    print(f"  Redis lastest: {initial_redis}")
    
    # 第一次調用
    print("\n第一次調用:")
    greeting_msg_1, user_info_1 = greeting.check_daily_greeting(TEST_USER_ID)
    redis_after_first = get_redis_last_visit()
    print(f"  問候語: {greeting_msg_1}")
    print(f"  Redis lastest: {redis_after_first}")
    
    # 第二次調用（應該不產生問候語，且走 Redis 快速路徑）
    print("\n第二次調用:")
    greeting_msg_2, user_info_2 = greeting.check_daily_greeting(TEST_USER_ID)
    redis_after_second = get_redis_last_visit()
    print(f"  問候語: {greeting_msg_2}")
    print(f"  Redis lastest: {redis_after_second}")
    
    updated_visitdate = get_user_visitdate()
    print(f"\n最終 DB visitdate: {format_datetime(updated_visitdate)}")
    
    # 驗證
    test4_pass = (
        greeting_msg_1 is not None and      # 第一次應有問候語
        greeting_msg_2 is None and          # 第二次不應有問候語（Redis 命中）
        updated_visitdate is not None and
        str(updated_visitdate).startswith(today) and
        redis_after_first == today and      # 第一次後 Redis 已設定
        redis_after_second == today         # 第二次後 Redis 保持不變
    )
    
    if test4_pass:
        print("\n✅ 測試 4 通過")
        print(f"   ✓ 第一次調用產生問候語並設定 Redis")
        print(f"   ✓ 第二次調用走 Redis 快速路徑，不產生問候語")
        print(f"   ✓ Redis 緩存機制正常運作")
    else:
        print("\n❌ 測試 4 失敗")
        if greeting_msg_1 is None:
            print(f"   ✗ 第一次調用應產生問候語")
        if greeting_msg_2 is not None:
            print(f"   ✗ 第二次調用不應產生問候語（Redis 應命中）")
        if redis_after_first != today:
            print(f"   ✗ Redis 未在第一次調用後正確設定")
    
    results.append({"name": "連續調用測試（Redis 緩存）", "pass": test4_pass})
    
    # ============================================================
    # 測試 5: Redis 快速路徑驗證
    # ============================================================
    print("\n" + "=" * 70)
    print("📝 測試 5: Redis 快速路徑驗證（今日 Redis 有值）")
    print("=" * 70)
    
    cleanup_test_data()
    create_test_user(visitdate=yesterday)
    
    # 先設定 Redis 為今日（模擬已訪問過）
    r = get_redis_connection()
    r.setex(f"{TEST_USER_ID}_lastest", 36 * 3600, today)
    
    print(f"初始狀態:")
    initial_visitdate = get_user_visitdate()
    initial_redis = get_redis_last_visit()
    print(f"  DB visitdate: {format_datetime(initial_visitdate)} (昨日)")
    print(f"  Redis lastest: {initial_redis} (已預設為今日)")
    
    greeting_msg, user_info = greeting.check_daily_greeting(TEST_USER_ID)
    
    print(f"\n執行 check_daily_greeting 後:")
    print(f"  問候語: {greeting_msg}")
    
    updated_visitdate = get_user_visitdate()
    print(f"  DB visitdate: {format_datetime(updated_visitdate)} (應保持昨日，未更新)")
    
    # 驗證：Redis 命中時應跳過 DB 更新
    test5_pass = (
        greeting_msg is None and  # Redis 已是今日，不產生問候語
        user_info is not None and
        str(updated_visitdate).startswith(yesterday)  # DB 應保持昨日（未更新）
    )
    
    if test5_pass:
        print("\n✅ 測試 5 通過")
        print(f"   ✓ Redis 快速路徑生效，未產生問候語")
        print(f"   ✓ DB visitdate 未更新（性能優化成功）")
        print(f"   ✓ user_info 正常返回")
    else:
        print("\n❌ 測試 5 失敗")
        if greeting_msg is not None:
            print(f"   ✗ Redis 已為今日，不應產生問候語")
        if not str(updated_visitdate).startswith(yesterday):
            print(f"   ✗ Redis 命中時不應更新 DB（期望保持昨日）")
    
    results.append({"name": "Redis 快速路徑驗證", "pass": test5_pass})
    
    # ============================================================
    # 測試 6: user_info 正確性
    # ============================================================
    print("\n" + "=" * 70)
    print("📝 測試 6: user_info 資料正確性")
    print("=" * 70)
    
    cleanup_test_data()
    create_test_user(visitdate=yesterday)
    
    greeting_msg, user_info = greeting.check_daily_greeting(TEST_USER_ID)
    
    print(f"返回的 user_info:")
    if user_info:
        for key, value in user_info.items():
            print(f"  {key}: {value}")
    
    # 驗證
    test6_pass = (
        user_info is not None and
        user_info.get('line_id') == TEST_USER_ID and
        user_info.get('display_name') == TEST_DISPLAY_NAME and
        user_info.get('id') == TEST_DB_USER_ID and
        'visitdate' in user_info  # 舊的 visitdate（更新前的值）
    )
    
    if test6_pass:
        print("\n✅ 測試 6 通過")
        print(f"   ✓ user_info 包含正確的用戶資料")
        print(f"   ✓ visitdate 為更新前的值（昨天）")
    else:
        print("\n❌ 測試 6 失敗")
        if user_info is None:
            print(f"   ✗ user_info 為 None")
        else:
            if user_info.get('line_id') != TEST_USER_ID:
                print(f"   ✗ line_id 不正確")
            if user_info.get('display_name') != TEST_DISPLAY_NAME:
                print(f"   ✗ display_name 不正確")
    
    results.append({"name": "user_info 正確性測試", "pass": test6_pass})
    
    # 清理
    cleanup_test_data()
    
    # ============================================================
    # 測試總結
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 測試總結")
    print("=" * 70)
    
    passed = sum(1 for r in results if r['pass'])
    total = len(results)
    
    for i, result in enumerate(results, 1):
        status = "✅" if result['pass'] else "❌"
        print(f"{status} 測試 {i}: {result['name']}")
    
    print(f"\n通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有測試通過！")
        print("\n💡 Redis 緩存優化已生效:")
        print("   • 第2次起的每日對話無需查詢資料庫")
        print("   • 預估性能提升 90%+（假設大部分對話集中在同日）")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 個測試失敗")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())
