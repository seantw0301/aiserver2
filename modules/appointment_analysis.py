#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
預約分析模塊 - 階段1
負責分析用戶輸入的預約資訊，包括：
1-0. 由 Redis 上取回前面對話生成的預約資料
1-1. 日期分析（時）：預設 null
1-2. 時間分析（時）：預設 null
1-3. 員工分析（人）：預設 [] 無
1-4. 是否預約（事）：預設 否
1-5. 分店分析（地）：預設 西門店
1-6. 療程分析（物）：預設 90 分鐘
1-7. 分析完之後生成 JSON
1-8. 分析完的資料，原始資料（不考慮預設值）寫回 Redis，修正後資料（加入預設值）送至後續查詢

使用現有的 ai_parser 底下的 module，不自創新 function
"""

import json
import time
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import redis

# 使用現有的解析器（來自 ai_parser）
from ai_parser.handle_time import parse_datetime_phrases
from ai_parser.handle_staff import getStaffNames
from ai_parser.handle_customer import getCustomerCount
from ai_parser.handle_isReserv import isReservation
from ai_parser.handle_duration import extract_duration
from ai_parser.handle_time2025 import parser_date_time

# Redis 配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_EXPIRY = 12 * 60 * 60  # 12小時過期時間（以秒為單位）

# 店家名稱映射（地）- 來自 natural_language_parser.py
BRANCH_MAPPING = {
    '西門': '西門',
    '延吉': '延吉',
    '西門店': '西門',
    '延吉店': '延吉',
    '西': '西門',
    '延': '延吉',
    '大巨蛋': '延吉',
    '台北巨蛋': '延吉',
    '西門二店': '家樂福',
    '西寧': '家樂福',
    '家樂福店': '家樂福'
}

# 默認值
DEFAULT_BRANCH = "西門"
DEFAULT_PROJECT = 90
DEFAULT_COUNT = 1


def _get_redis_client() -> Optional[redis.Redis]:
    """獲取 Redis 客戶端連接（來自 natural_language_parser.py）"""
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    except Exception as e:
        print(f"Redis 連接失敗: {e}")
        return None


def _get_data_from_redis(line_key: str) -> Optional[Dict[str, Any]]:
    """
    1-0. 從 Redis 獲取資料，檢查是否過期
    （來自 natural_language_parser.py 的 _get_data_from_redis）
    """
    try:
        r = _get_redis_client()
        if r is None:
            return None
        
        data_str = r.get(line_key)
        if not data_str:
            return None
        
        data = json.loads(data_str)
        
        # 檢查資料是否過期 (12小時)
        if "update" in data:
            update_time = float(data["update"])
            current_time = time.time()
            if current_time - update_time > REDIS_EXPIRY:
                return None  # 資料已過期
        else:
            return None  # 沒有時間戳記，視為無效
        
        return data
    except Exception as e:
        print(f"從 Redis 獲取資料失敗: {e}")
        return None


def _save_data_to_redis(line_key: str, data: Dict[str, Any]) -> bool:
    """
    1-8. 儲存資料到 Redis
    （來自 natural_language_parser.py 的 _save_data_to_redis）
    """
    try:
        r = _get_redis_client()
        if r is None:
            print(f"DEBUG [Analysis]: 無法連接 Redis，跳過儲存")
            return False
        
        # 深拷貝以避免修改原始資料
        save_data = data.copy()
        
        # 處理 user_info 中的 datetime 物件
        if 'user_info' in save_data and save_data['user_info']:
            user_info_copy = save_data['user_info'].copy()
            if 'visitdate' in user_info_copy and user_info_copy['visitdate']:
                visitdate = user_info_copy['visitdate']
                if isinstance(visitdate, datetime):
                    user_info_copy['visitdate'] = visitdate.strftime("%Y-%m-%d %H:%M:%S")
            save_data['user_info'] = user_info_copy
        
        # 添加時間戳記
        save_data["update"] = time.time()
        
        # 儲存到 Redis (12小時過期)
        r.setex(line_key, REDIS_EXPIRY, json.dumps(save_data, ensure_ascii=False))
        print(f"DEBUG [Analysis]: 資料已儲存到 Redis，line_key: {line_key}")
        return True
    except Exception as e:
        print(f"儲存資料到 Redis 失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_is_reservarion_by_string(inMsg: str) -> bool:

    #將多餘字像是"可以嗎", "行嗎", "呢", "行","?" 等字移除，避免影響判斷
    for char in ["可以嗎","可嗎","可","行嗎", "行", "能嗎","能","呢","?"]:
        inMsg = inMsg.replace(char, "")

    full_match_string = ['今天','明天','today','tomorrow']
    #檢查inMsg是否完全符合其中一個字串
    if inMsg in full_match_string:
        return True
    
    #檢查字句是否完全符合 星期一，星期二，星期三，星期四，星期五，星期六，星期日
    days_of_week = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日','星期天']
    if inMsg in days_of_week:
        return True
    
    #檢查字句是否完全符合 
    days_of_week2 = ['下週一', '下週二', '下週三', '下週四', '下週五', '下週六', '下週日']
    if inMsg in days_of_week2:
        return True
    
    #檢查字句是否完全符合 MM/DD 或 M/D 格式的日期
    date_pattern = r'^\d{1,2}/\d{1,2}$'
    if re.match(date_pattern, inMsg):
        return True

    return False;


def get_is_reservation(parsed_data: Dict[str, Any]) -> bool:
    """
    判斷訊息是否為預約相關訊息
    必須符合以下其中一項才視為預約：
    1. 有日期
    2. 有時間
    3. 有師傅名字
    4. 有療程時間長短
    5. 有"預約"、"不指定"等預約關鍵字
    
    特殊情況：如果包含猶豫/不確定的關鍵字，直接判定為非預約
    
    此函數用於判斷當前訊息的解析結果是否為預約相關
    （基於已解析的數據，不再次解析訊息）
    
    Args:
        parsed_data (Dict): 包含 date, time, masseur, project, keyword_match 的已解析數據
        
    Returns:
        bool: 是否為預約相關訊息
    """
    print(f"DEBUG [get_is_reservation]: 開始判斷是否為預約相關")
    
    # 先檢查是否有猶豫/不確定的關鍵字 - 如果有則直接返回 False
    message = parsed_data.get('message', '')
    hesitation_keywords = ['不確定', '再決定', '再約', '先看看','先不用','先不要','再說','再看看','之後再說','改天','想一下','考慮','暫時不用','不需要','暫緩','等下','等一下','聯絡','不確定','先不']
    has_hesitation = any(keyword in message for keyword in hesitation_keywords)
    if has_hesitation:
        print(f"DEBUG [get_is_reservation]: 檢測到猶豫/不確定關鍵字: {hesitation_keywords}")
        print(f"DEBUG [get_is_reservation]: 直接判定為非預約")
        return False
    
    # 條件1：檢查日期
    has_date = parsed_data.get('date') and str(parsed_data['date']).strip() != ''
    if has_date:
        print(f"DEBUG [get_is_reservation]: ✓ 條件1 - 有日期: {parsed_data['date']}")
    
    # 條件2：檢查時間
    has_time = parsed_data.get('time') and str(parsed_data['time']).strip() != ''
    if has_time:
        print(f"DEBUG [get_is_reservation]: ✓ 條件2 - 有時間: {parsed_data['time']}")
    
    # 條件3：檢查師傅名字
    has_masseur = parsed_data.get('masseur') and len(parsed_data['masseur']) > 0
    if has_masseur:
        print(f"DEBUG [get_is_reservation]: ✓ 條件3 - 有師傅: {parsed_data['masseur']}")
    
    # 條件4：檢查療程時間長短
    has_duration = parsed_data.get('project') and parsed_data['project'] > 0
    if has_duration:
        print(f"DEBUG [get_is_reservation]: ✓ 條件4 - 有療程時間: {parsed_data['project']} 分鐘")
    
    # 條件5：檢查預約相關關鍵字
    has_keyword = parsed_data.get('has_keyword', False)
    if has_keyword:
        print(f"DEBUG [get_is_reservation]: ✓ 條件5 - 有預約關鍵字")
    
    # 條件6：檢查是否有明確的人數（不是None）
    has_explicit_count = parsed_data.get('count') is not None
    if has_explicit_count:
        print(f"DEBUG [get_is_reservation]: ✓ 條件6 - 有明確人數: {parsed_data['count']}")
    
    # 判斷結果
    is_reservation = has_date or has_time or has_masseur or has_duration or has_keyword or has_explicit_count
    
    print(f"DEBUG [get_is_reservation]: 條件檢查結果:")
    print(f"  - 有日期: {has_date}")
    print(f"  - 有時間: {has_time}")
    print(f"  - 有師傅: {has_masseur}")
    print(f"  - 有療程: {has_duration}")
    print(f"  - 有關鍵字: {has_keyword}")
    print(f"  - 有明確人數: {has_explicit_count}")
    print(f"DEBUG [get_is_reservation]: 最終判斷 - 是預約: {is_reservation}")
    
    return is_reservation


def _check_reservation_keywords(message: str) -> bool:
    """
    檢查訊息中是否有預約相關關鍵字
    
    這個函數用來檢查訊息是否明確表達預約意圖。
    只有確實與預約相關的關鍵字才應該被包含。
    
    Args:
        message (str): 用戶訊息
        
    Returns:
        bool: 是否包含預約關鍵字
    """
    reservation_keywords = [
        '預約', '約', '訂', '排', '安排', '登記', 
        '預訂', '預定', '預排', '空位', '時段',
        '幾點', '什麼時候', '哪個時間', '幾號',
        '可以來', '要來', '想來', '安排時間', '還有時間', '分鐘可以', '分可以',
        '不指定', '都可以', '都可', '任何師', '會按', '按比較', '比較會'
    ]
    
    for keyword in reservation_keywords:
        if keyword in message:
            return True
    
    return False


def is_force_clear_time(message: str) -> bool:
    """
    檢查訊息是否包含需要強制清除時間的關鍵字
    
    當訊息包含查詢可用性或班表的關鍵字時，
    應該清除時間資訊，因為這不是設定具體預約時間
    
    Args:
        message (str): 用戶訊息
        
    Returns:
        bool: 是否需要強制清除時間
    """
    force_clear_keywords = [
        '班表', '師傅表', '排班表','排表'
    ]
    
    for keyword in force_clear_keywords:
        if keyword in message:
            return True
    
    return False


def analyze_appointment(line_key: str, message: str, user_info: Optional[Dict] = None) -> Dict[str, Any]:
    """
    分析預約訊息
    
    流程：
    1. 先完成基礎解析（1-1 ~ 1-6）
    2. 生成當前訊息的 RAW_DATA（1-7）
    3. 調用 get_is_reservation 判斷（1-4）
    4. 若 is_reservation=false，返回非預約結果
    5. 若 is_reservation=true：
       - 2-1. 從 Redis 取回前面對話的預約資料
       - 2-2. 整合上次 Redis 資料和當前解析結果，成為新的 RAW_DATA，存放 Redis
       - 2-3. 將 RAW_DATA 整合預設值，成為 query_data
       - 2-4. 將 query_data 送至查詢
    
    Args:
        line_key: LINE 用戶 ID
        message: 用戶訊息
        user_info: 用戶資訊
        
    Returns:
        {
            'raw_data': {},      # 原始資料（當前訊息的解析結果）
            'query_data': {},    # 查詢資料（套用預設值後）
            'is_reservation': bool,
            'has_update': bool
        }
    """
    print(f"DEBUG [Appointment]: 開始處理預約")
    print(f"DEBUG [Appointment]: line_key={line_key}")
    print(f"DEBUG [Appointment]: message={message}")
    
    print(f"\nDEBUG [Appointment]: ========== 階段1：解析當前訊息 ==========")
    
    # ===== 步驟 1-1 ~ 1-6: 基礎解析 =====
    
    # 1-1. 日期分析 & 1-2. 時間分析
    date_val = ""
    time_val = ""
    force_clear_time = False  # 新增：是否強制清除時間的標記
    try:
        date_val,time_val= parser_date_time(message,2)
        
        #如果不是今天，則判讀是否時間清空
        if date_val and date_val != datetime.now().strftime("%Y-%m-%d"):
            force_clear_time = is_force_clear_time(message)
            if force_clear_time :
                time_val =""
        
        """
        datetime_result, force_clear_time = parse_datetime_phrases(message)
        if datetime_result:
            if '日期' in datetime_result and datetime_result['日期'] and datetime_result['日期'] != 'null':
                date_val = str(datetime_result['日期']).replace('-', '/')
                print(f"DEBUG [Analysis]: 1-1. 日期分析 - {date_val}")
            
            # 時間處理：根據 force_clear_time 標記決定如何處理
            if '時間' in datetime_result:
                time_str = datetime_result['時間']
                if time_str is not None and time_str != 'null':
                    # 有具體時間值
                    time_val = str(time_str)
                    print(f"DEBUG [Analysis]: 1-2. 時間分析 - {time_val}")
                elif force_clear_time:
                    # force_clear_time=True 表示要強制清除時間
                    time_val = ""  # 設為空字符串表示要清除
                    print(f"DEBUG [Analysis]: 1-2. 時間分析 - 強制清除時間 (force_clear_time=True)")
                # else: time_val 保持為 ""，表示當前訊息沒有時間資訊
        
        print(f"DEBUG [Analysis]: force_clear_time = {force_clear_time}")
        """
    except Exception as e:
        print(f"警告：日期時間解析失敗：{e}")
    
    # 1-3. 員工分析
    masseur_val = []
    try:
        masseur_val = getStaffNames(message)
        if masseur_val:
            print(f"DEBUG [Analysis]: 1-3. 員工分析 - {masseur_val}")
    except Exception as e:
        print(f"警告：師傅判斷失敗：{e}")
    
    # 1-4. 先不在這裡判斷，先做完其他解析
    
    # 1-5. 分店分析
    branch_val = ""
    for branch_key in sorted(BRANCH_MAPPING.keys(), key=len, reverse=True):
        if branch_key in message:
            branch_val = BRANCH_MAPPING[branch_key]
            print(f"DEBUG [Analysis]: 1-5. 分店分析 - {branch_val}")
            break
    
    # 1-6. 療程分析
    print(f"DEBUG [Analysis]: 1-6. 療程分析 - 開始解析...")
    project_val = extract_duration(message)
    if project_val:
        print(f"DEBUG [Analysis]: 1-6. 療程分析 - ✓ 找到療程 {project_val} 分鐘")
    else:
        project_val = 0
        print(f"DEBUG [Analysis]: 1-6. 療程分析 - ✗ 未找到療程（設為 0）")
    
    # 人数分析 - 使用统一入口
    count_val, is_explicit = getCustomerCount(message, return_details=True)
    if is_explicit:
        print(f"DEBUG [Analysis]: 人数分析 - {count_val} (明确表达)")
    else:
        # 未明確指定時，保持 None，稍後在 query_data 套用預設值 1
        count_val = None
        print(f"DEBUG [Analysis]: 人数分析 - None (未明确指定，将在 query_data 套用预设值 1)")
    
    # 檢查預約相關關鍵字
    has_keyword = _check_reservation_keywords(message)
    
    # ===== 步驟 1-7: 生成當前訊息的 RAW_DATA（未結合 Redis） =====
    current_parsed_data = {
        "message": message,
        "branch": branch_val,
        "masseur": masseur_val,
        "date": date_val,
        "time": time_val,
        "project": project_val,
        "count": count_val,
        "has_keyword": has_keyword,
        "force_clear_time": force_clear_time  # 新增：記錄是否強制清除時間
    }
    
    print(f"\n📋 當前訊息的解析結果（RAW_DATA - 未結合 Redis）:")
    print(f"  📍 分店: {current_parsed_data['branch'] if current_parsed_data['branch'] else '未指定'}")
    print(f"  👤 師傅: {current_parsed_data['masseur'] if current_parsed_data['masseur'] else '未指定'}")
    print(f"  📅 日期: {current_parsed_data['date'] if current_parsed_data['date'] else '未指定'}")
    print(f"  ⏰ 時間: {current_parsed_data['time'] if current_parsed_data['time'] else '未指定'}")
    print(f"  💆 療程: {current_parsed_data['project'] if current_parsed_data['project'] else '未指定'} 分鐘")
    print(f"  👥 人數: {current_parsed_data['count']} 位")
    print(f"  🔑 預約關鍵字: {current_parsed_data['has_keyword']}")
    
    # ===== 步驟 1-4: 調用 get_is_reservation 判斷 =====
    is_reservation = get_is_reservation(current_parsed_data)
    if not is_reservation:
        is_reservation = get_is_reservarion_by_string(message)

    print(f"\nDEBUG [Analysis]: 1-4. 是否預約判斷 - {is_reservation}")
    
    # 如果不是預約相關，返回非預約結果
    if not is_reservation:
        print(f"DEBUG [Analysis]: 非預約訊息，返回查詢結果")
        result = {
            "branch": "",
            "masseur": [],
            "date": "",
            "time": "",
            "project": 0,
            "count": 0,
            "isReservation": False
        }
        if user_info:
            result['user_info'] = user_info
        
        return {
            'raw_data': result,
            'query_data': result,
            'is_reservation': False,
            'has_update': False
        }
    
    # ===== 是預約相關，執行以下步驟 =====
    print(f"\nDEBUG [Appointment]: ========== 階段2：預約相關處理 ==========")
    
    # 2-1. 從 Redis 取回前面對話的預約資料
    redis_data = _get_data_from_redis(line_key)
    
    # 2-2. 整合上次 Redis 資料和當前解析結果
    if redis_data:
        print(f"DEBUG [Analysis]: 2-1. 找到現有 Redis 資料，進行整合")
        print(f"DEBUG [Analysis]: Redis 中的人数: {redis_data.get('count', '未设置')}")
        # 有先前的 Redis 資料，覆蓋有新值的欄位
        raw_data = redis_data.copy()
        
        # 只有在當前訊息中有解析出結果的欄位才覆蓋
        if current_parsed_data['date']:
            raw_data['date'] = current_parsed_data['date']
        
        # 時間處理：根據 force_clear_time 決定是否更新
        if force_clear_time:
            # force_clear_time=True: 強制清除時間（無偏好關鍵詞）
            raw_data['time'] = ""
            print(f"DEBUG [Analysis]: 2-2. force_clear_time=True，清空時間")
        elif current_parsed_data['time']:
            # 有具體時間值，更新
            raw_data['time'] = current_parsed_data['time']
            print(f"DEBUG [Analysis]: 2-2. 更新時間為 {current_parsed_data['time']}")
        # else: time=None 且 force_clear_time=False，保留原值不修改
        else:
            print(f"DEBUG [Analysis]: 2-2. time=None 且 force_clear_time=False，保留原時間 {raw_data.get('time', '')}")
        
        if current_parsed_data['branch']:
            raw_data['branch'] = current_parsed_data['branch']
        
        if current_parsed_data['masseur']:
            raw_data['masseur'] = current_parsed_data['masseur']
        
        if current_parsed_data['project'] > 0:
            raw_data['project'] = current_parsed_data['project']
        
        # 人数：只有在有明確表達時才更新（不使用默认值覆盖）
        # 注意：getCustomerCount 返回的默认值 1 不应该覆盖 Redis 中的历史值
        # 只有当用户明确说 "3位"、"两个人" 等时才更新
        explicit_count, is_explicit = getCustomerCount(message, return_details=True)
        if is_explicit:
            raw_data['count'] = explicit_count
            print(f"DEBUG [Analysis]: 2-2. 检测到明确人数表达，更新人数为 {explicit_count}")
        else:
            print(f"DEBUG [Analysis]: 2-2. 无明确人数表达，保留 Redis 中的人数 {raw_data.get('count', 1)}")
        
        raw_data['isReservation'] = True
        has_update = raw_data != redis_data
        
    else:
        print(f"DEBUG [Analysis]: 2-1. 無現有 Redis 資料，使用當前訊息解析結果")
        # 沒有先前的 Redis 資料，使用當前訊息解析結果
        raw_data = {
            "branch": current_parsed_data['branch'],
            "masseur": current_parsed_data['masseur'],
            "date": current_parsed_data['date'],
            "time": current_parsed_data['time'],
            "project": current_parsed_data['project'],
            "count": current_parsed_data['count'],
            "isReservation": True
        }
        has_update = True
    
    # 添加用戶資訊到 raw_data
    if user_info:
        raw_data['user_info'] = user_info
    
    # 2-2. 將 RAW_DATA 存放 Redis
    print(f"DEBUG [Analysis]: 2-2. 將整合後的 RAW_DATA 存放 Redis")
    _save_data_to_redis(line_key, raw_data)
    
    # 2-3. 將 RAW_DATA 整合預設值，成為 query_data
    print(f"DEBUG [Analysis]: 2-3. 套用預設值生成 query_data")
    query_data = _apply_defaults(raw_data.copy())
    
    print(f"\n{'='*80}")
    print(f"📊 分析完成")
    print(f"{'='*80}")
    print(f"\n📋 RAW_DATA（當前訊息的解析結果）:")
    print(f"  📍 分店: {raw_data.get('branch', '') if raw_data.get('branch') else '未指定'}")
    print(f"  👤 師傅: {raw_data.get('masseur', []) if raw_data.get('masseur') else '未指定'}")
    print(f"  📅 日期: {raw_data.get('date', '') if raw_data.get('date') else '未指定'}")
    print(f"  ⏰ 時間: {raw_data.get('time', '') if raw_data.get('time') else '未指定'}")
    print(f"  💆 療程: {raw_data.get('project', 0)} 分鐘")
    print(f"  👥 人數: {raw_data.get('count', 1)} 位")
    
    print(f"\n🔧 query_data（套用預設值後）:")
    print(f"  📍 分店: {query_data.get('branch', '')} {' ⭐️ (預設)' if query_data.get('used_default_branch') else ''}")
    print(f"  👤 師傅: {query_data.get('masseur', []) if query_data.get('masseur') else '(無指定)'}")
    print(f"  📅 日期: {query_data.get('date', '')}")
    print(f"  ⏰ 時間: {query_data.get('time', '')}")
    print(f"  💆 療程: {query_data.get('project', 0)} 分鐘 {' ⭐️ (預設)' if query_data.get('used_default_project') else ''}")
    print(f"  👥 人數: {query_data.get('count', 1)} 位")
    print(f"  是否有更新: {has_update}")
    
    print(f"\n{'='*80}\n")
    
    # 2-4. 返回 query_data 用於查詢
    return {
        'raw_data': raw_data,
        'query_data': query_data,
        'is_reservation': True,
        'has_update': has_update
    }


def _apply_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    為查詢資料套用預設值
    
    預設值只在以下情況下應用：
    - 分店：西門店（當未指定時）
    - 療程：90分鐘（當未指定且有日期時）
    - 人數：1位（當未指定時）
    
    Args:
        data: RAW_DATA
        
    Returns:
        套用預設值後的 query_data
    """
    result = data.copy()
    
    # 移除 Redis 相關的臨時字段
    for key in ['update', 'used_default_branch', 'used_default_project']:
        if key in result:
            del result[key]
    
    # 分店預設：西門（當未指定時）
    if not result.get('branch'):
        result['branch'] = DEFAULT_BRANCH
        result['used_default_branch'] = True
        print(f"DEBUG [Analysis]: 套用預設分店 - {DEFAULT_BRANCH}")
    
    # 療程預設：90分鐘（當未指定且有日期時）
    if result.get('date') and (not result.get('project') or result.get('project') <= 0):
        result['project'] = DEFAULT_PROJECT
        result['used_default_project'] = True
        print(f"DEBUG [Analysis]: 套用預設療程 - {DEFAULT_PROJECT} 分鐘")
    
    # 人數預設：1位（當未指定時）
    if result.get('count') is None:
        result['count'] = DEFAULT_COUNT
        print(f"DEBUG [Analysis]: 套用預設人數 - {DEFAULT_COUNT} 位")
    
    return result
