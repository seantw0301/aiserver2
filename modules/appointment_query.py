#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
預約查詢模塊 - 階段2
負責查詢預約的可用性
使用 core.common 中現有的 room_status_manager.query_available_appointment
包含師傅地點分佈管理功能
"""

from typing import Dict, Any, Optional
import json
import time as time_module
from datetime import datetime as dt
import redis
from core.common import room_status_manager
from core.database import db_config
from core.blacklist import BlacklistManager

# Redis 配置
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# 分店名稱到 ID 的映射（根據 Store.sql）
STORE_NAME_TO_ID = {
    '西門': 1,
    '延吉': 2,
    '家樂福': 3,
    '西門店': 1,
    '延吉店': 2,
    '家樂福店': 3,
    'Ximen': 1,
    'Yanji': 2,
    'Carrefour': 3
}


def _get_redis_client() -> Optional[redis.Redis]:
    """獲取 Redis 客戶端連接"""
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    except Exception as e:
        print(f"Redis 連接失敗: {e}")
        return None


def _get_storeid_from_branch(branch: str) -> int:
    """
    根據分店名稱獲取 storeid
    
    Args:
        branch: 分店名稱
        
    Returns:
        storeid，預設為 1（西門）
    """
    return STORE_NAME_TO_ID.get(branch, 1)


def _get_redis_key_write_time(redis_client: redis.Redis, key: str) -> Optional[float]:
    """
    獲取 Redis key 的寫入時間
    由於 Redis 不直接儲存寫入時間，我們在 value 中包含 timestamp
    
    Args:
        redis_client: Redis 客戶端
        key: Redis key
        
    Returns:
        寫入時間的 Unix timestamp，如果不存在則返回 None
    """
    try:
        data_str = redis_client.get(key)
        if not data_str:
            return None
        
        data = json.loads(data_str)
        return data.get('timestamp')
        
    except Exception as e:
        print(f"獲取 Redis key 寫入時間錯誤: {e}")
        return None


def get_staff_store_distribution(query_date: str, storeid: int = None) -> Dict[str, list]:
    """
    查詢師傅店家分佈表（獨立函數，可被其他模組調用）
    
    流程：
    1. 取得師傅當日店家分佈表（依日期）
    2. 取得 Redis 資料
    3. 判別 Tasks 有沒有變化，且時間比 Redis 資料新
    4. 若有變化更新，則重新取得新的店家分佈表
    5. 存放 Redis
    6. 回傳新的分佈表（若沒有更新資料，則直接回傳 Redis 上資料）
    
    Args:
        query_date: 查詢日期，格式如 "2025/11/28" 或 "2025-11-28"
        storeid: 分店 ID（可選，不影響分佈表內容，僅用於日誌）
        
    Returns:
        師傅店家分佈字典，格式: {"師傅名": [storeid1, storeid2], ...}
    """
    return _get_staff_store_distribution(query_date, storeid or 1)


def _get_staff_store_distribution(query_date: str, storeid: int) -> Dict[str, list]:
    """
    獲取指定日期和分店的師傅店家分佈
    
    流程：
    0. 檢查 Redis 快取是否需要更新（比較 Tasks 表最後更新時間與 Redis key 時間戳）
    1. 從 Staffs 表獲取該分店師傅的預設店家列表 (instores)
    2. 從 Tasks 表查詢當天的工作記錄，更新師傅實際工作地點
    3. 將結果存入 Redis 快取
    
    Args:
        query_date: 查詢日期，格式如 "2025/11/28" 或 "2025-11-28"
        storeid: 分店 ID
        
    Returns:
        師傅店家分佈字典，格式: {"師傅名": [storeid1, storeid2], ...}
    """
    print("DEBUG [Store Distribution]: 開始獲取師傅店家分佈")
    print(f"  - 查詢日期: {query_date}")
    print(f"  - 分店ID: {storeid}")
    
    # 標準化日期格式為 YYYY-MM-DD
    normalized_date = query_date.replace('/', '-')
    redis_key = f"instores_{normalized_date}"
    
    # 連接 Redis
    r = _get_redis_client()
    if r is None:
        print("  ⚠️ Redis 連接失敗，將直接從資料庫查詢")
    
    # 檢查是否需要更新快取
    need_update = True
    if r:
        try:
            # 獲取 Redis key 的寫入時間
            redis_write_time = _get_redis_key_write_time(r, redis_key)
            # 獲取 Tasks 表的最後更新時間
            from core.tasks import TaskManager
            task_manager = TaskManager()
            tasks_last_update = task_manager.get_tasks_table_lastupdate_time()
            
            if redis_write_time and tasks_last_update:
                # 比較時間
                tasks_timestamp = tasks_last_update.timestamp()
                print(f"  - Redis 快取時間: {dt.fromtimestamp(redis_write_time)}")
                print(f"  - Tasks 最後更新: {tasks_last_update}")
                
                if redis_write_time >= tasks_timestamp:
                    print("  ✓ Redis 快取仍然有效，直接使用")
                    cached_data = r.get(redis_key)
                    if cached_data:
                        distribution = json.loads(cached_data)
                        return distribution.get('data', {})
                    need_update = True
                else:
                    print("  ⚠️ Tasks 表有更新，需要重新生成快取")
                    need_update = True
            else:
                print("  ⚠️ 無法取得時間戳，將重新生成快取")
                need_update = True
                
        except Exception as e:
            print(f"  ⚠️ 檢查快取時發生錯誤: {e}")
            need_update = True
    
    if not need_update:
        return {}
    
    # 需要更新快取，從資料庫重新生成
    print("  → 從資料庫重新生成師傅店家分佈")
    
    connection = db_config.get_connection()
    if not connection:
        print("  ⚠️ 無法連接到資料庫")
        return {}
    
    distribution = {}
    
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        
        # 步驟 1: 獲取所有師傅的預設店家列表（不限定分店）
        print("  → 步驟1: 從 Staffs 表獲取所有師傅的預設值")
        query_staffs = """
            SELECT name, instores
            FROM Staffs
            WHERE enable = 1
        """
        cursor.execute(query_staffs)
        staffs = cursor.fetchall()
        
        print(f"  → 找到 {len(staffs)} 位師傅")
        
        # 初始化分佈字典（使用預設值）
        for staff in staffs:
            staff_name = staff['name']
            instores_str = staff.get('instores', '[1]')
            
            try:
                # 解析 instores JSON 字串
                if isinstance(instores_str, str):
                    instores = json.loads(instores_str)
                else:
                    instores = instores_str if instores_str else [1]
                    
                distribution[staff_name] = instores
                print(f"    - {staff_name}: 預設 {instores}")
            except json.JSONDecodeError:
                print(f"    ⚠️ {staff_name}: instores 格式錯誤，使用 [1]")
                distribution[staff_name] = [1]
        
        # 步驟 2: 從 Tasks 表查詢當天的工作記錄
        print(f"  → 步驟2: 查詢 {normalized_date} 的工作記錄")
        query_tasks = """
            SELECT staff_name, storeid, start
            FROM Tasks
            WHERE DATE(start) = %s
            ORDER BY start
        """
        cursor.execute(query_tasks, (normalized_date,))
        tasks = cursor.fetchall()
        
        print(f"  → 找到 {len(tasks)} 筆工作記錄")
        
        # 更新實際工作地點（後面的記錄會覆蓋前面的）
        for task in tasks:
            staff_name = task['staff_name']
            task_storeid = task['storeid']
            
            if staff_name in distribution:
                # 更新為實際工作地點
                distribution[staff_name] = [task_storeid]
                print(f"    - {staff_name}: 更新為 [{task_storeid}] (工作時間: {task['start']})")
        
        # 步驟 3: 將結果存入 Redis
        if r:
            try:
                cache_data = {
                    'timestamp': time_module.time(),
                    'date': normalized_date,
                    'data': distribution
                }
                r.set(redis_key, json.dumps(cache_data))
                print(f"  ✓ 已將分佈資料存入 Redis (key: {redis_key})")
            except Exception as e:
                print(f"  ⚠️ 存入 Redis 失敗: {e}")
        
        print("  ✓ 師傅店家分佈生成完成")
        return distribution
        
    except Exception as e:
        print(f"  ⚠️ 獲取師傅店家分佈時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return {}
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


def _get_store_name_list(store_ids: list) -> str:
    """
    將 store_ids 轉換為店家名稱列表字串
    
    Args:
        store_ids: 店家 ID 列表，如 [1, 2, 3]
        
    Returns:
        店家名稱字串，如 "西門, 延吉, 家樂福"（不含括號）
    """
    store_id_to_name = {
        1: "西門",
        2: "延吉", 
        3: "家樂福"
    }
    
    store_names = [store_id_to_name.get(sid, f"店{sid}") for sid in store_ids]
    return ', '.join(store_names)


def _filter_block_masseurs(
    availability_result: Dict[str, Any],
    line_key: str
) -> Dict[str, Any]:
    """
    根據黑名單過濾師傅
    
    過濾邏輯：
    1. 獲取客戶的黑名單師傅列表
    2. 從 masseur_availability 的 available_masseurs 和 alternative_masseurs 中移除黑名單師傅
    3. 同步更新 booking_recommendation 的 recommended_masseurs 和 alternative_masseurs
    4. 更新 booking_feasible 和 can_book 狀態
    
    Args:
        availability_result: 原始查詢結果
        line_key: LINE 用戶 ID
        
    Returns:
        過濾後的查詢結果
    """
    # 檢查並過濾黑名單師傅
    blacklist_mgr = BlacklistManager()
    blocked_staffs = blacklist_mgr.getBlockedStaffsList(line_key)
    
    if not blocked_staffs:
        # 沒有黑名單，直接返回原結果
        print("DEBUG [Query]: 沒有黑名單師傅")  
        return availability_result
    
    print(f"DEBUG [Query]: 發現黑名單師傅: {blocked_staffs}")
    
    # 從 masseur_availability 中移除黑名單師傅
    masseur_avail = availability_result.get('masseur_availability', {})
    
    # 過濾 available_masseurs
    available = masseur_avail.get('available_masseurs', [])
    if available:
        filtered_available = []
        for item in available:
            staff_name = item.get('name') if isinstance(item, dict) else item
            if staff_name not in blocked_staffs:
                filtered_available.append(item)
            else:
                print(f"  → 過濾黑名單師傅: {staff_name}")
        masseur_avail['available_masseurs'] = filtered_available
    
    # 過濾 alternative_masseurs
    alternative = masseur_avail.get('alternative_masseurs', [])
    if alternative:
        filtered_alternative = []
        for item in alternative:
            staff_name = item.get('name') if isinstance(item, dict) else item
            if staff_name not in blocked_staffs:
                filtered_alternative.append(item)
            else:
                print(f"  → 過濾黑名單師傅: {staff_name}")
        masseur_avail['alternative_masseurs'] = filtered_alternative
    
    # 更新 masseur_availability
    availability_result['masseur_availability'] = masseur_avail
    
    # 重新檢查是否有足夠師傅
    guest_count = masseur_avail.get('guest_count', 1)
    available_count = len(masseur_avail.get('available_masseurs', []))
    
    # 同步更新 booking_recommendation
    if 'booking_recommendation' in availability_result:
        booking_rec = availability_result['booking_recommendation']
        booking_rec['recommended_masseurs'] = masseur_avail.get('available_masseurs', [])
        booking_rec['alternative_masseurs'] = masseur_avail.get('alternative_masseurs', [])
        
        # 更新 booking_feasible 狀態
        if available_count < guest_count:
            booking_rec['booking_feasible'] = False
            availability_result['can_book'] = False
        
        availability_result['booking_recommendation'] = booking_rec
    
    return availability_result


def _filter_masseurs_by_store_distribution(
    availability_result: Dict[str, Any],
    store_distribution: Dict[str, list],
    target_storeid: int,
    branch_name: str,
    query_time: str = ""
) -> Dict[str, Any]:
    """
    根據師傅店家分佈過濾查詢結果
    
    將師傅分為兩類：
    1. 可約師傅：當天在目標分店服務的師傅
    2. 其他建議師傅：當天不在目標分店的師傅（每行標註服務店家和時間）
    
    重要：原本在可用列表的師傅，如果不在目標分店，會被移到其他建議（不會消失）
    
    Args:
        availability_result: 原始查詢結果
        store_distribution: 師傅店家分佈字典
        target_storeid: 目標分店 ID
        branch_name: 分店名稱（用於日誌）
        query_time: 查詢時間（用於標註時間可用的師傅）
        
    Returns:
        過濾後的查詢結果
    """
    print("\nDEBUG [Store Filter]: 開始過濾師傅店家分佈")
    print(f"  - 目標分店: {branch_name} (ID: {target_storeid})")
    print(f"  - 查詢時間: {query_time}")
    
    # 獲取 masseur_availability 區塊
    masseur_avail = availability_result.get('masseur_availability', {})
    if not masseur_avail:
        print("  ⚠️ 無 masseur_availability 資料，跳過過濾")
        return availability_result
    
    # 獲取原始的可用和不可約師傅列表
    original_available = masseur_avail.get('available_masseurs', [])
    original_alternative = masseur_avail.get('alternative_masseurs', [])  # 新增：處理 alternative
    original_unavailable = masseur_avail.get('unavailable_masseurs', [])
    
    print(f"  - 原始可約師傅: {original_available}")
    print(f"  - 原始建議師傅: {len(original_alternative)} 位")
    print(f"  - 原始不可約師傅: {len(original_unavailable)} 位")
    
    # 新的分類列表
    valid_available = []           # 真正可用：在目標分店的師傅
    other_store_masseurs = []      # 其他建議：不在目標店的師傅（含店家資訊）
    
    # 處理可約師傅列表（原本時間上可用的師傅）
    for item in original_available:
        # 支援兩種格式：字串或字典
        if isinstance(item, dict):
            masseur_name = item.get('name', '')
            item_time = item.get('available_time', query_time)
        else:
            masseur_name = item
            item_time = query_time
        
        if not masseur_name:
            continue
            
        if masseur_name in store_distribution:
            staff_stores = store_distribution[masseur_name]
            
            if target_storeid in staff_stores:
                # 師傅當天在目標分店服務 → 保留在可用列表
                # 保持原始格式
                valid_available.append(item if isinstance(item, dict) else masseur_name)
                print(f"  ✓ {masseur_name}: 在 {branch_name} 服務")
            else:
                # 師傅當天在其他分店服務 → 移到其他建議，標註店家和時間
                store_names = _get_store_name_list(staff_stores)
                # 格式化時間：將 HH:MM:SS 轉為 HH:MM
                formatted_time = item_time[:5] if item_time and len(item_time) >= 5 else item_time
                time_info = f" - {formatted_time}" if formatted_time else ""
                
                # 根據原始格式決定輸出格式
                if isinstance(item, dict):
                    other_store_masseurs.append({
                        'name': masseur_name,
                        'stores': store_names,
                        'available_time': item_time,
                        'note': f'時間可用但在{store_names}'
                    })
                else:
                    other_store_masseurs.append(f"{masseur_name} {store_names}{time_info}")
                print(f"  → {masseur_name}: 時間可用但在 {store_names}")
        else:
            # 找不到分佈資訊 → 保守起見，保留在可用列表
            valid_available.append(item if isinstance(item, dict) else masseur_name)
            print(f"  ⚠️ {masseur_name}: 無店家分佈資訊，保留在可用列表")
    
    # 處理建議師傅列表（alternative_masseurs）
    for item in original_alternative:
        # 支援兩種格式：字串或字典
        if isinstance(item, dict):
            masseur_name = item.get('name', '')
            item_time = item.get('available_time', query_time)
        else:
            masseur_name = item
            item_time = query_time
        
        if not masseur_name:
            continue
        
        # 跳過 available_time 為 None 的師傅（表示當天完全無可用時段）
        if isinstance(item, dict) and item.get('available_time') is None:
            print(f"  ⊗ {masseur_name}: 當天無可用時段，不顯示")
            continue
            
        if masseur_name in store_distribution:
            staff_stores = store_distribution[masseur_name]
            store_names = _get_store_name_list(staff_stores)
            
            # 無論是否在目標店，都加入店家資訊
            formatted_time = item_time[:5] if item_time and len(item_time) >= 5 else item_time
            
            if isinstance(item, dict):
                # 更新字典格式，添加店家資訊
                other_store_masseurs.append({
                    'name': masseur_name,
                    'stores': store_names,
                    'available_time': item_time,
                    'note': f'在{store_names}'
                })
            else:
                time_info = f" - {formatted_time}" if formatted_time else ""
                other_store_masseurs.append(f"{masseur_name} {store_names}{time_info}")
            
            if target_storeid in staff_stores:
                print(f"  ✓ {masseur_name}: 在 {branch_name} 服務（建議時間）")
            else:
                print(f"  → {masseur_name}: 在 {store_names}")
        else:
            # 找不到分佈資訊 → 保留在建議列表
            other_store_masseurs.append(item if isinstance(item, dict) else masseur_name)
            print(f"  ⚠️ {masseur_name}: 無店家分佈資訊，保留在建議列表")
    
    # 處理不可約師傅列表（檢查是否因為不在目標店）
    for item in original_unavailable:
        # 支援兩種格式：[[師傅名, 原因], ...] 或 [{'name': '師傅名'}, ...]
        if isinstance(item, dict):
            masseur_name = item.get('name', '')
            original_reason = '不可用'
        elif isinstance(item, list) and len(item) >= 2:
            masseur_name = item[0]
            original_reason = item[1]
        else:
            continue
        
        if not masseur_name:
            continue
            
        if masseur_name in store_distribution:
            staff_stores = store_distribution[masseur_name]
            store_names = _get_store_name_list(staff_stores)
            
            # 不管是否在目標店，都標註店家資訊
            # 根據原始格式決定輸出格式
            if isinstance(item, dict):
                other_store_masseurs.append({
                    'name': masseur_name,
                    'stores': store_names,
                    'note': original_reason
                })
            else:
                # 格式：師傅名 (店家) - 原因
                other_store_masseurs.append(f"{masseur_name} {store_names} - {original_reason}")
            print(f"  ⚠️ {masseur_name}: {original_reason}，當天在 {store_names}")
        else:
            # 沒有分佈資訊，只顯示原因
            if isinstance(item, dict):
                other_store_masseurs.append({
                    'name': masseur_name,
                    'note': original_reason
                })
            else:
                other_store_masseurs.append(f"{masseur_name} - {original_reason}")
    
    # 更新結果
    masseur_avail['available_masseurs'] = valid_available
    
    # 將其他店的師傅設為 alternative_masseurs
    masseur_avail['alternative_masseurs'] = other_store_masseurs
    
    # 更新 sufficient_masseurs 標記
    guest_count = masseur_avail.get('guest_count', 1)
    masseur_avail['sufficient_masseurs'] = len(valid_available) >= guest_count
    
    # 更新訊息
    if len(valid_available) == 0 and len(other_store_masseurs) > 0:
        masseur_avail['message'] = f'指定師傅當天不在{branch_name}服務，請參考其他建議'
    elif len(valid_available) < guest_count and len(other_store_masseurs) > 0:
        masseur_avail['message'] = f'{len(valid_available)}/{guest_count} 位師傅在{branch_name}可用，其他師傅在不同分店'
    elif len(valid_available) >= guest_count:
        masseur_avail['message'] = f'已有足夠師傅在{branch_name}服務'
    
    # 更新總結果
    availability_result['masseur_availability'] = masseur_avail
    
    # 更新 can_book 標記（只有在目標分店有足夠師傅才能預訂）
    if len(valid_available) < guest_count:
        availability_result['can_book'] = False
    
    print("\n  過濾結果:")
    print(f"  - 可約師傅（在{branch_name}）: {valid_available}")
    print(f"  - 其他建議師傅: {len(other_store_masseurs)} 位")
    if other_store_masseurs:
        for suggestion in other_store_masseurs[:3]:  # 顯示前3個
            print(f"    • {suggestion}")
        if len(other_store_masseurs) > 3:
            print(f"    ... 還有 {len(other_store_masseurs) - 3} 位")
    print(f"  - 足夠人數: {masseur_avail['sufficient_masseurs']}")
    
    return availability_result


def query_appointment_availability(line_key: str, query_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    查詢預約可用性（直接使用 core.common 的現有函數）
    
    Args:
        line_key: LINE 用戶 ID
        query_data: 查詢資料（已套用預設值）
            {
                'branch': '西門',
                'masseur': ['彬'],
                'date': '2025/11/28',
                'time': '21:00',
                'project': 90,
                'count': 1,
                'isReservation': True
            }
        
    Returns:
        查詢結果（來自 room_status_manager.query_available_appointment）
    """
    print("DEBUG [Query]: 開始查詢可用性")
    print(f"DEBUG [Query]: 接收到的查詢資料:")
    print(f"  - 分店: {query_data.get('branch', '(無)')}")
    print(f"  - 師傅: {query_data.get('masseur', [])}")
    print(f"  - 日期: {query_data.get('date', '(無)')}")
    print(f"  - 時間: {query_data.get('time', '(無)')}")
    print(f"  - 療程: {query_data.get('project', 0)} 分鐘")
    print(f"  - 人數: {query_data.get('count', 1)} 位")
    if query_data.get('used_default_branch'):
        print(f"  ⭐️ 分店使用預設值")
    if query_data.get('used_default_project'):
        print(f"  ⭐️ 療程使用預設值")
    
    # 提前檢查是否為班表查詢（有日期但沒有時間），無論是否為預約訊息都允許
    branch = query_data.get('branch', '').strip()
    date = query_data.get('date', '').strip()
    time = query_data.get('time', '').strip()
    
    if date and not time:
        print(f"DEBUG [Query]: 偵測到班表查詢（有日期無時間）")
        print(f"  - 日期: {date}")
        print(f"  - 分店: {branch if branch else '全部'}")
        
        try:
            # 使用 common.py 中的班表查詢功能
            schedule_result = room_status_manager.get_staff_shifts_by_date(
                date_str=date,
                store_name=branch if branch else None
            )
            
            print(f"DEBUG [Query]: 班表查詢完成")
            print(f"  - 查詢日期: {schedule_result.get('date', date)}")
            print(f"  - 師傅數量: {len(schedule_result.get('staff_shifts', []))}")
            
            # 格式化給用戶的訊息
            staff_shifts = schedule_result.get('staff_shifts', [])
            if staff_shifts:
                user_message = f"{schedule_result.get('date', date)} 班表：\n" + "\n".join(staff_shifts)
            else:
                user_message = f"{schedule_result.get('date', date)} 沒有排班記錄"
            
            return {
                'should_query': True,
                'is_schedule_query': True,
                'schedule_result': schedule_result,
                'user_message': user_message,
                'query_type': 'schedule',
                'success': True
            }
        except Exception as e:
            print(f"DEBUG [Query]: 班表查詢時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'should_query': True,
                'is_schedule_query': True,
                'success': False,
                'error': str(e)
            }
    
    # 檢查是否為預約
    if not query_data.get('isReservation', False):
        print("DEBUG [Query]: 非預約訊息，跳過查詢")
        return {
            'should_query': False,
            'reason': '非預約訊息'
        }
    
    # 提取查詢參數
    project = query_data.get('project', 90)  # 預設90分鐘
    count = query_data.get('count', 1)       # 預設1人
    masseur = query_data.get('masseur', [])
    
    # 檢查是否有足夠的查詢條件（預約查詢）
    if not branch or not date or not time or project <= 0:
        missing = []
        if not branch:
            missing.append('分店')
        if not date:
            missing.append('日期')
        if not time:
            missing.append('時間')
        if project <= 0:
            missing.append('療程')
        
        print(f"DEBUG [Query]: 查詢條件不足，缺少: {', '.join(missing)}")
        return {
            'should_query': False,
            'reason': f'查詢條件不足，缺少: {", ".join(missing)}',
            'missing_fields': missing
        }
    
    # 檢查日期時間是否已過期（過去的時間）
    print(f"DEBUG [Query]: 檢查查詢時間是否已過期")
    try:
        from datetime import datetime
        
        # 組合日期時間字符串並解析
        datetime_str = f"{date.replace('/', '-')} {time}"
        query_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        now = datetime.now()
        
        if query_datetime < now:
            print(f"DEBUG [Query]: 查詢時間已過期")
            print(f"  - 查詢時間: {datetime_str}")
            print(f"  - 當前時間: {now.strftime('%Y-%m-%d %H:%M')}")
            print(f"  - 跳過實際查詢，返回過期錯誤")
            
            return {
                'should_query': True,  # 標記為需要處理（顯示結果）
                'success': False,      # 但查詢失敗
                'is_expired': True,    # 標記為過期時間
                'query_data': query_data,  # 保留查詢條件用於顯示
                'error': '無法查詢已過期時間'
            }
        else:
            print(f"DEBUG [Query]: 查詢時間有效（未過期）")
    except Exception as e:
        print(f"DEBUG [Query]: 過期檢查時發生錯誤: {e}，繼續執行查詢")
        # 如果檢查失敗，繼續執行查詢（避免因檢查邏輯錯誤而阻擋正常查詢）
    
    # 構建查詢參數（直接使用 room_status_manager 期望的格式）
    query_params = {
        'line_key': line_key,
        'branch': branch,
        'masseur': masseur,
        'date': date,
        'time': time,
        'project': project,
        'count': count
    }
    
    # 獲取師傅店家分佈（用於後續可能的擴展）
    storeid = _get_storeid_from_branch(branch)
    store_distribution = _get_staff_store_distribution(date, storeid)
    
    print("DEBUG [Query]: 執行可用性查詢")
    print(f"  - 店家: {branch} (ID: {storeid})")
    print(f"  - 日期: {date}")
    print(f"  - 時間: {time}")
    print(f"  - 療程: {project} 分鐘")
    print(f"  - 人數: {count}")
    print(f"  - 查詢師傅: {masseur if masseur else '無'}")
    
    try:
        # 直接調用 core.common 中的現有函數
        availability_result = room_status_manager.query_available_appointment(query_params)
        
        # 應用師傅店家分佈過濾
        if store_distribution:
            availability_result = _filter_masseurs_by_store_distribution(
                availability_result, 
                store_distribution, 
                storeid,
                branch,
                time  # 傳入查詢時間
            )
        
        # 添加查詢標記
        availability_result['should_query'] = True
        availability_result['query_params'] = query_params
        
        # 記錄查詢結果
        can_book = availability_result.get('can_book', False)
        print(f"DEBUG [Query]: 查詢完成，可預約: {can_book}")
        
        if availability_result.get('success'):
            masseur_avail = availability_result.get('masseur_availability', {})
            available_masseurs = masseur_avail.get('available_masseurs', [])
            unavailable_masseurs = masseur_avail.get('unavailable_masseurs', [])
            
            print(f"  - 可約師傅: {available_masseurs if available_masseurs else '無'}")
            if unavailable_masseurs:
                unavail_info = []
                for item in unavailable_masseurs:
                    if isinstance(item, list) and len(item) >= 2:
                        unavail_info.append(f"{item[0]}({item[1]})")
                if unavail_info:
                    print(f"  - 不可約師傅: {', '.join(unavail_info)}")
        
        return availability_result
        
    except Exception as e:
        print(f"DEBUG [Query]: 查詢可用性時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'should_query': True,
            'success': False,
            'error': str(e),
            'can_book': False
        }

#2025年12月修訂版本
def query_appointment_availability_202512(line_key: str, query_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    查詢預約可用性（2025年12月修訂版本）
    
    新增功能：
    1. 檢查客戶是否為超級黑名單
    2. 如果是超級黑名單，直接返回不可預約結果
    
    Args:
        line_key: LINE 用戶 ID
        query_data: 查詢資料
        
    Returns:
        查詢結果
    """
    # 檢查客戶是否為'超級黑名單'
    # 若為True，則無需往下做，直接返回不可預約結果
    blacklist_mgr = BlacklistManager()
    
    if blacklist_mgr.is_super_blacklist(line_key):
        print(f"DEBUG [Query]: 用戶 {line_key} 為超級黑名單，拒絕預約")
        return {
            'should_query': True,
            'success': False,
            'error': '本日無可預約的師傅，請您明日再試',
            'can_book': False
        }

    print("DEBUG [Query]: 開始查詢可用性")
    print(f"DEBUG [Query]: 接收到的查詢資料:")
    print(f"  - 分店: {query_data.get('branch', '(無)')}")
    print(f"  - 師傅: {query_data.get('masseur', [])}")
    print(f"  - 日期: {query_data.get('date', '(無)')}")
    print(f"  - 時間: {query_data.get('time', '(無)')}")
    print(f"  - 療程: {query_data.get('project', 0)} 分鐘")
    print(f"  - 人數: {query_data.get('count', 1)} 位")
    if query_data.get('used_default_branch'):
        print(f"  ⭐️ 分店使用預設值")
    if query_data.get('used_default_project'):
        print(f"  ⭐️ 療程使用預設值")
    
    # 提前檢查是否為班表查詢（有日期但沒有時間），無論是否為預約訊息都允許
    branch = query_data.get('branch', '').strip()
    date = query_data.get('date', '').strip()
    time = query_data.get('time', '').strip()
    project = query_data.get('project', 0)
    
    if date and not time:
        print(f"DEBUG [Query]: 偵測到班表查詢（有日期無時間）")
        print(f"  - 日期: {date}")
        print(f"  - 分店: {branch if branch else '全部'}")
        
        try:
            # 使用 common.py 中的班表查詢功能
            schedule_result = room_status_manager.get_staff_shifts_by_date(
                date_str=date,
                store_name=branch if branch else None
            )
            
            print(f"DEBUG [Query]: 班表查詢完成")
            print(f"  - 查詢日期: {schedule_result.get('date', date)}")
            print(f"  - 師傅數量: {len(schedule_result.get('staff_shifts', []))}")
            
            # 格式化給用戶的訊息
            staff_shifts = schedule_result.get('staff_shifts', [])
            if staff_shifts:
                user_message = f"{schedule_result.get('date', date)} 班表：\n" + "\n".join(staff_shifts)
            else:
                user_message = f"{schedule_result.get('date', date)} 沒有排班記錄"
            
            return {
                'should_query': True,
                'is_schedule_query': True,
                'schedule_result': schedule_result,
                'user_message': user_message,
                'query_type': 'schedule',
                'success': True
            }
        except Exception as e:
            print(f"DEBUG [Query]: 班表查詢時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'should_query': True,
                'is_schedule_query': True,
                'success': False,
                'error': str(e)
            }
    
    # 檢查是否為預約
    if not query_data.get('isReservation', False):
        print("DEBUG [Query]: 非預約訊息，跳過查詢")
        return {
            'should_query': False,
            'reason': '非預約訊息'
        }
    
    # 提取查詢參數
    count = query_data.get('count', 1)       # 預設1人
    masseur = query_data.get('masseur', [])
    
    # 檢查是否有足夠的查詢條件（預約查詢）
    if not branch or not date or not time or project <= 0:
        missing = []
        if not branch:
            missing.append('分店')
        if not date:
            missing.append('日期')
        if not time:
            missing.append('時間')
        if project <= 0:
            missing.append('療程')
        
        print(f"DEBUG [Query]: 查詢條件不足，缺少: {', '.join(missing)}")
        return {
            'should_query': False,
            'reason': f'查詢條件不足，缺少: {", ".join(missing)}',
            'missing_fields': missing
        }
    
    # 檢查日期時間是否已過期（過去的時間）
    print(f"DEBUG [Query]: 檢查查詢時間是否已過期")
    try:
        from datetime import datetime
        
        # 組合日期時間字符串並解析
        datetime_str = f"{date.replace('/', '-')} {time}"
        query_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M')
        now = datetime.now()
        
        if query_datetime < now:
            print(f"DEBUG [Query]: 查詢時間已過期")
            print(f"  - 查詢時間: {datetime_str}")
            print(f"  - 當前時間: {now.strftime('%Y-%m-%d %H:%M')}")
            print(f"  - 跳過實際查詢，返回過期錯誤")
            
            return {
                'should_query': True,  # 標記為需要處理（顯示結果）
                'success': False,      # 但查詢失敗
                'is_expired': True,    # 標記為過期時間
                'query_data': query_data,  # 保留查詢條件用於顯示
                'error': '無法查詢已過期時間'
            }
        else:
            print(f"DEBUG [Query]: 查詢時間有效（未過期）")
    except Exception as e:
        print(f"DEBUG [Query]: 過期檢查時發生錯誤: {e}，繼續執行查詢")
        # 如果檢查失敗，繼續執行查詢（避免因檢查邏輯錯誤而阻擋正常查詢）
    
    # 構建查詢參數（直接使用 room_status_manager 期望的格式）
    query_params = {
        'line_key': line_key,
        'branch': branch,
        'masseur': masseur,
        'date': date,
        'time': time,
        'project': project,
        'count': count
    }
    
    # 獲取師傅店家分佈（用於後續可能的擴展）
    storeid = _get_storeid_from_branch(branch)
    store_distribution = _get_staff_store_distribution(date, storeid)
    
    print("DEBUG [Query]: 執行可用性查詢")
    print(f"  - 店家: {branch} (ID: {storeid})")
    print(f"  - 日期: {date}")
    print(f"  - 時間: {time}")
    print(f"  - 療程: {project} 分鐘")
    print(f"  - 人數: {count}")
    print(f"  - 查詢師傅: {masseur if masseur else '無'}")
    
    try:
        # 直接調用 core.common 中的現有函數
        availability_result = room_status_manager.query_available_appointment_202512(query_params)
        
        # 應用黑名單過濾
        availability_result = _filter_block_masseurs(availability_result, line_key)
        
        # 應用師傅店家分佈過濾
        if store_distribution:
            availability_result = _filter_masseurs_by_store_distribution(
                availability_result, 
                store_distribution, 
                storeid,
                branch,
                time  # 傳入查詢時間
            )
        
        # 添加查詢標記
        availability_result['should_query'] = True
        availability_result['query_params'] = query_params
        
        # 記錄查詢結果
        can_book = availability_result.get('can_book', False)
        print(f"DEBUG [Query]: 查詢完成，可預約: {can_book}")
        
        if availability_result.get('success'):
            masseur_avail = availability_result.get('masseur_availability', {})
            available_masseurs = masseur_avail.get('available_masseurs', [])
            unavailable_masseurs = masseur_avail.get('unavailable_masseurs', [])
            
            print(f"  - 可約師傅: {available_masseurs if available_masseurs else '無'}")
            if unavailable_masseurs:
                unavail_info = []
                for item in unavailable_masseurs:
                    if isinstance(item, list) and len(item) >= 2:
                        unavail_info.append(f"{item[0]}({item[1]})")
                if unavail_info:
                    print(f"  - 不可約師傅: {', '.join(unavail_info)}")
        
        return availability_result
        
    except Exception as e:
        print(f"DEBUG [Query]: 查詢可用性時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'should_query': True,
            'success': False,
            'error': str(e),
            'can_book': False
        }
