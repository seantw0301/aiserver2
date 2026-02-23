"""
師傅可用性檢查改進版 - 使用預先計算可用性矩陣
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
from database import db_config


class MasseurAvailabilityMatrix:
    """
    師傅可用性矩陣類
    
    使用預先計算的矩陣來加速師傅可用性檢查，大幅減少數據庫查詢次數和計算量。
    """
    
    def __init__(self):
        """初始化函數"""
        self.db_config = db_config
        # 用於存儲計算好的可用性矩陣
        self.cache = {}
    
    def check_masseur_availability(self, store_id: int, date_str: str, 
                                  start_time: str, duration_minutes: int,
                                  masseur_names: List[str], guest_count: int) -> Dict:
        """
        使用可用性矩陣檢查師傅可用性
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串
            start_time: 開始時間
            duration_minutes: 持續時間
            masseur_names: 指定的師傅名單
            guest_count: 客人數量
            
        Returns:
            Dict: 師傅可用性結果
        """
        # 初始化結果字典
        result = {
            'requested_masseurs': masseur_names,
            'guest_count': guest_count,
            'available_masseurs': [],
            'unavailable_masseurs': [],
            'alternative_masseurs': [],
            'sufficient_masseurs': False,
            'message': ''
        }
        
        # 獲取或創建可用性矩陣
        availability_matrix = self._get_availability_matrix(store_id, date_str)
        
        # 計算需要的時間段
        time_slots = self._get_time_slots_for_duration(start_time, duration_minutes)
        
        # 檢查每個指定師傅的可用性
        for masseur_name in masseur_names:
            if masseur_name in availability_matrix:
                # 檢查該師傅在所有需要的時間段是否都可用
                is_available = self._check_masseur_available_in_time_slots(
                    availability_matrix, masseur_name, time_slots
                )
                
                if is_available:
                    # 師傅可用，添加到可用列表
                    result['available_masseurs'].append(masseur_name)
                else:
                    # 師傅不可用，尋找替代時間
                    alternative_time = self._find_alternative_time(
                        availability_matrix, masseur_name, start_time, duration_minutes
                    )
                    
                    if alternative_time:
                        # 找到替代時間
                        result['unavailable_masseurs'].append([masseur_name, alternative_time])
                    else:
                        # 無替代時間
                        result['unavailable_masseurs'].append([masseur_name, None])
            else:
                # 師傅不存在於矩陣中，視為不可用
                result['unavailable_masseurs'].append([masseur_name, None])
        
        # 檢查是否有足夠的師傅
        available_count = len(result['available_masseurs'])
        result['sufficient_masseurs'] = available_count >= guest_count
        
        return result
    
    def _get_availability_matrix(self, store_id: int, date_str: str) -> Dict:
        """
        獲取或創建可用性矩陣
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串
            
        Returns:
            Dict: 可用性矩陣
        """
        # 檢查快取中是否已存在
        cache_key = f"{store_id}_{date_str}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # 創建新的可用性矩陣
        matrix = self._build_availability_matrix(store_id, date_str)
        
        # 存入快取
        self.cache[cache_key] = matrix
        
        return matrix
    
    def _build_availability_matrix(self, store_id: int, date_str: str) -> Dict:
        """
        構建可用性矩陣
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串
            
        Returns:
            Dict: 可用性矩陣，格式為 {
                "masseur_name": {
                    "10:00": True,  # True表示可用，False表示不可用
                    "10:10": True,
                    ...
                },
                ...
            }
        """
        # 定義營業時間範圍
        start_time = "10:00"
        end_time = "22:30"
        
        # 生成時間段列表（每10分鐘一個時段）
        time_slots = []
        current_time = datetime.strptime(start_time, "%H:%M")
        end_datetime = datetime.strptime(end_time, "%H:%M")
        
        while current_time <= end_datetime:
            time_slots.append(current_time.strftime("%H:%M"))
            current_time += timedelta(minutes=10)
        
        # 獲取該店家的所有師傅
        all_masseurs = self._get_all_masseurs_by_store(store_id)
        
        # 初始化可用性矩陣（預設所有時間段都可用）
        matrix = {}
        for masseur in all_masseurs:
            matrix[masseur] = {time_slot: True for time_slot in time_slots}
        
        # 步驟1: 根據師傅班表更新可用性矩陣
        for masseur in all_masseurs:
            # 獲取師傅的班表
            schedule = self._get_masseur_schedule(masseur, date_str)
            
            # 如果有班表數據，根據班表更新可用性
            if schedule and 'schedule' in schedule:
                schedule_blocks = schedule['schedule']
                
                for time_slot in time_slots:
                    # 將時間轉換為從00:00開始的分鐘數，以匹配班表索引
                    time_obj = datetime.strptime(time_slot, "%H:%M")
                    minutes = time_obj.hour * 60 + time_obj.minute
                    block_index = minutes // 5  # 班表是每5分鐘一個塊
                    
                    # 如果該時間段師傅不在班，或者block_index超出範圍，標記為不可用
                    if block_index >= len(schedule_blocks) or not schedule_blocks[block_index]:
                        matrix[masseur][time_slot] = False
            else:
                # 如果師傅當天沒有班表數據，將所有時間段標記為不可用
                for time_slot in time_slots:
                    matrix[masseur][time_slot] = False
        
        # 步驟2: 獲取所有任務並更新可用性矩陣
        tasks = self._get_all_tasks_by_date_and_store(date_str, store_id)
        
        # 根據任務更新可用性矩陣
        for task in tasks:
            masseur_name = task.get('staff_name')
            if masseur_name and masseur_name in matrix:
                # 獲取任務開始和結束時間
                task_start = task.get('start')
                task_end = task.get('end')
                
                if task_start and task_end:
                    # 解析任務時間
                    task_start_dt = datetime.strptime(task_start, "%Y-%m-%d %H:%M:%S")
                    task_end_dt = datetime.strptime(task_end, "%Y-%m-%d %H:%M:%S")
                    
                    # 更新矩陣中的可用性
                    for time_slot in time_slots:
                        # 將時間段轉換為當天的datetime
                        slot_dt = datetime.strptime(f"{date_str} {time_slot}", "%Y/%m/%d %H:%M")
                        
                        # 如果時間段在任務時間內，標記為不可用
                        if task_start_dt <= slot_dt < task_end_dt:
                            matrix[masseur_name][time_slot] = False
        
        return matrix
    
    def _get_all_masseurs_by_store(self, store_id: int) -> List[str]:
        """
        獲取指定店家的所有師傅
        
        Args:
            store_id: 店家ID
            
        Returns:
            List[str]: 師傅名稱列表
        """
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT name 
                FROM Staffs 
                WHERE storeid = %s AND enable = 1
                ORDER BY name
            """
            cursor.execute(query, (store_id,))
            results = cursor.fetchall()
            
            return [staff['name'] for staff in results]
            
        except Exception as e:
            print(f"獲取店家師傅列表錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def _get_all_tasks_by_date_and_store(self, date_str: str, store_id: int) -> List[Dict]:
        """
        獲取指定日期和店家的所有任務
        
        Args:
            date_str: 日期字符串，格式為 "YYYY/MM/DD"
            store_id: 店家ID
            
        Returns:
            List[Dict]: 任務列表
        """
        # 將日期格式轉換為數據庫格式
        db_date = date_str.replace('/', '-')
        
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, start, end, staff_name, customer, project, count, remark, storeid
                FROM Tasks
                WHERE DATE(start) = %s AND storeid = %s
            """
            cursor.execute(query, (db_date, store_id))
            tasks = cursor.fetchall()
            
            return tasks
            
        except Exception as e:
            print(f"獲取任務列表錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def _get_masseur_schedule(self, masseur_name: str, date_str: str) -> Optional[Dict]:
        """
        獲取師傅的班表
        
        Args:
            masseur_name: 師傅名稱
            date_str: 日期字符串 (YYYY/MM/DD)
            
        Returns:
            Optional[Dict]: 班表數據，如果沒有則返回None
        """
        from sch import ScheduleManager
        
        try:
            schedule_manager = ScheduleManager()
            schedule = schedule_manager.get_schedule_by_name(masseur_name, date_str, include_tasks=True)
            return schedule
        except Exception as e:
            print(f"獲取師傅班表錯誤: {e}")
            return None
    
    def _get_time_slots_for_duration(self, start_time: str, duration_minutes: int) -> List[str]:
        """
        獲取指定開始時間和持續時間內的所有時間段
        
        Args:
            start_time: 開始時間，格式為 "HH:MM"
            duration_minutes: 持續時間（分鐘）
            
        Returns:
            List[str]: 時間段列表
        """
        time_slots = []
        current_time = datetime.strptime(start_time, "%H:%M")
        end_time = current_time + timedelta(minutes=duration_minutes)
        
        while current_time < end_time:
            time_slots.append(current_time.strftime("%H:%M"))
            current_time += timedelta(minutes=10)
        
        return time_slots
    
    def _check_masseur_available_in_time_slots(self, matrix: Dict, 
                                              masseur_name: str, 
                                              time_slots: List[str]) -> bool:
        """
        檢查師傅在指定時間段內是否都可用
        
        Args:
            matrix: 可用性矩陣
            masseur_name: 師傅名稱
            time_slots: 時間段列表
            
        Returns:
            bool: 是否都可用
        """
        if masseur_name not in matrix:
            return False
        
        for time_slot in time_slots:
            # 若時間段不在矩陣中或師傅在該時間段不可用，返回False
            if time_slot not in matrix[masseur_name] or not matrix[masseur_name][time_slot]:
                return False
        
        return True
    
    def _find_alternative_time(self, matrix: Dict, masseur_name: str, 
                              start_time: str, duration_minutes: int) -> Optional[str]:
        """
        查找師傅的替代可用時間
        
        Args:
            matrix: 可用性矩陣
            masseur_name: 師傅名稱
            start_time: 開始時間
            duration_minutes: 持續時間
            
        Returns:
            Optional[str]: 替代時間，如果找不到則返回None
        """
        if masseur_name not in matrix:
            return None
        
        # 從開始時間後10分鐘開始查找
        current_time = datetime.strptime(start_time, "%H:%M") + timedelta(minutes=10)
        end_time = datetime.strptime("22:30", "%H:%M")
        
        while current_time < end_time:
            current_time_str = current_time.strftime("%H:%M")
            
            # 檢查從current_time開始的時間段是否都可用
            time_slots = self._get_time_slots_for_duration(current_time_str, duration_minutes)
            is_available = self._check_masseur_available_in_time_slots(matrix, masseur_name, time_slots)
            
            if is_available:
                return current_time_str
            
            # 向後移動10分鐘
            current_time += timedelta(minutes=10)
        
        return None
    
    def clear_cache(self):
        """清除快取"""
        self.cache = {}


def create_test_example():
    """
    創建測試範例代碼
    
    示範如何使用MasseurAvailabilityMatrix類
    """
    # 範例代碼
    example_code = """
# 範例：如何在common.py中使用MasseurAvailabilityMatrix類

from masseur_availability_improved import MasseurAvailabilityMatrix

def query_available_appointment(self, query_data: Dict) -> Dict:
    # ... 原有代碼 ...
    
    # 現有的代碼獲取店家ID、日期等信息
    store_id = ...
    date_str = query_data['date']
    available_time = ...
    total_duration = ...  # 包含緩衝時間
    masseur_names = query_data.get('masseur', [])
    guest_count = query_data['count']
    
    # 創建矩陣檢查器實例（建議在RoomStatusManager初始化時創建一個實例並重複使用）
    masseur_matrix = MasseurAvailabilityMatrix()
    
    # 使用矩陣方法檢查師傅可用性
    masseur_availability_result = masseur_matrix.check_masseur_availability(
        store_id=store_id,
        date_str=date_str,
        start_time=available_time,
        duration_minutes=total_duration,
        masseur_names=masseur_names,
        guest_count=guest_count
    )
    
    # ... 後續處理與原來相同 ...
"""
    
    return example_code


# 性能測試代碼
def performance_test_code():
    """
    創建性能測試代碼
    
    用於比較原始方法和改進方法的性能差異
    """
    # 性能測試代碼
    test_code = """
# test_masseur_availability.py
# 用於測試原始方法和矩陣方法的性能差異

import time
from common import RoomStatusManager
from masseur_availability_improved import MasseurAvailabilityMatrix

def run_performance_test():
    # 測試參數
    store_id = 1  # 西門店
    date_str = "2025/08/21"
    start_time = "14:00"
    duration_minutes = 90
    masseur_names = ["遠", "川", "豪", "隆"]
    guest_count = 2
    
    # 創建測試對象
    room_manager = RoomStatusManager()
    matrix_checker = MasseurAvailabilityMatrix()
    
    # 測試原始方法
    print("測試原始方法...")
    start = time.time()
    for i in range(5):  # 執行5次以獲得更準確的測量
        result_original = room_manager._check_masseur_availability_improved(
            store_id=store_id,
            date_str=date_str,
            start_time=start_time,
            duration_minutes=duration_minutes,
            masseur_names=masseur_names,
            guest_count=guest_count
        )
    end = time.time()
    original_time = end - start
    print(f"原始方法耗時: {original_time:.4f}秒")
    
    # 測試矩陣方法
    print("測試矩陣方法...")
    start = time.time()
    for i in range(5):  # 執行5次以獲得更準確的測量
        result_matrix = matrix_checker.check_masseur_availability(
            store_id=store_id,
            date_str=date_str,
            start_time=start_time,
            duration_minutes=duration_minutes,
            masseur_names=masseur_names,
            guest_count=guest_count
        )
    end = time.time()
    matrix_time = end - start
    print(f"矩陣方法耗時: {matrix_time:.4f}秒")
    
    # 計算加速比
    speedup = original_time / matrix_time
    print(f"加速比: {speedup:.2f}倍")
    
    # 檢查結果是否一致
    print("檢查結果一致性...")
    print(f"原始方法可約師傅: {result_original['available_masseurs']}")
    print(f"矩陣方法可約師傅: {result_matrix['available_masseurs']}")
    print(f"結果一致: {set(result_original['available_masseurs']) == set(result_matrix['available_masseurs'])}")

if __name__ == "__main__":
    run_performance_test()
"""
    
    return test_code


# 整合建議
def integration_guide():
    """
    提供整合建議
    """
    guide = """
## 整合指南

要將MasseurAvailabilityMatrix整合到現有系統中，建議採取以下步驟：

1. 添加新類：
   - 將MasseurAvailabilityMatrix類添加到專案中
   - 不修改現有的_check_masseur_availability_improved方法

2. 在RoomStatusManager中添加實例：
   ```python
   def __init__(self):
       # 現有代碼...
       self.masseur_matrix = MasseurAvailabilityMatrix()
   ```

3. 修改query_available_appointment方法：
   ```python
   # 找到使用_check_masseur_availability_improved的地方
   masseur_availability_result = self.masseur_matrix.check_masseur_availability(
       store_id=store_id,
       date_str=date_str,
       start_time=available_time,
       duration_minutes=total_duration,
       masseur_names=masseur_names,
       guest_count=guest_count
   )
   ```

4. 緩存管理：
   - 在適當的時候清除緩存，例如當有新的預約添加時
   ```python
   # 例如在添加新預約後
   self.masseur_matrix.clear_cache()
   ```

5. 逐步整合：
   - 先在非關鍵流程中使用
   - 測試性能和結果正確性
   - 確認無誤後全面替換

預期效能提升：50%-90%，特別是在高峰期和連續查詢時。
"""
    
    return guide
