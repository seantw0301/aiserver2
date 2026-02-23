#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 query_appointment_availability 和 query_appointment_availability_202512 的差異
"""

import json
from datetime import datetime, timedelta
from modules.appointment_query import query_appointment_availability, query_appointment_availability_202512

def print_separator(title):
    """打印分隔線"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def print_result(title, result):
    """打印查詢結果"""
    print(f"\n{'-'*40}")
    print(f"{title}")
    print(f"{'-'*40}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"{'-'*40}\n")

def compare_results(test_name, old_result, new_result):
    """比較兩個結果的差異"""
    print(f"\n📊 {test_name} - 結果比較")
    print("=" * 80)
    
    # 比較基本屬性
    keys_to_compare = ['should_query', 'success', 'can_book', 'is_expired', 'is_schedule_query']
    
    print("\n基本屬性比較:")
    print("-" * 80)
    for key in keys_to_compare:
        old_val = old_result.get(key, '(無此欄位)')
        new_val = new_result.get(key, '(無此欄位)')
        match = '✓' if old_val == new_val else '✗'
        print(f"  {match} {key}:")
        print(f"      舊版本: {old_val}")
        print(f"      新版本: {new_val}")
    
    # 比較 masseur_availability
    if 'masseur_availability' in old_result or 'masseur_availability' in new_result:
        print("\n\n師傅可用性比較:")
        print("-" * 80)
        old_ma = old_result.get('masseur_availability', {})
        new_ma = new_result.get('masseur_availability', {})
        
        ma_keys = ['available_masseurs', 'unavailable_masseurs', 'alternative_masseurs', 
                   'sufficient_masseurs', 'message', 'guest_count']
        
        for key in ma_keys:
            old_val = old_ma.get(key, '(無此欄位)')
            new_val = new_ma.get(key, '(無此欄位)')
            match = '✓' if old_val == new_val else '✗'
            print(f"  {match} {key}:")
            print(f"      舊版本: {old_val}")
            print(f"      新版本: {new_val}")
    
    # 比較 room_availability
    if 'room_availability' in old_result or 'room_availability' in new_result:
        print("\n\n房間可用性比較:")
        print("-" * 80)
        old_ra = old_result.get('room_availability', {})
        new_ra = new_result.get('room_availability', {})
        
        ra_keys = ['available_rooms', 'sufficient_rooms', 'message', 'required_rooms']
        
        for key in ra_keys:
            old_val = old_ra.get(key, '(無此欄位)')
            new_val = new_ra.get(key, '(無此欄位)')
            match = '✓' if old_val == new_val else '✗'
            print(f"  {match} {key}:")
            print(f"      舊版本: {old_val}")
            print(f"      新版本: {new_val}")
    
    print("\n" + "=" * 80 + "\n")

def test_case_1():
    """測試案例 1: 基本預約查詢 - 明天下午3點，西門店，彬師傅"""
    print_separator("測試案例 1: 基本預約查詢")
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    query_data = {
        'branch': '西門',
        'masseur': ['彬'],
        'date': tomorrow,
        'time': '15:00',
        'project': 90,
        'count': 1,
        'isReservation': True
    }
    
    print(f"查詢條件: {json.dumps(query_data, ensure_ascii=False, indent=2)}")
    
    # 舊版本
    old_result = query_appointment_availability('test_user_001', query_data)
    print_result("舊版本結果 (query_appointment_availability)", old_result)
    
    # 新版本
    new_result = query_appointment_availability_202512('test_user_001', query_data)
    print_result("新版本結果 (query_appointment_availability_202512)", new_result)
    
    # 比較差異
    compare_results("測試案例 1", old_result, new_result)

def test_case_2():
    """測試案例 2: 多人預約 - 後天晚上8點，延吉店，2人"""
    print_separator("測試案例 2: 多人預約")
    
    day_after_tomorrow = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
    
    query_data = {
        'branch': '延吉',
        'masseur': [],  # 不指定師傅
        'date': day_after_tomorrow,
        'time': '20:00',
        'project': 90,
        'count': 2,
        'isReservation': True
    }
    
    print(f"查詢條件: {json.dumps(query_data, ensure_ascii=False, indent=2)}")
    
    # 舊版本
    old_result = query_appointment_availability('test_user_002', query_data)
    print_result("舊版本結果", old_result)
    
    # 新版本
    new_result = query_appointment_availability_202512('test_user_002', query_data)
    print_result("新版本結果", new_result)
    
    # 比較差異
    compare_results("測試案例 2", old_result, new_result)

def test_case_3():
    """測試案例 3: 班表查詢 - 明天的班表"""
    print_separator("測試案例 3: 班表查詢")
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    query_data = {
        'branch': '西門',
        'masseur': [],
        'date': tomorrow,
        'time': '',  # 沒有時間表示班表查詢
        'project': 90,
        'count': 1,
        'isReservation': True
    }
    
    print(f"查詢條件: {json.dumps(query_data, ensure_ascii=False, indent=2)}")
    
    # 舊版本
    old_result = query_appointment_availability('test_user_003', query_data)
    print_result("舊版本結果", old_result)
    
    # 新版本
    new_result = query_appointment_availability_202512('test_user_003', query_data)
    print_result("新版本結果", new_result)
    
    # 比較差異
    compare_results("測試案例 3", old_result, new_result)

def test_case_4():
    """測試案例 4: 過期時間查詢 - 昨天的時間"""
    print_separator("測試案例 4: 過期時間查詢")
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    query_data = {
        'branch': '西門',
        'masseur': ['彬'],
        'date': yesterday,
        'time': '15:00',
        'project': 90,
        'count': 1,
        'isReservation': True
    }
    
    print(f"查詢條件: {json.dumps(query_data, ensure_ascii=False, indent=2)}")
    
    # 舊版本
    old_result = query_appointment_availability('test_user_004', query_data)
    print_result("舊版本結果", old_result)
    
    # 新版本
    new_result = query_appointment_availability_202512('test_user_004', query_data)
    print_result("新版本結果", new_result)
    
    # 比較差異
    compare_results("測試案例 4", old_result, new_result)

def test_case_5():
    """測試案例 5: 指定多位師傅"""
    print_separator("測試案例 5: 指定多位師傅")
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    query_data = {
        'branch': '西門',
        'masseur': ['彬', '阿豪'],
        'date': tomorrow,
        'time': '18:00',
        'project': 60,
        'count': 2,
        'isReservation': True
    }
    
    print(f"查詢條件: {json.dumps(query_data, ensure_ascii=False, indent=2)}")
    
    # 舊版本
    old_result = query_appointment_availability('test_user_005', query_data)
    print_result("舊版本結果", old_result)
    
    # 新版本
    new_result = query_appointment_availability_202512('test_user_005', query_data)
    print_result("新版本結果", new_result)
    
    # 比較差異
    compare_results("測試案例 5", old_result, new_result)

def main():
    """執行所有測試案例"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 15 + "query_appointment_availability 版本比較測試" + " " * 19 + "║")
    print("╚" + "═" * 78 + "╝")
    
    try:
        # 執行各個測試案例
        test_case_1()
        test_case_2()
        test_case_3()
        test_case_4()
        test_case_5()
        
        print_separator("所有測試完成")
        print("✅ 測試執行完畢，請查看上方比較結果")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
