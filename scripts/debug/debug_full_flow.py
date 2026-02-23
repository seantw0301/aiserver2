#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試腳本：模擬完整的預約查詢流程
"""

from modules.appointment_analysis import analyze_appointment
from modules.appointment_query import query_appointment_availability
from modules.appointment_result import format_appointment_result

def test_appointment_flow():
    """測試完整的預約查詢流程"""
    
    # 用戶輸入的訊息（模擬來自LINE的訊息）
    user_message = "想預約 川、獻 18:00 / 2人同行 / 西門町，請問是否方便，謝謝"
    line_key = "U123456789"  # 測試 LINE ID
    
    print("=" * 80)
    print(f"測試訊息: {user_message}")
    print("=" * 80)
    
    # 步驟1: 分析訊息
    print("\n【步驟1】分析訊息")
    print("-" * 80)
    analysis_result = analyze_appointment(line_key, user_message)
    
    print(f"分析結果:")
    print(f"  - isReservation: {analysis_result.get('query_data', {}).get('isReservation')}")
    print(f"  - branch: {analysis_result.get('query_data', {}).get('branch')}")
    print(f"  - masseur: {analysis_result.get('query_data', {}).get('masseur')}")
    print(f"  - date: {analysis_result.get('query_data', {}).get('date')}")
    print(f"  - time: {analysis_result.get('query_data', {}).get('time')}")
    print(f"  - project: {analysis_result.get('query_data', {}).get('project')}")
    print(f"  - count: {analysis_result.get('query_data', {}).get('count')}")
    
    # 步驟2: 查詢可用性
    print("\n【步驟2】查詢可用性")
    print("-" * 80)
    availability_result = query_appointment_availability(line_key, analysis_result['query_data'])
    
    if availability_result.get('should_query'):
        print(f"查詢結果:")
        print(f"  - success: {availability_result.get('success')}")
        print(f"  - can_book: {availability_result.get('can_book')}")
        
        masseur_avail = availability_result.get('masseur_availability', {})
        print(f"\n  - available_masseurs: {masseur_avail.get('available_masseurs')}")
        print(f"  - alternative_masseurs: {masseur_avail.get('alternative_masseurs', [])}")
    else:
        print(f"跳過查詢: {availability_result.get('reason')}")
    
    # 步驟3: 格式化結果
    print("\n【步驟3】格式化結果")
    print("-" * 80)
    result = format_appointment_result(analysis_result, availability_result)
    
    print(f"最終結果:")
    if result.get('response_message'):
        print(f"  - 回應訊息:\n{result['response_message']}")
    print(f"  - can_book: {result.get('can_book')}")
    
    # 檢查可約師傅是否正確
    if availability_result.get('should_query') and availability_result.get('success'):
        print("\n【檢查】可約師傅是否正確")
        print("-" * 80)
        masseur_avail = availability_result.get('masseur_availability', {})
        available = masseur_avail.get('available_masseurs', [])
        
        if available:
            print(f"可約師傅列表: {available}")
            print(f"數據類型: {type(available[0]) if available else 'N/A'}")
            
            # 檢查是否有錯誤的店家名在列表中
            import re
            for masseur in available:
                masseur_name = masseur['name'] if isinstance(masseur, dict) else masseur
                if masseur_name in ['Ximen', 'Yanji', '西門', '延吉']:
                    print(f"❌ 錯誤: 發現店家名在師傅列表中: {masseur_name}")
                else:
                    print(f"✅ 正確: {masseur_name}")
        else:
            print("無可約師傅")


if __name__ == '__main__':
    test_appointment_flow()
