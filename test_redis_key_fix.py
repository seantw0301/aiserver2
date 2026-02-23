#!/usr/bin/env python3
"""
測試 Redis JSON 鍵類型修復
驗證從 Redis 讀取的數據能夠正確訪問
"""
import sys
sys.path.insert(0, '/Volumes/aiserver2')

from modules.workday_manager import WorkdayManager
from datetime import datetime, timedelta
import json

def test_avoid_block():
    """測試 avoid_block 數據結構"""
    print("=" * 60)
    print("測試 avoid_block 數據結構")
    print("=" * 60)
    
    workday_manager = WorkdayManager()
    
    # 使用未來日期
    test_date = (datetime.now() + timedelta(days=3)).strftime('%Y/%m/%d')
    print(f"\n測試日期: {test_date}")
    
    # 清除緩存以確保從資料庫重新獲取
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    query_date = test_date.replace('/', '-')
    redis_client.delete(f'avoid_block_{query_date}')
    print("✅ 已清除 Redis 緩存")
    
    # 第一次調用 - 從數據庫獲取並存入 Redis
    print("\n第一次調用（從資料庫獲取）...")
    result1 = workday_manager.get_all_task_avoid_block(test_date)
    
    if result1:
        print(f"✅ 獲取成功")
        print(f"店家數量: {len(result1)}")
        print(f"鍵類型: {[type(k).__name__ for k in list(result1.keys())[:3]]}")
        print(f"鍵列表: {list(result1.keys())}")
        
        # 驗證數據結構
        for store_id, blocks in list(result1.items())[:2]:
            print(f"\n店家 ID: {store_id} (類型: {type(store_id).__name__})")
            print(f"Blocks 長度: {len(blocks)}")
            print(f"前10個值: {blocks[:10]}")
    else:
        print("❌ 獲取失敗")
        return
    
    # 第二次調用 - 從 Redis 緩存獲取
    print("\n\n第二次調用（從 Redis 緩存獲取）...")
    result2 = workday_manager.get_all_task_avoid_block(test_date)
    
    if result2:
        print(f"✅ 獲取成功")
        print(f"店家數量: {len(result2)}")
        print(f"鍵類型: {[type(k).__name__ for k in list(result2.keys())[:3]]}")
        print(f"鍵列表: {list(result2.keys())}")
        
        # 驗證鍵類型一致性
        keys1 = set(result1.keys())
        keys2 = set(result2.keys())
        
        if keys1 == keys2:
            print("\n✅ 鍵集合一致")
        else:
            print(f"\n❌ 鍵集合不一致")
            print(f"第一次獨有: {keys1 - keys2}")
            print(f"第二次獨有: {keys2 - keys1}")
        
        # 測試字符串鍵訪問
        test_store_id = "1"
        if test_store_id in result2:
            print(f"\n✅ 可以使用字符串鍵 '{test_store_id}' 訪問")
            print(f"Block 數量: {len(result2[test_store_id])}")
        else:
            print(f"\n❌ 無法使用字符串鍵 '{test_store_id}' 訪問")
            print(f"可用鍵: {list(result2.keys())}")
    else:
        print("❌ 獲取失敗")

def test_room_status():
    """測試 room_status 數據結構"""
    print("\n\n" + "=" * 60)
    print("測試 room_status 數據結構")
    print("=" * 60)
    
    workday_manager = WorkdayManager()
    
    # 使用未來日期
    test_date = (datetime.now() + timedelta(days=3)).strftime('%Y/%m/%d')
    print(f"\n測試日期: {test_date}")
    
    # 清除緩存
    import redis
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    query_date = test_date.replace('/', '-')
    redis_client.delete(f'room_status_{query_date}')
    print("✅ 已清除 Redis 緩存")
    
    # 第一次調用
    print("\n第一次調用（從資料庫獲取）...")
    result1 = workday_manager.get_all_room_status(test_date)
    
    if result1:
        print(f"✅ 獲取成功")
        print(f"店家數量: {len(result1)}")
        print(f"鍵類型: {[type(k).__name__ for k in list(result1.keys())[:3]]}")
        print(f"鍵列表: {list(result1.keys())}")
    else:
        print("❌ 獲取失敗")
        return
    
    # 第二次調用
    print("\n第二次調用（從 Redis 緩存獲取）...")
    result2 = workday_manager.get_all_room_status(test_date)
    
    if result2:
        print(f"✅ 獲取成功")
        print(f"店家數量: {len(result2)}")
        print(f"鍵類型: {[type(k).__name__ for k in list(result2.keys())[:3]]}")
        print(f"鍵列表: {list(result2.keys())}")
        
        # 驗證鍵類型一致性
        keys1 = set(result1.keys())
        keys2 = set(result2.keys())
        
        if keys1 == keys2:
            print("\n✅ 鍵集合一致")
        else:
            print(f"\n❌ 鍵集合不一致")
        
        # 測試字符串鍵訪問
        test_store_id = "1"
        if test_store_id in result2:
            print(f"\n✅ 可以使用字符串鍵 '{test_store_id}' 訪問")
            print(f"店家名稱: {result2[test_store_id]['store_name']}")
            print(f"Free blocks 數量: {len(result2[test_store_id]['free_blocks'])}")
        else:
            print(f"\n❌ 無法使用字符串鍵 '{test_store_id}' 訪問")
    else:
        print("❌ 獲取失敗")

if __name__ == "__main__":
    test_avoid_block()
    test_room_status()
    print("\n\n" + "=" * 60)
    print("測試完成")
    print("=" * 60)
