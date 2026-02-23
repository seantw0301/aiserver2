"""
詳細驗證 get_all_work_day_status 函數的計算邏輯
針對特定師傅進行逐時段驗證
"""

from modules.workday_manager import WorkdayManager
from core.staffs import StaffManager
from core.sch import ScheduleManager
from core.tasks import TaskManager
import json

def verify_calculation_logic():
    """詳細驗證計算邏輯"""
    
    test_date = "2025-12-04"
    print(f"=== 詳細驗證計算邏輯 - {test_date} ===\n")
    
    # 初始化管理器
    staff_manager = StaffManager()
    sch_manager = ScheduleManager()
    task_manager = TaskManager()
    workday_manager = WorkdayManager()
    
    # 獲取原始數據
    all_staffs = staff_manager.get_all_staffs()
    sch_data = sch_manager.get_schedule_block_by_date_24H(test_date)
    tasks_data = task_manager.get_tasks_block_by_date_24H(test_date)
    work_data = workday_manager.get_all_work_day_status(test_date)
    
    # 選擇一個有排班的師傅進行詳細驗證
    test_staff_name = "鞋"
    
    print(f"驗證師傅：{test_staff_name}")
    print("=" * 70)
    
    # 獲取該師傅的數據
    sch_blocks = sch_data['staffs'].get(test_staff_name, {}).get('schedule', [])
    task_blocks = tasks_data['staffs'].get(test_staff_name, {}).get('tasks', [])
    work_blocks = work_data['data'].get(test_staff_name, {}).get('freeblocks', [])
    
    print(f"\n原始數據：")
    print(f"  排班時段數：{len(sch_blocks)}")
    print(f"  工作時段數：{len(task_blocks)}")
    print(f"  可用時段數：{len(work_blocks)}")
    
    # 統計
    sch_true = sum(1 for x in sch_blocks if x)
    task_true = sum(1 for x in task_blocks if x)
    work_true = sum(1 for x in work_blocks if x)
    
    print(f"\n統計結果：")
    print(f"  有排班的時段：{sch_true}/{len(sch_blocks)} ({sch_true/len(sch_blocks)*100:.1f}%)")
    print(f"  有工作的時段：{task_true}/{len(task_blocks)} ({task_true/len(task_blocks)*100:.1f}%)")
    print(f"  可用的時段：{work_true}/{len(work_blocks)} ({work_true/len(work_blocks)*100:.1f}%)")
    
    # 手動計算驗證
    print(f"\n邏輯驗證 (可用 = 有排班 AND 無工作)：")
    manual_free = 0
    mismatches = []
    
    for i in range(len(sch_blocks)):
        expected_free = sch_blocks[i] and not task_blocks[i]
        actual_free = work_blocks[i]
        
        if expected_free:
            manual_free += 1
        
        if expected_free != actual_free:
            mismatches.append({
                'index': i,
                'time': f"{i//12:02d}:{(i%12)*5:02d}",
                'schedule': sch_blocks[i],
                'task': task_blocks[i],
                'expected': expected_free,
                'actual': actual_free
            })
    
    print(f"  手動計算可用時段：{manual_free}")
    print(f"  函數返回可用時段：{work_true}")
    
    if manual_free == work_true:
        print(f"  ✅ 計算正確！")
    else:
        print(f"  ❌ 計算不一致！差異：{abs(manual_free - work_true)}")
    
    if mismatches:
        print(f"\n⚠️ 發現 {len(mismatches)} 個不匹配的時段：")
        for m in mismatches[:5]:  # 只顯示前5個
            print(f"  時段 {m['index']} ({m['time']}): "
                  f"排班={m['schedule']}, 工作={m['task']}, "
                  f"預期={m['expected']}, 實際={m['actual']}")
    else:
        print(f"\n✅ 所有時段計算一致")
    
    # 顯示部分時段的詳細資訊
    print(f"\n部分時段詳細資訊 (時段 100-120，約 08:00-10:00)：")
    print(f"{'時段':>4} {'時間':>8} {'排班':>4} {'工作':>4} {'可用':>4}")
    print("-" * 35)
    for i in range(100, min(120, len(sch_blocks))):
        time_str = f"{i//12:02d}:{(i%12)*5:02d}"
        print(f"{i:4d} {time_str:>8} {str(sch_blocks[i]):>4} {str(task_blocks[i]):>4} {str(work_blocks[i]):>4}")
    
    # 驗證所有師傅
    print(f"\n\n=== 驗證所有師傅 ===")
    print(f"{'師傅':^6} {'排班':>6} {'工作':>6} {'可用':>6} {'狀態':^8}")
    print("-" * 40)
    
    for staff_name in work_data['data'].keys():
        sch = sch_data['staffs'].get(staff_name, {}).get('schedule', [])
        task = tasks_data['staffs'].get(staff_name, {}).get('tasks', [])
        work = work_data['data'].get(staff_name, {}).get('freeblocks', [])
        
        sch_count = sum(1 for x in sch if x)
        task_count = sum(1 for x in task if x)
        work_count = sum(1 for x in work if x)
        
        # 手動計算
        expected_count = sum(1 for i in range(len(sch)) if sch[i] and not task[i])
        
        status = "✅" if expected_count == work_count else "❌"
        print(f"{staff_name:^6} {sch_count:6d} {task_count:6d} {work_count:6d} {status:^8}")

if __name__ == "__main__":
    verify_calculation_logic()
