#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調查「川」在 2025-12-05 20:35 的查詢結果為何建議 21:50
"""

from modules.workday_manager import WorkdayManager
from core.tasks import TaskManager
from core.sch import ScheduleManager
from core.database import DatabaseConfig

print('='*80)
print('調查「川」在 2025-12-05 的狀況')
print('='*80)

# 初始化
workday_mgr = WorkdayManager()
task_mgr = TaskManager()
sch_mgr = ScheduleManager()
db_config = DatabaseConfig()

date_str = '2025-12-05'
staff_name = '川'

# 1. 查詢資料庫中「川」的工作安排
print(f'\n【步驟 1】查詢「{staff_name}」在 {date_str} 的工作安排')
print('-'*80)

conn = db_config.get_connection()
cursor = conn.cursor(dictionary=True)

query = """
SELECT start, end, mins 
FROM Tasks 
WHERE staff_name = %s AND DATE(start) = %s
ORDER BY start
"""
cursor.execute(query, (staff_name, date_str))
tasks = cursor.fetchall()

if tasks:
    for task in tasks:
        print(f"  {task['start']} - {task['end']} ({task['mins']}分鐘)")
else:
    print(f"  無工作安排")

# 2. 獲取 workday_manager 計算的 freeblocks
print(f'\n【步驟 2】獲取 workday_manager 計算的 freeblocks')
print('-'*80)

all_work_status = workday_mgr.get_all_work_day_status(date_str)

if staff_name in all_work_status:
    freeblocks = all_work_status[staff_name]['freeblocks']
    print(f"✓ 找到 {staff_name} 的 freeblocks 數據 (共 {len(freeblocks)} blocks)")
    
    # 3. 檢查關鍵時間點
    print(f'\n【步驟 3】檢查關鍵時間點的 freeblocks 狀態')
    print('-'*80)
    print(f'{"Block":>5} | {"時間":>8} | {"freeblocks":>11} | 說明')
    print('-'*60)
    
    # 檢查 21:00-23:00
    for i in range(252, 276):
        h = (i * 5) // 60
        m = (i * 5) % 60
        value = freeblocks[i]
        status = f'{value} ({"可用" if value else "不可用"})'
        
        desc = ''
        if i == 261:
            desc = '21:45'
        elif i == 262:
            desc = '21:50 (建議時間?)'
        elif i == 263:
            desc = '21:55'
        elif i == 264:
            desc = '22:00'
        
        if desc or (i >= 261 and i <= 270):
            print(f'{i:5d} | {h:02d}:{m:02d} | {status:>11} | {desc}')
    
    # 4. 模擬查找邏輯
    print(f'\n【步驟 4】模擬 query_available_appointment_202512 的查找邏輯')
    print('-'*80)
    
    available_index = 247  # 20:35
    iTotalBlocks = (90 + 15) // 5  # 21 blocks
    
    print(f'原始查詢: block {available_index} (20:35), 需要 {iTotalBlocks} blocks')
    print()
    
    iStaffTesIndex = available_index + 3  # 從 20:50 開始
    found_time = None
    iteration = 0
    
    while iStaffTesIndex < 282:
        iteration += 1
        start_time = f'{(iStaffTesIndex*5)//60:02d}:{(iStaffTesIndex*5)%60:02d}'
        
        # 檢查邊界
        if iStaffTesIndex + iTotalBlocks > len(freeblocks):
            print(f'第 {iteration} 次: block {iStaffTesIndex} ({start_time}) - 超出範圍')
            break
        
        # 檢查連續可用性
        blocks_to_check = freeblocks[iStaffTesIndex:iStaffTesIndex+iTotalBlocks]
        is_all_available = all(block for block in blocks_to_check)
        
        true_count = sum(1 for b in blocks_to_check if b)
        false_count = len(blocks_to_check) - true_count
        
        if iteration <= 10 or is_all_available:  # 只顯示前10次或找到的那次
            print(f'第 {iteration:2d} 次: block {iStaffTesIndex} ({start_time}) - True: {true_count:2d}, False: {false_count:2d} -> {"✓ 找到!" if is_all_available else "✗"}')
        
        if is_all_available:
            found_time = start_time
            print(f'\n✓ 找到可用時間: {found_time} (block {iStaffTesIndex})')
            
            # 顯示這個時間段的詳細情況
            print(f'\n詳細檢查 {found_time} 開始的 {iTotalBlocks} blocks:')
            print(f'{"Block":>5} | {"時間":>8} | {"狀態":>6}')
            print('-'*30)
            for j in range(iStaffTesIndex, iStaffTesIndex + iTotalBlocks):
                h = (j * 5) // 60
                m = (j * 5) % 60
                status = '可用' if freeblocks[j] else '不可用'
                print(f'{j:5d} | {h:02d}:{m:02d} | {status:>6}')
            
            break
        
        iStaffTesIndex += 3
    
    if not found_time:
        print(f'\n✗ 未找到可用時間')
else:
    print(f"✗ 未找到 {staff_name} 的數據")

cursor.close()
conn.close()

print()
print('='*80)
