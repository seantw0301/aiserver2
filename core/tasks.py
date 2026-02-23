from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from .database import db_config
from .staffs import StaffManager
from .store import StoreManager

class TaskManager:
    """預約任務管理模塊"""
    
    def __init__(self):
        self.db_config = db_config
        self.staff_manager = StaffManager()
        self.store_manager = StoreManager()
    
    def get_tasks_table_lastupdate_time(self) -> Optional[datetime]:
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
            AND TABLE_NAME = 'Tasks'
            """
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result and result.get('UPDATE_TIME'):
                #確認轉成datetime格式
                update_time = result['UPDATE_TIME']
                if isinstance(update_time, str):
                    update_time = datetime.fromisoformat(update_time)
                print(f"Tasks表最後更新時間: {update_time}")
                return update_time
            else:
                print("Tasks表最後更新時間: 無法獲取")
                return None
            
        except Exception as e:
            print(f"獲取Tasks表更新時間錯誤: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
            connection.close()

        return
    
    def get_all_tasks(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """獲取所有預約列表（支援分頁）"""
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, customer_name, start, end, staff_id, course_id, 
                       price, discount, master_income, company_income, 
                       `desc`, ispaid, mins, storeid, staff_name, note, 
                       course_name, exdata, history, memberid, history_pri, 
                       usetickettype, real_master_income, real_company_income, 
                       paytype, is_confirmed
                FROM Tasks 
                ORDER BY start DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, (limit, offset))
            tasks = cursor.fetchall()
            
            # 處理日期時間格式
            for task in tasks:
                if task.get('start'):
                    task['start'] = task['start'].isoformat()
                if task.get('end'):
                    task['end'] = task['end'].isoformat()
                if task.get('is_confirmed') is not None:
                    # 將 bytes 轉換為 boolean
                    task['is_confirmed'] = bool(task['is_confirmed'])
            
            return tasks
            
        except Exception as e:
            print(f"獲取預約列表錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """根據ID獲取預約資訊"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, customer_name, start, end, staff_id, course_id, 
                       price, discount, master_income, company_income, 
                       `desc`, ispaid, mins, storeid, staff_name, note, 
                       course_name, exdata, history, memberid, history_pri, 
                       usetickettype, real_master_income, real_company_income, 
                       paytype, is_confirmed
                FROM Tasks 
                WHERE id = %s
            """
            cursor.execute(query, (task_id,))
            task = cursor.fetchone()
            
            if task:
                # 處理日期時間格式
                if task.get('start'):
                    task['start'] = task['start'].isoformat()
                if task.get('end'):
                    task['end'] = task['end'].isoformat()
                if task.get('is_confirmed') is not None:
                    task['is_confirmed'] = bool(task['is_confirmed'])
            
            return task
            
        except Exception as e:
            print(f"獲取預約資訊錯誤: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_tasks_by_date(self, target_date: str) -> List[Dict]:
        """獲取指定日期的所有預約"""
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT *
                FROM Tasks 
                WHERE DATE(start) = %s
                ORDER BY start ASC
            """
            cursor.execute(query, (target_date,))
            tasks = cursor.fetchall()
            
            # 處理日期時間格式
            for task in tasks:
                if task.get('start'):
                    task['start'] = task['start'].isoformat()
                if task.get('end'):
                    task['end'] = task['end'].isoformat()
                if task.get('is_confirmed') is not None:
                    task['is_confirmed'] = bool(task['is_confirmed'])
            
            return tasks
            
        except Exception as e:
            print(f"獲取日期預約錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_tasks_block_by_date_24H(self, target_date: str) -> Dict:
        block_len  =288 +6  
        # 初始所有師傅工作表，預設其288+6 個時間塊為False（False表示該時間段無工作）
        result = {
                'date': target_date,
                'staffs': {}
            }
        all_staffs = self.staff_manager.get_all_staffs()
        for staff in all_staffs:
            staff_name = staff['name']
            result['staffs'][staff_name] = {
                'staff_id': staff['id'],
                'tasks': [False] * block_len
            }
        #取出當日所有師傅的工作時段，並標記在對應的時間塊中
        all_tasks = self.get_tasks_by_date(target_date)
        for task in all_tasks:
            staff_name = task['staff_name']
            if staff_name in result['staffs']:
                # 標記該師傅的工作時段為True
                # 需要將task的start和end時間轉換為對應的block索引，然後標記
                start_time = task['start']
                end_time = task['end']
                # 轉換時間為block索引的邏輯需要實現
                # 這裡暫時假設有一個函數convert_time_to_block_index
                start_block = self.convert_time_to_block_index(start_time, is_end_time=False)
                #結束時間必需給予15分鐘準備，緩衝時間
                end_block = self.convert_time_to_block_index(end_time, is_end_time=True) + 3
                
                # 處理跨日情況：如果 end_block <= start_block，表示工作跨越午夜
                if end_block <= start_block:
                    # 跨日：從 start_block 到當天結束 (288)，然後從第二天開始 (0) 到 end_block
                    for i in range(start_block, block_len):
                        result['staffs'][staff_name]['tasks'][i] = True
                    for i in range(0, end_block):
                        result['staffs'][staff_name]['tasks'][i] = True
                else:
                    # 同日：從 start_block 到 end_block
                    for i in range(start_block, min(end_block, block_len)):
                        result['staffs'][staff_name]['tasks'][i] = True
        
        return result
    
   

    def convert_time_to_block_index(self, time_str: str, is_end_time: bool = False) -> int:
        """將時間字串轉換為block索引（每5分鐘一個block，從00:00開始）
        
        支援格式：
        - HH:MM (例如 "20:00")
        - HH:MM:SS (例如 "20:00:00")
        - ISO格式 (例如 "2025-12-05T20:00:00")
        
        Args:
            time_str: 時間字串
            is_end_time: 是否為結束時間（如果是且為 00:00，則視為 24:00）
        """
        try:
            # 如果是簡單的 HH:MM 或 HH:MM:SS 格式
            if 'T' not in time_str and '-' not in time_str.split(':')[0]:
                time_parts = time_str.split(':')
                hours = int(time_parts[0])
                minutes = int(time_parts[1]) if len(time_parts) > 1 else 0
                
                # 如果是結束時間且為 00:00，視為 24:00 (1440分鐘 = block 288)
                if is_end_time and hours == 0 and minutes == 0:
                    return 288  # 24:00 = 1440分鐘 / 5 = 288
                
                # 計算從當天00:00開始的分鐘數
                minutes_from_midnight = hours * 60 + minutes
                # 每5分鐘一個block
                block_index = minutes_from_midnight // 5
                return block_index
            else:
                # 解析ISO格式時間字串
                dt = datetime.fromisoformat(time_str)
                
                # 如果是結束時間且為 00:00，視為 24:00 (1440分鐘 = block 288)
                if is_end_time and dt.hour == 0 and dt.minute == 0:
                    return 288  # 24:00 = 1440分鐘 / 5 = 288
                
                # 計算從當天00:00開始的分鐘數
                minutes_from_midnight = dt.hour * 60 + dt.minute
                # 每5分鐘一個block
                block_index = minutes_from_midnight // 5
                return block_index
        except Exception as e:
            print(f"時間轉換錯誤: {e}, 輸入值: {time_str}")
            return 0
    
    def convert_block_index_to_time(self, block_index: int) -> str:
        """將block索引轉換為時間字串（HH:MM格式）"""
        try:
            # 每個block代表5分鐘
            total_minutes = block_index * 5
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            # 確保時間在有效範圍內（0-23小時，0-59分鐘）
            if hours >= 24:
                hours = 23
                minutes = 55
            
            # 返回 HH:MM 格式
            return f"{hours:02d}:{minutes:02d}"
        except Exception as e:
            print(f"Block索引轉換錯誤: {e}")
            return "00:00"
    
    def get_tasks_by_staff(self, staff_name: str, target_date: str = None) -> List[Dict]:
        """獲取指定師傅的預約（可選指定日期）"""
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            if target_date:
                query = """
                    SELECT id, customer_name, start, end, staff_id, course_id, 
                           price, discount, master_income, company_income, 
                           `desc`, ispaid, mins, storeid, staff_name, note, 
                           course_name, exdata, history, memberid, history_pri, 
                           usetickettype, real_master_income, real_company_income, 
                           paytype, is_confirmed
                    FROM Tasks 
                    WHERE staff_name = %s AND DATE(start) = %s
                    ORDER BY start ASC
                """
                cursor.execute(query, (staff_name, target_date))
            else:
                query = """
                    SELECT id, customer_name, start, end, staff_id, course_id, 
                           price, discount, master_income, company_income, 
                           `desc`, ispaid, mins, storeid, staff_name, note, 
                           course_name, exdata, history, memberid, history_pri, 
                           usetickettype, real_master_income, real_company_income, 
                           paytype, is_confirmed
                    FROM Tasks 
                    WHERE staff_name = %s
                    ORDER BY start DESC
                    LIMIT 50
                """
                cursor.execute(query, (staff_name,))
            
            tasks = cursor.fetchall()
            
            # 處理日期時間格式
            for task in tasks:
                if task.get('start'):
                    task['start'] = task['start'].isoformat()
                if task.get('end'):
                    task['end'] = task['end'].isoformat()
                if task.get('is_confirmed') is not None:
                    task['is_confirmed'] = bool(task['is_confirmed'])
            
            return tasks
            
        except Exception as e:
            print(f"獲取師傅預約錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_tasks_by_customer(self, customer_name: str) -> List[Dict]:
        """根據客戶名稱獲取預約記錄"""
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, customer_name, start, end, staff_id, course_id, 
                       price, discount, master_income, company_income, 
                       `desc`, ispaid, mins, storeid, staff_name, note, 
                       course_name, exdata, history, memberid, history_pri, 
                       usetickettype, real_master_income, real_company_income, 
                       paytype, is_confirmed
                FROM Tasks 
                WHERE customer_name LIKE %s
                ORDER BY start DESC
                LIMIT 50
            """
            search_term = f"%{customer_name}%"
            cursor.execute(query, (search_term,))
            tasks = cursor.fetchall()
            
            # 處理日期時間格式
            for task in tasks:
                if task.get('start'):
                    task['start'] = task['start'].isoformat()
                if task.get('end'):
                    task['end'] = task['end'].isoformat()
                if task.get('is_confirmed') is not None:
                    task['is_confirmed'] = bool(task['is_confirmed'])
            
            return tasks
            
        except Exception as e:
            print(f"獲取客戶預約錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def create_task(self, task_data: Dict) -> Optional[int]:
        """創建新預約"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            query = """
                INSERT INTO Tasks (customer_name, start, end, staff_id, course_id, 
                                 price, discount, master_income, company_income, 
                                 `desc`, ispaid, mins, storeid, staff_name, note, 
                                 course_name, exdata, memberid, usetickettype, 
                                 real_master_income, real_company_income, paytype, is_confirmed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                task_data.get('customer_name'),
                task_data.get('start'),
                task_data.get('end'),
                task_data.get('staff_id'),
                task_data.get('course_id'),
                task_data.get('price', 1800),
                task_data.get('discount', 0),
                task_data.get('master_income', 0),
                task_data.get('company_income', 0),
                task_data.get('desc', ''),
                task_data.get('ispaid', 0),
                task_data.get('mins', 90),
                task_data.get('storeid', 0),
                task_data.get('staff_name', '未指定'),
                task_data.get('note', ''),
                task_data.get('course_name', '無'),
                task_data.get('exdata'),
                task_data.get('memberid'),
                task_data.get('usetickettype', 0),
                task_data.get('real_master_income', 0),
                task_data.get('real_company_income', 0),
                task_data.get('paytype', 0),
                task_data.get('is_confirmed', False)
            )
            
            cursor.execute(query, values)
            connection.commit()
            task_id = cursor.lastrowid
            
            return task_id
            
        except Exception as e:
            print(f"創建預約錯誤: {e}")
            connection.rollback()
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def update_task(self, task_id: int, task_data: Dict) -> bool:
        """更新預約資訊"""
        connection = self.db_config.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # 建立動態更新查詢
            update_fields = []
            values = []
            
            for field in ['customer_name', 'start', 'end', 'staff_id', 'course_id', 
                         'price', 'discount', 'master_income', 'company_income', 
                         'desc', 'ispaid', 'mins', 'storeid', 'staff_name', 'note', 
                         'course_name', 'exdata', 'memberid', 'usetickettype', 
                         'real_master_income', 'real_company_income', 'paytype', 'is_confirmed']:
                if field in task_data:
                    if field == 'desc':
                        update_fields.append("`desc` = %s")
                    else:
                        update_fields.append(f"{field} = %s")
                    values.append(task_data[field])
            
            if not update_fields:
                return False
            
            query = f"""
                UPDATE Tasks 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            values.append(task_id)
            
            cursor.execute(query, values)
            connection.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"更新預約錯誤: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def delete_task(self, task_id: int) -> bool:
        """刪除預約"""
        connection = self.db_config.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            query = "DELETE FROM Tasks WHERE id = %s"
            cursor.execute(query, (task_id,))
            connection.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"刪除預約錯誤: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def confirm_task(self, task_id: int, is_confirmed: bool = True) -> bool:
        """師傅確認預約"""
        return self.update_task(task_id, {'is_confirmed': is_confirmed})
    
    def get_task_statistics(self, start_date: str = None, end_date: str = None) -> Dict:
        """獲取預約統計資訊"""
        connection = self.db_config.get_connection()
        if not connection:
            return {}
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # 基本統計查詢
            base_conditions = []
            params = []
            
            if start_date:
                base_conditions.append("DATE(start) >= %s")
                params.append(start_date)
            
            if end_date:
                base_conditions.append("DATE(start) <= %s")
                params.append(end_date)
            
            where_clause = ""
            if base_conditions:
                where_clause = "WHERE " + " AND ".join(base_conditions)
            
            # 總預約數
            query = f"SELECT COUNT(*) as total_tasks FROM Tasks {where_clause}"
            cursor.execute(query, params)
            total_tasks = cursor.fetchone()['total_tasks']
            
            # 已確認預約數
            confirmed_query = f"SELECT COUNT(*) as confirmed_tasks FROM Tasks {where_clause}"
            if where_clause:
                confirmed_query += " AND is_confirmed = 1"
            else:
                confirmed_query += " WHERE is_confirmed = 1"
            cursor.execute(confirmed_query, params)
            confirmed_tasks = cursor.fetchone()['confirmed_tasks']
            
            # 已付款預約數
            paid_query = f"SELECT COUNT(*) as paid_tasks FROM Tasks {where_clause}"
            if where_clause:
                paid_query += " AND ispaid = 1"
            else:
                paid_query += " WHERE ispaid = 1"
            cursor.execute(paid_query, params)
            paid_tasks = cursor.fetchone()['paid_tasks']
            
            # 總收入
            income_query = f"SELECT SUM(price) as total_income, SUM(real_master_income) as total_master_income, SUM(real_company_income) as total_company_income FROM Tasks {where_clause}"
            cursor.execute(income_query, params)
            income_data = cursor.fetchone()
            
            # 各師傅預約統計
            staff_query = f"""
                SELECT staff_name, COUNT(*) as task_count, SUM(price) as total_price
                FROM Tasks {where_clause}
                GROUP BY staff_name
                ORDER BY task_count DESC
            """
            cursor.execute(staff_query, params)
            staff_stats = cursor.fetchall()
            
            return {
                'total_tasks': total_tasks,
                'confirmed_tasks': confirmed_tasks,
                'paid_tasks': paid_tasks,
                'total_income': income_data['total_income'] or 0,
                'total_master_income': income_data['total_master_income'] or 0,
                'total_company_income': income_data['total_company_income'] or 0,
                'staff_statistics': staff_stats,
                'date_range': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
            
        except Exception as e:
            print(f"獲取統計資料錯誤: {e}")
            return {}
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def search_tasks(self, keyword: str) -> List[Dict]:
        """搜索預約（根據客戶名稱、師傅名稱或課程名稱）"""
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, customer_name, start, end, staff_id, course_id, 
                       price, discount, master_income, company_income, 
                       `desc`, ispaid, mins, storeid, staff_name, note, 
                       course_name, exdata, history, memberid, history_pri, 
                       usetickettype, real_master_income, real_company_income, 
                       paytype, is_confirmed
                FROM Tasks 
                WHERE customer_name LIKE %s OR staff_name LIKE %s OR course_name LIKE %s
                ORDER BY start DESC
                LIMIT 100
            """
            search_term = f"%{keyword}%"
            cursor.execute(query, (search_term, search_term, search_term))
            tasks = cursor.fetchall()
            
            # 處理日期時間格式
            for task in tasks:
                if task.get('start'):
                    task['start'] = task['start'].isoformat()
                if task.get('end'):
                    task['end'] = task['end'].isoformat()
                if task.get('is_confirmed') is not None:
                    task['is_confirmed'] = bool(task['is_confirmed'])
            
            return tasks
            
        except Exception as e:
            print(f"搜索預約錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
