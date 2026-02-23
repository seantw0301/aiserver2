#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
師傅 Freeblock 檢查測試程式
用來測試 workday_manager.py 中的 get_freeblock 方法
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.workday_manager import WorkdayManager
from datetime import datetime, timedelta
import json

def format_time_from_block_index(block_index: int) -> str:
    """將 block index 轉換為時間字串 (HH:MM)"""
    # 每個 block 代表 5 分鐘
    total_minutes = block_index * 5
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"

def display_freeblock_table(freeblocks: list, start_time: str, blockcount: int):
    """顯示時間與 freeblock 值的對映表"""
    print("\n" + "="*80)
    print("🕐 時間與 Freeblock 對映表")
    print("="*80)

    # 計算開始的 block index
    start_hour, start_minute = map(int, start_time.split(':'))
    start_block_index = (start_hour * 60 + start_minute) // 5

    print(f"📅 開始時間: {start_time} (Block Index: {start_block_index})")
    print(f"📏 區塊數量: {blockcount}")
    print(f"⏱️  總時長: {blockcount * 5} 分鐘")
    print()

    # 顯示表頭
    print(f"{'Block Index':<12} {'時間':<8} {'Freeblock':<10} {'狀態'}")
    print("-" * 50)

    # 顯示每個 block 的資訊
    for i in range(blockcount):
        block_index = start_block_index + i
        time_str = format_time_from_block_index(block_index)
        freeblock_value = freeblocks[i] if i < len(freeblocks) else "N/A"

        # 判斷狀態
        if freeblock_value == True:
            status = "✅ 可用"
        elif freeblock_value == False:
            status = "❌ 不可用"
        else:
            status = "❓ 未知"

        print(f"{block_index:<12} {time_str:<8} {str(freeblock_value):<10} {status}")

    print("-" * 50)

    # 統計資訊
    if freeblocks:
        available_count = sum(1 for block in freeblocks if block == True)
        unavailable_count = sum(1 for block in freeblocks if block == False)
        total_blocks = len(freeblocks)

        print(f"\n📊 統計資訊:")
        print(f"   總區塊數: {total_blocks}")
        print(f"   可用區塊: {available_count} ({available_count/total_blocks*100:.1f}%)")
        print(f"   不可用區塊: {unavailable_count} ({unavailable_count/total_blocks*100:.1f}%)")

        # 連續可用區塊分析
        max_consecutive = 0
        current_consecutive = 0
        for block in freeblocks:
            if block == True:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        print(f"   最長連續可用: {max_consecutive} 區塊 ({max_consecutive*5} 分鐘)")

        # 判斷是否可以接受預約
        if available_count == total_blocks:
            print("   🎉 完全可用！可以接受預約")
        elif available_count >= total_blocks * 0.8:
            print("   ✅ 大部分可用，可以接受預約")
        elif available_count > 0:
            print("   ⚠️ 部分可用，需要檢查具體時間")
        else:
            print("   ❌ 完全不可用，無法接受預約")
    else:
        print("\n❌ 無 freeblock 資料")

def main():
    """主程式"""
    print("🧪 師傅 Freeblock 檢查測試程式")
    print("="*50)

    # 預設參數
    default_date = '2025-12-7'
    default_staff = '偉'
    default_time = '11:00'
    default_blocks = 36 # 36個5分鐘區塊 = 3小時

    # 讓使用者輸入參數，或使用預設值
    print("請輸入查詢參數 (按 Enter 使用預設值):")

    date_input = input(f"日期 (預設: {default_date}): ").strip()
    check_date = date_input if date_input else default_date

    staff_input = input(f"師傅名稱 (預設: {default_staff}): ").strip()
    staff_name = staff_input if staff_input else default_staff

    time_input = input(f"開始時間 (預設: {default_time}): ").strip()
    start_time = time_input if time_input else default_time

    blocks_input = input(f"區塊數量 (預設: {default_blocks}): ").strip()
    try:
        blockcount = int(blocks_input) if blocks_input else default_blocks
    except ValueError:
        print("❌ 區塊數量必須是數字，使用預設值")
        blockcount = default_blocks

    print(f"\n🔍 查詢參數:")
    print(f"   日期: {check_date}")
    print(f"   師傅: {staff_name}")
    print(f"   開始時間: {start_time}")
    print(f"   區塊數量: {blockcount} (相當於 {blockcount * 5} 分鐘)")

    # 初始化 WorkdayManager
    try:
        workday_manager = WorkdayManager()

        # 呼叫 get_freeblock 方法
        print("\n⏳ 正在查詢 freeblock 資料...")
        freeblocks = workday_manager.get_freeblock(
            check_date=check_date,
            staff_name=staff_name,
            start_time=start_time,
            blockcount=blockcount
        )

        if freeblocks is not None:
            print("✅ 成功獲取 freeblock 資料")
            display_freeblock_table(freeblocks, start_time, blockcount)
        else:
            print("❌ 無法獲取 freeblock 資料")
            print("   可能的原因:")
            print("   - 師傅名稱不存在")
            print("   - 日期格式錯誤")
            print("   - 系統錯誤")

    except Exception as e:
        print(f"❌ 程式執行錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()