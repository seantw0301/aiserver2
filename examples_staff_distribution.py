#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
師傅店家分佈系統使用範例
展示如何在實際場景中使用新增的功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.appointment_query import (
    _get_staff_store_distribution,
    _get_storeid_from_branch,
    query_appointment_availability
)
from datetime import datetime, timedelta


def example_1_basic_usage():
    """範例 1: 基本使用 - 查詢今天西門店的師傅分佈"""
    print("=" * 60)
    print("範例 1: 查詢今天西門店的師傅分佈")
    print("=" * 60)
    
    today = datetime.now().strftime("%Y-%m-%d")
    storeid = _get_storeid_from_branch("西門")
    
    distribution = _get_staff_store_distribution(today, storeid)
    
    print(f"\n今天 ({today}) 西門店的師傅分佈：")
    for staff_name, stores in distribution.items():
        if storeid in stores:
            print(f"  ✓ {staff_name} 今天在西門店服務")


def example_2_check_specific_staff():
    """範例 2: 檢查特定師傅今天在哪個店"""
    print("\n" + "=" * 60)
    print("範例 2: 檢查特定師傅今天在哪個店")
    print("=" * 60)
    
    today = datetime.now().strftime("%Y-%m-%d")
    target_staff = "彬"
    
    # 查詢所有分店
    for branch_name, branch_id in [("西門", 1), ("延吉", 2), ("家樂福", 3)]:
        distribution = _get_staff_store_distribution(today, branch_id)
        
        if target_staff in distribution:
            staff_stores = distribution[target_staff]
            if branch_id in staff_stores:
                print(f"  ✓ {target_staff} 今天在 {branch_name} 服務")
            break


def example_3_tomorrow_booking():
    """範例 3: 查詢明天可預約的師傅"""
    print("\n" + "=" * 60)
    print("範例 3: 查詢明天延吉店的師傅分佈")
    print("=" * 60)
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    storeid = _get_storeid_from_branch("延吉")
    
    distribution = _get_staff_store_distribution(tomorrow, storeid)
    
    available_staff = [
        staff for staff, stores in distribution.items() 
        if storeid in stores
    ]
    
    print(f"\n明天 ({tomorrow}) 延吉店可能服務的師傅：")
    for staff in available_staff:
        print(f"  - {staff}")
    
    print(f"\n共 {len(available_staff)} 位師傅")


def example_4_different_date_formats():
    """範例 4: 使用不同日期格式"""
    print("\n" + "=" * 60)
    print("範例 4: 支援不同的日期格式")
    print("=" * 60)
    
    date_formats = [
        "2025-11-28",
        "2025/11/28",
        datetime(2025, 11, 28).strftime("%Y-%m-%d")
    ]
    
    for date_str in date_formats:
        distribution = _get_staff_store_distribution(date_str, 1)
        print(f"  ✓ 日期格式 '{date_str}' 查詢成功，共 {len(distribution)} 位師傅")


def example_5_integration_with_query():
    """範例 5: 整合到預約查詢中"""
    print("\n" + "=" * 60)
    print("範例 5: 整合到預約查詢流程")
    print("=" * 60)
    
    # 模擬用戶查詢
    query_data = {
        'branch': '西門',
        'masseur': ['彬', '川'],
        'date': '2025/11/28',
        'time': '18:00',
        'project': 90,
        'count': 2,
        'isReservation': True
    }
    
    print("\n用戶查詢條件：")
    print(f"  - 分店: {query_data['branch']}")
    print(f"  - 查詢師傅: {query_data['masseur']}")
    print(f"  - 日期: {query_data['date']}")
    print(f"  - 時間: {query_data['time']}")
    
    # 檢查師傅是否在該分店
    storeid = _get_storeid_from_branch(query_data['branch'])
    distribution = _get_staff_store_distribution(query_data['date'], storeid)
    
    print("\n師傅店家分佈檢查：")
    for staff in query_data['masseur']:
        if staff in distribution:
            staff_stores = distribution[staff]
            if storeid in staff_stores:
                print(f"  ✓ {staff} 當天在{query_data['branch']}服務")
            else:
                store_names = {1: "西門", 2: "延吉", 3: "家樂福"}
                actual_stores = [store_names.get(s, str(s)) for s in staff_stores]
                print(f"  ⚠️ {staff} 當天在 {', '.join(actual_stores)} 服務")
        else:
            print(f"  ⚠️ 找不到 {staff} 的資訊")


def example_6_weekly_schedule():
    """範例 6: 查詢一週的師傅排班"""
    print("\n" + "=" * 60)
    print("範例 6: 查詢師傅一週的排班分佈")
    print("=" * 60)
    
    target_staff = "川"
    today = datetime.now()
    
    print(f"\n{target_staff} 本週排班：")
    print("-" * 40)
    
    store_names = {1: "西門", 2: "延吉", 3: "家樂福"}
    
    for i in range(7):
        date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
        weekday = (today + timedelta(days=i)).strftime("%A")
        
        # 查詢所有分店找出師傅的位置
        found = False
        for storeid in [1, 2, 3]:
            distribution = _get_staff_store_distribution(date, storeid)
            if target_staff in distribution:
                staff_stores = distribution[target_staff]
                store_list = [store_names[s] for s in staff_stores if s in store_names]
                print(f"  {date} ({weekday[:3]}): {', '.join(store_list)}")
                found = True
                break
        
        if not found:
            print(f"  {date} ({weekday[:3]}): 休假或無資料")


def main():
    """執行所有範例"""
    print("\n" + "=" * 60)
    print("師傅店家分佈系統 - 使用範例")
    print("=" * 60)
    
    examples = [
        example_1_basic_usage,
        example_2_check_specific_staff,
        example_3_tomorrow_booking,
        example_4_different_date_formats,
        example_5_integration_with_query,
        example_6_weekly_schedule
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n⚠️ 範例執行錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("所有範例執行完畢")
    print("=" * 60)


if __name__ == "__main__":
    main()
