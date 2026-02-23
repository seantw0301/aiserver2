#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試腳本：比較 query_appointment_availability 和 query_appointment_availability_202512 的回傳訊息差別
"""

import json
from datetime import datetime, timedelta
from modules.appointment_query import query_appointment_availability, query_appointment_availability_202512

def print_separator(title=""):
    """打印分隔線"""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    else:
        print(f"{'='*80}\n")

def print_result(result, title=""):
    """格式化打印查詢結果"""
    if title:
        print(f"\n{title}:")
        print("-" * 60)
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("-" * 60)

def compare_results(result1, result2, test_name):
    """比較兩個結果的差異"""
    print(f"\n📊 【{test_name}】差異分析:")
    print("-" * 60)
    
    # 比較基本欄位
    fields_to_compare = [
        'should_query', 'success', 'can_book', 'is_schedule_query', 
        'is_expired', 'error', 'query_type'
    ]
    
    differences = []
    
    for field in fields_to_compare:
        val1 = result1.get(field, '(未設置)')
        val2 = result2.get(field, '(未設置)')
        
        if val1 != val2:
            differences.append(f"  • {field}: 舊版={val1}, 新版={val2}")
    
    # 比較可用師傅
    if 'masseur_availability' in result1 or 'masseur_availability' in result2:
        avail1 = result1.get('masseur_availability', {})
        avail2 = result2.get('masseur_availability', {})
        
        available1 = avail1.get('available_masseurs', [])
        available2 = avail2.get('available_masseurs', [])
        
        if available1 != available2:
            differences.append(f"  • 可用師傅: 舊版={available1}, 新版={available2}")
    
    # 比較回傳的 key
    keys1 = set(result1.keys())
    keys2 = set(result2.keys())
    
    only_in_old = keys1 - keys2
    only_in_new = keys2 - keys1
    
    if only_in_old:
        differences.append(f"  • 僅在舊版出現的 key: {list(only_in_old)}")
    
    if only_in_new:
        differences.append(f"  • 僅在新版出現的 key: {list(only_in_new)}")
    
    if differences:
        print("⚠️  發現差異:")
        for diff in differences:
            print(diff)
    else:
        print("✅ 兩個版本回傳結果相同")
    
    print("-" * 60)

def run_test(test_name, query_data):
    """執行單個測試案例"""
    print_separator(f"測試案例: {test_name}")
    
    print("📝 測試資料:")
    print(json.dumps(query_data, ensure_ascii=False, indent=2))
    
    # 執行舊版查詢
    print("\n🔵 執行舊版 query_appointment_availability...")
    result_old = query_appointment_availability("test_user_001", query_data.copy())
    print_result(result_old, "舊版回傳結果")
    
    # 執行新版查詢
    print("\n🟢 執行新版 query_appointment_availability_202512...")
    result_new = query_appointment_availability_202512("test_user_001", query_data.copy())
    print_result(result_new, "新版回傳結果")
    
    # 比較結果
    compare_results(result_old, result_new, test_name)

def main():
    """主測試函數"""
    print_separator("預約查詢函數比較測試")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"測試目的: 比較 query_appointment_availability 和 query_appointment_availability_202512 的回傳差異")
    
    # 準備測試時間（未來時間）
    future_time = datetime.now() + timedelta(hours=2)
    future_date = future_time.strftime('%Y-%m-%d')
    future_time_str = future_time.strftime('%H:%M')
    
    # 測試案例 1: 正常預約查詢（指定師傅）
    test_case_1 = {
        'branch': '西門',
        'masseur': ['彬'],
        'date': future_date,
        'time': future_time_str,
        'project': 90,
        'count': 1,
        'isReservation': True
    }
    run_test("正常預約查詢（指定師傅）", test_case_1)
    
    # 測試案例 2: 正常預約查詢（不指定師傅）
    test_case_2 = {
        'branch': '西門',
        'masseur': [],
        'date': future_date,
        'time': future_time_str,
        'project': 60,
        'count': 1,
        'isReservation': True
    }
    run_test("正常預約查詢（不指定師傅）", test_case_2)
    
    # 測試案例 3: 班表查詢（有日期無時間）
    test_case_3 = {
        'branch': '西門',
        'masseur': [],
        'date': future_date,
        'time': '',
        'project': 90,
        'count': 1,
        'isReservation': True
    }
    run_test("班表查詢（有日期無時間）", test_case_3)
    
    # 測試案例 4: 過期時間查詢
    past_time = datetime.now() - timedelta(hours=1)
    past_date = past_time.strftime('%Y-%m-%d')
    past_time_str = past_time.strftime('%H:%M')
    
    test_case_4 = {
        'branch': '延吉',
        'masseur': [],
        'date': past_date,
        'time': past_time_str,
        'project': 90,
        'count': 1,
        'isReservation': True
    }
    run_test("過期時間查詢", test_case_4)
    
    # 測試案例 5: 非預約訊息
    test_case_5 = {
        'branch': '西門',
        'masseur': [],
        'date': future_date,
        'time': future_time_str,
        'project': 90,
        'count': 1,
        'isReservation': False
    }
    run_test("非預約訊息", test_case_5)
    
    # 測試案例 6: 查詢條件不足（缺少時間）
    test_case_6 = {
        'branch': '家樂福',
        'masseur': ['小黑'],
        'date': future_date,
        'time': '',
        'project': 120,
        'count': 2,
        'isReservation': True
    }
    run_test("查詢條件不足（視為班表查詢）", test_case_6)
    
    # 測試案例 7: 多位師傅預約
    test_case_7 = {
        'branch': '西門',
        'masseur': ['彬', '阿育'],
        'date': future_date,
        'time': future_time_str,
        'project': 90,
        'count': 2,
        'isReservation': True
    }
    run_test("多位師傅預約", test_case_7)
    
    print_separator("測試完成")
    print("\n📌 總結:")
    print("  • 已完成 7 個測試案例")
    print("  • 請查看上方各測試的差異分析")
    print("  • 重點關注 success, can_book, masseur_availability 等欄位的差異")

if __name__ == "__main__":
    main()
