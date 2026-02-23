"""
測試 WorkdayManager.get_all_work_day_status 函數
檢測 2025-12-4 的結果
"""

from modules.workday_manager import WorkdayManager
from datetime import datetime
import json

def test_get_all_work_day_status():
    """測試獲取 2025-12-4 的工作日狀態"""
    
    # 初始化 WorkdayManager
    manager = WorkdayManager()
    
    # 測試日期：2025-12-4
    test_date = "2025-12-04"
    
    print(f"=== 測試日期：{test_date} ===\n")
    
    try:
        # 調用函數
        result = manager.get_all_work_day_status(test_date)
        
        if result is None:
            print("❌ 函數返回 None，可能發生錯誤")
            return
        
        # 顯示結果
        print(f"✅ 成功獲取工作日狀態")
        print(f"\n更新時間：{result.get('update_time')}")
        print(f"\n師傅數量：{len(result.get('data', {}))}")
        
        # 顯示每個師傅的詳細資訊
        data = result.get('data', {})
        if data:
            print("\n=== 師傅工作狀態詳情 ===\n")
            for staff_name, staff_info in data.items():
                freeblocks = staff_info.get('freeblocks', [])
                total_blocks = len(freeblocks)
                free_count = sum(1 for block in freeblocks if block)
                
                print(f"師傅：{staff_name}")
                print(f"  - 總時段數：{total_blocks}")
                print(f"  - 可用時段數：{free_count}")
                print(f"  - 可用率：{free_count/total_blocks*100:.1f}%")
                
                # 顯示前 10 個時段作為範例
                print(f"  - 前10個時段狀態：{freeblocks[:10]}")
                print()
        else:
            print("\n⚠️ 沒有任何師傅有可用時段")
        
        # 保存完整結果到 JSON 文件
        output_file = f"workday_status_{test_date}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n💾 完整結果已保存到：{output_file}")
        
    except Exception as e:
        print(f"❌ 測試過程發生錯誤：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_get_all_work_day_status()
