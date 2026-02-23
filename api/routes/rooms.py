from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import json
from api.models import AppointmentQuery, PreferStoreQuery, RoomAvailabilityQuery
from core.common import room_status_manager, CommonUtils
from core.tasks import TaskManager
from modules.workday_manager import WorkdayManager
from utils import run_in_executor

router = APIRouter(prefix="/rooms", tags=["Rooms"])

@router.get("/status/{store_id}/{date}", summary="獲取指定店家指定日期的房間狀態表")
async def get_room_status_table(store_id: int, date: str):
    """獲取指定店家指定日期的房間狀態表"""
    try:
        date_formatted = date.replace('-', '/')
        room_status = await run_in_executor(room_status_manager.build_room_status_table, store_id, date_formatted)
        
        if room_status is None:
            raise HTTPException(status_code=404, detail=f'找不到店家ID {store_id}')
        
        return {
            'success': True,
            'data': room_status,
            'store_id': store_id,
            'date': date_formatted
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f'獲取房間狀態表錯誤: {str(e)}')

@router.get("/status/{store_id}/{date}/{time}", summary="獲取指定時間的房間狀態")
async def get_room_status_at_time(store_id: int, date: str, time: str):
    """獲取指定時間的房間狀態"""
    try:
        date_formatted = date.replace('-', '/')
        room_status = await run_in_executor(room_status_manager.get_room_status_at_time, store_id, date_formatted, time)
        
        if room_status is None:
            raise HTTPException(status_code=404, detail=f'找不到店家ID {store_id} 或無效的日期時間')
        
        return {
            'success': True,
            'data': room_status,
            'store_id': store_id,
            'date': date_formatted,
            'time': time
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f'獲取房間狀態錯誤: {str(e)}')

@router.get("/available_slots/{store_id}/{date}", summary="獲取當日仍然可以預約的時段")
async def get_available_times(store_id: int, date: str):
    """獲取當日仍然可以預約的時段
    
    判斷輸入的時間是否為今天，若為今日，則時間為現在時間+2小時之後，15分鐘為間格
    如： 現在時間為14:10，則可預約時間為16:15、16:30、16:45、17:00...為時間字串集合
    ["16:15", "16:30", "16:45", "17:00", ...] 最晚為 "22:30"
    若不為今天時間，則由09:00 開始到22:30, 初始化字串集合
    """
    try:   
        from datetime import datetime, timedelta
        
        # 解析輸入日期
        date_str = date.replace('-', '/')
        try:
            input_date = datetime.strptime(date_str, '%Y/%m/%d')
        except ValueError:
            raise HTTPException(status_code=400, detail='日期格式錯誤，應為 YYYY-MM-DD 或 YYYY/MM/DD')
        
        # 獲取當前日期和時間
        now = datetime.now()
        today = now.date()
        
        # 判斷是否為今天
        is_today = input_date.date() == today
        
        available_times = []
        
        if is_today:
            # 如果是今天，從現在時間+2小時開始
            start_time = now + timedelta(hours=2)
            
            # 調整到下一個15分鐘間隔（向上取整）
            minutes = start_time.minute
            if minutes % 15 != 0:
                minutes = ((minutes // 15) + 1) * 15
                if minutes >= 60:
                    start_time = start_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                else:
                    start_time = start_time.replace(minute=minutes, second=0, microsecond=0)
            else:
                start_time = start_time.replace(second=0, microsecond=0)
            
            # 從調整後的時間開始，每15分鐘一個時段，直到22:30
            end_time = datetime.combine(today, datetime.strptime("22:30", "%H:%M").time())
            
            current_time = start_time
            while current_time <= end_time:
                available_times.append(current_time.strftime("%H:%M"))
                current_time += timedelta(minutes=15)
        else:
            # 如果不是今天，從09:00開始到22:30
            start_time = datetime.combine(input_date.date(), datetime.strptime("09:00", "%H:%M").time())
            end_time = datetime.combine(input_date.date(), datetime.strptime("22:30", "%H:%M").time())
            
            current_time = start_time
            while current_time <= end_time:
                available_times.append(current_time.strftime("%H:%M"))
                current_time += timedelta(minutes=15)
        """獲取本日己有工作的時間，需排除不能用的時段"""
        workday_manager = WorkdayManager()
        # 呼叫時傳入整數 store_id，並保護返回值類型
        all_avoid_block = await run_in_executor(workday_manager.get_all_avoid_block_by_storeid, store_id, date_str)
        # 將 all_avoid_block 列出的時間，排除在 available_times 中
        if isinstance(all_avoid_block, (list, tuple)):
            for avoid_time in all_avoid_block:
                if avoid_time in available_times:
                    available_times.remove(avoid_time)
        else:
            # 若回傳為 None 或其他類型，記錄 debug 並繼續（不造成錯誤）
            print(f"[DEBUG] get_available_times - all_avoid_block 非 list: {type(all_avoid_block)}")

        return {
            "success": True,
            "data": available_times,
            "store_id": store_id,
            "date": date_str,
            "is_today": is_today,
            "count": len(available_times)
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        # 發生錯誤時返回空列表
        return {"success": True, "data": []}

@router.get("/available/{store_id}/{date}/{time}", summary="獲取指定時間的可用房間")
async def get_available_rooms_at_time(store_id: int, date: str, time: str):
    """獲取指定時間的可用房間"""
    try:
        date_formatted = date.replace('-', '/')
        available_rooms = await run_in_executor(room_status_manager.get_available_rooms_at_time, store_id, date_formatted, time)
        
        return {
            'success': True,
            'data': {
                'available_rooms': available_rooms,
                'count': len(available_rooms)
            },
            'store_id': store_id,
            'date': date_formatted,
            'time': time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'獲取可用房間錯誤: {str(e)}')

@router.get("/summary/{store_id}/{date}", summary="獲取房間使用率摘要")
async def get_room_status_summary(store_id: int, date: str):
    """獲取房間使用率摘要"""
    try:
        date_formatted = date.replace('-', '/')
        summary = await run_in_executor(room_status_manager.get_room_status_summary, store_id, date_formatted)
        
        if not summary:
            raise HTTPException(status_code=404, detail=f'找不到店家ID {store_id} 或無法獲取摘要資訊')
        
        return {
            'success': True,
            'data': summary
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f'獲取房間摘要錯誤: {str(e)}')

@router.get("/detailed/{store_id}/{date}", summary="獲取詳細房間狀態表格")
async def get_detailed_room_status_table(store_id: int, date: str):
    """獲取詳細房間狀態表格"""
    try:
        date_formatted = date.replace('-', '/')
        detailed_status = await run_in_executor(room_status_manager.get_detailed_room_status_table, store_id, date_formatted)
        
        if not detailed_status:
            raise HTTPException(status_code=404, detail=f'找不到店家ID {store_id} 或無法獲取詳細狀態')
        
        return {
            'success': True,
            'data': detailed_status
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f'獲取詳細房間狀態錯誤: {str(e)}')

@router.get("/array/{store_id}/{date}", summary="獲取房間狀態數組表格")
async def get_room_status_array_table(store_id: int, date: str):
    """獲取房間狀態數組表格"""
    try:
        date_formatted = date.replace('-', '/')
        array_table = await run_in_executor(room_status_manager.get_room_status_array_table, store_id, date_formatted)
        
        if not array_table:
            raise HTTPException(status_code=404, detail=f'找不到店家ID {store_id} 或無法獲取房間狀態數組')
        
        return {
            'success': True,
            'data': array_table
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f'獲取房間狀態數組錯誤: {str(e)}')

@router.post("/appointments/query", summary="查詢可用預約時段和師傅")
async def query_available_appointment(query_data: AppointmentQuery):
    """查詢可用預約時段和師傅"""
    try:
        query_dict = query_data.dict()
        date_str = query_dict.get('date', '').strip()
        date_formats = ['%Y/%m/%d', '%Y-%m-%d']
        date_obj = None
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                query_dict['date'] = date_obj.strftime('%Y/%m/%d')
                break
            except ValueError:
                continue
        
        result = await run_in_executor(room_status_manager.query_available_appointment, query_dict)
        return result
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        return {
            'success': False,
            'error': f'查詢預約時發生錯誤: {str(e)}',
            'step': 'error'
        }

@router.post("/appointments/prefer-store", summary="查詢師傅偏好的店家")
async def query_prefer_store(query_data: PreferStoreQuery):
    """根據師傅名字和日期，查詢偏好的店家"""
    try:
        if not query_data.masseur_name.strip():
            raise HTTPException(status_code=400, detail='師傅名稱不能為空')
        
        date_str = query_data.date.strip()
        try:
            date_formats = ['%Y/%m/%d', '%Y-%m-%d']
            date_obj = None
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if date_obj is None:
                raise ValueError('無法解析日期格式')
        except ValueError:
            raise HTTPException(status_code=400, detail='日期格式錯誤，應為 YYYY/MM/DD 或 YYYY-MM-DD')
        
        result = await run_in_executor(CommonUtils.getPreferStore, query_data.date, query_data.masseur_name)
        
        store_names = []
        for store_id in result:
            if store_id == 1:
                store_names.append("西門館")
            elif store_id == 2:
                store_names.append("延吉館")
            else:
                store_names.append(f"店家{store_id}")
        
        return {
            'success': True,
            'masseur_name': query_data.masseur_name,
            'date': query_data.date,
            'prefer_store_ids': result,
            'prefer_store_names': store_names,
            'message': f'師傅 {query_data.masseur_name} 在 {query_data.date} 的偏好店家: {", ".join(store_names) if store_names else "無"}',
            'total_stores': len(result)
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f'查詢偏好店家時發生錯誤: {str(e)}')

@router.post("/earliest-available", summary="查詢最早可用房間時間")
async def find_earliest_available_rooms(query_data: RoomAvailabilityQuery):
    """查詢最早可用房間時間"""
    try:
        if query_data.store_id <= 0:
            raise HTTPException(status_code=400, detail='店家ID必須為正整數')
        
        if query_data.duration_minutes <= 0:
            raise HTTPException(status_code=400, detail='使用時間必須為正整數（分鐘）')
        
        if not (1 <= query_data.required_rooms <= 4):
            raise HTTPException(status_code=400, detail='需要房間數必須為1-4之間的整數')
        
        try:
            datetime.strptime(query_data.start_time, '%H:%M')
        except ValueError:
            raise HTTPException(status_code=400, detail='開始時間格式錯誤，應為 HH:MM')
        
        date_str = query_data.date
        try:
            date_formats = ['%Y/%m/%d', '%Y-%m-%d']
            date_obj = None
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    date_str = date_obj.strftime('%Y/%m/%d')
                    break
                except ValueError:
                    continue
            
            if date_obj is None:
                raise ValueError('無法解析日期格式')
        except ValueError:
            raise HTTPException(status_code=400, detail='日期格式錯誤，應為 YYYY/MM/DD 或 YYYY-MM-DD')
        
        result = await run_in_executor(
            room_status_manager.find_earliest_available_time_for_rooms,
            query_data.store_id,
            date_str,
            query_data.start_time,
            query_data.duration_minutes,
            query_data.required_rooms
        )
        
        return result
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f'查詢最早可用時間時發生錯誤: {str(e)}')

@router.get("/checkRoomCanBook", summary="檢查是否可以預約房間")
async def check_room_can_book(
    date: str = Query(..., description="預約日期，格式: YYYY-MM-DD"),
    time: str = Query(..., description="預約開始時間，格式: HH:MM"),
    guest: int = Query(..., description="客人數量", ge=1),
    duration: int = Query(..., description="預約時長（分鐘）", ge=1),
    storeid: str = Query(None, description="店家ID（可選，不指定則檢查所有店家）"),
    lineid: str = Query(None, description="LINE 用戶 ID")
):
    """
    檢查指定日期時間是否有足夠的房間可以預約
    
    參數：
    - date: 預約日期（格式: YYYY-MM-DD）
    - time: 預約開始時間（格式: HH:MM）
    - guest: 需要的房間數量
    - duration: 預約時長（分鐘）
    - storeid: 店家ID（可選，不指定則檢查所有店家）
    - lineid: LINE 用戶 ID（用於超級黑名單檢查）
    
    返回：
    - result: true/false
    - store_id: 檢查的店家ID（如果指定了storeid，則返回該ID；如果找到可用房間則返回找到的店家ID）
    """
    try:
        # 0. 檢查是否為超級黑名單
        from core.blacklist import BlacklistManager
        blacklist_manager = BlacklistManager()
        
        # 添加日誌來跟蹤黑名單檢查
        print(f"[DEBUG] checkRoomCanBook - 檢查 lineid: {lineid}")
        if lineid:
            is_blacklisted = blacklist_manager.is_super_blacklist(lineid)
            print(f"[DEBUG] checkRoomCanBook - 黑名單檢查結果: {is_blacklisted}")
            if is_blacklisted:
                print(f"[DEBUG] checkRoomCanBook - {lineid} 是超級黑名單，返回 false")
                return {'result': False}
        else:
            print(f"[DEBUG] checkRoomCanBook - lineid 為空，跳過黑名單檢查")
        
        # 是否要避開進出場時間（檢查是否有其它客人進出）
        # bMustCheckAvoidBlock = True
        bMustCheckAvoidBlock = False

        # 1. 驗證日期格式 (YYYY-MM-DD)
        date_str = date.strip()
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # 轉換為 YYYY/MM/DD 格式用於內部處理
            date_str = date_obj.strftime('%Y/%m/%d')
        except ValueError:
            return {'result': False, 'error': '日期格式錯誤，應為 YYYY-MM-DD'}
        
        # 2. 驗證時間格式
        time_str = time.strip()
        try:
            time_obj = datetime.strptime(time_str, '%H:%M')
        except ValueError:
            return {'result': False, 'error': '時間格式錯誤，應為 HH:MM'}
        
        # 3. 驗證客人數量和持續時間
        if guest < 1:
            return {'result': False, 'error': '客人數量必須大於 0'}
        
        if duration < 1:
            return {'result': False, 'error': '預約時長必須大於 0 分鐘'}
        
        # 4. 驗證並轉換店家ID（如果提供）
        store_id_to_check = None
        if storeid is not None:
            storeid = storeid.strip()
            if not storeid:
                return {'result': False, 'error': '店家ID不能為空'}
            store_id_to_check = storeid
        
        # 5. 獲取工作日管理器和任務管理器
        workday_manager = WorkdayManager()
        task_manager = TaskManager()
        
        # 6. 獲取該日期的房間狀態
        room_status_data = await run_in_executor(workday_manager.get_all_room_status, date_str)
        #顯示room_status_data 供 debug 
        print(room_status_data)

        if room_status_data is None:
            return {'result': False, 'error': '無法獲取該日期的房間狀態'}
        
        # 7. 計算需要的 block 數量
        # 每個 block 代表 5 分鐘
        duration_blocks = (duration + 4) // 5  # 向上取整
        
        # 8. 計算開始 block 索引
        start_block_index = await run_in_executor(task_manager.convert_time_to_block_index, time_str)
        
        # 9. 計算結束 block 索引
        end_block_index = start_block_index + duration_blocks
        
        # [調試信息]
        print(f"[DEBUG] 時間計算: start_block_index={start_block_index}, end_block_index={end_block_index}, duration_blocks={duration_blocks}")
        
        # 10. 檢查時間範圍是否超過 24 小時
        # block_len = 288 + 6 = 294 (288 個 block 代表 24 小時，再加 6 個 block 的緩衝)
        # end_block_index 應該小於 294（陣列長度）
        if end_block_index > 294:
            return {'result': False, 'error': '預約時間超過當日營業時間'}
        
        # 11. 如果指定了店家ID，只檢查該店家
        if store_id_to_check is not None:
            # 確保使用字符串鍵訪問字典
            if store_id_to_check not in room_status_data:
                return {'result': False, 'error': f'店家ID {store_id_to_check} 不存在'}
            
            store_data = room_status_data[store_id_to_check]
            free_blocks = store_data.get('free_blocks', [])
            
            # 檢查指定時間段內的可用房間數
            available_rooms = float('inf')
            for block_idx in range(start_block_index, end_block_index):
                if 0 <= block_idx < len(free_blocks):
                    available_rooms = min(available_rooms, free_blocks[block_idx])
                else:
                    available_rooms = 0
                    break
            
            # 檢查該店家是否有足夠的房間
            if available_rooms >= guest:
                if bMustCheckAvoidBlock:
                    print("檢查避免區塊中...")
                    all_avoid_block = await run_in_executor(workday_manager.get_all_task_avoid_block, date_str)
                    
                    # 驗證 all_avoid_block 的有效性
                    # 使用字符串鍵訪問，因為 Redis JSON 反序列化後鍵為字符串
                    if not all_avoid_block or store_id_to_check not in all_avoid_block:
                        print(f"錯誤: all_avoid_block 資料不完整或店家 {store_id_to_check} 不存在")
                        print(f"[DEBUG] all_avoid_block 鍵: {list(all_avoid_block.keys()) if all_avoid_block else 'None'}")
                        return {'result': False, 'error': f'無法檢查店家 {store_id_to_check} 的時段資料', 'store_id': store_id_to_check}
                    
                    store_avoid_blocks = all_avoid_block[store_id_to_check]
                    block_len = len(store_avoid_blocks)
                    
                    # 驗證索引範圍
                    if start_block_index < 0 or start_block_index >= block_len:
                        print(f"錯誤: 進場時間索引 {start_block_index} 超出範圍 (0-{block_len-1})")
                        return {'result': False, 'error': f'預約開始時間超出有效範圍', 'store_id': store_id_to_check}
                    
                    if end_block_index < 0 or end_block_index >= block_len:
                        print(f"錯誤: 出場時間索引 {end_block_index} 超出範圍 (0-{block_len-1})")
                        return {'result': False, 'error': f'預約結束時間超出有效範圍', 'store_id': store_id_to_check}
                    
                    #檢查進場時間
                    is_can_book = store_avoid_blocks[start_block_index]
                    if is_can_book:
                        print("進場時間可預約")
                        #檢查出場時間
                        is_can_book = store_avoid_blocks[end_block_index]
                        if is_can_book:
                            print("出場時間可預約")
                            return {'result': True, 'store_id': store_id_to_check}
                        else:
                            print("出場時間不可預約")
                            return {'result': False, 'error': f'店家 {store_id_to_check} 此時段有其它客人進出', 'store_id': store_id_to_check}
                    else:
                        print("進場時間不可預約")
                        return {'result': False, 'error': f'店家 {store_id_to_check} 此時段有其它客人進出', 'store_id': store_id_to_check}
                else: 
                    return {'result': True, 'store_id': store_id_to_check}
            else:
                return {'result': False, 'error': f'店家 {store_id_to_check} 沒有足夠的房間可以預約', 'store_id': store_id_to_check}
        
        # 12. 如果未指定店家ID，檢查所有店家
        for store_id, store_data in room_status_data.items():
            free_blocks = store_data.get('free_blocks', [])
            
            # 檢查指定時間段內的可用房間數
            available_rooms = float('inf')
            for block_idx in range(start_block_index, end_block_index):
                if 0 <= block_idx < len(free_blocks):
                    available_rooms = min(available_rooms, free_blocks[block_idx])
                else:
                    available_rooms = 0
                    break
            
            # 如果有任何一個店家有足夠的房間，就返回 true
            if available_rooms >= guest:
                return {'result': True, 'store_id': store_id}
        
        # 13. 如果沒有任何店家有足夠的房間，返回 false
        return {'result': False, 'error': '沒有足夠的房間可以預約'}
        
    except Exception as e:
        print(f"檢查房間預約時發生錯誤: {str(e)}")
        return {'result': False, 'error': f'檢查時發生錯誤: {str(e)}'}

@router.get("/checkStaffCanBook", summary="檢查可以提供服務的師傅")
async def check_staff_can_book(
    date: str = Query(..., description="預約日期，格式: YYYY-MM-DD"),
    time: str = Query(..., description="預約開始時間，格式: HH:MM"),
    guest: int = Query(..., description="客人數量（用於參數驗證，不在此API中使用）", ge=1),
    duration: int = Query(..., description="預約時長（分鐘）", ge=1),
    storeid: str = Query(None, description="店家ID（可選，用於篩選師傅所在的店家）"),
    lineid: str = Query(None, description="LINE 用戶 ID")
):
    """
    檢查指定日期時間段內有哪些師傅可以連續提供服務
    
    參數：
    - date: 預約日期（格式: YYYY-MM-DD）
    - time: 預約開始時間（格式: HH:MM）
    - guest: 客人數量（用於與 checkRoomCanBook 參數一致，此API中不使用）
    - duration: 預約時長（分鐘）
    - storeid: 店家ID（可選，若指定則只篩選該店家的師傅）
    - lineid: LINE 用戶 ID（用於超級黑名單檢查）
    
    返回：
    - result: true/false
    - available_staffs: 可提供服務的師傅列表，格式為 [{"name": "師傅名", "stores": [1, 2]}]
    - count: 可提供服務的師傅數量
    """
    try:
        # 0. 檢查是否為超級黑名單
        from core.blacklist import BlacklistManager
        blacklist_manager = BlacklistManager()
        
        # 添加日誌來跟蹤黑名單檢查
        print(f"[DEBUG] checkStaffCanBook - 檢查 lineid: {lineid}")
        if lineid:
            is_blacklisted = blacklist_manager.is_super_blacklist(lineid)
            print(f"[DEBUG] checkStaffCanBook - 黑名單檢查結果: {is_blacklisted}")
            if is_blacklisted:
                print(f"[DEBUG] checkStaffCanBook - {lineid} 是超級黑名單，返回 false")
                return {'result': False, 'available_staffs': []}
        else:
            print(f"[DEBUG] checkStaffCanBook - lineid 為空，跳過黑名單檢查")

        #檢查是否為師傅個加黑名單
        blacklist=[]
        if lineid:
            blacklist = blacklist_manager.getBlockedStaffsList(lineid)
        
        # 1. 驗證日期格式 (YYYY-MM-DD)
        date_str = date.strip()
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            # 轉換為 YYYY/MM/DD 格式用於內部處理
            date_str = date_obj.strftime('%Y/%m/%d')
        except ValueError:
            return {'result': False, 'error': '日期格式錯誤，應為 YYYY-MM-DD', 'available_staffs': []}
        
        # 2. 驗證時間格式
        time_str = time.strip()
        try:
            time_obj = datetime.strptime(time_str, '%H:%M')
        except ValueError:
            return {'result': False, 'error': '時間格式錯誤，應為 HH:MM', 'available_staffs': []}
        
        # 3. 驗證預約時長
        if duration < 1:
            return {'result': False, 'error': '預約時長必須大於 0 分鐘', 'available_staffs': []}
        
        # 4. 驗證並轉換店家ID（如果提供）
        store_id_filter = None
        if storeid is not None:
            storeid = storeid.strip()
            if storeid:
                try:
                    store_id_filter = int(storeid)
                except ValueError:
                    return {'result': False, 'error': '店家ID必須為有效的整數', 'available_staffs': []}
        
        # 5. 獲取工作日管理器和任務管理器
        workday_manager = WorkdayManager()
        task_manager = TaskManager()
        
        # 6. 獲取該日期的師傅工作狀態
        work_day_status = await run_in_executor(workday_manager.get_all_work_day_status, date_str)
        
        if work_day_status is None:
            return {'result': False, 'error': '無法獲取該日期的師傅工作狀態', 'available_staffs': []}
        
        # 7. 獲取該日期的師傅店家分佈
        staff_store_map = await run_in_executor(workday_manager.get_all_staff_store_map, date_str)
        
        if staff_store_map is None:
            return {'result': False, 'error': '無法獲取該日期的師傅店家分佈', 'available_staffs': []}
        
        # 8. 計算需要的 block 數量
        # 每個 block 代表 5 分鐘
        duration_blocks = (duration + 4) // 5  # 向上取整
        
        # 9. 計算開始 block 索引
        start_block_index = await run_in_executor(task_manager.convert_time_to_block_index, time_str)
        
        # 10. 計算結束 block 索引
        end_block_index = start_block_index + duration_blocks
        
        # 11. 檢查時間範圍是否超過 24 小時
        # block_len = 288 + 6 = 294 (288 個 block 代表 24 小時，再加 6 個 block 的緩衝)
        if end_block_index > 288:
            return {'result': False, 'error': '預約時間超過當日營業時間', 'available_staffs': []}
        
        # 12. 尋找可以連續提供服務的師傅
        available_staffs = []
        
        for staff_name, staff_data in work_day_status.items():
            freeblocks = staff_data.get('freeblocks', [])
            
            # 檢查該師傅在指定時間段內是否可以連續服務
            can_serve = True
            for block_idx in range(start_block_index, end_block_index):
                if 0 <= block_idx < len(freeblocks):
                    # 只有當 block 為 true（有排班且無工作）時才能服務
                    if not freeblocks[block_idx]:
                        can_serve = False
                        break
                else:
                    # 超出範圍
                    can_serve = False
                    break
            
            # 如果該師傅可以連續提供服務，進一步檢查店家分佈
            if can_serve:
                # 從師傅店家分佈中獲取該師傅的店家列表
                staff_info = staff_store_map.get(staff_name)
                
                if staff_info is None:
                    # 師傅不在店家分佈中，跳過
                    continue
                
                # 獲取師傅的店家列表，確保轉換為整數集合
                instores = staff_info.get('instores', [])
                
                # 處理多種 instores 格式：可能是字符串 "[1,2,3]"、列表 [1,2,3] 或其他
                instores_set = set()
                if isinstance(instores, str):
                    # 如果是字符串，嘗試解析為列表
                    try:
                        instores_list = json.loads(instores)
                        if isinstance(instores_list, list):
                            instores_set = set(int(s) for s in instores_list if s)
                    except (json.JSONDecodeError, ValueError, TypeError):
                        # 解析失敗，使用空集合
                        instores_set = set()
                elif isinstance(instores, list):
                    # 如果已經是列表，直接轉換為整數集合
                    instores_set = set(int(s) for s in instores if s)
                elif isinstance(instores, (set, tuple)):
                    # 如果是集合或元組，直接轉換
                    instores_set = set(int(s) for s in instores if s)
                
                # 如果指定了店家ID，檢查師傅是否在該店家
                if store_id_filter is not None:
                    if store_id_filter not in instores_set:
                        # 師傅不在指定的店家，跳過
                        continue
                
                # 檢查該師傅是否在用戶的黑名單中
                if lineid and staff_name in blacklist:
                    # 該師傅在黑名單中，跳過
                    print(f"[DEBUG] checkStaffCanBook - 師傅 {staff_name} 在用戶 {lineid} 的黑名單中，跳過")
                    continue

                # 該師傅符合所有條件，加入結果
                available_staffs.append({
                    'name': staff_name,
                    'stores': sorted(list(instores_set))
                })
        
        # 13. 返回結果
        if available_staffs:
            return {
                'result': True,
                'available_staffs': available_staffs,
                'count': len(available_staffs)
            }
        else:
            return {
                'result': False,
                'error': '沒有師傅可以在指定時間提供服務',
                'available_staffs': []
            }
        
    except Exception as e:
        print(f"檢查師傅可預約時發生錯誤: {str(e)}")
        return {'result': False, 'error': f'檢查時發生錯誤: {str(e)}', 'available_staffs': []}

