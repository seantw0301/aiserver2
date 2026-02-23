import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# 導入新的三階段模塊
from modules.appointment_analysis import analyze_appointment
#from modules.appointment_query import query_appointment_availability
from modules.appointment_query import query_appointment_availability_202512
from modules.appointment_result import format_appointment_result


def process_appointment(line_key: str, message: str, user_info: Optional[Dict]) -> Dict[str, Any]:
    """
    處理預約邏輯，分三個階段執行：
    
    階段1 - 分析 (appointment_analysis.py)：
        1-0. 由 Redis 上取回前面對話生成的預約資料
        1-1. 日期分析（時）
        1-2. 時間分析（時）
        1-3. 員工分析（人）
        1-4. 是否預約（事）
        1-5. 分店分析（地）
        1-6. 療程分析（物）
        1-7. 生成 JSON
        1-8. 原始資料寫回 Redis，修正後資料（加入預設值）送至後續查詢
    
    階段2 - 查詢 (appointment_query.py)：
        查詢可用性（師傅、房間）
        （只有當 isReservation=true 時才執行）
    
    階段3 - 生成結果 (appointment_result.py)：
        格式化回應訊息
        （只有當 isReservation=true 時才執行）
    
    Args:
        line_key: LINE user ID
        message: User's message text
        user_info: User information from greeting module (including visitdate)
        
    Returns:
        Dict containing:
        - isReservation: bool - 是否為預約相關訊息
        - 若為預約，返回查詢和結果資料
        - 若非預約，返回簡單結果（keyword 判讀由 parse.py 層級處理）
    """
    print(f"\n{'='*60}")
    print(f"DEBUG [Appointment]: 開始處理預約")
    print(f"DEBUG [Appointment]: line_key={line_key}")
    print(f"DEBUG [Appointment]: message={message}")
    print(f"{'='*60}\n")
    
    # ==================== 階段1：分析 ====================
    print(f"DEBUG [Appointment]: ========== 階段1：分析 ==========")
    analysis_result = analyze_appointment(line_key, message, user_info)
    
    # 取得原始資料和查詢資料
    raw_data = analysis_result.get('raw_data', {})
    query_data = analysis_result.get('query_data', {})
    is_reservation = query_data.get('isReservation', False)
    
    print(f"DEBUG [Appointment]: 分析結果：")
    print(f"  - 是否為預約: {is_reservation}")
    print(f"  - 是否有更新: {analysis_result.get('has_update', False)}")
    
    # 如果不是預約，直接返回非預約結果
    # keyword 判讀由 parse.py 層級的 keyword.py 模塊處理
    if not is_reservation:
        print(f"DEBUG [Appointment]: 非預約訊息，返回非預約結果")
        print(f"DEBUG [Appointment]: 結束處理\n")
        
        return {
            'isReservation': False
        }
    
    # ==================== 階段2：查詢 ====================
    print(f"\nDEBUG [Appointment]: ========== 階段2：查詢 ==========")
    #檢查資料是否完整
    #若分店為空白或None，則設置為西門
    if not query_data.get('branch'):
        query_data['branch'] = '西門'
    #若師傅為空白或None,則設置為[]
    if not query_data.get('masseur'):
        query_data['masseur'] = []
    #若日期為空白或None,則設置為本日
    if not query_data.get('date'):
        query_data['date'] = datetime.now().strftime('%Y-%m-%d')
    #若時間為空白或None,則設置為當下時間+30分鐘
    #if not query_data.get('time'):
    #    query_data['time'] = (datetime.now() + timedelta(minutes=30)).strftime('%H:%M')
    #若療程為空白或None,則設置為90
    if not query_data.get('project'):
        query_data['project'] = 90
    #若人數為空白或None,則設置為1
    if not query_data.get('count'):
        query_data['count'] = 1

    #原本舊版本
    #availability_result = query_appointment_availability(line_key, query_data)
    #改用新版本
    availability_result = query_appointment_availability_202512(line_key, query_data)

    print(f"DEBUG [Appointment]: 查詢結果：")
    print(f"  - 是否執行查詢: {availability_result.get('should_query', False)}")
    if availability_result.get('should_query'):
        print(f"  - 查詢成功: {availability_result.get('success', False)}")
        print(f"  - 可預約: {availability_result.get('can_book', False)}")
    
    # ==================== 階段3：生成結果 ====================
    print(f"\nDEBUG [Appointment]: ========== 階段3：生成結果 ==========")
    final_result = format_appointment_result(analysis_result, availability_result)
    
    print(f"\nDEBUG [Appointment]: 處理完成")
    print(f"{'='*60}\n")
    
    return final_result
