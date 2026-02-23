"""
驗證 WorkdayManager.get_all_room_status 函數的正確性
隨機測試過去三天的數據，對比資料庫實際數據
"""

from datetime import datetime, timedelta
import json
import random
import sys
import os

# 添加項目根目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_room_status_for_date(test_date):
    """驗證指定日期的房間狀態"""
    
    # 延遲導入以避免循環導入
    from modules.workday_manager import WorkdayManager
    from core.store import StoreManager
    
    print(f"\n{'='*70}")
    print(f"驗證日期：{test_date}")
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
    
    # room_status 直接就是 data 字典
    print(f"✅ 房間狀態獲取成功")
    print(f"   店家數量：{len(room_status)}")
    
    # 步驟 3: 手動計算並驗證
    print(f"\n步驟 3: 手動計算並驗證正確性")
    print("-" * 70)
    
    # 獲取佔用狀態
    store_occupied_status = store_manager.get_store_occupied_block_by_date_24H(test_date)
    
    all_match = True
    
    print(f"{'店家':^10} {'房間數':>6} {'平均可用':>8} {'平均佔用':>8} {'驗證':^6}")
    print("-" * 70)
    
    for store in all_stores:
        store_id = store['id']
        store_name = store['name']
        max_rooms = int(store['rooms'])
        
        # 統一使用字符串鍵訪問字典
        store_id_str = str(store_id)
        function_data = room_status.get(store_id_str, {})
        function_blocks = function_data.get('free_blocks', [])
        
        # 手動計算 - 也使用字符串鍵
        occupied_blocks = store_occupied_status['data'].get(store_id_str, {}).get('blocks', [0] * 294)
        manual_blocks = [max(max_rooms - occ, 0) for occ in occupied_blocks]
        
        # 比較
        if function_blocks == manual_blocks:
            match = "✅"
        else:
            match = "❌"
            all_match = False
        
        # 計算平均值
        avg_free = sum(function_blocks) / len(function_blocks) if function_blocks else 0
        avg_occupied = sum(occupied_blocks) / len(occupied_blocks) if occupied_blocks else 0
        
        print(f"{store_name:^10} {max_rooms:6d} {avg_free:8.2f} {avg_occupied:8.2f} {match:^6}")
    
    # 步驟 4: 詳細檢查所有店家在下午三點時段 (15:00)
    print(f"\n步驟 4: 詳細檢查所有店家在下午三點時段 (15:00)")
    print("-" * 70)
    
    # 下午三點對應的時段：15:00 = 15*12 = 180
    # 顯示 15:00 前後各 6 個時段 (14:30-15:30)
    start_block = 174  # 14:30
    end_block = 187    # 15:35
    
    print(f"\n時段範圍：14:30 - 15:35 (圍繞下午三點)")
    print(f"{'店家':^10} {'時段':>4} {'時間':>8} {'最大':>4} {'佔用':>4} {'計算可用':>8} {'函數可用':>8} {'驗證':^6}")
    print("-" * 75)
    
    total_mismatch = 0
    
    for store in all_stores:
        store_id = store['id']
        store_name = store['name']
        max_rooms = int(store['rooms'])
        
        store_id_str = str(store_id)
        function_blocks = room_status.get(store_id_str, {}).get('free_blocks', [])
        occupied_blocks = store_occupied_status['data'].get(store_id_str, {}).get('blocks', [0] * 294)
        
        for i in range(start_block, min(end_block, len(function_blocks))):
            time_str = f"{i//12:02d}:{(i%12)*5:02d}"
            occupied = occupied_blocks[i] if i < len(occupied_blocks) else 0
            manual_free = max(max_rooms - occupied, 0)
            function_free = function_blocks[i]
            
            match = "✅" if manual_free == function_free else "❌"
            if manual_free != function_free:
                total_mismatch += 1
            
            # 標記 15:00 時段
            marker = "★" if i == 180 else " "
            
            print(f"{store_name:^10} {i:4d} {time_str:>8}{marker} {max_rooms:4d} {occupied:4d} {manual_free:8d} {function_free:8d} {match:^6}")
    
    if total_mismatch > 0:
        print(f"\n⚠️ 發現 {total_mismatch} 個時段不匹配")
    else:
        print(f"\n✅ 所有時段計算完全一致")
    
    # 步驟 5: 分析下午三點時段的使用情況
    print(f"\n步驟 5: 下午三點時段 (15:00) 使用情況分析")
    print("-" * 70)
    
    block_1500 = 180  # 15:00 對應的 block index
    
    print(f"\n{'店家':^10} {'最大房間':>8} {'佔用數':>6} {'可用數':>6} {'佔用率':>8} {'狀態':^10}")
    print("-" * 70)
    
    for store in all_stores:
        store_id = store['id']
        store_name = store['name']
        max_rooms = int(store['rooms'])
        
        store_id_str = str(store_id)
        function_blocks = room_status.get(store_id_str, {}).get('free_blocks', [])
        occupied_blocks = store_occupied_status['data'].get(store_id_str, {}).get('blocks', [0] * 294)
        
        if block_1500 < len(function_blocks):
            available = function_blocks[block_1500]
            occupied = occupied_blocks[block_1500] if block_1500 < len(occupied_blocks) else 0
            occupancy_rate = (occupied / max_rooms * 100) if max_rooms > 0 else 0
            
            # 判斷狀態
            if available == 0:
                status = "客滿"
            elif available == max_rooms:
                status = "空閒"
            elif occupancy_rate >= 75:
                status = "繁忙"
            elif occupancy_rate >= 50:
                status = "適中"
            else:
                status = "輕鬆"
            
            print(f"{store_name:^10} {max_rooms:8d} {occupied:6d} {available:6d} {occupancy_rate:7.1f}% {status:^10}")
    
    # 比較三天的數據
    print(f"\n註：★ 標記為 15:00 時段")
    
    # 總結
    print(f"\n{'='*70}")
    print(f"驗證總結")
    print(f"{'='*70}")
    print(f"驗證店家數：{len(all_stores)}")
    print(f"計算一致性：{'✅ 全部正確' if all_match else '❌ 發現不一致'}")
    
    # 保存結果
    output_file = f"room_status_{test_date}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(room_status, f, ensure_ascii=False, indent=2)
    print(f"完整結果已保存：{output_file}")
    
    return all_match

def main():
    """主函數：測試過去三天的數據"""
    
    print("="*70)
    print("驗證 get_all_room_status 函數 - 過去三天隨機測試")
    print("="*70)
    
    # 生成過去三天的日期
    today = datetime.now().date()
    past_dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 4)]
    
    # 隨機選擇測試順序
    random.shuffle(past_dates)
    
    print(f"\n測試日期：{', '.join(past_dates)}")
    
    results = {}
    for test_date in past_dates:
        result = verify_room_status_for_date(test_date)
        results[test_date] = result
    
    # 最終總結
    print(f"\n\n{'='*70}")
    print("最終總結")
    print(f"{'='*70}")
    
    all_passed = all(results.values())
    
    for test_date, passed in results.items():
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"{test_date}: {status}")
    
    if all_passed:
        print(f"\n🎉 所有測試通過！get_all_room_status 函數運作完全正確。")
    else:
        print(f"\n⚠️ 部分測試失敗，請檢查函數邏輯。")
    
    return all_passed

if __name__ == "__main__":
    main()
