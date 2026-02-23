"""
師傅可用性檢查改進版 - 使用預先計算可用性矩陣 + 平行處理
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from database import db_config
import concurrent.futures
from masseur_availability_improved import MasseurAvailabilityMatrix


class ParallelMasseurAvailabilityMatrix(MasseurAvailabilityMatrix):
    """
    師傅可用性矩陣類 - 平行處理版
    
    繼承自MasseurAvailabilityMatrix，添加平行處理功能以加速多師傅檢查。
    """
    
    def __init__(self, max_workers=None):
        """
        初始化函數
        
        Args:
            max_workers: 最大工作線程數，預設為None（使用系統預設值）
        """
        super().__init__()
        self.max_workers = max_workers
    
    def check_masseur_availability(self, store_id: int, date_str: str, 
                                  start_time: str, duration_minutes: int,
                                  masseur_names: List[str], guest_count: int) -> Dict:
        """
        使用可用性矩陣檢查師傅可用性（平行處理版）
        
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
        
        # 如果沒有指定師傅，直接返回結果
        if not masseur_names:
            result['sufficient_masseurs'] = False
            result['message'] = '未指定師傅'
            return result
        
        # 獲取或創建可用性矩陣
        availability_matrix = self._get_availability_matrix(store_id, date_str)
        
        # 計算需要的時間段
        time_slots = self._get_time_slots_for_duration(start_time, duration_minutes)
        
        # 使用平行處理檢查每個師傅的可用性
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 創建任務列表，每個任務處理一位師傅
            future_to_masseur = {
                executor.submit(
                    self._check_masseur_availability_parallel, 
                    availability_matrix, 
                    masseur_name, 
                    time_slots,
                    start_time,
                    duration_minutes
                ): masseur_name for masseur_name in masseur_names
            }
            
            # 收集結果
            for future in concurrent.futures.as_completed(future_to_masseur):
                masseur_name = future_to_masseur[future]
                try:
                    is_available, alternative_time = future.result()
                    
                    if is_available:
                        # 師傅可用，添加到可用列表
                        result['available_masseurs'].append(masseur_name)
                    else:
                        # 師傅不可用
                        result['unavailable_masseurs'].append([masseur_name, alternative_time])
                except Exception as e:
                    print(f"處理師傅 {masseur_name} 時發生錯誤: {e}")
                    # 發生錯誤時，將師傅視為不可用
                    result['unavailable_masseurs'].append([masseur_name, None])
        
        # 檢查是否有足夠的師傅
        available_count = len(result['available_masseurs'])
        result['sufficient_masseurs'] = available_count >= guest_count
        
        return result
    
    def _check_masseur_availability_parallel(self, matrix: Dict, 
                                           masseur_name: str, 
                                           time_slots: List[str],
                                           start_time: str,
                                           duration_minutes: int) -> Tuple[bool, Optional[str]]:
        """
        平行處理版本的師傅可用性檢查
        
        Args:
            matrix: 可用性矩陣
            masseur_name: 師傅名稱
            time_slots: 時間段列表
            start_time: 開始時間
            duration_minutes: 持續時間
            
        Returns:
            Tuple[bool, Optional[str]]: (是否可用, 替代時間)
        """
        # 檢查師傅是否存在
        if masseur_name not in matrix:
            return False, None
        
        # 檢查師傅在指定時間段是否可用
        is_available = True
        for time_slot in time_slots:
            if time_slot not in matrix[masseur_name] or not matrix[masseur_name][time_slot]:
                is_available = False
                break
        
        # 如果不可用，尋找替代時間
        alternative_time = None
        if not is_available:
            alternative_time = self._find_alternative_time(matrix, masseur_name, start_time, duration_minutes)
        
        return is_available, alternative_time


def create_test_example():
    """
    創建測試範例代碼
    
    示範如何使用ParallelMasseurAvailabilityMatrix類
    """
    # 範例代碼
    example_code = """
# 範例：如何在common.py中使用ParallelMasseurAvailabilityMatrix類

from masseur_availability_parallel import ParallelMasseurAvailabilityMatrix

def query_available_appointment(self, query_data: Dict) -> Dict:
    # ... 原有代碼 ...
    
    # 現有的代碼獲取店家ID、日期等信息
    store_id = ...
    date_str = query_data['date']
    available_time = ...
    total_duration = ...  # 包含緩衝時間
    masseur_names = query_data.get('masseur', [])
    guest_count = query_data['count']
    
    # 創建平行處理矩陣檢查器實例（建議在RoomStatusManager初始化時創建一個實例並重複使用）
    masseur_matrix = ParallelMasseurAvailabilityMatrix(max_workers=4)  # 可以根據系統性能調整工作線程數
    
    # 使用平行處理矩陣方法檢查師傅可用性
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
    
    用於比較原始方法、矩陣方法和平行處理方法的性能差異
    """
    # 性能測試代碼
    test_code = """
# test_masseur_availability_parallel.py
# 用於測試原始方法、矩陣方法和平行處理方法的性能差異

import time
from common import RoomStatusManager
from masseur_availability_improved import MasseurAvailabilityMatrix
from masseur_availability_parallel import ParallelMasseurAvailabilityMatrix

def run_performance_test():
    # 測試參數
    store_id = 1  # 西門店
    date_str = "2025/08/21"
    start_time = "14:00"
    duration_minutes = 90
    masseur_names = ["遠", "川", "豪", "隆", "修", "緯", "廷", "立"]  # 測試多位師傅以展示平行處理優勢
    guest_count = 4
    
    # 創建測試對象
    room_manager = RoomStatusManager()
    matrix_checker = MasseurAvailabilityMatrix()
    parallel_checker = ParallelMasseurAvailabilityMatrix(max_workers=4)
    
    # 測試原始方法
    print("測試原始方法...")
    start = time.time()
    for i in range(3):  # 執行3次以獲得更準確的測量
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
    for i in range(3):  # 執行3次以獲得更準確的測量
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
    
    # 測試平行處理方法
    print("測試平行處理方法...")
    start = time.time()
    for i in range(3):  # 執行3次以獲得更準確的測量
        result_parallel = parallel_checker.check_masseur_availability(
            store_id=store_id,
            date_str=date_str,
            start_time=start_time,
            duration_minutes=duration_minutes,
            masseur_names=masseur_names,
            guest_count=guest_count
        )
    end = time.time()
    parallel_time = end - start
    print(f"平行處理方法耗時: {parallel_time:.4f}秒")
    
    # 計算加速比
    matrix_speedup = original_time / matrix_time
    parallel_speedup = original_time / parallel_time
    parallel_vs_matrix = matrix_time / parallel_time
    
    print(f"矩陣方法相比原始方法加速比: {matrix_speedup:.2f}倍")
    print(f"平行處理方法相比原始方法加速比: {parallel_speedup:.2f}倍")
    print(f"平行處理方法相比矩陣方法加速比: {parallel_vs_matrix:.2f}倍")
    
    # 檢查結果是否一致
    print("檢查結果一致性...")
    original_available = set(result_original['available_masseurs'])
    matrix_available = set(result_matrix['available_masseurs'])
    parallel_available = set(result_parallel['available_masseurs'])
    
    print(f"原始方法與矩陣方法結果一致: {original_available == matrix_available}")
    print(f"原始方法與平行處理方法結果一致: {original_available == parallel_available}")
    print(f"矩陣方法與平行處理方法結果一致: {matrix_available == parallel_available}")

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
## 平行處理整合指南

要將ParallelMasseurAvailabilityMatrix整合到現有系統中，建議採取以下步驟：

1. 添加新類：
   - 將ParallelMasseurAvailabilityMatrix類添加到專案中
   - 確保同時保留MasseurAvailabilityMatrix類以便比較和測試

2. 在RoomStatusManager中添加實例：
   ```python
   def __init__(self):
       # 現有代碼...
       self.masseur_matrix = ParallelMasseurAvailabilityMatrix(max_workers=4)  # 根據系統情況調整線程數
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

5. 性能調整：
   - 根據伺服器配置調整max_workers參數
   - 對於4核CPU，建議使用4個工作線程
   - 對於8核或更高，可以使用8-12個工作線程

6. 測試與監控：
   - 先在非生產環境測試性能提升
   - 監控記憶體使用情況，線程池可能增加記憶體消耗
   - 確認結果正確性與原始方法一致

預期效能提升：
- 相比原始方法：5-20倍加速（取決於同時查詢的師傅數量）
- 相比矩陣方法：2-5倍加速（師傅數量越多，提升越明顯）
- 系統資源使用：會增加CPU使用率，但總體處理時間減少
"""
    
    return guide
