"""
調試 get_all_room_status 函數
檢查 store_occupied_status 的實際內容
"""

from modules.workday_manager import WorkdayManager
from core.store import StoreManager
import json

def debug_room_status():
    """調試房間狀態計算"""
    
    test_date = "2025-12-04"
    
    workday_manager = WorkdayManager()
    store_manager = StoreManager()
    
    print(f"調試日期：{test_date}\n")
    
    # 獲取所有店家
    all_stores = store_manager.get_all_stores()
    print(f"店家列表：")
    for store in all_stores:
        print(f"  {store['name']} (ID: {store['id']}): {store['rooms']} 間房")
    
    # 獲取佔用狀態
    print(f"\n獲取佔用狀態...")
    store_occupied_status = store_manager.get_store_occupied_block_by_date_24H(test_date)
    
    print(f"\nstore_occupied_status 結構：")
    print(f"  keys: {list(store_occupied_status.keys())}")
    
    if 'data' in store_occupied_status:
        print(f"\n  data keys: {list(store_occupied_status['data'].keys())}")
        print(f"  data keys types: {[type(k) for k in store_occupied_status['data'].keys()]}")
        
        for key, value in store_occupied_status['data'].items():
            print(f"\n  Store {key} (type: {type(key)}):")
            if isinstance(value, dict):
                print(f"    keys: {list(value.keys())}")
                if 'blocks' in value:
                    blocks = value['blocks']
                    print(f"    blocks length: {len(blocks)}")
                    print(f"    blocks[180] (15:00): {blocks[180]}")
                    print(f"    blocks[240] (20:00): {blocks[240]}")
                    print(f"    sum of blocks: {sum(blocks)}")
                    print(f"    max of blocks: {max(blocks)}")
    
    # 保存完整數據以供檢查
    with open('debug_occupied_status.json', 'w', encoding='utf-8') as f:
        json.dump(store_occupied_status, f, ensure_ascii=False, indent=2)
    
    print(f"\n完整數據已保存到：debug_occupied_status.json")
    
    # 測試獲取房間狀態
    print(f"\n\n測試 get_all_room_status...")
    room_status = workday_manager.get_all_room_status(test_date)
    
    print(f"\nroom_status keys: {list(room_status.keys())}")
    print(f"room_status keys types: {[type(k) for k in room_status.keys()]}")
    
    for key, value in room_status.items():
        print(f"\n  Store {key} (type: {type(key)}):")
        print(f"    store_name: {value.get('store_name')}")
        free_blocks = value.get('free_blocks', [])
        print(f"    free_blocks[180] (15:00): {free_blocks[180]}")
        print(f"    free_blocks[240] (20:00): {free_blocks[240]}")
    
    # 保存房間狀態
    with open('debug_room_status.json', 'w', encoding='utf-8') as f:
        json.dump(room_status, f, ensure_ascii=False, indent=2)
    
    print(f"\n房間狀態已保存到：debug_room_status.json")

if __name__ == "__main__":
    debug_room_status()
