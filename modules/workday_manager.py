"""
Workday Manager Module
管理工作日相關功能
"""

from core.sch import ScheduleManager
from core.tasks import TaskManager
from core.store import StoreManager
from core import store
from core.staffs import StaffManager
from core.database import db_config
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import redis
import json
import re

class WorkdayManager:
    """工作日管理器"""
    
    def __init__(self):
        
        self.db_config = db_config
        """初始化工作日管理器"""
        self.staff_manager = StaffManager()
        self.sch_manager = ScheduleManager() 
        self.task_manager = TaskManager()
        self.store_manager = StoreManager()
    
    def get_workday_info(self):
        """取得工作日資訊"""
        pass
    
    def update_workday(self):
        """更新工作日"""
        pass

    def get_table_lastupdate_time(self, tablename: str) -> Optional[datetime]:
        """獲取Tasks表的最後更新時間"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT UPDATE_TIME 
                FROM information_schema.tables 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = %s
                """
            cursor.execute(query, (tablename,))
            result = cursor.fetchone()

            if result and result.get('UPDATE_TIME'):
                update_time = result['UPDATE_TIME']
                # 若為字串，嘗試轉換為 datetime
                if isinstance(update_time, str):
                    try:
                        update_time = datetime.fromisoformat(update_time)
                    except ValueError:
                        # fallback to common datetime format
                        update_time = datetime.strptime(update_time, '%Y-%m-%d %H:%M:%S')
                print(f"{tablename}最後更新時間: {update_time}")
                return update_time
            else:
                print( tablename + "最後更新時間: 無法獲取")
                return None

        finally:
            if connection.is_connected():
                cursor.close()
            connection.close()

        return

    def get_all_forcelocations(self, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        """取得 forcelocation 表的所有資料，返回 [{'staff_name': str, 'instores': [int,...]}, ...]"""
        if not date_str:
            date_str = datetime.now().date().isoformat()

        connection = self.db_config.get_connection()
        if not connection:
            return []
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT staff_name, instores, joindate FROM forcelocation WHERE DATE(joindate) = %s"
            cursor.execute(query, (date_str,))
            
            rows = cursor.fetchall()
            result = []
            for row in rows:
                staff_name = row.get('staff_name')
                instores_raw = row.get('instores')
                instores = []
                if instores_raw:
                    # 首選 JSON 解析（資料庫內為 JSON 字串，例如 "[1,2]")，不再嘗試逗號分隔備援
                    if isinstance(instores_raw, str):
                        try:
                            parsed = json.loads(instores_raw)
                            if isinstance(parsed, list):
                                instores = [int(x) for x in parsed if x is not None and x != '']
                            else:
                                instores = []
                        except Exception:
                            print(f"Warning: invalid JSON in forcelocation.instores for staff {staff_name}: {instores_raw}")
                            instores = []
                    elif isinstance(instores_raw, (list, tuple, set)):
                        instores = [int(x) for x in instores_raw if x is not None and x != '']
                    else:
                        try:
                            instores = [int(instores_raw)]
                        except Exception:
                            instores = []
                result.append({'staff_name': staff_name, 'instores': instores})
            return result
        except Exception as e:
            print(f"獲取forcelocation表資料錯誤: {e}")
            return []
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass
            connection.close()

    def get_all_task_avoid_block(self, check_date:str):
        try:

            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            
            query_date = re.sub('/','-', check_date)
            #redis_client.delete('avoid_block_' + query_date)
            cached_json = redis_client.get('avoid_block_' + query_date)         
            if cached_json:
                cached_info = json.loads(cached_json)
                cached_data = cached_info.get('data')
                cached_update_time = cached_info.get('update_time') #需轉換為datetime物件
                if cached_update_time:
                    cached_update_time = datetime.fromisoformat(cached_update_time)
            else:
                cached_data = None
                cached_update_time = None
            
            # 獲取資料庫最後更新時間
            db_store_update_time = self.store_manager.get_store_table_lastupdate_time()
            db_tasks_update_time = self.task_manager.get_tasks_table_lastupdate_time()

            # 判斷是否需要更新緩存
            need_update = False
            
            if not cached_data or not cached_update_time:
                need_update = True
            else:
                #比較2個表單更的時間表，若任何一個比 cached_update_time 新，則需要更新緩存
                if (db_store_update_time and db_store_update_time > cached_update_time) or \
                   (db_tasks_update_time and db_tasks_update_time > cached_update_time):
                    need_update = True

            #不需更新資料，直接返回緩存數據
            if not need_update:
                print("✅ avoid_block 資料，使用緩存資料")
                return cached_data
            
            print("🔄 avoid_block 資料，重新從資料庫重新獲取")
            block_len= 288 +6  
            result = {
                'update_time': datetime.now().isoformat(),  #現在時間
                'data': {}
                }         
            #預設當天,所有店家 的 288+6個block都是free
            all_stores = self.store_manager.get_all_stores()
            for storex in all_stores:
                storeid=storex.get('id')
                # 統一使用字符串作為鍵，避免 Redis JSON 序列化問題
                result['data'][str(storeid)] = [True] * block_len

            #取得當日所有tasks的工作
            all_tasks = self.task_manager.get_tasks_by_date(check_date)
            #取出storeid 及 start and end 時間
            for task in all_tasks:
                storeid=task.get('storeid')
                start_time=task.get('start')  # ✅ 使用 'start' 而不是 'start_time'
                end_time=task.get('end')      # ✅ 使用 'end' 而不是 'end_time'
                
                # 驗證時間字符串是否存在
                if not start_time or not end_time:
                    print(f"警告：Task 缺少時間信息 - storeid: {storeid}, start_time: {start_time}, end_time: {end_time}")
                    continue
                
                # 驗證 storeid 是否存在於 result['data'] 中
                # 統一使用字符串鍵
                storeid_key = str(storeid)
                if storeid_key not in result['data']:
                    print(f"警告：Store ID {storeid} 不在結果中，跳過此 task")
                    continue
                
                #轉換為實際block index 位置（確保傳遞 is_end_time 參數）
                try:
                    index_block_start = self.task_manager.convert_time_to_block_index(start_time, is_end_time=False)
                    index_block_end = self.task_manager.convert_time_to_block_index(end_time, is_end_time=True)
                except Exception as e:
                    print(f"錯誤：無法轉換時間字符串 - start_time: {start_time}, end_time: {end_time}, 錯誤: {e}")
                    continue
                
                # 安全地設置 block 值，檢查邊界
                block_len = 294  # 288 + 6
                for offset in [1, 0, -1, -2]:
                    idx = index_block_start + offset
                    if 0 <= idx < block_len:
                        result['data'][storeid_key][idx] = False
                
                for offset in [1, 0, -1, -2]:
                    idx = index_block_end + offset
                    if 0 <= idx < block_len:
                        result['data'][storeid_key][idx] = False

            # 將資料存放在 redis 上
            redis_client.set('avoid_block_' + query_date, json.dumps(result, ensure_ascii=False))
            
            return result['data']

        except Exception as e:
            print(f"獲取avoid_block狀態錯誤: {e}")
            return None

    def get_all_avoid_block_by_storeid(self, store_id: int, check_date: str):
        all_task_avoid_block=self.get_all_task_avoid_block(check_date)
        #找出符合storeid的avoid_block
        store_key= str(store_id)
        store_avoid_block = all_task_avoid_block.get(store_key, [])
        # 由第一個到最後一個 block 的狀態列表，若為 False 則轉成時間字串，置入新的集合中
        avoid_block = []
        # 安全遍歷：若 store_avoid_block 長度不足則跳過對應 index
        for i in range(288):
            if i < len(store_avoid_block) and store_avoid_block[i] == False:
                # Convert block index to time string
                # 第0個時間為00:00 第一個block為00:05 第2個block為00:10
                time_str = f"{(i * 5) // 60:02d}:{(i * 5) % 60:02d}"
                avoid_block.append(time_str)
        print(f"avoid_block: {avoid_block}")
        return avoid_block

    def get_all_staff_store_map(self, check_date:str):
        #參考其它function, 先取得在redis上資料再比對Staffs及Tasks兩張表格最後更新時間點，決定是否要實際由資料庫更新資料
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            
            query_date = re.sub('/','-', check_date)
            #在debug階段先清除redis staff_store_XXX 資料
            #redis_client.delete('staff_store_' + query_date)
            
            cached_json = redis_client.get('staff_store_' + query_date)         
            if cached_json:
                cached_info = json.loads(cached_json)
                cached_data = cached_info.get('data')
                cached_update_time = cached_info.get('update_time') #需轉換為datetime物件
                if cached_update_time:
                    cached_update_time = datetime.fromisoformat(cached_update_time)
            else:
                cached_data = None
                cached_update_time = None
            
            # 獲取資料庫最後更新時間
            db_satffs_update_time = self.staff_manager.get_staffs_table_lastupdate_time()
            db_tasks_update_time = self.task_manager.get_tasks_table_lastupdate_time()
            db_forcelocation_update_time = self.get_table_lastupdate_time("forcelocation")

            # 判斷是否需要更新緩存
            need_update = False
            
            if not cached_data or not cached_update_time:
                need_update = True
            else:
                #比較2個表單更的時間表，若任何一個比 cached_update_time 新，則需要更新緩存
                if (db_satffs_update_time and db_satffs_update_time > cached_update_time) or \
                   (db_tasks_update_time and db_tasks_update_time > cached_update_time) or \
                   (db_forcelocation_update_time and db_forcelocation_update_time > cached_update_time):
                    need_update = True

            #不需更新資料，直接返回緩存數據
            if not need_update:
                print("✅ staff_store 資料，使用緩存資料")
                return cached_data

            print("🔄 staff_store 資料，重新從資料庫重新獲取")
            all_staffs = self.staff_manager.get_all_staffs()
            #取得當天所有的tasks資料
            all_tasks = self.task_manager.get_tasks_by_date(check_date) 
            #取得每一個tasks裡的 storeid 和staff_name , 將 all_staffs裡的 instores值
            #例如原本川為 [1,2,3] 因為 tasks裡的storeid =1 所以川的instores值會變為 [1] 單一一間
            
            # 建立師傅名字到店家ID集合的映射
            staff_store_map = {}
            for task in all_tasks:
                staff_name = task.get('staff_name')
                store_id = task.get('storeid')
                
                # 確保 staff_name 和 store_id 都存在
                if staff_name and store_id is not None:
                    if staff_name not in staff_store_map:
                        staff_store_map[staff_name] = set()
                    # 將 store_id 轉換為整數並添加到集合中
                    staff_store_map[staff_name].add(int(store_id))
            
            # 更新 all_staffs 中每個師傅的 instores 值
            result = {
                'update_time': datetime.now().isoformat(),
                'data': {}
            }
            
            for staff in all_staffs:
                staff_name = staff['name']
                
                # 如果該師傅在當天有任務，則 instores 值更新為任務所在的店家ID列表
                if staff_name in staff_store_map:
                    staff['instores'] = sorted(list(staff_store_map[staff_name]))
                # 否則保持原有的 instores 值
                # (不修改staff['instores']，保留從Staffs表查詢的原始值)
                
                result['data'][staff_name] = staff

            #由forcelocation表更新資料
            all_forcelocations = self.get_all_forcelocations()
            for forcelocation in all_forcelocations:
                staff_name = forcelocation.get('staff_name')
                # 將 instores 值強制取代為 forcelocation 中的值（get_all_forcelocations 已回傳解析好的 int 列表）
                if staff_name in result['data']:
                    instores = forcelocation.get('instores', [])
                    try:
                        instores_list = [int(x) for x in instores if x is not None and x != '']
                    except Exception:
                        instores_list = []
                    # 去重並排序
                    result['data'][staff_name]['instores'] = sorted(list(set(instores_list)))

            
            # 將資料存放在 redis 上
            redis_client.set('staff_store_' + query_date, json.dumps(result, ensure_ascii=False))
            
            return result['data']

        except Exception as e:
            print(f"獲取staff_store狀態錯誤: {e}")
            return None

    def get_all_work_day_status(self, check_date:str):
        #在redis上以work_data存放，在調用redis資料前，檢查相關的表單有沒有更新，若有更新則由資料庫由重取，若沒有任何更新，則由redis由的work_data提取
        #判斷 Staffs，Tasks， sch 三張表單的最後更新時間，若有任何一個表單時間有更新，則必需對work_data做更新
        """獲取指定日期所有師傅的24小時班表 (00:00-24:00，5分鐘間隔),再多加30分鐘緩衝 ÷6""" 
        block_len= 288 +6  
        result = {
                'update_time': datetime.now().isoformat(),  #現在時間
                'data': {}
            }
        
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            
            query_date = re.sub('/','-', check_date)

            cached_json = redis_client.get('work_data_' + query_date)         
            if cached_json:
                cached_info = json.loads(cached_json)
                cached_data = cached_info.get('data')
                cached_update_time = cached_info.get('update_time') #需轉換為datetime物件
                if cached_update_time:
                    cached_update_time = datetime.fromisoformat(cached_update_time)
            else:
                cached_data = None
                cached_update_time = None
            
            # 獲取資料庫最後更新時間
            db_satffs_update_time = self.staff_manager.get_staffs_table_lastupdate_time()
            db_sch_update_time = self.sch_manager.get_sch_table_lastupdate_time()
            db_tasks_update_time = self.task_manager.get_tasks_table_lastupdate_time()

            # 判斷是否需要更新緩存
            need_update = False
            
            if not cached_data or not cached_update_time:
                need_update = True
            else:
                #比較三個表單更的時間表，若任何一個比 cached_update_time 新，則需要更新緩存
                if (db_satffs_update_time and db_satffs_update_time > cached_update_time) or \
                   (db_sch_update_time and db_sch_update_time > cached_update_time) or \
                   (db_tasks_update_time and db_tasks_update_time > cached_update_time):
                    need_update = True

            #不需更新資料，直接返回緩存數據
            if not need_update:
                print("✅ work_day 資料，使用緩存資料")
                return cached_data

            print("🔄 work_day 資料，重新從資料庫重新獲取")
            #進行資料更新
            #由staffs模組的StaffManager取得所有員工資料
            
            all_staffs = self.staff_manager.get_all_staffs()
            #取得當天所有人的排班情況
            sch_data = self.sch_manager.get_schedule_block_by_date_24H(check_date)
            #取得當天所有人的工作情況
            tasks_data = self.task_manager.get_tasks_block_by_date_24H(check_date)
            #整合 sch_data 和 tasks_data 生成 work_data,規則為：比對288+6個block，只有當 sch_data 的block 為 true(有排班) 且 tasks_data 的block為false（無工作)時，work_data的block才為True(可安排客人)，其它情況皆為 False

            for staff in all_staffs:
                staff_name = staff['name']     
                #由staff_name 取得 sch_data中資料
                sch_staff_data = sch_data['staffs'].get(staff_name, {})
                tasks_staff_data = tasks_data['staffs'].get(staff_name, {})
                work_data_blocks = []
                for sch_block, task_block in zip(sch_staff_data.get('schedule', []), tasks_staff_data.get('tasks', [])):
                    work_data_blocks.append(sch_block and not task_block)

                #結果檢查，若work_data_blocks全為False，則不加入結果, 並將 staff_name 從結果中移除
                if any(work_data_blocks):
                    # 將結果存入work_data
                    result['data'][staff_name] = {
                        'freeblocks': work_data_blocks
                    }
                else:
                    # 不加入結果，將 staff_name 從結果中移除
                    if staff_name in result['data']:
                        del result['data'][staff_name]
            
            #將資料存放redis上
            redis_client.set('work_data_' + query_date, json.dumps(result, ensure_ascii=False))
        
            return result['data']

        except Exception as e:
            print(f"獲取工作日狀態錯誤: {e}")
            return None

    #取得當日288+6個block,每一個分店房間可以使用的數量
    def get_all_room_status(self, check_date):
        #在redis上以work_data存放，在調用redis資料前，檢查相關的表單有沒有更新，若有更新則由資料庫由重取，若沒有任何更新，則由redis由的work_data提取
        #判斷 Staffs，Tasks， sch 三張表單的最後更新時間，若有任何一個表單時間有更新，則必需對work_data做更新
        """獲取指定日期所有師傅的24小時班表 (00:00-24:00，5分鐘間隔),再多加30分鐘緩衝 ÷6""" 
        block_len= 288 +6  

        
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            
            # 從Redis獲取緩存數據
            # staffs_data為一個json格式，其中包含 update_time 和 data
            #轉換時間字串格式
            query_date = re.sub('/','-', check_date)


            cached_json = redis_client.get('room_status_' + query_date)         
            if cached_json:
                cached_info = json.loads(cached_json)
                cached_data = cached_info.get('data')
                cached_update_time = cached_info.get('update_time') #需轉換為datetime物件
                if cached_update_time:
                    cached_update_time = datetime.fromisoformat(cached_update_time)
            else:
                cached_data = None
                cached_update_time = None
            
            # 獲取資料庫最後更新時間
            db_store_update_time = self.store_manager.get_store_table_lastupdate_time()
            db_tasks_update_time = self.task_manager.get_tasks_table_lastupdate_time()

            # 判斷是否需要更新緩存
            need_update = False
            
            if not cached_data or not cached_update_time:
                print("需要由資料庫更新")
                need_update = True
            else:
                #比較三個表單更的時間表，若任何一個比 cached_update_time 新，則需要更新緩存
                if (db_store_update_time and db_store_update_time > cached_update_time) or \
                   (db_tasks_update_time and db_tasks_update_time > cached_update_time):
                    print("需要由資料庫更新")
                    need_update = True

            #不需更新資料，直接返回緩存數據
            if not need_update:
                print("不需要更新，直接返回緩存數據")
                return cached_data

            #進行資料更新
            #由staffs模組的StaffManager取得所有員工資料
            
            all_stores = self.store_manager.get_all_stores()
            result = {
                'update_time': datetime.now().isoformat(),  #現在時間
                'data': {}
            }
            #將回傳資料初始化為每間店家，最大的房間數量
            for store in all_stores:
                # 統一使用字符串作為鍵，避免 Redis JSON 序列化問題
                result['data'][str(store['id'])] = {
                    'store_name': store['name'],
                    'free_blocks': [int(store['rooms'])] * block_len #為初始資料                             
                }
            
            store_occupied_status = self.store_manager.get_store_occupied_block_by_date_24H(query_date)
            #將每個block 減去己佔用的數量為最終結果
            for store_id, store_data in result['data'].items():
                #原有可以使用的數量 減去佔用數量
                # store_occupied_status['data'] 的 key 是整數，直接使用 store_id
                occupied_blocks = store_occupied_status['data'].get(store_id, {}).get('blocks', [0] * block_len)
                free_blocks = store_data['free_blocks']
                # 計算每個block的剩餘可用數量
                result['data'][store_id]['free_blocks'] = [max(free - occupied, 0) for free, occupied in zip(free_blocks, occupied_blocks)]

            #將資料存放在 redis 上
            redis_client.set('room_status_' + query_date, json.dumps(result))

            return result['data']

        except Exception as e:
            print(f"獲取工作日狀態錯誤: {e}")
            return None   
        
    def get_freeblock(self, check_date:str, staff_name:str, start_time:str, blockcount:int)-> list:
        all_workday=self.get_all_work_day_status(check_date)
        #計算出開始的block index
        iStart = self.task_manager.convert_time_to_block_index(start_time)
        #在all_workday中取出staff_name的班表情況
        if all_workday and staff_name in all_workday:
            staff_info = all_workday[staff_name]
            freeblocks_data = staff_info.get('freeblocks', [])
            #由 iStart 開始取 blockcount 個 ，到新array
            free_blocks = freeblocks_data[iStart:iStart+blockcount]
            return free_blocks
        return None