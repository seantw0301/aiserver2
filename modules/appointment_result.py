#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
預約結果生成模塊 - 階段3
負責根據查詢結果生成格式化的回應訊息
使用原始邏輯，不自創新函數
"""

from typing import Dict, Any, Optional


def _format_time_hm(time_str: str) -> str:
    """
    將時間字符串格式化為 HH:MM 格式
    支持 HH:MM:SS -> HH:MM 的轉換
    
    Args:
        time_str: 時間字符串（如 "18:00:00" 或 "18:00"）
        
    Returns:
        HH:MM 格式的時間字符串，如果無效則返回原值
    """
    if not time_str or not isinstance(time_str, str):
        return time_str
    
    # 如果已經是 HH:MM 格式（5 個字符），直接返回
    if len(time_str) == 5 and time_str[2] == ':':
        return time_str
    
    # 如果是 HH:MM:SS 格式，取前 5 個字符
    if len(time_str) >= 8 and time_str[2] == ':':
        return time_str[:5]
    
    # 其他情況，返回原值
    return time_str


def format_appointment_result(
    analysis_result: Dict[str, Any],
    availability_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    整合分析結果和查詢結果，生成完整的預約處理結果
    （基於原始 appointment.py 的邏輯）
    
    Args:
        analysis_result: 分析模塊的結果
        availability_result: 查詢模塊的結果（可選）
        
    Returns:
        完整的預約處理結果
    """
    print("DEBUG [Result]: format_appointment_result 開始執行")
    print(f"DEBUG [Result]: availability_result = {availability_result is not None}")
    if availability_result:
        print(f"DEBUG [Result]: should_query = {availability_result.get('should_query', False)}")
        print(f"DEBUG [Result]: is_schedule_query = {availability_result.get('is_schedule_query', False)}")
        print(f"DEBUG [Result]: success = {availability_result.get('success', False)}")
    
    # 取得查詢資料（已套用預設值）
    query_data = analysis_result.get('query_data', {})
    
    # 基礎結果（從 query_data 複製）
    result = query_data.copy()
    
    # 如果有查詢結果，添加到返回資料中並生成回應訊息
    if availability_result and availability_result.get('should_query', False):
        # 將查詢結果添加到返回數據中
        result['availability'] = availability_result
        
        # 檢查是否為班表查詢
        if availability_result.get('is_schedule_query', False):
            # 處理班表查詢結果
            if availability_result.get('success'):
                # 檢查是否有預格式化的用戶訊息
                user_message = availability_result.get('user_message')
                if user_message:
                    result['response_message'] = user_message
                    result['can_book'] = True
                    result['is_schedule_query'] = True
                    print("DEBUG [Result]: 使用預格式化的班表訊息")
                    return result
                
                # 如果沒有預格式化訊息，使用原有邏輯
                schedule_result = availability_result.get('schedule_result', {})
                staff_shifts = schedule_result.get('staff_shifts', [])
                query_date = schedule_result.get('date', query_data.get('date', ''))
                
                # 獲取師傅店家分佈資訊
                from modules.appointment_query import get_staff_store_distribution
                store_distribution = get_staff_store_distribution(query_date)
                
                # 店家 ID 到名稱的映射
                store_id_to_name = {
                    1: "西門",
                    2: "延吉", 
                    3: "家樂福"
                }
                
                # 檢查是否有指定師傅，如果有則只顯示該師傅的班表
                specified_masseurs = query_data.get('masseur', [])
                if specified_masseurs:
                    # 過濾出指定的師傅（staff_shifts 現在是字符串列表，如 "蒙:(12:30-22:30)"）
                    filtered_shifts = []
                    for shift_str in staff_shifts:
                        if ':' in shift_str:
                            masseur_name = shift_str.split(':')[0]
                            if masseur_name in specified_masseurs:
                                filtered_shifts.append(shift_str)
                    staff_shifts = filtered_shifts
                
                if staff_shifts:
                    response_parts = []
                    response_parts.append(f"📅 {query_date} 班表\n")
                    
                    for shift in staff_shifts:
                        # 解析字符串格式 "師傅名稱:(時間區間)"
                        if ':' in shift:
                            staff_name, shift_times = shift.split(':', 1)
                        else:
                            staff_name = shift
                            shift_times = ""
                        
                        if staff_name and shift_times:
                            # 獲取師傅的店家分佈
                            store_info = ""
                            if staff_name in store_distribution:
                                store_ids = store_distribution[staff_name]
                                store_names = [store_id_to_name.get(sid, f"店{sid}") for sid in store_ids]
                                if len(store_names) == 1:
                                    store_info = f" - {store_names[0]}"
                                else:
                                    store_info = f" - ({', '.join(store_names)})"
                            
                            response_parts.append(f"【{staff_name}】{shift_times}{store_info}\n")
                    
                    result['response_message'] = '\n'.join(response_parts)
                    result['can_book'] = True  # 班表查詢成功
                    result['is_schedule_query'] = True
                    
                    print("DEBUG [Result]: 班表查詢結果生成完成")
                    print(f"  - 查詢日期: {query_date}")
                    print(f"  - 師傅數量: {len(staff_shifts)}")
                    if specified_masseurs:
                        print(f"  - 查詢師傅: {specified_masseurs}")
                else:
                    if specified_masseurs:
                        result['response_message'] = f"📅 {query_date}\n\n查無 {', '.join(specified_masseurs)} 的班表資料"
                    else:
                        result['response_message'] = f"📅 {query_date}\n\n查無班表資料"
                    result['can_book'] = False
                    result['is_schedule_query'] = True
                    
                    print("DEBUG [Result]: 班表查詢無資料")
            else:
                # 班表查詢失敗
                error_msg = availability_result.get('error', '未知錯誤')
                result['response_message'] = f"❌ 班表查詢失敗：{error_msg}"
                result['can_book'] = False
                result['is_schedule_query'] = True
                
                print(f"DEBUG [Result]: 班表查詢失敗 - {error_msg}")
            
            return result
        
        # 根據查詢結果生成回應訊息（使用原始邏輯）
        if availability_result.get('success'):
            print("DEBUG [Result]: 進入成功分支，開始生成回應訊息")
            # 構建回應訊息
            response_parts = []
            
            # 查詢結果
            query_data_from_avail = availability_result.get('query_data', {})
            can_book = availability_result.get('can_book', False)
            print(f"DEBUG [Result]: can_book = {can_book}")
            
            if can_book:
                print("DEBUG [Result]: can_book=True，生成可約訊息")
                # 可約師傅（原始邏輯）
                masseur_avail = availability_result.get('masseur_availability', {})
                available = masseur_avail.get('available_masseurs', [])
                unavailable = masseur_avail.get('unavailable_masseurs', [])
                alternative = masseur_avail.get('alternative_masseurs', [])
                
                response_parts.append("\n✅ 可預約")
                
                # 顯示查詢條件
                response_parts.append("\n📋 查詢條件：")
                branch = query_data.get('branch', '')
                if query_data.get('used_default_branch'):
                    branch += " (預設)"
                response_parts.append(f"店家：{branch}")
                
                date = query_data.get('date', '')
                time = query_data.get('time', '')
                time = _format_time_hm(time)  # 格式化時間為 HH:MM
                response_parts.append(f"日期時間：{date} {time}")
                
                project = query_data.get('project', 0)
                if query_data.get('used_default_project'):
                    response_parts.append(f"療程：{project} 分鐘 (預設)")
                else:
                    response_parts.append(f"療程：{project} 分鐘")
                
                count = query_data.get('count', 1)
                response_parts.append(f"人數：{count} 位")
                
                masseur_list = query_data.get('masseur', [])
                #if masseur_list:
                #    response_parts.append(f"指定師傅：{', '.join(masseur_list)}")
                
                response_parts.append("")  # 空行分隔
                
                if available:
                    # 處理 available 可能是字典列表或字符串列表的情況
                    if available and isinstance(available[0], dict):
                        # 字典列表：提取 name 欄位
                        available_names = [item['name'] for item in available]
                        response_parts.append(f"可約師傅：{', '.join(available_names)}")
                        print(f"DEBUG [Result]: 可約師傅: {', '.join(available_names)}")
                    else:
                        # 字符串列表
                        response_parts.append(f"可約師傅：{', '.join(available)}")
                        print(f"DEBUG [Result]: 可約師傅: {', '.join(available)}")
                
                # 只顯示 alternative_masseurs（已包含所有其他師傅資訊）
                # alternative_masseurs 包含：
                # 1. 時間可用但不在目標分店的師傅（含店家標註和時間）
                # 2. 時間不可用的師傅（含店家標註和時段）
                if alternative:
                    print(f"DEBUG [Result]: alternative_masseurs 數量: {len(alternative)}")
                    # 先過濾出需要顯示的師傅（排除 note='不可用' 的）
                    filtered_alternative = []
                    for alt in alternative:
                        if isinstance(alt, dict):
                            note = alt.get('note', '')
                            # 跳過不可用的師傅
                            if note == '不可用':
                                continue
                            filtered_alternative.append(alt)
                        else:
                            filtered_alternative.append(alt)
                    
                    # 只有在有需要顯示的師傅時才顯示「其他師傅」區塊
                    if filtered_alternative:
                        response_parts.append("\n其他師傅：")
                        for alt in filtered_alternative:
                            if isinstance(alt, dict):
                                name = alt.get('name', '未知')
                                time = alt.get('available_time', '')
                                stores = alt.get('stores', '')
                                
                                print(f"DEBUG [Result Format]: 師傅 {name}, time={repr(time)}, type={type(time)}, stores={stores}")
                                
                                # 格式化時間顯示（去除秒數）
                                # 只有 time 不是 None 且不是空字串時才格式化
                                if time and time != 'None' and time is not None and len(time) > 5:
                                    time = time[:5]
                                    print(f"DEBUG [Result Format]: 時間格式化後 {name}, time={time}")
                                
                                # 格式化顯示 - 只有當 time 有實際值時才顯示時間
                                if stores and time and time != 'None' and time is not None:
                                    print(f"DEBUG [Result Format]: 顯示 {name} with store and time")
                                    response_parts.append(f"  • {name} ({stores}) - {time}")
                                elif time and time != 'None' and time is not None:
                                    print(f"DEBUG [Result Format]: 顯示 {name} with time only")
                                    response_parts.append(f"  • {name} - {time}")
                                elif stores:
                                    print(f"DEBUG [Result Format]: 顯示 {name} with store only")
                                    response_parts.append(f"  • {name} ({stores})")
                                else:
                                    print(f"DEBUG [Result Format]: 顯示 {name} name only")
                                    response_parts.append(f"  • {name}")
                            else:
                                # 如果是字串格式，直接顯示
                                response_parts.append(f"  • {alt}")
            else:
                print("DEBUG [Result]: can_book=False，生成無法預約訊息")
                # 判斷無法預約的原因
                reason = ""
                masseur_avail = availability_result.get('masseur_availability', {})
                room_avail = availability_result.get('room_availability', {})
                
                available_masseurs = masseur_avail.get('available_masseurs', [])
                unavailable_masseurs = masseur_avail.get('unavailable_masseurs', [])
                
                # 檢查是否為單一師傅查詢
                masseur_list = query_data.get('masseur', [])
                is_single_masseur = len(masseur_list) == 1
                
                # 確定理由
                if not available_masseurs and unavailable_masseurs:
                    # 有不可約師傅，需要判斷是"有排班但時段不可用"還是"無排班"
                    # unavailable_masseurs 格式: [[師傅名, 時間], ...]
                    # 如果時間存在，表示師傅有排班但此時段不可用
                    # 如果時間為 None，表示無排班
                    
                    has_schedule = False
                    for item in unavailable_masseurs:
                        if isinstance(item, (list, tuple)) and len(item) > 1:
                            time_info = item[1]
                            if time_info is not None:  # 時間存在 = 有排班但此時段不可用
                                has_schedule = True
                                break
                    
                    if is_single_masseur:
                        # 單一師傅查詢
                        if has_schedule:
                            # 有排班但此時段不可用
                            reason = "該時段查詢失敗"
                        else:
                            # 無排班
                            reason = "約滿或無排班"
                    else:
                        # 多位師傅查詢（無指定或多位指定）
                        reason = "該時段查詢失敗"
                elif not available_masseurs:
                    if is_single_masseur:
                        reason = "約滿或無排班"
                    else:
                        reason = "該時段查詢失敗"
                elif not room_avail.get('available_at_requested_time', False):
                    reason = "無可用房間"
                else:
                    # 人數不足或其他原因
                    requested_count = query_data.get('count', 1)
                    if len(available_masseurs) < requested_count:
                        reason = f"師傅不足(需{requested_count}位/有{len(available_masseurs)}位)"
                    else:
                        reason = "其他原因"
                
                response_parts.append(f"\n⚠️請參考建議名單 ({reason})")
            
                # 顯示查詢條件
                response_parts.append("\n📋 查詢條件：")
                branch = query_data.get('branch', '')
                if query_data.get('used_default_branch'):
                    branch += " (預設)"
                response_parts.append(f"店家：{branch}")
                
                date = query_data.get('date', '')
                time = query_data.get('time', '')
                time = _format_time_hm(time)  # 格式化時間為 HH:MM
                response_parts.append(f"日期時間：{date} {time}")
                
                project = query_data.get('project', 0)
                if query_data.get('used_default_project'):
                    response_parts.append(f"療程：{project} 分鐘 (預設)")
                else:
                    response_parts.append(f"療程：{project} 分鐘")
                
                count = query_data.get('count', 1)
                response_parts.append(f"人數：{count} 位")
                
                masseur_list = query_data.get('masseur', [])
                #if masseur_list:
                #    response_parts.append(f"指定師傅：{', '.join(masseur_list)}")
                
                response_parts.append("")  # 空行分隔
                
                # 取得 alternative_masseurs
                alternative = masseur_avail.get('alternative_masseurs', [])
                
                # 只顯示 alternative_masseurs（已包含所有其他師傅資訊）
                # alternative_masseurs 包含：
                # 1. 時間可用但不在目標分店的師傅（含店家標註和時間）
                # 2. 時間不可用的師傅（含店家標註和時段）
                if alternative:
                    # 先過濾出有可用時段的師傅
                    filtered_alternative = []
                    for alt in alternative:
                        if isinstance(alt, dict):
                            time = alt.get('available_time', '')
                            # 只保留有時間的師傅
                            if time and time != 'None' and time != '無':
                                filtered_alternative.append(alt)
                        else:
                            filtered_alternative.append(alt)
                    
                    # 只有在有可用時段的師傅時才顯示「建議時段」區塊
                    if filtered_alternative:
                        response_parts.append("\n💡 建議名單：")
                        for alt in filtered_alternative:
                            if isinstance(alt, dict):
                                name = alt.get('name', '未知')
                                time = alt.get('available_time', '')
                                stores = alt.get('stores', '')
                                
                                # 格式化時間顯示（去除秒數）
                                if time and len(time) > 5:
                                    time = time[:5]
                                
                                # 格式化顯示：師傅-時間 店家
                                if stores:
                                    response_parts.append(f" • {name}-{time} {stores}")
                                else:
                                    response_parts.append(f" • {name}-{time}")
                            else:
                                # 字串格式的備用處理
                                response_parts.append(f" • {alt}")
                
                # 房間建議已移除（時間已在查詢條件中顯示）
            
            result['response_message'] = '\n'.join(response_parts)
            result['availability_checked'] = True
            
            print("DEBUG [Result]: 結果生成完成")
            print(f"  - 可預約: {can_book}")
            print(f"  - 回應訊息: {result.get('response_message', '無')}")
        else:
            # 查詢失敗的情況
            print("DEBUG [Result]: 查詢失敗，生成錯誤訊息")
            
            # 檢查是否為過期時間
            is_expired = availability_result.get('is_expired', False)
            
            response_parts = []
            
            if is_expired:
                # 過期時間的特殊訊息
                response_parts.append("\n❌ 無法查詢已過期時間")
            else:
                # 一般查詢失敗
                response_parts.append("\n❌ 查詢失敗")
            
            # 顯示查詢條件
            response_parts.append("\n📋 查詢條件：")
            branch = query_data.get('branch', '')
            if query_data.get('used_default_branch'):
                branch += " (預設)"
            response_parts.append(f"店家：{branch}")
            
            date = query_data.get('date', '')
            time = query_data.get('time', '')
            time = _format_time_hm(time)  # 格式化時間為 HH:MM
            response_parts.append(f"日期時間：{date} {time}")
            
            project = query_data.get('project', 0)
            if query_data.get('used_default_project'):
                response_parts.append(f"療程：{project} 分鐘 (預設)")
            else:
                response_parts.append(f"療程：{project} 分鐘")
            
            count = query_data.get('count', 1)
            response_parts.append(f"人數：{count} 位")
            
            masseur_list = query_data.get('masseur', [])
            #if masseur_list:
            #    response_parts.append(f"指定師傅：{', '.join(masseur_list)}")
            
            response_parts.append("")  # 空行分隔
            
            if is_expired:
                # 過期時間不顯示"無師傅符合查詢條件"
                pass
            else:
                # 一般查詢失敗才顯示
                response_parts.append("無師傅符合查詢條件")
            
            # 如果有錯誤訊息，也顯示出來
            error_msg = availability_result.get('error', '')
            if error_msg:
                response_parts.append(f"\n錯誤訊息：{error_msg}")
            
            result['response_message'] = '\n'.join(response_parts)
            result['availability_checked'] = True
            result['can_book'] = False
            
            print(f"  - 回應訊息: {result.get('response_message', '無')}")
    
    return result

