#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試「川」在 21:50 的 freeblocks 狀態
"""

from modules.workday_manager import WorkdayManager

workday_mgr = WorkdayManager()
date_str = '2025-12-05'

all_work_status = workday_mgr.get_all_work_day_status(date_str)

if '川' in all_work_status:
    chuan_freeblocks = all_work_status['川']['freeblocks']
    
    print('檢查「川」的 freeblocks 數據:')
    print('='*80)
    
    start_block = 262  # 21:50
    duration = 90
    buffer = 15
    total_blocks = (duration + buffer) // 5
    end_block = start_block + total_blocks
    
    print(f'查詢: 21:50 開始 {duration}分鐘 + {buffer}分緩衝')
    print(f'  開始 block: {start_block} (21:50)')
    print(f'  需要 blocks: {total_blocks}')
    print(f'  結束 block: {end_block} (23:15, 不含)')
    print()
    
    print(f'{"Block":>5} | {"時間":>8} | {"freeblocks":>11} | 說明')
    print('-'*60)
    
    all_free = True
    for i in range(start_block, min(end_block, len(chuan_freeblocks))):
        h = (i * 5) // 60
        m = (i * 5) % 60
        free_value = chuan_freeblocks[i]
        is_free = free_value > 0
        status = f'{free_value:>3} ({"可用" if is_free else "不可用"})'
        
        if i == 262:
            desc = '21:50 開始'
        elif i == 264:
            desc = '22:00 (工作2開始)'
        else:
            desc = ''
        
        print(f'{i:5d} | {h:02d}:{m:02d} | {status} | {desc}')
        
        if not is_free:
            all_free = False
    
    print()
    print('結論:')
    if all_free:
        print('✓ 所有區塊都可用')
    else:
        print('✗ 有區塊不可用，不應該建議 21:50')
else:
    print('找不到「川」的數據')
