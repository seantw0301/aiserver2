"""
驗證 2025-12-04 下午三點到五點的房間狀態
"""

from datetime import datetime
import json

def verify_3pm_to_5pm():
    """驗證 2025-12-04 下午 3:00-5:00 的房間狀態"""
    
    # 延遲導入以避免循環導入
    from modules.workday_manager import WorkdayManager
    from core.store import StoreManager
    
    test_date = "2025-12-04"
    
    print(f"{'='*70}")
    print(f"驗證日期：{test_date} 下午 3:00-5:00")
    print(f"{'='*70}\n")
    
    # 初始化管理器
    workday_manager = WorkdayManager()
    store_manager = StoreManager()
    
    # 步驟 1: 獲取基礎數據
    print("步驟 1: 獲取資料庫基礎數據")
    print("-" * 70)
    
    all_stores = store_manager.get_all_stores()
    print(f"✅ 店家總數：{len(all_stores)}")
    for store in all_stores:
        print(f"   - {store['name']} (ID: {store['id']}): {store['rooms']} 間房")
    
    # 步驟 2: 使用函數獲取房間狀態
    print(f"\n步驟 2: 使用 get_all_room_status 函數計算")
    print("-" * 70)
    
    room_status = workday_manager.get_all_room_status(test_date)
    
    if not room_status:
        print("❌ 函數返回 None")
        return False
    
    print(f"✅ 房間狀態獲取成功")
    
    # 步驟 3: 獲取佔用數據進行驗證
    print(f"\n步驟 3: 獲取佔用數據並驗證 15:00-17:00")
    print("-" * 70)
    
    store_occupied_status = store_manager.get_store_occupied_block_by_date_24H(test_date)
    
    # 15:00 = 時段 180 (15*12)
    # 17:00 = 時段 204 (17*12)
    start_block = 180  # 15:00
    end_block = 204    # 17:00
    
    print(f"\n{'店家':^10} {'房間數':>6} | {'時間':>8} {'最大':>4} {'佔用':>4} {'計算可用':>8} {'函數可用':>8} {'驗證':^6}")
    print("-" * 85)
    
    all_match = True
    
    for store in all_stores:
        store_id = store['id']  # 整數
        store_id_str = str(store_id)  # 字符串用於所有字典訪問
        store_name = store['name']
        max_rooms = int(store['rooms'])
        
        # 從函數結果獲取（key 是字符串）
        function_data = room_status.get(store_id_str, {})
        function_blocks = function_data.get('free_blocks', [])
        
        # 獲取佔用數據（統一使用字符串鍵）
        occupied_blocks = store_occupied_status['data'].get(store_id_str, {}).get('blocks', [0] * 294)
        
        # 只顯示該店家在 15:00-17:00 的第一筆數據
        first_shown = False
        
        for i in range(start_block, end_block):
            time_str = f"{i//12:02d}:{(i%12)*5:02d}"
            occupied = occupied_blocks[i] if i < len(occupied_blocks) else 0
            manual_free = max(max_rooms - occupied, 0)
            function_free = function_blocks[i] if i < len(function_blocks) else 0
            
            match = "✅" if manual_free == function_free else "❌"
            if manual_free != function_free:
                all_match = False
            
            # 只顯示每個店家的第一筆和有問題的數據
            if not first_shown:
                print(f"{store_name:^10} {max_rooms:6d} | {time_str:>8} {max_rooms:4d} {occupied:4d} {manual_free:8d} {function_free:8d} {match:^6}")
                first_shown = True
            elif manual_free != function_free:
                print(f"{'':^10} {'':6} | {time_str:>8} {max_rooms:4d} {occupied:4d} {manual_free:8d} {function_free:8d} {match:^6}")
    
    # 步驟 4: 統計分析 15:00-17:00
    print(f"\n步驟 4: 統計分析 15:00-17:00 時段")
    print("-" * 70)
    
    for store in all_stores:
        store_id = store['id']  # 整數
        store_id_str = str(store_id)  # 字符串
        store_name = store['name']
        max_rooms = int(store['rooms'])
        
        function_data = room_status.get(store_id_str, {})
        function_blocks = function_data.get('free_blocks', [])
        occupied_blocks = store_occupied_status['data'].get(store_id, {}).get('blocks', [0] * 294)
        
        # 統計 15:00-17:00 的數據
        period_free = [function_blocks[i] for i in range(start_block, end_block) if i < len(function_blocks)]
        period_occupied = [occupied_blocks[i] for i in range(start_block, end_block) if i < len(occupied_blocks)]
        
        avg_free = sum(period_free) / len(period_free) if period_free else 0
        avg_occupied = sum(period_occupied) / len(period_occupied) if period_occupied else 0
        max_occupied = max(period_occupied) if period_occupied else 0
        min_free = min(period_free) if period_free else 0
        
        print(f"\n{store_name}:")
        print(f"  最大房間數：{max_rooms}")
        print(f"  平均可用：{avg_free:.2f} 間")
        print(f"  平均佔用：{avg_occupied:.2f} 間")
        print(f"  最高佔用：{max_occupied} 間")
        print(f"  最少可用：{min_free} 間")
        
        # 找出最繁忙的時段
        if period_occupied:
            busy_blocks = [start_block + i for i, occ in enumerate(period_occupied) if occ == max_occupied]
            if busy_blocks:
                print(f"  最繁忙時段：")
                for block in busy_blocks[:3]:
                    time_str = f"{block//12:02d}:{(block%12)*5:02d}"
                    print(f"    - {time_str}")
                if len(busy_blocks) > 3:
                    print(f"    ... 還有 {len(busy_blocks) - 3} 個時段")
    
    # 步驟 5: 詳細時段表
    print(f"\n步驟 5: 詳細時段表 (15:00-17:00)")
    print("-" * 70)
    
    # 顯示所有時段的詳細表格
    print(f"\n{'時間':>8} | {'西門':^12} | {'延吉':^12} | {'家樂福':^12}")
    print(f"{'':>8} | {'佔用':>4} {'可用':>4} | {'佔用':>4} {'可用':>4} | {'佔用':>4} {'可用':>4}")
    print("-" * 70)
    
    for i in range(start_block, end_block, 6):  # 每30分鐘顯示一次
        time_str = f"{i//12:02d}:{(i%12)*5:02d}"
        
        row_data = [time_str]
        for store in all_stores:
            store_id = store['id']  # 整數
            store_id_str = str(store_id)  # 字符串
            max_rooms = int(store['rooms'])
            
            function_data = room_status.get(store_id_str, {})
            function_blocks = function_data.get('free_blocks', [])
            occupied_blocks = store_occupied_status['data'].get(store_id, {}).get('blocks', [0] * 294)
            
            occupied = occupied_blocks[i] if i < len(occupied_blocks) else 0
            free = function_blocks[i] if i < len(function_blocks) else 0
            
            row_data.append(f"{occupied:4d} {free:4d}")
        
        print(f"{row_data[0]:>8} | {row_data[1]:^12} | {row_data[2]:^12} | {row_data[3]:^12}")
    
    # 總結
    print(f"\n{'='*70}")
    print(f"驗證總結")
    print(f"{'='*70}")
    print(f"驗證時段：15:00-17:00 ({end_block - start_block} 個時段)")
    print(f"計算一致性：{'✅ 全部正確' if all_match else '❌ 發現不一致'}")
    
    return all_match

if __name__ == "__main__":
    result = verify_3pm_to_5pm()
    
    if result:
        print("\n🎉 驗證通過！15:00-17:00 時段計算正確。")
    else:
        print("\n⚠️ 驗證失敗！發現計算不一致。")
