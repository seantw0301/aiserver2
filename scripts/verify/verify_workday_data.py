"""
驗證資料庫中的數據
檢查 Staffs, Sch, Tasks 表的實際內容
"""

from modules.workday_manager import WorkdayManager
from core.staffs import StaffManager
from core.sch import ScheduleManager
from core.tasks import TaskManager
from datetime import datetime
import json

def verify_database_data():
    """驗證資料庫數據"""
    
    test_date = "2025-12-04"
    print(f"=== 驗證日期：{test_date} 的資料庫數據 ===\n")
    
    # 初始化管理器
    staff_manager = StaffManager()
    sch_manager = ScheduleManager()
    task_manager = TaskManager()
    
    print("1. 檢查師傅資料 (Staffs)")
    print("-" * 50)
    try:
        all_staffs = staff_manager.get_all_staffs()
        print(f"✅ 師傅總數：{len(all_staffs)}")
        for staff in all_staffs[:5]:  # 只顯示前5個
            print(f"   - {staff.get('name')} (ID: {staff.get('id')})")
        if len(all_staffs) > 5:
            print(f"   ... 還有 {len(all_staffs) - 5} 位師傅")
    except Exception as e:
        print(f"❌ 獲取師傅資料錯誤：{e}")
    
    print(f"\n2. 檢查排班資料 (Schedule) - {test_date}")
    print("-" * 50)
    try:
        sch_data = sch_manager.get_schedule_block_by_date_24H(test_date)
        print(f"✅ 排班數據獲取成功")
        print(f"   更新時間：{sch_data.get('update_time')}")
        staffs_sch = sch_data.get('staffs', {})
        print(f"   有排班的師傅數：{len(staffs_sch)}")
        
        # 顯示前3個師傅的排班情況
        for i, (staff_name, staff_data) in enumerate(list(staffs_sch.items())[:3]):
            schedule = staff_data.get('schedule', [])
            true_count = sum(1 for block in schedule if block)
            print(f"   - {staff_name}: {true_count}/{len(schedule)} 個時段有排班")
            print(f"     前10個時段: {schedule[:10]}")
            
    except Exception as e:
        print(f"❌ 獲取排班資料錯誤：{e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n3. 檢查工作資料 (Tasks) - {test_date}")
    print("-" * 50)
    try:
        tasks_data = task_manager.get_tasks_block_by_date_24H(test_date)
        print(f"✅ 工作數據獲取成功")
        print(f"   更新時間：{tasks_data.get('update_time')}")
        staffs_tasks = tasks_data.get('staffs', {})
        print(f"   有工作的師傅數：{len(staffs_tasks)}")
        
        # 顯示前3個師傅的工作情況
        for i, (staff_name, staff_data) in enumerate(list(staffs_tasks.items())[:3]):
            tasks = staff_data.get('tasks', [])
            true_count = sum(1 for block in tasks if block)
            print(f"   - {staff_name}: {true_count}/{len(tasks)} 個時段有工作")
            print(f"     前10個時段: {tasks[:10]}")
            
    except Exception as e:
        print(f"❌ 獲取工作資料錯誤：{e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n4. 分析為何沒有可用時段")
    print("-" * 50)
    try:
        # 找一個有排班的師傅來詳細分析
        if staffs_sch:
            staff_name = list(staffs_sch.keys())[0]
            sch_blocks = staffs_sch[staff_name].get('schedule', [])
            task_blocks = staffs_tasks.get(staff_name, {}).get('tasks', [])
            
            print(f"分析師傅：{staff_name}")
            print(f"排班時段數：{len(sch_blocks)}")
            print(f"工作時段數：{len(task_blocks)}")
            
            if len(sch_blocks) != len(task_blocks):
                print(f"⚠️ 警告：排班和工作的時段數不一致！")
            
            # 計算可用時段
            free_blocks = []
            for i, (sch, task) in enumerate(zip(sch_blocks, task_blocks)):
                is_free = sch and not task
                free_blocks.append(is_free)
                if i < 10:  # 顯示前10個時段的詳細分析
                    print(f"   時段 {i}: 排班={sch}, 工作={task}, 可用={is_free}")
            
            free_count = sum(1 for block in free_blocks if block)
            print(f"\n結論：可用時段數 = {free_count}/{len(free_blocks)}")
            
    except Exception as e:
        print(f"❌ 分析錯誤：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_database_data()
