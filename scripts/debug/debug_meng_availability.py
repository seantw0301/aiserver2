#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調查「蒙」師傅在 2025-12-07 20:00 不可用的原因
"""

from modules.workday_manager import WorkdayManager
from core.tasks import TaskManager

def main():
    print("="*80)
    print("調查「蒙」師傅在 2025-12-07 20:00 (90分鐘) 不可用的原因")
    print("="*80)
    
    # 初始化管理器
    workday_manager = WorkdayManager()
    task_manager = TaskManager()
    
    # 查詢參數
    date_str = "2025-12-07"
    time_str = "20:00"
    duration = 90  # 分鐘
    
    # 計算區塊索引
    start_index = task_manager.convert_time_to_block_index(time_str)
    total_blocks = (duration + 15) // 5  # 包含15分鐘緩衝
    
    print(f"\n查詢資訊:")
    print(f"  日期: {date_str}")
    print(f"  時間: {time_str}")
    print(f"  療程時長: {duration} 分鐘")
    print(f"  總共需要: {total_blocks} 個區塊 ({total_blocks * 5} 分鐘)")
    print(f"  開始區塊索引: {start_index}")
    print(f"  結束區塊索引: {start_index + total_blocks - 1}")
    
    # 取得當天所有工作狀態
    print(f"\n正在查詢當天工作狀態...")
    all_work_status = workday_manager.get_all_work_day_status(date_str)
    
    if '蒙' not in all_work_status:
        print(f"\n❌ 錯誤: 找不到「蒙」師傅的工作狀態")
        return
    
    staff_info = all_work_status['蒙']
    freeblocks = staff_info.get('freeblocks', [])
    
    print(f"\n「蒙」師傅的工作狀態:")
    print(f"  總區塊數: {len(freeblocks)}")
    
    # 檢查所需時段的每個區塊
    print(f"\n檢查所需時段的區塊 (索引 {start_index} 到 {start_index + total_blocks - 1}):")
    print("-" * 80)
    
    is_available = True
    unavailable_blocks = []
    
    for i in range(start_index, start_index + total_blocks):
        if i >= len(freeblocks):
            print(f"  ⚠️  區塊 {i}: 超出範圍")
            is_available = False
            unavailable_blocks.append(i)
        else:
            block_value = freeblocks[i]
            time_for_block = task_manager.convert_block_index_to_time(i)
            
            if block_value > 0:
                print(f"  ✓  區塊 {i} ({time_for_block}): 可用 (值={block_value})")
            else:
                print(f"  ✗  區塊 {i} ({time_for_block}): 不可用 (值={block_value})")
                is_available = False
                unavailable_blocks.append(i)
    
    print("-" * 80)
    
    # 總結
    print(f"\n總結:")
    if is_available:
        print(f"  ✅ 「蒙」師傅在 {time_str} 可用 (90分鐘)")
    else:
        print(f"  ❌ 「蒙」師傅在 {time_str} 不可用 (90分鐘)")
        print(f"  不可用的區塊數: {len(unavailable_blocks)}")
        print(f"  不可用的區塊索引: {unavailable_blocks[:10]}{'...' if len(unavailable_blocks) > 10 else ''}")
    
    # 顯示當天「蒙」師傅的整體狀況
    print(f"\n「蒙」師傅當天整體狀況:")
    available_count = sum(1 for block in freeblocks if block > 0)
    unavailable_count = sum(1 for block in freeblocks if block == 0)
    print(f"  可用區塊: {available_count}/{len(freeblocks)} ({available_count/len(freeblocks)*100:.1f}%)")
    print(f"  不可用區塊: {unavailable_count}/{len(freeblocks)} ({unavailable_count/len(freeblocks)*100:.1f}%)")
    
    # 找出連續可用的時段
    print(f"\n尋找「蒙」師傅當天可用的時段 (需要 {total_blocks} 個連續區塊):")
    found_available = False
    i = 0
    while i < len(freeblocks) - total_blocks:
        if all(freeblocks[i+j] > 0 for j in range(total_blocks)):
            available_start = task_manager.convert_block_index_to_time(i)
            available_end = task_manager.convert_block_index_to_time(i + total_blocks - 1)
            print(f"  ✓ {available_start} - {available_end}")
            found_available = True
            i += total_blocks  # 跳過這段已找到的時段
        else:
            i += 1
    
    if not found_available:
        print(f"  ❌ 當天沒有符合 {duration} 分鐘的連續可用時段")
    
    # 顯示 20:00 附近的區塊詳情 (前後各5個區塊)
    print(f"\n20:00 附近的區塊詳情 (索引 {start_index-5} 到 {start_index+total_blocks+5}):")
    print("-" * 80)
    for i in range(max(0, start_index-5), min(len(freeblocks), start_index+total_blocks+5)):
        time_for_block = task_manager.convert_block_index_to_time(i)
        block_value = freeblocks[i]
        status = "✓ 可用" if block_value > 0 else "✗ 不可用"
        marker = " <<<" if start_index <= i < start_index + total_blocks else ""
        print(f"  區塊 {i:3d} ({time_for_block}): {status:8s} (值={block_value}){marker}")
    print("-" * 80)
    
    print("\n" + "="*80)

if __name__ == '__main__':
    main()
