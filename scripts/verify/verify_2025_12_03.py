"""
驗證 2025-12-03 的工作日狀態是否與資料庫相符
"""

from modules.workday_manager import WorkdayManager
from core.staffs import StaffManager
from core.sch import ScheduleManager
from core.tasks import TaskManager
import json

def verify_date(test_date):
    """驗證指定日期的數據"""
    
    print(f"{'='*70}")
    print(f"驗證日期：{test_date}")
    print(f"{'='*70}\n")
    
    # 初始化管理器
    staff_manager = StaffManager()
    sch_manager = ScheduleManager()
    task_manager = TaskManager()
    workday_manager = WorkdayManager()
    
    # 1. 獲取原始數據
    print("步驟 1: 獲取資料庫原始數據")
    print("-" * 70)
    
    all_staffs = staff_manager.get_all_staffs()
    print(f"✅ 師傅總數：{len(all_staffs)}")
    
    sch_data = sch_manager.get_schedule_block_by_date_24H(test_date)
    sch_staffs = sch_data.get('staffs', {})
    print(f"✅ 有排班記錄的師傅數：{len(sch_staffs)}")
    
    tasks_data = task_manager.get_tasks_block_by_date_24H(test_date)
    tasks_staffs = tasks_data.get('staffs', {})
    print(f"✅ 有工作記錄的師傅數：{len(tasks_staffs)}")
    
    # 2. 使用函數計算
    print(f"\n步驟 2: 使用 get_all_work_day_status 函數計算")
    print("-" * 70)
    
    work_data = workday_manager.get_all_work_day_status(test_date)
    
    if not work_data:
        print("❌ 函數返回 None")
        return
    
    work_staffs = work_data.get('data', {})
    print(f"✅ 有可用時段的師傅數：{len(work_staffs)}")
    print(f"   更新時間：{work_data.get('update_time')}")
    
    # 3. 手動驗證計算邏輯
    print(f"\n步驟 3: 手動驗證計算邏輯")
    print("-" * 70)
    print(f"{'師傅':^6} {'排班':>6} {'工作':>6} {'計算可用':>8} {'函數可用':>8} {'驗證':^6}")
    print("-" * 70)
    
    all_match = True
    total_verified = 0
    
    # 遍歷所有有排班的師傅
    for staff_name in sch_staffs.keys():
        sch_blocks = sch_staffs.get(staff_name, {}).get('schedule', [])
        task_blocks = tasks_staffs.get(staff_name, {}).get('tasks', [])
        
        # 手動計算可用時段
        manual_free = sum(1 for i in range(len(sch_blocks)) if sch_blocks[i] and not task_blocks[i])
        
        # 從函數結果獲取
        if staff_name in work_staffs:
            function_free = sum(1 for x in work_staffs[staff_name].get('freeblocks', []) if x)
            match = "✅" if manual_free == function_free else "❌"
            if manual_free != function_free:
                all_match = False
        else:
            # 師傅不在結果中，檢查是否正確（應該是沒有可用時段）
            function_free = 0
            match = "✅" if manual_free == 0 else "❌"
            if manual_free != 0:
                all_match = False
        
        sch_count = sum(1 for x in sch_blocks if x)
        task_count = sum(1 for x in task_blocks if x)
        
        print(f"{staff_name:^6} {sch_count:6d} {task_count:6d} {manual_free:8d} {function_free:8d} {match:^6}")
        total_verified += 1
    
    # 4. 詳細檢查幾個師傅
    print(f"\n步驟 4: 詳細檢查部分師傅的時段")
    print("-" * 70)
    
    # 選擇前3個有可用時段的師傅
    sample_staffs = list(work_staffs.keys())[:3] if work_staffs else []
    
    for staff_name in sample_staffs:
        print(f"\n師傅：{staff_name}")
        
        sch_blocks = sch_staffs.get(staff_name, {}).get('schedule', [])
        task_blocks = tasks_staffs.get(staff_name, {}).get('tasks', [])
        work_blocks = work_staffs.get(staff_name, {}).get('freeblocks', [])
        
        print(f"  總時段數：{len(sch_blocks)}")
        
        # 找出可用時段的時間範圍
        free_ranges = []
        start_idx = None
        
        for i in range(len(work_blocks)):
            if work_blocks[i]:
                if start_idx is None:
                    start_idx = i
            else:
                if start_idx is not None:
                    free_ranges.append((start_idx, i-1))
                    start_idx = None
        
        if start_idx is not None:
            free_ranges.append((start_idx, len(work_blocks)-1))
        
        print(f"  可用時段數：{sum(1 for x in work_blocks if x)}")
        print(f"  可用時段範圍：")
        
        for start, end in free_ranges[:5]:  # 只顯示前5個範圍
            start_time = f"{start//12:02d}:{(start%12)*5:02d}"
            end_time = f"{end//12:02d}:{(end%12)*5:02d}"
            print(f"    {start_time} - {end_time} (共 {end-start+1} 個時段)")
        
        if len(free_ranges) > 5:
            print(f"    ... 還有 {len(free_ranges)-5} 個時段範圍")
    
    # 5. 總結
    print(f"\n{'='*70}")
    print(f"驗證總結")
    print(f"{'='*70}")
    print(f"驗證師傅數：{total_verified}")
    print(f"計算一致性：{'✅ 全部正確' if all_match else '❌ 發現不一致'}")
    
    # 保存結果
    output_file = f"workday_status_{test_date}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(work_data, f, ensure_ascii=False, indent=2)
    print(f"完整結果已保存：{output_file}")
    
    return all_match

if __name__ == "__main__":
    # 驗證 2025-12-03
    result = verify_date("2025-12-03")
    
    if result:
        print("\n🎉 驗證通過！函數計算結果與資料庫完全相符。")
    else:
        print("\n⚠️ 驗證失敗！發現計算不一致的情況。")
