#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清除 Redis 緩存工具
用於清除所有與預約系統相關的 Redis 緩存數據，確保使用最新的資料庫數據
"""

import redis
import sys
import os
from datetime import datetime, timedelta

# 添加父目錄到 sys.path，以便導入模組
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.database import db_config

# Redis 配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0


def get_redis_client():
    """獲取 Redis 客戶端連接"""
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    except Exception as e:
        print(f"❌ Redis 連接失敗: {e}")
        return None


def clear_all_cache(redis_client):
    """清除所有緩存"""
    print("\n" + "="*80)
    print("清除所有 Redis 緩存")
    print("="*80)
    
    # 獲取所有 key
    all_keys = redis_client.keys('*')
    
    if not all_keys:
        print("\n⚠️  Redis 中沒有任何數據")
        return 0
    
    print(f"\n找到 {len(all_keys)} 個 key:")
    for key in sorted(all_keys):
        print(f"  - {key}")
    
    # 確認刪除
    print("\n" + "-"*80)
    confirm = input("⚠️  確定要刪除所有緩存嗎？(yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ 取消操作")
        return 0
    
    # 刪除所有 key
    deleted = redis_client.delete(*all_keys)
    print(f"\n✓ 已刪除 {deleted} 個 key")
    return deleted


def clear_date_cache(redis_client, date_str=None):
    """清除指定日期的緩存"""
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    print("\n" + "="*80)
    print(f"清除日期相關的 Redis 緩存: {date_str}")
    print("="*80)
    
    # 查找相關的 key
    patterns = [
        f'*{date_str}*',
        f'work_data_{date_str}',
        f'room_status_{date_str}',
        f'instores_{date_str}'
    ]
    
    all_matching_keys = set()
    for pattern in patterns:
        keys = redis_client.keys(pattern)
        all_matching_keys.update(keys)
    
    if not all_matching_keys:
        print(f"\n⚠️  沒有找到 {date_str} 相關的緩存")
        return 0
    
    print(f"\n找到 {len(all_matching_keys)} 個相關的 key:")
    for key in sorted(all_matching_keys):
        print(f"  - {key}")
    
    # 刪除
    deleted = redis_client.delete(*all_matching_keys)
    print(f"\n✓ 已刪除 {deleted} 個 key")
    return deleted


def clear_specific_cache(redis_client, cache_type):
    """清除特定類型的緩存"""
    print("\n" + "="*80)
    print(f"清除特定類型的 Redis 緩存: {cache_type}")
    print("="*80)
    
    type_patterns = {
        'work': 'work_data_*',
        'room': 'room_status_*',
        'store': 'instores_*',
        'staffs': 'staffs_data*'
    }
    
    pattern = type_patterns.get(cache_type)
    if not pattern:
        print(f"❌ 不支援的緩存類型: {cache_type}")
        print(f"可用類型: {', '.join(type_patterns.keys())}")
        return 0
    
    keys = redis_client.keys(pattern)
    
    if not keys:
        print(f"\n⚠️  沒有找到 {cache_type} 類型的緩存")
        return 0
    
    print(f"\n找到 {len(keys)} 個 key:")
    for key in sorted(keys):
        print(f"  - {key}")
    
    deleted = redis_client.delete(*keys)
    print(f"\n✓ 已刪除 {deleted} 個 key")
    return deleted


def clear_date_range_cache(redis_client, days=7):
    """清除最近幾天的緩存"""
    print("\n" + "="*80)
    print(f"清除最近 {days} 天的 Redis 緩存")
    print("="*80)
    
    all_keys_to_delete = set()
    
    # 生成日期列表
    today = datetime.now()
    for i in range(days):
        date = today - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        
        # 查找該日期的所有 key
        patterns = [f'*{date_str}*']
        for pattern in patterns:
            keys = redis_client.keys(pattern)
            all_keys_to_delete.update(keys)
    
    if not all_keys_to_delete:
        print(f"\n⚠️  沒有找到最近 {days} 天的緩存")
        return 0
    
    print(f"\n找到 {len(all_keys_to_delete)} 個相關的 key:")
    for key in sorted(all_keys_to_delete)[:20]:  # 只顯示前20個
        print(f"  - {key}")
    if len(all_keys_to_delete) > 20:
        print(f"  ... 還有 {len(all_keys_to_delete) - 20} 個")
    
    deleted = redis_client.delete(*all_keys_to_delete)
    print(f"\n✓ 已刪除 {deleted} 個 key")
    return deleted


def reset_all_visitdate_to_yesterday():
    """重設所有用戶的 visitdate 為昨天（用於測試 greeting message）"""
    print("\n" + "="*80)
    print("重設所有用戶的 visitdate 為昨天")
    print("="*80)
    print("\n📋 修改的資料庫欄位：")
    print("   表：line_users")
    print("   欄位：visitdate")
    print("   說明：記錄用戶最後一次訪問的日期（YYYY-MM-DD 格式）")
    print("\n⚠️  注意：")
    print("   - 只修改資料庫還不夠，Redis latest 標記仍存在")
    print("   - 需要同時執行「選項 7」清除 Redis latest 標記")
    print("   - 兩個操作都完成後，用戶再次登入才會顯示 greeting message")
    
    try:
        connection = db_config.get_connection()
        if not connection:
            print("❌ 無法連接資料庫")
            return 0
        
        cursor = connection.cursor()
        
        # 先查看有多少用戶
        cursor.execute("SELECT COUNT(*) as count FROM line_users")
        result = cursor.fetchone()
        user_count = result[0] if result else 0
        
        if user_count == 0:
            print("\n⚠️  資料庫中沒有用戶")
            cursor.close()
            connection.close()
            return 0
        
        print(f"\n找到 {user_count} 個用戶")
        
        # 確認操作
        print("\n" + "-"*80)
        confirm = input("⚠️  確定要將所有用戶的 visitdate 重設為昨天嗎？(yes/no): ").strip().lower()
        
        if confirm != 'yes':
            print("❌ 取消操作")
            cursor.close()
            connection.close()
            return 0
        
        # 計算昨天的日期
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # 更新所有用戶的 visitdate
        update_query = "UPDATE line_users SET visitdate = %s WHERE visitdate IS NOT NULL OR visitdate IS NULL"
        cursor.execute(update_query, (yesterday,))
        connection.commit()
        
        updated_count = cursor.rowcount
        
        print(f"\n✓ 已重設 {updated_count} 個用戶的 visitdate 為 {yesterday}（資料庫 line_users.visitdate）")
        print("\n💡 後續步驟：")
        print("   1. 執行「選項 7」清除所有用戶 Redis latest 標記")
        print("   2. 用戶再次登入時將顯示 greeting message")
        
        cursor.close()
        connection.close()
        return updated_count
        
    except Exception as e:
        print(f"❌ 操作失敗: {e}")
        import traceback
        traceback.print_exc()
        return 0


def clear_daily_greeting_flags(redis_client):
    """清除所有用戶的首次登入標記（允許測試 greeting message）"""
    print("\n" + "="*80)
    print("清除所有用戶的首次登入標記")
    print("="*80)
    print("\n📋 清除的 Redis Key：")
    print("   格式：{line_user_id}_lastest")
    print("   說明：存儲用戶最後訪問日期，過期時間 36 小時")
    print("   範例：U1234567890abcdef1234567890abcdef_lastest = '2025-12-16'")
    print("\n⚠️  注意：")
    print("   - 只清除 Redis 還不夠，資料庫 visitdate 仍是今日")
    print("   - 需要同時執行「選項 6」重設 visitdate 為昨天")
    print("   - 兩個操作都完成後，用戶再次登入才會顯示 greeting message")
    
    # 查找所有 _lastest 的 key（首次登入標記）
    pattern = '*_lastest'
    keys = redis_client.keys(pattern)
    
    if not keys:
        print(f"\n⚠️  沒有找到任何首次登入標記")
        return 0
    
    print(f"\n找到 {len(keys)} 個首次登入標記:")
    for key in sorted(keys):
        print(f"  - {key}")
    
    # 確認刪除
    print("\n" + "-"*80)
    confirm = input("⚠️  確定要刪除所有首次登入標記嗎？(yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("❌ 取消操作")
        return 0
    
    # 刪除所有標記
    deleted = redis_client.delete(*keys)
    print(f"\n✓ 已刪除 {deleted} 個首次登入標記（Redis Key：*_lastest）")
    print("\n💡 後續步驟：")
    print("   1. 執行「選項 6」重設所有用戶 visitdate 為昨天")
    print("   2. 用戶再次登入時將顯示 greeting message")
    return deleted


def list_all_keys(redis_client):
    """列出所有 key"""
    print("\n" + "="*80)
    print("Redis 中所有的 key")
    print("="*80)
    
    all_keys = redis_client.keys('*')
    
    if not all_keys:
        print("\n⚠️  Redis 中沒有任何數據")
        return
    
    print(f"\n共 {len(all_keys)} 個 key:")
    for key in sorted(all_keys):
        # 獲取 key 的類型
        key_type = redis_client.type(key)
        print(f"  - {key} ({key_type})")


def show_menu():
    """顯示主選單"""
    print("\n" + "="*80)
    print("Redis 緩存管理工具")
    print("="*80)
    print("\n請選擇操作:")
    print("  1. 列出所有緩存 key")
    print("  2. 清除今天的緩存")
    print("  3. 清除指定日期的緩存")
    print("  4. 清除最近 7 天的緩存")
    print("  5. 清除特定類型的緩存 (work/room/store/staffs)")
    print("  6. 重設所有用戶 visitdate 為昨天（測試 greeting message）")
    print("  7. 清除所有用戶的 Redis 首次登入標記")
    print("  8. 清除所有緩存 (危險操作！)")
    print("  0. 退出")
    print("-"*80)


def main():
    """主程序"""
    # 連接 Redis
    redis_client = get_redis_client()
    if redis_client is None:
        sys.exit(1)
    
    # 檢查連接
    try:
        redis_client.ping()
        print("✓ Redis 連接成功")
    except Exception as e:
        print(f"❌ Redis 連接測試失敗: {e}")
        sys.exit(1)
    
    # 互動式選單
    while True:
        show_menu()
        choice = input("\n請輸入選項 (0-8): ").strip()
        
        if choice == '0':
            print("\n👋 再見！")
            break
        
        elif choice == '1':
            list_all_keys(redis_client)
        
        elif choice == '2':
            today = datetime.now().strftime('%Y-%m-%d')
            clear_date_cache(redis_client, today)
        
        elif choice == '3':
            date_str = input("\n請輸入日期 (格式: YYYY-MM-DD，例如 2025-12-05): ").strip()
            try:
                # 驗證日期格式
                datetime.strptime(date_str, '%Y-%m-%d')
                clear_date_cache(redis_client, date_str)
            except ValueError:
                print("❌ 日期格式錯誤，請使用 YYYY-MM-DD 格式")
        
        elif choice == '4':
            clear_date_range_cache(redis_client, 7)
        
        elif choice == '5':
            print("\n可用類型: work, room, store, staffs")
            cache_type = input("請輸入緩存類型: ").strip().lower()
            clear_specific_cache(redis_client, cache_type)
        
        elif choice == '6':
            reset_all_visitdate_to_yesterday()
        
        elif choice == '7':
            clear_daily_greeting_flags(redis_client)
        
        elif choice == '8':
            clear_all_cache(redis_client)
        
        else:
            print("❌ 無效的選項，請重新選擇")
        
        # 等待用戶按下 Enter 繼續
        input("\n按 Enter 鍵繼續...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已中斷")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
