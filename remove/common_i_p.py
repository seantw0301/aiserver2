from typing import Dict, List, Optional
from datetime import datetime, timedelta
from database import db_config
from store import StoreManager
from tasks import TaskManager
from staffs import StaffManager
from sch import ScheduleManager
from masseur_availability_parallel import ParallelMasseurAvailabilityMatrix

class RoomStatusManager:
    """房间状态管理模块"""
    
    def __init__(self):
        self.db_config = db_config
        self.store_manager = StoreManager()
        self.task_manager = TaskManager()
        self.staff_manager = StaffManager()
        self.schedule_manager = ScheduleManager()
        self.masseur_parallel_matrix = ParallelMasseurAvailabilityMatrix(max_workers=4)  # 根據系統情況調整線程數
    
    def _generate_time_slots(self, date_str: str) -> List[str]:
        """生成指定日期的时间段列表 (5分钟间隔)"""
        time_slots = []
        start_time = datetime.strptime(f"{date_str} 00:00", "%Y/%m/%d %H:%M")
        
        # 生成一天24小时的时间段 (24 * 12 = 288个5分钟间隔)
        for i in range(288):
            current_time = start_time + timedelta(minutes=i * 5)
            time_slots.append(current_time.strftime("%Y/%m/%d %H:%M"))
        
        return time_slots
    
    def _get_room_occupancy_from_tasks(self, store_id: int, date_str: str) -> Dict[str, List[int]]:
        """根据预约任务获取房间占用情况"""
        # 获取指定日期和店家的所有预约
        tasks = self.task_manager.get_tasks_by_date(date_str.replace('/', '-'))
        store_tasks = [task for task in tasks if task.get('storeid') == store_id]
        
        # 获取店家房间数
        store = self.store_manager.get_store_by_id(store_id)
        rooms_count = store.get('rooms', 4) if store else 4
        
        # 初始化房间占用状态 {time_slot: [occupied_room_ids]}
        room_occupancy = {}
        
        # 按预约开始时间排序，确保按时间顺序分配房间
        store_tasks.sort(key=lambda x: x.get('start', ''))
        
        for task in store_tasks:
            if not task.get('start') or not task.get('end'):
                continue
            
            start_time = task['start']
            end_time = task['end']
            
            # 如果start_time是字符串，转换为datetime对象
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            if isinstance(end_time, str):
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # 为结束时间添加15分钟缓冲时间
            end_time = end_time + timedelta(minutes=15)
            
            # 计算预约占用的时间段
            current_time = start_time.replace(second=0, microsecond=0)
            # 将分钟调整到5分钟的倍数
            current_time = current_time.replace(minute=(current_time.minute // 5) * 5)
            
            # 生成需要检查的所有时间段
            required_time_slots = []
            temp_time = current_time
            while temp_time < end_time:
                required_time_slots.append(temp_time.strftime("%Y/%m/%d %H:%M"))
                temp_time += timedelta(minutes=5)
            
            # 寻找可用房间：从房间1到房间rooms_count依序检查
            assigned_room = None
            for room_id in range(1, rooms_count + 1):  # 房间ID从1开始
                # 检查这个房间在所有需要的时间段是否都可用
                room_available = True
                for time_slot in required_time_slots:
                    if time_slot in room_occupancy and room_id in room_occupancy[time_slot]:
                        room_available = False
                        break
                
                if room_available:
                    assigned_room = room_id
                    break
            
            # 如果找到可用房间，标记为占用
            if assigned_room:
                for time_slot in required_time_slots:
                    if time_slot not in room_occupancy:
                        room_occupancy[time_slot] = []
                    if assigned_room not in room_occupancy[time_slot]:
                        room_occupancy[time_slot].append(assigned_room)
        
        return room_occupancy
    
    def build_room_status_table(self, store_id: int, date_str: str) -> Optional[Dict]:
        """
        建置房间状态表
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串，格式为 "YYYY/MM/DD"
        
        Returns:
            Dict: 房间状态表 {store_id: {time_slot: {room_id: bool}}}
            格式: [store_id]["YYYY/MM/DD HH:MM"][room_id] = True/False
        """
        # 获取店家信息
        store = self.store_manager.get_store_by_id(store_id)
        if not store:
            return None
        
        rooms_count = store.get('rooms', 4)  # 默认4个房间
        
        # 生成时间段
        time_slots = self._generate_time_slots(date_str)
        
        # 获取房间占用情况
        room_occupancy = self._get_room_occupancy_from_tasks(store_id, date_str)
        
        # 初始化房间状态表
        room_status = {
            store_id: {}
        }
        
        # 为每个时间段生成房间状态
        for time_slot in time_slots:
            room_status[store_id][time_slot] = {}
            occupied_rooms = room_occupancy.get(time_slot, [])
            
            # 为每个房间设置状态
            for room_id in range(1, rooms_count + 1):
                room_status[store_id][time_slot][room_id] = room_id in occupied_rooms
        
        return room_status
    
    def get_room_status_at_time(self, store_id: int, date_str: str, time_str: str) -> Optional[Dict[int, bool]]:
        """
        获取指定时间的房间状态
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串，格式为 "YYYY/MM/DD"
            time_str: 时间字符串，格式为 "HH:MM"
        
        Returns:
            Dict[int, bool]: {room_id: is_occupied}
        """
        full_time = f"{date_str} {time_str}"
        room_status = self.build_room_status_table(store_id, date_str)
        
        if not room_status or store_id not in room_status:
            return None
        
        return room_status[store_id].get(full_time, {})
    
    def get_available_rooms_at_time(self, store_id: int, date_str: str, time_str: str) -> List[int]:
        """
        获取指定时间的可用房间列表
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串，格式为 "YYYY/MM/DD"
            time_str: 时间字符串，格式为 "HH:MM"
        
        Returns:
            List[int]: 可用房间ID列表
        """
        room_status = self.get_room_status_at_time(store_id, date_str, time_str)
        if not room_status:
            return []
        
        return [room_id for room_id, is_occupied in room_status.items() if not is_occupied]
    
    def get_room_status_summary(self, store_id: int, date_str: str) -> Dict:
        """
        获取房间状态摘要信息
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串，格式为 "YYYY/MM/DD"
        
        Returns:
            Dict: 摘要信息
        """
        room_status = self.build_room_status_table(store_id, date_str)
        if not room_status or store_id not in room_status:
            return {}
        
        store_status = room_status[store_id]
        total_slots = len(store_status)
        
        if total_slots == 0:
            return {}
        
        # 计算每个房间的使用率
        store_info = self.store_manager.get_store_by_id(store_id)
        rooms_count = store_info.get('rooms', 4) if store_info else 4
        
        room_usage = {}
        for room_id in range(1, rooms_count + 1):
            occupied_count = sum(
                1 for time_slot in store_status.values() 
                if time_slot.get(room_id, False)
            )
            room_usage[room_id] = {
                'occupied_slots': occupied_count,
                'total_slots': total_slots,
                'usage_rate': round(occupied_count / total_slots * 100, 2) if total_slots > 0 else 0
            }
        
        return {
            'store_id': store_id,
            'date': date_str,
            'total_time_slots': total_slots,
            'total_rooms': rooms_count,
            'room_usage': room_usage
        }
    
    def get_detailed_room_status_table(self, store_id: int, date_str: str) -> Optional[Dict]:
        """
        获取详细的房间状态表格，显示每个房间每个时间段的占用状态
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串，格式为 "YYYY/MM/DD"
        
        Returns:
            Dict: 详细房间状态表
            格式: {
                'store_id': int,
                'date': str,
                'rooms_count': int,
                'time_slots_count': int,
                'rooms': {
                    '1': {
                        'room_id': 1,
                        'total_occupied_slots': int,
                        'usage_rate': float,
                        'time_slots': {
                            '2025/08/13 00:00': 0,  # 0=可用, 1=占用
                            '2025/08/13 00:05': 0,
                            ...
                        }
                    },
                    ...
                }
            }
        """
        # 获取店家信息
        store = self.store_manager.get_store_by_id(store_id)
        if not store:
            return None
        
        rooms_count = store.get('rooms', 4)
        
        # 生成时间段
        time_slots = self._generate_time_slots(date_str)
        
        # 获取房间占用情况
        room_occupancy = self._get_room_occupancy_from_tasks(store_id, date_str)
        
        # 构建详细房间状态表
        detailed_status = {
            'store_id': store_id,
            'date': date_str,
            'rooms_count': rooms_count,
            'time_slots_count': len(time_slots),
            'rooms': {}
        }
        
        # 为每个房间构建状态
        for room_id in range(1, rooms_count + 1):
            room_data = {
                'room_id': room_id,
                'total_occupied_slots': 0,
                'usage_rate': 0.0,
                'time_slots': {}
            }
            
            occupied_count = 0
            
            # 为每个时间段设置占用状态
            for time_slot in time_slots:
                occupied_rooms = room_occupancy.get(time_slot, [])
                is_occupied = room_id in occupied_rooms
                room_data['time_slots'][time_slot] = 1 if is_occupied else 0
                
                if is_occupied:
                    occupied_count += 1
            
            # 计算使用率
            room_data['total_occupied_slots'] = occupied_count
            room_data['usage_rate'] = round(occupied_count / len(time_slots) * 100, 2) if time_slots else 0
            
            detailed_status['rooms'][str(room_id)] = room_data
        
        return detailed_status
    
    def get_room_status_array_table(self, store_id: int, date_str: str) -> Optional[Dict]:
        """
        获取房间状态数组表格，每个房间返回288个时间段的状态数组
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串，格式为 "YYYY/MM/DD"
        
        Returns:
            Dict: 房间状态数组表格
            格式: {
                'store_id': int,
                'date': str,
                'rooms_count': int,
                'time_slots_count': int,
                'time_labels': ['00:00', '00:05', '00:10', ...],  # 时间标签数组
                'rooms': {
                    '1': [0, 0, 0, 1, 1, 0, ...],  # 房间1的288个状态值
                    '2': [0, 0, 0, 0, 1, 1, ...],  # 房间2的288个状态值
                    '3': [0, 0, 0, 0, 0, 1, ...],  # 房间3的288个状态值
                    '4': [0, 0, 0, 0, 0, 0, ...]   # 房间4的288个状态值
                },
                'summary': {
                    '1': {'occupied_slots': int, 'usage_rate': float},
                    '2': {'occupied_slots': int, 'usage_rate': float},
                    '3': {'occupied_slots': int, 'usage_rate': float},
                    '4': {'occupied_slots': int, 'usage_rate': float}
                }
            }
        """
        # 获取店家信息
        store = self.store_manager.get_store_by_id(store_id)
        if not store:
            return None
        
        rooms_count = store.get('rooms', 4)
        
        # 生成时间段
        time_slots = self._generate_time_slots(date_str)
        
        # 生成时间标签（只显示时间，不显示日期）
        time_labels = [slot.split(' ')[1] for slot in time_slots]
        
        # 获取房间占用情况
        room_occupancy = self._get_room_occupancy_from_tasks(store_id, date_str)
        
        # 构建房间状态数组表格
        array_table = {
            'store_id': store_id,
            'date': date_str,
            'rooms_count': rooms_count,
            'time_slots_count': len(time_slots),
            'time_labels': time_labels,
            'rooms': {},
            'summary': {}
        }
        
        # 为每个房间构建状态数组
        for room_id in range(1, rooms_count + 1):
            room_status_array = []
            occupied_count = 0
            
            # 为每个时间段设置占用状态
            for time_slot in time_slots:
                occupied_rooms = room_occupancy.get(time_slot, [])
                is_occupied = room_id in occupied_rooms
                status_value = 1 if is_occupied else 0
                room_status_array.append(status_value)
                
                if is_occupied:
                    occupied_count += 1
            
            # 保存房间状态数组
            array_table['rooms'][str(room_id)] = room_status_array
            
            # 计算摘要信息
            array_table['summary'][str(room_id)] = {
                'occupied_slots': occupied_count,
                'usage_rate': round(occupied_count / len(time_slots) * 100, 2) if time_slots else 0
            }
        
        return array_table
    
    def find_earliest_available_time_for_rooms(self, store_id: int, date_str: str, start_time: str, 
                                               duration_minutes: int, required_rooms: int = 1) -> Dict:
        """
        改進版：查詢特定日期、開始時間，N個房間可同時使用的最早可用時間
        
        程式邏輯：
        1. 單房間查詢：逐個時段檢查，找連續可用時段
        2. 多房間查詢：先找各房間最早時間，再按優先順序檢查多房間可用性
        3. 若無符合條件時段，從第四早時間重新開始查詢
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串，格式為 "YYYY/MM/DD" 
            start_time: 開始查詢時間，格式為 "HH:MM"
            duration_minutes: 所需使用時間（分鐘）
            required_rooms: 所需房間數量，默認為1
            
        Returns:
            Dict: 查詢結果
        """
        try:
            # 獲取店家資訊
            store = self.store_manager.get_store_by_id(store_id)
            if not store:
                return {
                    "success": False,
                    "earliest_time": None,
                    "room_details": {},
                    "message": "店家不存在"
                }
            
            rooms_count = store.get('rooms', 4)
            
            # 生成288個時間段陣列
            time_slots = []
            for hour in range(24):
                for minute in range(0, 60, 5):
                    time_slots.append(f"{hour:02d}:{minute:02d}")
            
            # 調整開始時間到5分鐘間隔
            start_index = self._adjust_start_time_to_slot(start_time, time_slots)
            if start_index is None:
                return {
                    "success": False,
                    "earliest_time": None,
                    "room_details": {},
                    "message": "查詢時間超出當天範圍"
                }
            
            # 計算需要的時間段數量（duration + 15分鐘緩衝）
            required_slots = (duration_minutes + 15) // 5
            
            # 獲取房間狀態陣列
            room_status_array = self._get_room_status_arrays(store_id, date_str, rooms_count)
            if not room_status_array:
                return {
                    "success": False,
                    "earliest_time": None,
                    "room_details": {},
                    "message": "無法獲取房間狀態"
                }
            
            # 步驟1: 為每個房間找最早可用時間（改進演算法）
            room_earliest_times = {}
            for room_id in range(1, rooms_count + 1):
                room_earliest_times[str(room_id)] = self._find_room_earliest_time_improved(
                    room_status_array[room_id], time_slots, start_index, required_slots
                )
            
            # 步驟2: 處理查詢邏輯
            if required_rooms == 1:
                # 單房間查詢：返回最早可用時間
                return self._handle_single_room_query(room_earliest_times)
            else:
                # 多房間查詢：改進演算法
                return self._handle_multi_room_query_improved(
                    room_status_array, room_earliest_times, time_slots, 
                    required_slots, required_rooms, start_index
                )
                
        except Exception as e:
            return {
                "success": False,
                "earliest_time": None,
                "room_details": {},
                "message": f"查詢過程中發生錯誤: {str(e)}"
            }
    
    def _adjust_start_time_to_slot(self, start_time: str, time_slots: List[str]) -> Optional[int]:
        """
        調整開始時間到5分鐘間隔，返回索引
        """
        try:
            # 首先嘗試直接找到時間索引
            return time_slots.index(start_time)
        except ValueError:
            # 處理 "HH:MM:SS" 格式的時間
            if start_time.count(':') == 2:
                # 如果是 "HH:MM:SS" 格式，只取 "HH:MM" 部分
                adjusted_time = ":".join(start_time.split(":")[:2])
                try:
                    return time_slots.index(adjusted_time)
                except ValueError:
                    pass
            
            # 如果時間不在5分鐘間隔內，找到最接近的下一個時間
            parts = start_time.split(':')
            start_hour = int(parts[0])
            start_minute = int(parts[1])
            start_minute = ((start_minute // 5) + 1) * 5
            if start_minute >= 60:
                start_minute = 0
                start_hour += 1
                if start_hour >= 24:
                    return None
            adjusted_time = f"{start_hour:02d}:{start_minute:02d}"
            try:
                return time_slots.index(adjusted_time)
            except ValueError:
                return None
    
    def _get_room_status_arrays(self, store_id: int, date_str: str, rooms_count: int) -> Optional[Dict]:
        """
        獲取房間狀態陣列，每個房間288個時段的狀態
        """
        room_status_table = self.build_room_status_table(store_id, date_str)
        if not room_status_table or store_id not in room_status_table:
            return None
        
        store_status = room_status_table[store_id]
        
        # 生成時間段
        time_slots = []
        for hour in range(24):
            for minute in range(0, 60, 5):
                time_slots.append(f"{hour:02d}:{minute:02d}")
        
        # 構建每個房間的狀態陣列
        room_arrays = {}
        for room_id in range(1, rooms_count + 1):
            room_array = []
            for time_slot in time_slots:
                full_time_key = f"{date_str} {time_slot}"
                room_status = store_status.get(full_time_key, {})
                is_occupied = room_status.get(room_id, False)
                room_array.append(1 if is_occupied else 0)  # 1=占用, 0=可用
            room_arrays[room_id] = room_array
        
        return room_arrays
    
    def _find_room_earliest_time_improved(self, room_array: List[int], time_slots: List[str], 
                                         start_index: int, required_slots: int) -> Dict:
        """
        改進版：為單個房間找最早可用時間
        
        邏輯：
        1. 從start_index開始檢查每個時段
        2. 找到可用時段時設為開始時間，累加可用分鐘數
        3. 遇到占用時段時重置計數器
        4. 達到required_slots時返回開始時間
        """
        current_start_index = None
        available_minutes = 0
        
        for i in range(start_index, len(room_array)):
            is_available = (room_array[i] == 0)  # 0=可用, 1=占用
            
            if is_available:
                if current_start_index is None:
                    # 設置開始時間
                    current_start_index = i
                    available_minutes = 5
                else:
                    # 累加可用分鐘數
                    available_minutes += 5
                
                # 檢查是否滿足所需時間
                if available_minutes >= required_slots * 5:
                    return {"earliest_time": time_slots[current_start_index]}
            else:
                # 遇到占用時段，重置計數器
                current_start_index = None
                available_minutes = 0
        
        return {"earliest_time": None}
    
    def _handle_single_room_query(self, room_earliest_times: Dict) -> Dict:
        """
        處理單房間查詢
        """
        earliest_times = [info["earliest_time"] for info in room_earliest_times.values() 
                         if info["earliest_time"] is not None]
        
        if earliest_times:
            earliest_time = min(earliest_times)
            return {
                "success": True,
                "earliest_time": earliest_time,
                "room_details": room_earliest_times,
                "message": f"找到可用時間: {earliest_time}"
            }
        else:
            return {
                "success": False,
                "earliest_time": None,
                "room_details": room_earliest_times,
                "message": "當天無可用時段"
            }
    
    def _handle_multi_room_query_improved(self, room_status_array: Dict, room_earliest_times: Dict,
                                        time_slots: List[str], required_slots: int, 
                                        required_rooms: int, start_index: int) -> Dict:
        """
        改進版：處理多房間查詢邏輯
        
        邏輯：
        1. 收集各房間最早時間並排序
        2. 按優先順序檢查：最早/次早/第三早/第四早
        3. 若都不符合，從第四早時間重新開始查詢
        """
        # 收集所有可用的開始時間並排序
        available_times = []
        for room_info in room_earliest_times.values():
            earliest_time = room_info.get("earliest_time")
            if earliest_time and earliest_time not in available_times:
                available_times.append(earliest_time)
        
        if not available_times:
            return {
                "success": False,
                "earliest_time": None,
                "room_details": room_earliest_times,
                "message": "無任何房間可用"
            }
        
        # 如果沒有足夠的時間點，直接從 start_index 開始遞歸搜索
        if len(available_times) < 2:
            return self._recursive_multi_room_search(
                room_status_array, time_slots, start_index,
                required_slots, required_rooms
            )
        
        available_times.sort()
        
        # 按照優先順序檢查每個時間點
        # 最多檢查4個時間，但不超過實際可用時間數量
        max_check = min(4, len(available_times))
        for check_time in available_times[:max_check]:
            try:
                check_index = time_slots.index(check_time)
            except ValueError:
                continue
            
            # 檢查從這個時間開始的連續時段內，有多少房間可用
            available_rooms_count = self._count_available_rooms_in_period_improved(
                room_status_array, check_index, required_slots
            )
            
            if available_rooms_count >= required_rooms:
                return {
                    "success": True,
                    "earliest_time": check_time,
                    "room_details": room_earliest_times,
                    "message": f"找到可用時間: {check_time}，可用房間數: {available_rooms_count}"
                }
        
        # 若最早、次早、第三、第四都不符合條件，從最後一個檢查的時間重新開始查詢
        if available_times:
            # 使用最後一個可用時間，而不是硬編碼第四個
            last_checked_time = available_times[min(3, len(available_times) - 1)]
            try:
                last_index = time_slots.index(last_checked_time)
                return self._recursive_multi_room_search(
                    room_status_array, time_slots, last_index, 
                    required_slots, required_rooms
                )
            except ValueError:
                pass
        
        return {
            "success": False,
            "earliest_time": None,
            "room_details": room_earliest_times,
            "message": f"無法找到 {required_rooms} 個房間同時可用的時段"
        }
    
    def _count_available_rooms_in_period_improved(self, room_status_array: Dict, 
                                                start_index: int, required_slots: int) -> int:
        """
        改進版：計算指定時間段內可用的房間數量
        """
        available_rooms = 0
        
        for room_array in room_status_array.values():
            room_available = True
            
            # 檢查這個房間在整個所需時間段內是否都可用
            for i in range(start_index, min(start_index + required_slots, len(room_array))):
                if room_array[i] == 1:  # 1=占用
                    room_available = False
                    break
            
            if room_available:
                available_rooms += 1
        
        return available_rooms
    
    def _recursive_multi_room_search(self, room_status_array: Dict, time_slots: List[str],
                                   start_index: int, required_slots: int, 
                                   required_rooms: int) -> Dict:
        """
        遞歸搜尋多房間可用時段（從指定時間開始重新查詢）
        """
        # 從指定時間開始，逐個時段檢查
        for i in range(start_index, len(time_slots)):
            available_rooms_count = self._count_available_rooms_in_period_improved(
                room_status_array, i, required_slots
            )
            
            if available_rooms_count >= required_rooms:
                return {
                    "success": True,
                    "earliest_time": time_slots[i],
                    "room_details": {},
                    "message": f"重新查詢找到可用時間: {time_slots[i]}，可用房間數: {available_rooms_count}"
                }
        
        return {
            "success": False,
            "earliest_time": None,
            "room_details": {},
            "message": f"查詢結束仍無法找到 {required_rooms} 個房間同時可用的時段"
        }

    def _find_single_room_earliest_time(self, store_status: Dict, room_id: int, 
                                      time_slots: List[str], start_index: int, 
                                      required_slots: int, date_str: str) -> Dict:
        """
        為單個房間找最早可用時間
        
        Args:
            store_status: 店家狀態數據
            room_id: 房間ID
            time_slots: 所有時間段列表
            start_index: 開始查詢的索引
            required_slots: 需要的連續時間段數
            date_str: 日期字符串
            
        Returns:
            Dict: {"earliest_time": str or None}
        """
        current_start_time = None
        available_minutes = 0
        
        for i in range(start_index, len(time_slots)):
            time_slot = time_slots[i]
            full_time_key = f"{date_str} {time_slot}"
            
            # 檢查這個時間段房間是否可用
            room_status = store_status.get(full_time_key, {})
            is_occupied = room_status.get(room_id, False)
            
            if not is_occupied:  # 房間可用
                if current_start_time is None:
                    current_start_time = time_slot
                    available_minutes = 5
                else:
                    available_minutes += 5
                
                # 檢查是否已滿足所需時間
                if available_minutes >= required_slots * 5:
                    return {"earliest_time": current_start_time}
                    
            else:  # 房間被占用
                # 重置計數器
                current_start_time = None
                available_minutes = 0
        
        return {"earliest_time": None}
    
    def _find_multi_room_earliest_time(self, store_status: Dict, room_earliest_times: Dict,
                                     time_slots: List[str], required_slots: int, 
                                     required_rooms: int, date_str: str) -> Dict:
        """
        處理多房間查詢邏輯
        
        Args:
            store_status: 店家狀態數據
            room_earliest_times: 各房間最早可用時間
            time_slots: 所有時間段列表
            required_slots: 需要的連續時間段數
            required_rooms: 需要的房間數量
            date_str: 日期字符串
            
        Returns:
            Dict: 查詢結果
        """
        # 收集所有可用的開始時間並排序
        available_times = []
        for room_info in room_earliest_times.values():
            earliest_time = room_info.get("earliest_time")
            if earliest_time and earliest_time not in available_times:
                available_times.append(earliest_time)
        
        available_times.sort()
        
        # 按照優先順序檢查每個時間點
        for check_time in available_times:
            try:
                check_index = time_slots.index(check_time)
            except ValueError:
                continue
            
            # 檢查從這個時間開始的連續時段內，有多少房間可用
            available_rooms_count = self._count_available_rooms_in_period(
                store_status, time_slots, check_index, required_slots, date_str
            )
            
            if available_rooms_count >= required_rooms:
                return {
                    "success": True,
                    "earliest_time": check_time,
                    "room_details": room_earliest_times,
                    "message": f"找到可用時間: {check_time}，可用房間數: {available_rooms_count}"
                }
        
        return {
            "success": False,
            "earliest_time": None,
            "room_details": room_earliest_times,
            "message": f"無法找到 {required_rooms} 個房間同時可用的時段"
        }
    
    def _count_available_rooms_in_period(self, store_status: Dict, time_slots: List[str],
                                       start_index: int, required_slots: int, date_str: str) -> int:
        """
        計算指定時間段內可用的房間數量
        
        Args:
            store_status: 店家狀態數據
            time_slots: 所有時間段列表
            start_index: 開始時間索引
            required_slots: 需要檢查的時間段數
            date_str: 日期字符串
            
        Returns:
            int: 可用房間數量
        """
        # 假設最多4個房間
        room_ids = [1, 2, 3, 4]
        available_rooms = 0
        
        for room_id in room_ids:
            room_available = True
            
            # 檢查這個房間在整個所需時間段內是否都可用
            for i in range(start_index, min(start_index + required_slots, len(time_slots))):
                time_slot = time_slots[i]
                full_time_key = f"{date_str} {time_slot}"
                room_status = store_status.get(full_time_key, {})
                is_occupied = room_status.get(room_id, False)
                
                if is_occupied:
                    room_available = False
                    break
            
            if room_available:
                available_rooms += 1
        
        return available_rooms
    
    def query_available_appointment(self, query_data: Dict) -> Dict:
        """
        改善版預約查詢功能
        
        新的查詢邏輯：
        1. client 傳來查詢訊息：{"branch":"西門","masseur":["鞋","川","豪"],"date":"2025/8/14","time":"14:00","project":90,"count":1}
        2. 首先依count數量，取得最早符合可用房間數的時段，若全天皆無可用時段，則直接返回無法預約的提示
        3. 取出可用的時段之後，才取出masseur的排班情況，並檢查該師傅是否可以預約
        
        Args:
            query_data: 查詢數據
            {
                "branch": "西門",           # 店家名稱
                "masseur": ["鞋","川","豪"], # 無/一個/或多個師傅名稱
                "date": "2025/8/14",       # 預約日期
                "time": "14:00",           # 開始時間
                "project": 90,             # 60/90/120分鐘(必需+15分鐘結束緩衝)
                "count": 1                 # 來客數1個或多個
            }
        
        Returns:
            Dict: 查詢結果
        """
        try:
            # 步驟1: 驗證輸入數據
            validation_result = self._validate_query_data(query_data)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'step': 'validation'
                }
            
            branch_name = query_data['branch']
            masseur_names = query_data.get('masseur', [])
            date_str = query_data['date']
            time_str = query_data['time']
            project_duration = query_data['project']
            guest_count = query_data['count']
            
            # 根據店家名稱獲取店家ID
            store = self.store_manager.get_store_by_name(branch_name)
            if not store:
                return {
                    'success': False,
                    'error': f'找不到店家: {branch_name}',
                    'step': 'store_lookup'
                }
            
            store_id = store['id']
            
            # 步驟2: 首先依count數量，取得最早符合可用房間數的時段
            # 注意：project需要加15分鐘緩衝時間，所以需要判斷是否有75/105/135空檔時間
            total_duration = project_duration + 15  # 加15分鐘結束緩衝
            
            room_query_result = self.find_earliest_available_time_for_rooms(
                store_id=store_id,
                date_str=date_str,
                start_time=time_str,
                duration_minutes=project_duration,  # 函數內部會自動加15分鐘緩衝
                required_rooms=guest_count
            )
            
            # 步驟3: 若全天皆無可用時段，則直接返回無法預約的提示
            if not room_query_result['success'] or room_query_result['earliest_time'] is None:
                return {
                    'success': False,
                    'error': '無法預約',
                    'reason': '全天無可用房間時段',
                    'step': 'room_availability_check',
                    'query_data': query_data,
                    'store_info': {
                        'id': store_id,
                        'name': branch_name,
                        'total_rooms': store.get('rooms', 4)
                    },
                    'room_availability': {
                        'available_at_requested_time': False,
                        'earliest_available_time': None,
                        'required_duration': total_duration,
                        'required_rooms': guest_count,
                        'message': room_query_result.get('message', '無可用時段'),
                        'room_query_details': room_query_result
                    },
                    'suggestions': [
                        '請選擇其他日期',
                        '考慮減少來客數量',
                        '選擇較短的服務時間'
                    ]
                }
            
            # 步驟4: 取出可用的時段之後，才取出masseur的排班情況
            available_time = room_query_result['earliest_time']
            
            masseur_availability_result = self._check_masseur_availability_improved(
                store_id=store_id,
                date_str=date_str,
                start_time=available_time,
                duration_minutes=total_duration,  # 包含15分鐘緩衝時間
                masseur_names=masseur_names,
                guest_count=guest_count
            )
            
            # 生成最終預約建議
            can_book = masseur_availability_result.get('sufficient_masseurs', False)
            
            result = {
                'success': True,
                'can_book': can_book,
                'step': 'complete',
                'query_data': query_data,
                'store_info': {
                    'id': store_id,
                    'name': branch_name,
                    'total_rooms': store.get('rooms', 4)
                },
                'room_availability': {
                    'available_at_requested_time': (available_time == time_str),
                    'earliest_available_time': available_time,
                    'requested_time': time_str,
                    'total_duration': total_duration,
                    'project_duration': project_duration,
                    'buffer_time': 15,
                    'required_rooms': guest_count,
                    'time_difference_minutes': self._calculate_time_difference(time_str, available_time),
                    'room_query_details': room_query_result
                },
                'masseur_availability': masseur_availability_result,
                'booking_recommendation': {
                    'recommended_time': available_time,
                    'recommended_masseurs': masseur_availability_result.get('available_masseurs', []),
                    'alternative_masseurs': masseur_availability_result.get('alternative_masseurs', []),
                    'booking_feasible': can_book,
                    'notes': self._generate_booking_notes(masseur_availability_result, available_time, time_str)
                }
            }
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'查詢預約時發生錯誤: {str(e)}',
                'step': 'error'
            }
    
    def _validate_query_data(self, query_data: Dict) -> Dict:
        """
        驗證查詢數據
        """
        # 檢查必要參數
        required_fields = ['branch', 'date', 'time', 'project', 'count']
        for field in required_fields:
            if field not in query_data:
                return {
                    'valid': False,
                    'error': f'缺少必要參數: {field}'
                }
        
        # 驗證項目時長
        project_duration = query_data['project']
        if project_duration not in [60, 90, 120]:
            return {
                'valid': False,
                'error': '項目時長必須為60、90或120分鐘'
            }
        
        # 驗證客人數量
        guest_count = query_data['count']
        if not isinstance(guest_count, int) or guest_count < 1 or guest_count > 4:
            return {
                'valid': False,
                'error': '客人數量必須在1-4之間'
            }
        
        # 驗證師傅名單（可以為空）
        masseur_names = query_data.get('masseur', [])
        if not isinstance(masseur_names, list):
            return {
                'valid': False,
                'error': '師傅名單必須為陣列格式'
            }
        
        return {
            'valid': True,
            'error': None
        }
    
    def _check_masseur_availability_improved(self, store_id: int, date_str: str, 
                                           start_time: str, duration_minutes: int,
                                           masseur_names: List[str], guest_count: int) -> Dict:
        """
        改進版師傅可用性檢查 - 使用平行處理提高效能
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串
            start_time: 開始時間
            duration_minutes: 持續時間（已包含緩衝）
            masseur_names: 指定的師傅名單
            guest_count: 客人數量
            
        Returns:
            Dict: 師傅可用性結果
        """
        # 使用平行處理矩陣檢查師傅可用性
        result = self.masseur_parallel_matrix.check_masseur_availability(
            store_id=store_id,
            date_str=date_str,
            start_time=start_time,
            duration_minutes=duration_minutes,
            masseur_names=masseur_names,
            guest_count=guest_count
        )
        
        # 如果需要在 unavailable_masseurs 中的師傅確認房間可用性，這裡處理
        room_occupancy = self._get_room_occupancy_from_tasks(store_id, date_str)
        rooms_count = self._get_store_rooms_count(store_id)
        
        # 處理不可約師傅的替代時間，檢查房間可用性
        updated_unavailable = []
        for masseur_info in result['unavailable_masseurs']:
            masseur_name = masseur_info[0]
            alt_time = masseur_info[1]
            
            if alt_time:
                # 檢查替代時間的房間可用性 - 使用串行版本（效能測試顯示串行版本更快）
                alt_time_dt = datetime.strptime(f"{date_str} {alt_time}", "%Y/%m/%d %H:%M")
                room_can_use = self._check_time_slot_availability_for_one_room(
                    alt_time_dt, 
                    duration_minutes,
                    room_occupancy, 
                    rooms_count
                )
                
                if not room_can_use:
                    # 如果替代時間沒有可用房間，尋找其他時間
                    alt_time = None
            
            updated_unavailable.append([masseur_name, alt_time])
        
        result['unavailable_masseurs'] = updated_unavailable
        
        return result
    
    def _clear_masseur_availability_cache(self):
        """
        清除師傅可用性矩陣的快取
        
        在添加、更新或刪除任務後調用，確保下次查詢時獲取最新數據
        """
        if hasattr(self, 'masseur_parallel_matrix'):
            self.masseur_parallel_matrix.clear_cache()
    
    def _generate_improved_appointment_recommendation(self, room_result: Dict, 
                                                    masseur_result: Dict, 
                                                    query_data: Dict, 
                                                    available_time: str) -> Dict:
        """
        生成改進版預約建議
        """
        recommendation = {
            'can_book': False,
            'recommended_time': available_time,
            'time_difference': self._calculate_time_difference(query_data['time'], available_time),
            'recommended_masseurs': [],
            'booking_details': {},
            'notes': []
        }
        
        # 檢查是否可以預約
        room_available = room_result.get('success', False)
        masseur_sufficient = masseur_result.get('sufficient_masseurs', False)
        
        if room_available and masseur_sufficient:
            recommendation['can_book'] = True
            recommendation['recommended_masseurs'] = masseur_result['available_masseurs']
            
            # 如果需要替代師傅
            if masseur_result['alternative_masseurs']:
                recommendation['recommended_masseurs'].extend(masseur_result['alternative_masseurs'])
                recommendation['notes'].append('包含建議的替代師傅')
            
            recommendation['booking_details'] = {
                'store_id': room_result.get('store_id'),
                'date': query_data['date'],
                'time': available_time,
                'duration': query_data['project'],
                'guest_count': query_data['count'],
                'masseurs': recommendation['recommended_masseurs'][:query_data['count']]
            }
            
            if available_time != query_data['time']:
                recommendation['notes'].append(f'建議時間調整為 {available_time}')
        else:
            if not room_available:
                recommendation['notes'].append('無可用房間')
            if not masseur_sufficient:
                recommendation['notes'].append('師傅人數不足')
        
        return recommendation
    
    def _calculate_time_difference(self, requested_time: str, available_time: str) -> int:
        """
        計算時間差異（分鐘）
        """
        try:
            time_format = "%H:%M"
            req_time = datetime.strptime(requested_time, time_format)
            avail_time = datetime.strptime(available_time, time_format)
            diff = (avail_time - req_time).total_seconds() / 60
            return int(diff)
        except (ValueError, TypeError):
            return 0
    
    def _generate_booking_notes(self, masseur_result: Dict, available_time: str, requested_time: str) -> List[str]:
        """
        生成預約註記
        """
        notes = []
        
        # 時間差異註記
        time_diff = self._calculate_time_difference(requested_time, available_time)
        if time_diff > 0:
            notes.append(f"建議時間比預期晚 {time_diff} 分鐘")
        elif time_diff == 0:
            notes.append("時間符合預期")
        
        # 師傅可用性註記
        available_count = len(masseur_result.get('available_masseurs', []))
        alternative_count = len(masseur_result.get('alternative_masseurs', []))
        unavailable_count = len(masseur_result.get('unavailable_masseurs', []))
        
        if unavailable_count > 0:
            notes.append(f"有 {unavailable_count} 位指定師傅不可用")
        
        if alternative_count > 0:
            notes.append(f"建議 {alternative_count} 位替代師傅")
        
        if available_count > 0:
            notes.append(f"有 {available_count} 位師傅可用")
        
        # 如果沒有註記，添加一個預設註記
        if not notes:
            notes.append("預約查詢完成")
        
        return notes
    
    def _find_all_available_masseurs(self, store_id: int, date_str: str, 
                                   start_time: str, duration_minutes: int) -> List[str]:
        """
        查找所有可用的師傅
        """
        try:
            # 獲取該店家所有師傅
            all_staffs = self.staff_manager.get_all_staffs()
            available_masseurs = []
            
            for staff_data in all_staffs:
                if staff_data.get('storeid') == store_id:  # 使用 'storeid' 而不是 'store_id'
                    staff_name = staff_data.get('name', '')
                    if self._check_single_masseur_availability(
                        store_id, date_str, start_time, duration_minutes, staff_name
                    ):
                        available_masseurs.append(staff_name)
            
            return available_masseurs
        except Exception:
            return []
    
    def _check_single_masseur_availability(self, store_id: int, date_str: str,
                                         start_time: str, duration_minutes: int,
                                         masseur_name: str) -> bool:
        """
        檢查單個師傅的可用性 - 使用包含工作安排的綜合班表
        """
        try:
            print(f"檢查師傅: {masseur_name}, 日期: {date_str}, 時間: {start_time}")
            
            # 獲取師傅的綜合班表（包含已有工作安排）
            schedule_data = self.schedule_manager.get_schedule_by_name(masseur_name, date_str, include_tasks=True)
            if not schedule_data:
                print(f"師傅 {masseur_name} 沒有班表數據")
                return False
            
            # 檢查師傅是否在班 - 使用包含工作安排的 5 分鐘間隔班表
            schedule_blocks = schedule_data.get('schedule', [])
            if not schedule_blocks:
                print(f"師傅 {masseur_name} 班表空白")
                return False
            
            # 解析開始時間
            start_datetime = datetime.strptime(f"{date_str} {start_time}", "%Y/%m/%d %H:%M")
            
            # 計算需要檢查的時間區間（5分鐘間隔的 blocks）
            start_hour = start_datetime.hour
            start_minute = start_datetime.minute
            # 計算從 00:00 開始的總分鐘數，與 _convert_to_5min_blocks 方法保持一致
            total_minutes = start_hour * 60 + start_minute
            start_block = total_minutes // 5
            
            # 計算需要的 blocks 數量
            required_blocks = (duration_minutes + 4) // 5  # 向上取整
            end_block = start_block + required_blocks
            
            print(f"師傅 {masseur_name} 需要檢查的 block 區間: {start_block} - {end_block}, 總數: {required_blocks}")
            print(f"師傅 {masseur_name} 班表長度: {len(schedule_blocks)}")
            
            # 檢查所有需要的時間段是否都可用
            for block in range(start_block, end_block):
                if block >= len(schedule_blocks) or not schedule_blocks[block]:
                    print(f"師傅 {masseur_name} 在 block {block} 不可用，超出範圍或值為空")
                    return False
            
            print(f"師傅 {masseur_name} 可用!")
            return True
            
        except Exception as e:
            print(f"檢查師傅 {masseur_name} 可用性時發生錯誤: {str(e)}")
            return False
    
    def _get_staff_existing_tasks(self, store_id: int, staff_name: str, date_str: str) -> List[Dict]:
        """
        獲取師傅當天的現有預約
        """
        try:
            # 獲取師傅當天的預約
            staff_tasks = self.task_manager.get_tasks_by_staff(staff_name, date_str)
            
            # 過濾出該店家的預約
            store_tasks = []
            for task in staff_tasks:
                if task.get('storeid') == store_id:
                    store_tasks.append(task)
            
            return store_tasks
        except Exception:
            return []
    
    def _find_alternative_masseurs(self, store_id: int, date_str: str, start_time: str,
                                 duration_minutes: int, exclude_names: List[str],
                                 needed_count: int) -> List[str]:
        """
        尋找替代師傅
        """
        try:
            all_available = self._find_all_available_masseurs(store_id, date_str, start_time, duration_minutes)
            alternatives = []
            
            for masseur_name in all_available:
                if masseur_name not in exclude_names and len(alternatives) < needed_count:
                    alternatives.append(masseur_name)
            
            return alternatives
        except Exception:
            return []
    
    def _check_room_availability(self, store_id: int, date_str: str, time_str: str, 
                                duration_minutes: int, guest_count: int) -> Dict:
        """
        检查房间可用性
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串
            time_str: 开始时间字符串
            duration_minutes: 持续时间（分钟，已包含缓冲）
            guest_count: 客人数量
        
        Returns:
            Dict: 房间可用性结果
        """
        # 获取店家房间数
        store = self.store_manager.get_store_by_id(store_id)
        rooms_count = store.get('rooms', 4) if store else 4
        
        # 解析查询时间
        query_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M")
        
        # 获取当天的房间占用情况
        room_occupancy = self._get_room_occupancy_from_tasks(store_id, date_str)
        
        # 检查指定时间的房间可用性
        requested_time_result = self._check_time_slot_availability(
            query_datetime, duration_minutes, room_occupancy, rooms_count, guest_count
        )
        
        result = {
            'requested_time': time_str,
            'duration_minutes': duration_minutes,
            'guest_count': guest_count,
            'available_at_requested_time': requested_time_result['available'],
            'available_rooms_count': requested_time_result['available_rooms_count'],
            'room_suggestions': []
        }
        
        # 如果指定时间不可用，寻找替代时间
        if not requested_time_result['available']:
            suggestions = self._find_alternative_time_slots(
                query_datetime, duration_minutes, room_occupancy, rooms_count, guest_count, date_str
            )
            result['room_suggestions'] = suggestions
        else:
            result['available_rooms'] = requested_time_result['available_rooms']
        
        return result
    
    def _get_store_rooms_count(self, store_id: int) -> int:
        """
        获取店家的房间数量
        
        Args:
            store_id: 店家ID
            
        Returns:
            int: 房间数量
        """
        store = self.store_manager.get_store_by_id(store_id)
        return store.get('rooms', 4) if store else 4
        
    def _check_time_slot_availability_for_one_room_parallel(self, start_datetime: datetime, duration_minutes: int,
                                          room_occupancy: Dict, rooms_count: int) -> bool:
        """
        使用平行處理方式檢查特定時間段是否有一間房可以使用
        
        Args:
            start_datetime: 開始時間
            duration_minutes: 持續時間（分鐘）
            room_occupancy: 房間占用情況
            rooms_count: 房間總數
        
        Returns:
            bool: 是否有一間房間可用
        """
        import concurrent.futures
        
        # 生成需要檢查的所有時間段
        required_time_slots = []
        current_time = start_datetime.replace(second=0, microsecond=0)
        # 調整到5分鐘間隔
        current_time = current_time.replace(minute=(current_time.minute // 5) * 5)
        
        end_time = current_time + timedelta(minutes=duration_minutes)
        
        while current_time < end_time:
            required_time_slots.append(current_time.strftime("%Y/%m/%d %H:%M"))
            current_time += timedelta(minutes=5)
        
        # 定義檢查單個房間可用性的函數
        def check_room_availability(room_id):
            room_available = True
            for time_slot in required_time_slots:
                if time_slot in room_occupancy and room_id in room_occupancy[time_slot]:
                    room_available = False
                    break
            return room_available
        
        # 使用平行處理同時檢查所有房間
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 將所有房間的檢查任務提交給執行器
            future_to_room = {
                executor.submit(check_room_availability, room_id): room_id 
                for room_id in range(1, rooms_count + 1)
            }
            
            # 一旦有任何一個房間返回可用，立即返回True
            for future in concurrent.futures.as_completed(future_to_room):
                try:
                    room_available = future.result()
                    if room_available:
                        # 取消所有其他正在執行的任務
                        for f in future_to_room:
                            if f != future and not f.done():
                                f.cancel()
                        return True
                except Exception as e:
                    print(f"檢查房間可用性時發生錯誤: {e}")
        
        # 如果沒有找到可用房間，返回False
        return False
        
    def _check_time_slot_availability_for_one_room(self, start_datetime: datetime, duration_minutes: int,
                                    room_occupancy: Dict, rooms_count: int) ->  bool:
        """
        检查特定时间段,是否有一間房可以使用
        
        Args:
            start_datetime: 开始时间
            duration_minutes: 持续时间（分钟）
            room_occupancy: 房间占用情况
            rooms_count: 房间总数
        
        Returns:
            Dict: 时间段可用性结果
        """
        # 生成需要检查的所有时间段
        required_time_slots = []
        current_time = start_datetime.replace(second=0, microsecond=0)
        # 调整到5分钟间隔
        current_time = current_time.replace(minute=(current_time.minute // 5) * 5)
        
        end_time = current_time + timedelta(minutes=duration_minutes)
        
        while current_time < end_time:
            required_time_slots.append(current_time.strftime("%Y/%m/%d %H:%M"))
            current_time += timedelta(minutes=5)
        
        # 检查每个房间的可用性,只要有任何一間房間是可以使用的，即返回True，無需再檢查其它的
        for room_id in range(1, rooms_count + 1):
            room_available = True
            for time_slot in required_time_slots:
                if time_slot in room_occupancy and room_id in room_occupancy[time_slot]:
                    room_available = False
                    break
            
            if room_available:
                return True
            
        
        return False
    

    def _check_time_slot_availability(self, start_datetime: datetime, duration_minutes: int,
                                    room_occupancy: Dict, rooms_count: int, guest_count: int) -> Dict:
        """
        检查特定时间段的房间可用性
        
        Args:
            start_datetime: 开始时间
            duration_minutes: 持续时间（分钟）
            room_occupancy: 房间占用情况
            rooms_count: 房间总数
            guest_count: 客人数量
        
        Returns:
            Dict: 时间段可用性结果
        """
        # 生成需要检查的所有时间段
        required_time_slots = []
        current_time = start_datetime.replace(second=0, microsecond=0)
        # 调整到5分钟间隔
        current_time = current_time.replace(minute=(current_time.minute // 5) * 5)
        
        end_time = current_time + timedelta(minutes=duration_minutes)
        
        while current_time < end_time:
            required_time_slots.append(current_time.strftime("%Y/%m/%d %H:%M"))
            current_time += timedelta(minutes=5)
        
        # 检查每个房间的可用性
        available_rooms = []
        
        for room_id in range(1, rooms_count + 1):
            room_available = True
            for time_slot in required_time_slots:
                if time_slot in room_occupancy and room_id in room_occupancy[time_slot]:
                    room_available = False
                    break
            
            if room_available:
                available_rooms.append(room_id)
        
        return {
            'available': len(available_rooms) >= guest_count,
            'available_rooms_count': len(available_rooms),
            'available_rooms': available_rooms[:guest_count] if len(available_rooms) >= guest_count else available_rooms,
            'required_time_slots': required_time_slots
        }
    
    def _find_alternative_time_slots(self, query_datetime: datetime, duration_minutes: int,
                                   room_occupancy: Dict, rooms_count: int, guest_count: int, date_str: str) -> List[Dict]:
        """
        寻找替代时间段
        
        Args:
            query_datetime: 原查询时间
            duration_minutes: 持续时间（分钟）
            room_occupancy: 房间占用情况
            rooms_count: 房间总数
            guest_count: 客人数量
            date_str: 日期字符串
        
        Returns:
            List[Dict]: 替代时间段建议
        """
        suggestions = []
        
        # 为每个房间寻找下一个可用时间
        for room_id in range(1, rooms_count + 1):
            next_available = self._find_next_available_time_for_room(
                room_id, query_datetime, duration_minutes, room_occupancy, date_str
            )
            if next_available:
                suggestions.append({
                    'room_id': room_id,
                    'next_available_time': next_available['time'],
                    'time_difference_minutes': next_available['time_diff']
                })
        
        # 如果需要多个房间，暫時簡化處理
        if guest_count > 1:
            # 多房間搜索功能暫時簡化
            suggestions.append({
                'type': 'multi_room_pending',
                'message': f'需要{guest_count}間房間，請聯繫店家安排',
                'time': None,
                'time_difference_minutes': 0,
                'guest_count': guest_count,
                'note': '多房間預約功能開發中'
            })
        
        # 按时间差排序，最接近的排在前面
        suggestions.sort(key=lambda x: x['time_difference_minutes'])
        
        return suggestions
    
    def _find_best_multi_guest_time_slot(self, store_id: int, date_str: str, query_datetime: datetime,
                                       duration_minutes: int, guest_count: int, masseur_names: List[str]) -> Optional[Dict]:
        """
        為多人預約尋找最佳時間段（同時考慮房間和師傅可用性）
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串
            query_datetime: 查詢時間
            duration_minutes: 持續時間（分鐘）
            guest_count: 客人數量
            masseur_names: 師傅姓名列表
        
        Returns:
            Optional[Dict]: 最佳時間段建議
        """
        # 從查詢時間開始，每15分鐘檢查一次（提高效率）
        current_check_time = query_datetime.replace(second=0, microsecond=0)
        current_check_time = current_check_time.replace(minute=(current_check_time.minute // 15) * 15)
        
        # 最多檢查到當天晚上11:00
        end_of_day = datetime.strptime(f"{date_str} 23:00", "%Y/%m/%d %H:%M")
        
        best_options = []
        
        while current_check_time <= end_of_day and len(best_options) < 3:
            check_time_str = current_check_time.strftime("%H:%M")
            
            # 檢查房間可用性
            room_result = self._check_room_availability(
                store_id, date_str, check_time_str, duration_minutes, guest_count
            )
            
            if room_result['available_at_requested_time']:
                # 檢查師傅可用性
                masseur_result = self._check_masseur_availability(
                    store_id, date_str, check_time_str, duration_minutes, masseur_names
                )
                
                available_masseurs = [m for m in masseur_result['masseur_status'] if m['available']]
                
                if len(available_masseurs) >= guest_count:
                    time_diff = int((current_check_time - query_datetime).total_seconds() / 60)
                    best_options.append({
                        'time': check_time_str,
                        'time_difference_minutes': time_diff,
                        'available_rooms': room_result.get('available_rooms', [])[:guest_count],
                        'available_masseurs': available_masseurs[:guest_count],
                        'room_count': len(room_result.get('available_rooms', [])),
                        'masseur_count': len(available_masseurs)
                    })
            
            current_check_time += timedelta(minutes=15)
        
        return best_options[0] if best_options else None
    
    def _find_next_available_time_for_room(self, room_id: int, start_datetime: datetime,
                                         duration_minutes: int, room_occupancy: Dict, date_str: str) -> Optional[Dict]:
        """
        为特定房间寻找下一个可用时间
        
        Args:
            room_id: 房间ID
            start_datetime: 开始搜索时间
            duration_minutes: 持续时间（分钟）
            room_occupancy: 房间占用情况
            date_str: 日期字符串
        
        Returns:
            Optional[Dict]: 下一个可用时间信息
        """
        # 从查询时间开始，每5分钟检查一次
        current_check_time = start_datetime.replace(second=0, microsecond=0)
        current_check_time = current_check_time.replace(minute=(current_check_time.minute // 5) * 5)
        
        # 最多检查到当天晚上11:55
        end_of_day = datetime.strptime(f"{date_str} 23:55", "%Y/%m/%d %H:%M")
        
        while current_check_time <= end_of_day:
            # 检查这个房间在这个时间段是否可用
            available = True
            check_end_time = current_check_time + timedelta(minutes=duration_minutes)
            
            temp_time = current_check_time
            while temp_time < check_end_time:
                time_slot = temp_time.strftime("%Y/%m/%d %H:%M")
                if time_slot in room_occupancy and room_id in room_occupancy[time_slot]:
                    available = False
                    break
                temp_time += timedelta(minutes=5)
            
            if available:
                time_diff = int((current_check_time - start_datetime).total_seconds() / 60)
                return {
                    'time': current_check_time.strftime("%H:%M"),
                    'time_diff': time_diff
                }
            
            current_check_time += timedelta(minutes=5)
        
        return None
    
    def _find_multi_room_available_time(self, start_datetime: datetime, duration_minutes: int,
                                      room_occupancy: Dict, rooms_count: int, guest_count: int, date_str: str) -> List[Dict]:
        """
        寻找满足多房间需求的可用时间
        
        Args:
            start_datetime: 开始搜索时间
            duration_minutes: 持续时间（分钟）
            room_occupancy: 房间占用情况
            rooms_count: 房间总数
            guest_count: 客人数量
            date_str: 日期字符串
        
        Returns:
            List[Dict]: 多房间可用时间建议
        """
        suggestions = []
        
        # 从查询时间开始，每5分钟检查一次
        current_check_time = start_datetime.replace(second=0, microsecond=0)
        current_check_time = current_check_time.replace(minute=(current_check_time.minute // 5) * 5)
        
        # 最多检查到当天晚上11:55
        end_of_day = datetime.strptime(f"{date_str} 23:55", "%Y/%m/%d %H:%M")
        
        while current_check_time <= end_of_day:
            availability_result = self._check_time_slot_availability(
                current_check_time, duration_minutes, room_occupancy, rooms_count, guest_count
            )
            
            if availability_result['available']:
                time_diff = int((current_check_time - start_datetime).total_seconds() / 60)
                suggestions.append({
                    'type': 'multi_room',
                    'time': current_check_time.strftime("%H:%M"),
                    'time_difference_minutes': time_diff,
                    'available_rooms': availability_result['available_rooms'],
                    'guest_count': guest_count
                })
                
                # 找到第一个就可以了，因为我们要最接近的时间
                break
            
            current_check_time += timedelta(minutes=5)
        
        return suggestions
    
    def _check_masseur_availability(self, store_id: int, date_str: str, time_str: str,
                                  duration_minutes: int, masseur_names: List[str]) -> Dict:
        """
        检查师傅可用性（包含排班和预约冲突检查）
        
        Args:
            store_id: 店家ID
            date_str: 日期字符串
            time_str: 开始时间字符串
            duration_minutes: 持续时间（分钟，已包含缓冲）
            masseur_names: 师傅姓名列表
        
        Returns:
            Dict: 师傅可用性结果
        """
        result = {
            'requested_time': time_str,
            'duration_minutes': duration_minutes,
            'masseur_status': []
        }
        
        # 如果没有指定师傅，获取该店家的所有师傅
        if not masseur_names:
            all_staffs = self.staff_manager.get_all_staffs()
            store_staffs = [staff for staff in all_staffs if staff.get('storeid') == store_id]
            masseur_names = [staff['name'] for staff in store_staffs]
        
        # 获取指定日期的所有预约
        tasks = self.task_manager.get_tasks_by_date(date_str.replace('/', '-'))
        store_tasks = [task for task in tasks if task.get('storeid') == store_id]
        
        # 解析查询时间
        query_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M")
        query_end_datetime = query_datetime + timedelta(minutes=duration_minutes)
        
        # 检查每个师傅的可用性
        for masseur_name in masseur_names:
            masseur_info = self.staff_manager.get_staff_by_name(masseur_name)
            if not masseur_info:
                result['masseur_status'].append({
                    'name': masseur_name,
                    'available': False,
                    'reason': '师傅不存在',
                    'staff_id': None,
                    'schedule_available': False,
                    'booking_conflicts': [],
                    'schedule_details': None
                })
                continue
            
            # 检查师傅是否属于该店家
            if masseur_info.get('storeid') != store_id:
                result['masseur_status'].append({
                    'name': masseur_name,
                    'available': False,
                    'reason': '师傅不属于该店家',
                    'staff_id': masseur_info['id'],
                    'schedule_available': False,
                    'booking_conflicts': [],
                    'schedule_details': None
                })
                continue
            
            # 1. 检查师傅排班情况
            schedule_data = self.schedule_manager.get_schedule_by_name(masseur_name, date_str)
            schedule_available = False
            schedule_details = {
                'has_schedule': False,
                'working_during_query_time': False,
                'query_time_blocks': []
            }
            
            if schedule_data:
                schedule_details['has_schedule'] = True
                schedule = schedule_data.get('schedule', [])
                
                # 计算查询时间段对应的5分钟块索引
                query_start_minutes = query_datetime.hour * 60 + query_datetime.minute
                query_end_minutes = query_end_datetime.hour * 60 + query_end_datetime.minute
                
                # 如果跨天，结束时间最多到23:59
                if query_end_minutes >= 24 * 60:
                    query_end_minutes = 24 * 60 - 1
                
                start_block = query_start_minutes // 5
                end_block = query_end_minutes // 5
                
                # 检查查询时间段内的所有5分钟块
                working_blocks = []
                all_blocks_working = True
                
                for block_idx in range(start_block, min(end_block + 1, 288)):
                    is_working = schedule[block_idx] if block_idx < len(schedule) else False
                    # 計算時間標籤
                    total_minutes = block_idx * 5
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    time_label = f"{hours:02d}:{minutes:02d}"
                    
                    working_blocks.append({
                        'block_index': block_idx,
                        'time': time_label,
                        'working': is_working
                    })
                    if not is_working:
                        all_blocks_working = False
                
                schedule_details['working_during_query_time'] = all_blocks_working
                schedule_details['query_time_blocks'] = working_blocks
                schedule_available = all_blocks_working
            
            # 2. 检查师傅在查询时间段的预约冲突
            masseur_tasks = [task for task in store_tasks if task.get('staff_id') == masseur_info['id']]
            booking_conflicts = []
            no_booking_conflicts = True
            
            for task in masseur_tasks:
                if not task.get('start') or not task.get('end'):
                    continue
                
                task_start = datetime.fromisoformat(task['start'].replace('Z', '+00:00'))
                task_end = datetime.fromisoformat(task['end'].replace('Z', '+00:00'))
                # 为任务结束时间添加15分钟缓冲
                task_end_with_buffer = task_end + timedelta(minutes=15)
                
                # 检查时间是否重叠
                if (query_datetime < task_end_with_buffer and query_end_datetime > task_start):
                    no_booking_conflicts = False
                    booking_conflicts.append({
                        'task_id': task['id'],
                        'customer': task.get('customer_name', ''),
                        'start': task_start.strftime("%H:%M"),
                        'end': task_end.strftime("%H:%M"),
                        'end_with_buffer': task_end_with_buffer.strftime("%H:%M"),
                        'course_name': task.get('course_name', '')
                    })
            
            # 3. 综合判断师傅是否可用
            final_available = schedule_available and no_booking_conflicts
            
            # 4. 生成可用性原因说明
            if final_available:
                reason = '可预约'
            else:
                reasons = []
                if not schedule_available:
                    if not schedule_details['has_schedule']:
                        reasons.append('无排班')
                    else:
                        reasons.append('排班时间不符')
                if not no_booking_conflicts:
                    reasons.append('已有预约冲突')
                reason = '、'.join(reasons)
            
            result['masseur_status'].append({
                'name': masseur_name,
                'available': final_available,
                'reason': reason,
                'staff_id': masseur_info['id'],
                'schedule_available': schedule_available,
                'booking_conflicts': booking_conflicts,
                'schedule_details': schedule_details
            })
        
        return result
    
    def _generate_appointment_recommendation(self, room_result: Dict, masseur_result: Dict, query_data: Dict) -> Dict:
        """
        生成预约建议
        
        Args:
            room_result: 房间可用性结果
            masseur_result: 师傅可用性结果
            query_data: 原始查询数据
        
        Returns:
            Dict: 预约建议
        """
        recommendation = {
            'can_book_at_requested_time': False,
            'available_masseurs_count': 0,
            'total_masseurs_checked': len(masseur_result['masseur_status']),
            'room_status': {
                'available': room_result['available_at_requested_time'],
                'available_rooms_count': room_result['available_rooms_count']
            },
            'masseur_summary': {
                'available': [],
                'unavailable_due_to_schedule': [],
                'unavailable_due_to_booking': [],
                'unavailable_other': []
            },
            'booking_feasibility': {},
            'alternative_suggestions': []
        }
        
        # 分析师傅可用性
        available_masseurs = []
        for masseur in masseur_result['masseur_status']:
            if masseur['available']:
                available_masseurs.append(masseur)
                recommendation['masseur_summary']['available'].append({
                    'name': masseur['name'],
                    'staff_id': masseur['staff_id'],
                    'reason': masseur['reason']
                })
            else:
                # 分類不可用的原因
                if '排班' in masseur['reason'] or '无排班' in masseur['reason']:
                    recommendation['masseur_summary']['unavailable_due_to_schedule'].append({
                        'name': masseur['name'],
                        'reason': masseur['reason'],
                        'schedule_details': masseur.get('schedule_details')
                    })
                elif '冲突' in masseur['reason'] or '已有预约' in masseur['reason']:
                    recommendation['masseur_summary']['unavailable_due_to_booking'].append({
                        'name': masseur['name'],
                        'reason': masseur['reason'],
                        'conflicts': masseur.get('booking_conflicts', [])
                    })
                else:
                    recommendation['masseur_summary']['unavailable_other'].append({
                        'name': masseur['name'],
                        'reason': masseur['reason']
                    })
        
        recommendation['available_masseurs_count'] = len(available_masseurs)
        
        # 判断是否可以在请求时间预约
        room_available = room_result['available_at_requested_time']
        required_masseurs = query_data['count']
        sufficient_masseurs = len(available_masseurs) >= required_masseurs
        
        recommendation['can_book_at_requested_time'] = room_available and sufficient_masseurs
        
        # 详细的预约可行性分析
        recommendation['booking_feasibility'] = {
            'room_requirement_met': room_available,
            'masseur_requirement_met': sufficient_masseurs,
            'required_rooms': required_masseurs,
            'available_rooms': room_result['available_rooms_count'],
            'required_masseurs': required_masseurs,
            'available_masseurs': len(available_masseurs)
        }
        
        if recommendation['can_book_at_requested_time']:
            # 可以预约的情况
            recommendation['booking_details'] = {
                'time': query_data['time'],
                'duration': f"{query_data['project']}分鐘 (含15分鐘緩衝)",
                'available_rooms': room_result.get('available_rooms', [])[:required_masseurs],
                'recommended_masseurs': available_masseurs[:required_masseurs],
                'message': '可以在请求时间预约',
                'booking_instructions': f"為{required_masseurs}位客人安排{query_data['project']}分鐘課程"
            }
        else:
            # 不能预约的情况，生成替代建议
            issues = []
            if not room_available:
                issues.append(f"房間不足 (需要{required_masseurs}間，可用{room_result['available_rooms_count']}間)")
            if not sufficient_masseurs:
                issues.append(f"師傅不足 (需要{required_masseurs}位，可用{len(available_masseurs)}位)")
            
            recommendation['booking_issues'] = issues
            
            # 生成时间替代建议
            if room_result.get('room_suggestions'):
                for suggestion in room_result['room_suggestions'][:5]:  # 取前5个建议
                    alt_suggestion = {
                        'type': 'time_alternative',
                        'suggested_time': suggestion.get('next_available_time') or suggestion.get('time'),
                        'time_difference_minutes': suggestion['time_difference_minutes'],
                        'reason': "房間可用性",
                        'room_info': suggestion
                    }
                    
                    # 检查在建议时间师傅是否可用
                    if suggestion.get('time'):
                        # 这里可以进一步检查师傅在建议时间的可用性
                        alt_suggestion['masseur_status'] = 'need_recheck'
                        alt_suggestion['note'] = '需要重新檢查師傅在此時間的可用性'
                    
                    recommendation['alternative_suggestions'].append(alt_suggestion)
            
            # 师傅建议
            if len(available_masseurs) > 0 and not room_available:
                recommendation['alternative_suggestions'].append({
                    'type': 'masseur_available',
                    'message': f'有{len(available_masseurs)}位師傅可用，但房間不足',
                    'available_masseurs': [m['name'] for m in available_masseurs],
                    'suggestion': '請考慮調整時間或減少人數'
                })
            
            if not recommendation['alternative_suggestions']:
                recommendation['alternative_suggestions'].append({
                    'type': 'no_availability',
                    'message': '當天在此時間無法安排預約',
                    'suggestions': [
                        '請嘗試其他時間段',
                        '請嘗試其他日期',
                        '請聯繫店家了解更多選項'
                    ]
                })
        
        return recommendation

class CommonUtils:
    """通用工具类"""
    
    @staticmethod
    def format_time_to_5min_interval(time_str: str) -> str:
        """
        将时间格式化为5分钟间隔
        
        Args:
            time_str: 时间字符串，格式为 "HH:MM"
        
        Returns:
            str: 格式化后的时间字符串
        """
        try:
            time_obj = datetime.strptime(time_str, "%H:%M")
            # 将分钟调整到5分钟的倍数
            adjusted_minutes = (time_obj.minute // 5) * 5
            adjusted_time = time_obj.replace(minute=adjusted_minutes)
            return adjusted_time.strftime("%H:%M")
        except ValueError:
            return time_str
    
    @staticmethod
    def validate_date_format(date_str: str) -> bool:
        """
        验证日期格式是否正确
        
        Args:
            date_str: 日期字符串，格式为 "YYYY/MM/DD"
        
        Returns:
            bool: 是否为有效格式
        """
        try:
            datetime.strptime(date_str, "%Y/%m/%d")
            return True
        except ValueError:
            return False
    
    @staticmethod
    def convert_date_format(date_str: str, from_format: str, to_format: str) -> str:
        """
        转换日期格式
        
        Args:
            date_str: 原日期字符串
            from_format: 原格式
            to_format: 目标格式
        
        Returns:
            str: 转换后的日期字符串
        """
        try:
            date_obj = datetime.strptime(date_str, from_format)
            return date_obj.strftime(to_format)
        except ValueError:
            return date_str
    
    @staticmethod
    def getPreferStore(date_str: str, staff_name: str) -> List[int]:
        """
        獲取師傅偏好的店家
        
        Args:
            date_str: 日期字符串，格式為 "YYYY/MM/DD"
            staff_name: 師傅姓名
        
        Returns:
            List[int]: 店家ID列表，[1]代表西門, [2]代表延吉, [1,2]代表兩店皆可
        """
        connection = db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # 優先取得師傅在指定日期的工作列表
            query = """
                SELECT `storeid` 
                FROM Tasks 
                WHERE DATE(start) = %s AND `staff_name` = %s 
                ORDER BY `end` DESC 
                LIMIT 0,1
            """
            cursor.execute(query, (date_str.replace('/', '-'), staff_name))
            task = cursor.fetchone()
            
            if task and 'storeid' in task:
                return [task['storeid']]
            
            # 若無工作資料，從 Staffs 表取得 instores 值
            query = """
                SELECT `instores` 
                FROM Staffs 
                WHERE `name` = %s AND `storeid` = 1
            """
            cursor.execute(query, (staff_name,))
            staff = cursor.fetchone()
            
            if staff and 'instores' in staff and staff['instores']:
                try:
                    # 嘗試將字符串解析為JSON數組
                    import json
                    return json.loads(staff['instores'])
                except:
                    # 如果解析失敗，返回空列表
                    return []
            
            return []
            
        except Exception as e:
            print(f"獲取師傅偏好店家錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

# 创建全局实例
room_status_manager = RoomStatusManager()
