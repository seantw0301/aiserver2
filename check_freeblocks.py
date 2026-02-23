#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查 workday_manager 生成的 freeblocks 數據是否正確
"""

import redis

# 清除緩存
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
redis_client.delete('work_data_2025-12-05')
print('✓ Redis 緩存已清除\n')

from modules.workday_manager import WorkdayManager

workday_mgr = WorkdayManager()
all_work_status = workday_mgr.get_all_work_day_status('2025-12-05')

print('='*80)
print('檢查「川」的 freeblocks 數據是否正確')
print('='*80)

if '川' in all_work_status:
    freeblocks = all_work_status['川']['freeblocks']
    
    print(f'\nfreeblocks 總數: {len(freeblocks)} blocks')
    print()
    print('檢查關鍵時間點 (21:30-23:00):')
    print(f'{"Block":>5} | {"時間":>8} | {"freeblocks":>10} | 說明')
    print('-'*60)
    
    for i in range(258, 276):
        h = (i * 5) // 60
        m = (i * 5) % 60
        value = freeblocks[i]
        status = f'{value} ({"可用" if value else "不可用"})'
        
        desc = ''
        if i == 258:
            desc = '21:30 (工作1實際結束)'
        elif i == 260:
            desc = '21:40 (工作1緩衝中)'
        elif i == 261:
            desc = '21:45 (工作1緩衝結束)'
        elif i == 262:
            desc = '21:50 (建議時間)'
        elif i == 264:
            desc = '22:00 (工作2開始!)'
        elif i == 287:
            desc = '23:55 (當天最後)'
        
        print(f'{i:5d} | {h:02d}:{m:02d} | {status:>10} | {desc}')
    
    print()
    print('='*80)
    print('分析：')
    print('  工作1: 19:30-21:30 + 15分緩衝 = 19:30-21:45')
    print('    → blocks 234-260 應該是 False (不可用)')
    print('  工作2: 22:00-00:00 + 15分緩衝 = 22:00-00:15 (跨日)')
    print('    → blocks 264-287 應該是 False (不可用)')
    print('  空檔: 21:45-22:00')
    print('    → blocks 261-263 應該是 True (可用)')
    print()
    
    # 驗證數據
    errors = []
    
    # 檢查 21:30-21:45 (工作1緩衝)
    for i in range(258, 261):
        if freeblocks[i]:
            errors.append(f'block {i} ({(i*5)//60:02d}:{(i*5)%60:02d}) 應該不可用但是可用')
    
    # 檢查 21:45-22:00 (空檔)
    for i in range(261, 264):
        if not freeblocks[i]:
            errors.append(f'block {i} ({(i*5)//60:02d}:{(i*5)%60:02d}) 應該可用但是不可用')
    
    # 檢查 22:00-23:55 (工作2)
    for i in range(264, 288):
        if freeblocks[i]:
            errors.append(f'block {i} ({(i*5)//60:02d}:{(i*5)%60:02d}) 應該不可用但是可用')
    
    if errors:
        print('✗ 發現錯誤的 freeblocks 數據:')
        for error in errors[:10]:  # 只顯示前10個
            print(f'  - {error}')
        if len(errors) > 10:
            print(f'  ... 還有 {len(errors)-10} 個錯誤')
    else:
        print('✓ freeblocks 數據正確！')
    
    print()
    print('='*80)
    print('檢查 21:50 開始 90分鐘+15分緩衝的連續性:')
    start_block = 262
    total_blocks = 21
    
    print(f'  需要檢查: blocks {start_block}-{start_block+total_blocks-1}')
    print(f'  即: 21:50-23:15')
    
    all_available = all(freeblocks[i] for i in range(start_block, start_block + total_blocks))
    unavailable_blocks = [i for i in range(start_block, start_block + total_blocks) if not freeblocks[i]]
    
    print(f'  全部可用? {all_available}')
    if unavailable_blocks:
        print(f'  不可用的 blocks ({len(unavailable_blocks)}個): {unavailable_blocks[:5]}...')
    
    print()
    if all_available:
        print('✗ 錯誤：21:50 被判斷為可用，但實際上 22:00 有工作！')
    else:
        print('✓ 正確：21:50 不可用，因為連續性不足')
    print('='*80)
else:
    print('✗ 未找到「川」的數據')
