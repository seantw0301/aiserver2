from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from .database import db_config
from .staffs import StaffManager

class ScheduleManager:
    """班表管理模塊"""
    
    # 時間區間對應表 (30分鐘間隔)
    TIME_SLOTS = [
        '0800', '0830', '0900', '0930', '1000', '1030',
        '1100', '1130', '1200', '1230', '1300', '1330',
        '1400', '1430', '1500', '1530', '1600', '1630',
        '1700', '1730', '1800', '1830', '1900', '1930',
        '2000', '2030', '2100', '2130', '2200', '2230',
        '2300', '2330'
    ]
    
    def __init__(self):
        self.db_config = db_config
        self.staff_manager = StaffManager()
    
    def get_sch_table_lastupdate_time(self) -> Optional[datetime]:
        """獲取sch表的最後更新時間"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT UPDATE_TIME 
            FROM information_schema.tables 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'sch'
            """
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result and result.get('UPDATE_TIME'):
                #確認轉成datetime格式
                update_time = result['UPDATE_TIME']
                if isinstance(update_time, str):
                    update_time = datetime.fromisoformat(update_time)
                print(f"sch表最後更新時間: {update_time}")
                return update_time
            else:
                print("sch表最後更新時間: 無法獲取")
                return None
            
        except Exception as e:
            print(f"獲取sch表更新時間錯誤: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
            connection.close()
    
    def _convert_to_5min_blocks(self, schedule_data: Dict) -> List[bool]:
        """將30分鐘間隔的班表轉換為5分鐘間隔的班表，並在排班結束後加上30分鐘緩衝"""
        # 一天24小時，每5分鐘一個block = 24 * 12 = 288個blocks, 再額外緩衝30分鐘 +6 
        block_len= 288 +6 
        blocks = [False] * block_len
        
        for time_slot in self.TIME_SLOTS:
            if schedule_data.get(time_slot, 0) == 1:
                # 計算實際時間對應的 block 索引
                # TIME_SLOTS 從 08:00 開始，每30分鐘一個時段
                hour = int(time_slot[:2])
                minute = int(time_slot[2:])
                
                # 計算從 00:00 開始的總分鐘數
                total_minutes = hour * 60 + minute
                
                # 計算對應的 5 分鐘 block 索引（從 00:00 開始）
                start_block = total_minutes // 5
                # 每個時段涵蓋 30 分鐘 = 6 個 5 分鐘 blocks
                end_block = start_block + 6
                
                for j in range(start_block, end_block):
                    if j < block_len:  # 確保不超出範圍
                        blocks[j] = True
        
        # 在排班結束後加上 30 分鐘緩衝
        # 找到最後一個有排班的 block
        last_scheduled_block = -1
        for i in range(block_len - 1, -1, -1):
            if blocks[i]:
                last_scheduled_block = i
                break
        
        # 如果有排班，在最後一個排班 block 之後加上 30 分鐘（6 個 blocks）緩衝
        #if last_scheduled_block >= 0:
        #    buffer_end = min(last_scheduled_block + 7, block_len)  # +7 因為要從下一個 block 開始加 6 個
        #    for i in range(last_scheduled_block + 1, buffer_end):
        #        blocks[i] = True
                        
        return blocks
    
 
    def _get_tasks_blocks(self, staff_name: str, target_date: str, cursor) -> List[bool]:
        """獲取師傅在指定日期的已有工作時段，轉換為5分鐘間隔的 blocks"""
        # 初始化所有時段為可用（False表示沒有工作）
        task_blocks = [False] * (288 + 6)
        
        try:
            # 查詢該師傅當天的工作安排
            query = """
                SELECT start, end, mins FROM Tasks 
                WHERE staff_name = %s AND DATE(start) = %s
            """
            cursor.execute(query, (staff_name, target_date))
            tasks = cursor.fetchall()
            
            for task in tasks:
                start_time = task['start']
                mins = task.get('mins', 0)
                
                # 如果是字符串，轉換為 datetime
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                
                # 計算實際結束時間（開始時間 + 工作時長）
                actual_end_time = start_time + timedelta(minutes=mins)
                # 計算緩衝結束時間（實際結束時間 + 15分鐘緩衝）
                buffer_end_time = actual_end_time + timedelta(minutes=15)
                
                # 轉換開始時間為 block 索引
                start_hour = start_time.hour
                start_minute = start_time.minute
                start_block = start_hour * 12 + start_minute // 5
                
                # 轉換緩衝結束時間為 block 索引
                buffer_end_hour = buffer_end_time.hour
                buffer_end_minute = buffer_end_time.minute
                buffer_end_block = buffer_end_hour * 12 + buffer_end_minute // 5
                
                # 如果緩衝結束時間的分鐘數不是5的倍數，需要向上取整到下一個block
                if buffer_end_minute % 5 != 0:
                    buffer_end_block += 1
                
                # 標記工作時段為不可用（True表示有工作）
                # 需要處理跨日的情況
                if buffer_end_block <= start_block:
                    # 跨日情況：從 start_block 到當天結束 (288)，然後從第二天開始 (0) 到 buffer_end_block
                    for block in range(start_block, 288):
                        task_blocks[block] = True
                    for block in range(0, buffer_end_block):
                        task_blocks[block] = True
                    print(f"工作安排: {start_time.strftime('%H:%M')} - {actual_end_time.strftime('%H:%M')} + 15分緩衝 (跨日)")
                    print(f"占用blocks: {start_block}-287 (當日), 0-{buffer_end_block-1} (次日)")
                else:
                    # 同日情況：從 start_block 到 buffer_end_block
                    for block in range(start_block, min(buffer_end_block, 288)):
                        task_blocks[block] = True
                    print(f"工作安排: {start_time.strftime('%H:%M')} - {actual_end_time.strftime('%H:%M')} + 15分緩衝")
                    print(f"占用blocks: {start_block}-{min(buffer_end_block, 288)-1}")
            
            return task_blocks
            
        except Exception as e:
            print(f"獲取工作時段錯誤: {e}")
            return [False] * 288
    
    def _get_time_label_for_block(self, block_index: int) -> str:
        """根據block索引獲取時間標籤"""
        total_minutes = block_index * 5
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}"
    
    def get_schedule_by_name(self, staff_name: str, target_date: str, include_tasks: bool = True) -> Optional[Dict]:
        """根據師傅姓名和日期獲取班表 (5分鐘間隔)，可選是否包含已有工作時段"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # 直接通過 staff_name 獲取班表
            # 移除 status = 1 的限制，因為班表數據本身已經表示排班
            query = """
                SELECT * FROM sch 
                WHERE staff_name = %s AND date = %s
            """
            cursor.execute(query, (staff_name, target_date))
            schedule = cursor.fetchone()
            
            if not schedule:
                # 如果沒有找到班表，返回全部為False的陣列
                return {
                    'staff_name': staff_name,
                    'date': target_date,
                    'schedule': [False] * 288,
                    'message': '該日期沒有班表資料'
                }
            
            # 獲取 staff_id
            staff_id = schedule.get('staff_id')
            
            # 轉換為5分鐘間隔的班表
            blocks = self._convert_to_5min_blocks(schedule)
            
            # 如果不包含工作時段（用於班表顯示），不添加額外的緩衝
            if not include_tasks:
                # 移除 _convert_to_5min_blocks 添加的30分鐘緩衝
                blocks = blocks[:288]
            else:
                # 在班表末尾加上15分鐘的緩衝（將最後一個有班的時段後面加上3個blocks的緩衝）
                # 找到最後一個有班的block
                last_working_block = -1
                for i in range(len(blocks) - 1, -1, -1):
                    if blocks[i]:
                        last_working_block = i
                        break
                
                # 如果有班表，在末尾加上15分鐘緩衝（3個5分鐘blocks）
                if last_working_block >= 0:
                    for i in range(last_working_block + 1, min(last_working_block + 4, 288)):
                        blocks[i] = True
            
            # 如果需要包含已有工作時段，則將工作時段設為不可用
            if include_tasks:
                tasks_blocks = self._get_tasks_blocks(staff_name, target_date, cursor)
                # 將已有工作時段設為不可用（False）
                # 正確邏輯: 可用 = 有排班 AND 無工作佔用
                for i in range(len(blocks)):
                    if tasks_blocks[i]:  # 如果有工作佔用，設為不可用
                        blocks[i] = False
            
            return {
                'staff_name': staff_name,
                'date': target_date,
                'schedule': blocks,
                'staff_id': staff_id,
                'include_tasks': include_tasks
            }
            
        except Exception as e:
            print(f"獲取班表錯誤: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_schedule_by_date(self, target_date: str) -> Dict:

        """獲取指定日期所有師傅的班表 (5分鐘間隔)"""
        connection = self.db_config.get_connection()
        if not connection:
            return {}
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # 獲取該日期所有的班表
            query = """
                SELECT s.*, st.name as staff_name
                FROM sch s
                JOIN Staffs st ON s.staff_id = st.id
                WHERE s.date = %s AND s.status = 1 AND st.enable = 1
                ORDER BY st.name
            """
            cursor.execute(query, (target_date,))
            schedules = cursor.fetchall()
            
            result = {
                'date': target_date,
                'staffs': {}
            }
            
            # 處理每個師傅的班表
            for schedule in schedules:
                staff_name = schedule['staff_name']
                blocks = self._convert_to_5min_blocks(schedule)
                
                result['staffs'][staff_name] = {
                    'staff_id': schedule['staff_id'],
                    'schedule': blocks
                }
            
            # 獲取所有啟用的師傅，確保沒有班表的師傅也包含在結果中
            all_staffs = self.staff_manager.get_all_staffs()
            for staff in all_staffs:
                staff_name = staff['name']
                if staff_name not in result['staffs']:
                    result['staffs'][staff_name] = {
                        'staff_id': staff['id'],
                        'schedule': [False] * 288
                    }
            
            return result
            
        except Exception as e:
            print(f"獲取日期班表錯誤: {e}")
            return {}
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_schedule_block_by_date_24H(self, target_date: str) -> Dict:
        """獲取指定日期所有師傅的24小時班表 (00:00-24:00，5分鐘間隔),再多加30分鐘緩衝 ÷6""" 
        block_len= 288 +6  
        result = {
                'date': target_date,
                'staffs': {}
            }
        # 獲取所有師傅，預設其288個時間塊為False（False表示該時間段無班表）
        all_staffs = self.staff_manager.get_all_staffs()
        for staff in all_staffs:
            staff_name = staff['name']
            result['staffs'][staff_name] = {
                'staff_id': staff['id'],
                'schedule': [False] * block_len
            }

        connection = self.db_config.get_connection()
        if not connection:
            return {}
        try:
            cursor = connection.cursor(dictionary=True)
            
            # 獲取該日期所有的班表
            query = """
                SELECT *
                FROM sch 
                WHERE date = %s and status = 1
                ORDER BY staff_name
            """
            cursor.execute(query, (target_date,))
            schedules = cursor.fetchall()
                    
            # 處理每個師傅的班表,將有排表的block 設置為True 
            for schedule in schedules:
                staff_name = schedule['staff_name']
                blocks = self._convert_to_5min_blocks(schedule)           
                result['staffs'][staff_name] = {
                    'staff_id': schedule['staff_id'],
                    'schedule': blocks
                }
            
            
            return result
            
        except Exception as e:
            print(f"獲取日期班表錯誤: {e}")
            return {}
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_schedule_with_time_labels(self, staff_name: str, target_date: str, include_tasks: bool = True) -> Optional[Dict]:
        """獲取帶時間標籤的班表 (用於除錯和展示)"""
        schedule_data = self.get_schedule_by_name(staff_name, target_date, include_tasks)
        if not schedule_data:
            return None
        
        # 添加時間標籤
        schedule_with_labels = {}
        for i, is_working in enumerate(schedule_data['schedule']):
            time_label = self._get_time_label_for_block(i)
            schedule_with_labels[time_label] = is_working
        
        return {
            'staff_name': staff_name,
            'date': target_date,
            'schedule_with_labels': schedule_with_labels,
            'total_blocks': len(schedule_data['schedule']),
            'working_blocks': sum(schedule_data['schedule']),
            'include_tasks': include_tasks
        }
    
    def get_available_time_blocks(self, staff_name: str, target_date: str) -> Optional[Dict]:
        """獲取師傅的可用時間段（排除已有工作安排）"""
        return self.get_schedule_by_name(staff_name, target_date, include_tasks=True)
    
    def get_detailed_schedule_analysis(self, staff_name: str, target_date: str) -> Optional[Dict]:
        """獲取詳細的班表分析，包含原始班表和可用時間"""
        # 獲取原始班表（不包含工作安排）
        original_schedule = self.get_schedule_by_name(staff_name, target_date, include_tasks=False)
        if not original_schedule:
            return None
        
        # 獲取包含工作安排的可用時間
        available_schedule = self.get_schedule_by_name(staff_name, target_date, include_tasks=True)
        
        # 計算工作安排時段
        work_blocks = []
        for i in range(288):
            if original_schedule['schedule'][i] and not available_schedule['schedule'][i]:
                work_blocks.append(i)
        
        return {
            'staff_name': staff_name,
            'date': target_date,
            'original_schedule': original_schedule['schedule'],  # 原始班表
            'available_schedule': available_schedule['schedule'],  # 可用時間
            'work_blocks': work_blocks,  # 已有工作的時段
            'total_shift_blocks': sum(original_schedule['schedule']),  # 總班表時間
            'available_blocks': sum(available_schedule['schedule']),  # 可用時間
            'work_occupied_blocks': len(work_blocks)  # 被工作占用的時間
        }

    def get_scheduled_staff_names(self, target_date: str) -> List[str]:
        """
        獲取指定日期有排班的師傅名字列表(不重複)
        
        Args:
            target_date: 目標日期，格式為 "YYYY-MM-DD" 或 "YYYY/MM/DD"
            
        Returns:
            List[str]: 有排班的師傅名字列表
        """
        # 檢查並轉換日期格式
        if '/' in target_date:
            target_date = target_date.replace('/', '-')
        
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            # 查詢該日期有排班且有任一時段不為0的師傅
            # 移除 status = 1 的限制，因為排班表中的師傅即使未被激活也應被考慮
            query = """
                SELECT DISTINCT staff_name
                FROM sch
                WHERE date = %s AND (
                    `0800`=1 OR `0830`=1 OR `0900`=1 OR `0930`=1 OR `1000`=1 OR `1030`=1 OR
                    `1100`=1 OR `1130`=1 OR `1200`=1 OR `1230`=1 OR `1300`=1 OR `1330`=1 OR
                    `1400`=1 OR `1430`=1 OR `1500`=1 OR `1530`=1 OR `1600`=1 OR `1630`=1 OR
                    `1700`=1 OR `1730`=1 OR `1800`=1 OR `1830`=1 OR `1900`=1 OR `1930`=1 OR
                    `2000`=1 OR `2030`=1 OR `2100`=1 OR `2130`=1 OR `2200`=1 OR `2230`=1 OR
                    `2300`=1 OR `2330`=1
                )
            """
            cursor.execute(query, (target_date,))
            results = cursor.fetchall()
            # 提取師傅名字
            staff_names = [result['staff_name'] for result in results]
            print(f"[DEBUG] 日期 {target_date} 有排班的師傅: {staff_names}")
            return staff_names
            
        except Exception as e:
            print(f"獲取排班師傅列表錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_schedule_pretty_display(self, staff_name: str, target_date: str, include_tasks: bool = True) -> str:
        """以易讀的格式顯示師傅的排班，左側顯示時間"""
        schedule_data = self.get_schedule_by_name(staff_name, target_date, include_tasks)
        if not schedule_data:
            return f"無法獲取師傅 {staff_name} 在 {target_date} 的排班信息"
        
        # 用於轉換 block 索引到時間標籤
        def get_time_label(block_index):
            total_minutes = block_index * 5
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours:02d}:{minutes:02d}"
        
        # 獲取開始和結束時間 (08:00 - 23:55)
        start_block = 8 * 12  # 08:00 對應的 block 索引
        end_block = 24 * 12 - 1  # 23:55 對應的 block 索引
        
        result = []
        result.append(f"師傅: {staff_name}  日期: {target_date}")
        result.append("=" * 60)
        result.append("時間    | 排班狀態 (每格 5 分鐘，● 表示有班，○ 表示無班)")
        result.append("-" * 60)
        
        # 每行顯示一個小時
        for hour in range(8, 24):
            hour_start_block = hour * 12
            time_label = f"{hour:02d}:00"
            
            # 創建一個小時內的排班狀態
            status_symbols = []
            for i in range(12):  # 每小時 12 個 5 分鐘區塊
                block_index = hour_start_block + i
                if block_index < len(schedule_data['schedule']):
                    if schedule_data['schedule'][block_index]:
                        status_symbols.append("●")  # 有班
                    else:
                        status_symbols.append("○")  # 無班
            
            # 每 6 個區塊 (30 分鐘) 加一個空格，增加可讀性
            formatted_symbols = []
            for i in range(0, 12, 6):
                formatted_symbols.append("".join(status_symbols[i:i+6]))
            
            result.append(f"{time_label} | {' '.join(formatted_symbols)}")
        
        result.append("=" * 60)
        result.append("● = 有班 (可預約)    ○ = 無班 (不可預約)")
        if include_tasks:
            result.append("注意: 已扣除現有工作時段")
        
        return "\n".join(result)
