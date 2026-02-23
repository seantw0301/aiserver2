"""
調試蒙在 2025-12-07 的詳細工作日狀態
檢查排班情況、工作情況、以及最終 freeblock 情況
"""

from modules.workday_manager import WorkdayManager
from core.sch import ScheduleManager
from core.tasks import TaskManager
from datetime import datetime
import json

def debug_meng_workday_status():
    """詳細分析蒙在 2025-12-07 的工作日狀態"""
    
    check_date = "2025-12-07"
    staff_name = "蒙"
    
    print(f"=" * 80)
    print(f"調試 {staff_name} 在 {check_date} 的工作日狀態")
    print(f"=" * 80)
    
    # 初始化管理器
    workday_manager = WorkdayManager()
    sch_manager = ScheduleManager()
    task_manager = TaskManager()
    
    # 1. 獲取排班情況 (schedule)
    print(f"\n【步驟 1】獲取排班情況 (sch_data)")
    print("-" * 80)
    sch_data = sch_manager.get_schedule_block_by_date_24H(check_date)
    
    if staff_name in sch_data['staffs']:
        meng_schedule = sch_data['staffs'][staff_name]['schedule']
        print(f"✓ {staff_name} 排班數據已找到")
        print(f"  總 blocks: {len(meng_schedule)}")
        print(f"  有排班的 blocks (True): {sum(meng_schedule)}")
        print(f"  沒排班的 blocks (False): {len(meng_schedule) - sum(meng_schedule)}")
        
        # 找出排班的時間段
        print(f"\n  排班時間段:")
        in_shift = False
        shift_start = None
        for i, is_scheduled in enumerate(meng_schedule):
            if is_scheduled and not in_shift:
                shift_start = i
                in_shift = True
            elif not is_scheduled and in_shift:
                hours = shift_start // 12
                minutes = (shift_start % 12) * 5
                end_hours = i // 12
                end_minutes = (i % 12) * 5
                print(f"    {hours:02d}:{minutes:02d} - {end_hours:02d}:{end_minutes:02d} (blocks {shift_start}-{i-1})")
                in_shift = False
        
        # 處理最後一段
        if in_shift:
            hours = shift_start // 12
            minutes = (shift_start % 12) * 5
            end_hours = len(meng_schedule) // 12
            end_minutes = (len(meng_schedule) % 12) * 5
            print(f"    {hours:02d}:{minutes:02d} - {end_hours:02d}:{end_minutes:02d} (blocks {shift_start}-{len(meng_schedule)-1})")
    else:
        print(f"✗ {staff_name} 未找到排班數據")
        meng_schedule = None
    
    # 2. 獲取工作情況 (tasks)
    print(f"\n【步驟 2】獲取工作情況 (tasks_data)")
    print("-" * 80)
    tasks_data = task_manager.get_tasks_block_by_date_24H(check_date)
    
    if staff_name in tasks_data['staffs']:
        meng_tasks = tasks_data['staffs'][staff_name]['tasks']
        print(f"✓ {staff_name} 工作數據已找到")
        print(f"  總 blocks: {len(meng_tasks)}")
        print(f"  有工作的 blocks (True): {sum(meng_tasks)}")
        print(f"  空閒的 blocks (False): {len(meng_tasks) - sum(meng_tasks)}")
        
        # 找出工作的時間段
        print(f"\n  工作時間段:")
        in_task = False
        task_start = None
        for i, has_task in enumerate(meng_tasks):
            if has_task and not in_task:
                task_start = i
                in_task = True
            elif not has_task and in_task:
                hours = task_start // 12
                minutes = (task_start % 12) * 5
                end_hours = i // 12
                end_minutes = (i % 12) * 5
                print(f"    {hours:02d}:{minutes:02d} - {end_hours:02d}:{end_minutes:02d} (blocks {task_start}-{i-1})")
                in_task = False
        
        # 處理最後一段
        if in_task:
            hours = task_start // 12
            minutes = (task_start % 12) * 5
            end_hours = len(meng_tasks) // 12
            end_minutes = (len(meng_tasks) % 12) * 5
            print(f"    {hours:02d}:{minutes:02d} - {end_hours:02d}:{end_minutes:02d} (blocks {task_start}-{len(meng_tasks)-1})")
    else:
        print(f"✗ {staff_name} 未找到工作數據")
        meng_tasks = None
    
    # 3. 計算最終 freeblock (schedule=True AND tasks=False)
    print(f"\n【步驟 3】計算最終 freeblock")
    print("-" * 80)
    
    if meng_schedule and meng_tasks:
        freeblocks = []
        for sch_block, task_block in zip(meng_schedule, meng_tasks):
            # 只有排班 AND 沒有工作時才是 freeblock
            freeblocks.append(sch_block and not task_block)
        
        print(f"計算規則: freeblock = (schedule=True) AND (tasks=False)")
        print(f"  總 blocks: {len(freeblocks)}")
        print(f"  可用 blocks (True): {sum(freeblocks)}")
        print(f"  不可用 blocks (False): {len(freeblocks) - sum(freeblocks)}")
        print(f"  可用率: {sum(freeblocks)/len(freeblocks)*100:.1f}%")
        
        # 找出可用的時間段
        print(f"\n  可用時間段 (freeblock=True):")
        in_free = False
        free_start = None
        for i, is_free in enumerate(freeblocks):
            if is_free and not in_free:
                free_start = i
                in_free = True
            elif not is_free and in_free:
                hours = free_start // 12
                minutes = (free_start % 12) * 5
                end_hours = i // 12
                end_minutes = (i % 12) * 5
                duration = (i - free_start) * 5
                print(f"    {hours:02d}:{minutes:02d} - {end_hours:02d}:{end_minutes:02d} (blocks {free_start:3d}-{i-1:3d}, 持續 {duration:3d} 分鐘)")
                in_free = False
        
        # 處理最後一段
        if in_free:
            hours = free_start // 12
            minutes = (free_start % 12) * 5
            end_hours = len(freeblocks) // 12
            end_minutes = (len(freeblocks) % 12) * 5
            duration = (len(freeblocks) - free_start) * 5
            print(f"    {hours:02d}:{minutes:02d} - {end_hours:02d}:{end_minutes:02d} (blocks {free_start:3d}-{len(freeblocks)-1:3d}, 持續 {duration:3d} 分鐘)")
        
        # 4. 檢查 20:00 開始的 21 個 blocks (90分鐘+15分鐘緩衝)
        print(f"\n【步驟 4】檢查 20:00 開始的預約需求 (90分鐘 + 15分鐘緩衝 = 21 blocks)")
        print("-" * 80)
        
        start_time = "20:00"
        start_hour, start_minute = map(int, start_time.split(':'))
        start_block = start_hour * 12 + start_minute // 5
        required_blocks = 21  # 90分鐘 + 15分鐘緩衝 = 105分鐘 = 21 blocks
        end_block = start_block + required_blocks
        
        print(f"開始時間: {start_time}")
        print(f"開始 block: {start_block} ({start_hour:02d}:{start_minute:02d})")
        print(f"需要 blocks: {required_blocks} (105分鐘)")
        print(f"結束 block: {end_block} ({(end_block//12):02d}:{(end_block%12)*5:02d})")
        print(f"\n逐 block 檢查 (blocks {start_block}-{end_block-1}):")
        print(f"{'Block':>5} | {'時間':^11} | {'排班':^4} | {'工作':^4} | {'可用':^4} | 狀態")
        print("-" * 60)
        
        all_available = True
        for i in range(start_block, end_block):
            if i < len(freeblocks):
                hours = i // 12
                minutes = (i % 12) * 5
                sch = meng_schedule[i]
                task = meng_tasks[i]
                free = freeblocks[i]
                status = "✓" if free else "✗"
                if not free:
                    all_available = False
                    reason = ""
                    if not sch:
                        reason = "(無排班)"
                    elif task:
                        reason = "(有工作)"
                    print(f"{i:5d} | {hours:02d}:{minutes:02d} - {hours:02d}:{(minutes+5)%60:02d} | {sch!s:^4} | {task!s:^4} | {free!s:^4} | {status} {reason}")
                else:
                    print(f"{i:5d} | {hours:02d}:{minutes:02d} - {hours:02d}:{(minutes+5)%60:02d} | {sch!s:^4} | {task!s:^4} | {free!s:^4} | {status}")
        
        print(f"\n結論:")
        if all_available:
            print(f"✓ {staff_name} 在 {start_time} 可接受 90分鐘預約")
        else:
            print(f"✗ {staff_name} 在 {start_time} 無法接受 90分鐘預約")
            print(f"  原因: 需要連續 {required_blocks} 個可用 blocks，但其中有部分不可用")
    
    # 5. 從 WorkdayManager 獲取最終結果並比對
    print(f"\n【步驟 5】從 WorkdayManager 獲取最終結果")
    print("-" * 80)
    
    work_day_status = workday_manager.get_all_work_day_status(check_date)
    
    if staff_name in work_day_status:
        manager_freeblocks = work_day_status[staff_name]['freeblocks']
        print(f"✓ WorkdayManager 返回的 {staff_name} freeblock 數據:")
        print(f"  總 blocks: {len(manager_freeblocks)}")
        print(f"  可用 blocks: {sum(manager_freeblocks)}")
        print(f"  可用率: {sum(manager_freeblocks)/len(manager_freeblocks)*100:.1f}%")
        
        # 比對本地計算和 Manager 返回的結果
        if meng_schedule and meng_tasks:
            if freeblocks == manager_freeblocks:
                print(f"\n✓ 驗證通過: 本地計算結果與 WorkdayManager 一致")
            else:
                print(f"\n✗ 驗證失敗: 本地計算結果與 WorkdayManager 不一致")
                # 找出差異
                diff_count = sum(1 for i in range(len(freeblocks)) if freeblocks[i] != manager_freeblocks[i])
                print(f"  差異 blocks 數量: {diff_count}")
    else:
        print(f"✗ WorkdayManager 未返回 {staff_name} 的數據")
        print(f"  可能原因: 該員工當天所有 blocks 都不可用")
    
    print(f"\n" + "=" * 80)

if __name__ == "__main__":
    debug_meng_workday_status()
