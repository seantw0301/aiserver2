#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試腳本：直接測試查詢可用性
"""

from modules.appointment_query import query_appointment_availability

def test_query_availability():
    """直接測試查詢可用性"""
    
    query_data = {
        'branch': '西門',
        'masseur': ['川', '獻'],
        'date': '2025-12-29',
        'time': '18:00',
        'project': 90,
        'count': 2,
        'isReservation': True,
        'used_default_branch': False,
        'used_default_project': False
    }
    
    line_key = "U123456789"
    
    print("=" * 80)
    print("測試查詢可用性")
    print("=" * 80)
    print(f"查詢參數:")
    for key, value in query_data.items():
        print(f"  - {key}: {value}")
    
    result = query_appointment_availability(line_key, query_data)
    
    print("\n" + "=" * 80)
    print("查詢結果")
    print("=" * 80)
    
    if result.get('should_query'):
        print(f"success: {result.get('success')}")
        print(f"can_book: {result.get('can_book')}")
        
        masseur_avail = result.get('masseur_availability', {})
        if masseur_avail:
            available = masseur_avail.get('available_masseurs', [])
            print(f"\n可約師傅: {available}")
            print(f"  - 類型: {type(available)}")
            if available:
                print(f"  - 第一個元素類型: {type(available[0])}")
                print(f"  - 第一個元素值: {available[0]}")
                
                # 檢查是否有錯誤的店家名
                for i, masseur in enumerate(available):
                    name = masseur['name'] if isinstance(masseur, dict) else masseur
                    print(f"    [{i}] {name} (type: {type(masseur)})")
                    if name in ['Ximen', 'Yanji', 'Ximen2']:
                        print(f"        ❌ 錯誤: 這是店家英文名!")
    else:
        print(f"跳過查詢: {result.get('reason')}")


if __name__ == '__main__':
    test_query_availability()
