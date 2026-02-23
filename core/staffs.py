from typing import List, Dict, Optional
from datetime import datetime, date
from .database import db_config
import redis
import json

class StaffManager:
    """師傅管理模塊"""
    
    def __init__(self):
        self.db_config = db_config

    def get_staffs_table_lastupdate_time(self) -> Optional[datetime]:
        """獲取Staffs表的最後更新時間"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT UPDATE_TIME 
            FROM information_schema.tables 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'Staffs'
            """
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result and result.get('UPDATE_TIME'):
                #確認轉成datetime格式
                update_time = result['UPDATE_TIME']
                if isinstance(update_time, str):
                    update_time = datetime.fromisoformat(update_time)
                print(f"Staffs表最後更新時間: {update_time}")
                return update_time
            else:
                print("Staffs表最後更新時間: 無法獲取")
                return None
            
        except Exception as e:
            print(f"獲取Staffs表更新時間錯誤: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
            connection.close()

        return 


    def get_all_staffs(self) -> List[Dict]:
        # 先由redis中取得 staffs_data ,取得其最後更新的時間,若staffs_data不存在，或者是比Staffs資料庫更新的時間早，則由資料庫中更新資料，否則直接取用redis中的staffs_data
        
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            
            # 從Redis獲取緩存數據
            # staffs_data為一個json格式，其中包含 update_time 和 data
            cached_json = redis_client.get('staffs_data')         
            if cached_json:
                cached_info = json.loads(cached_json)
                cached_data = cached_info.get('data')
                cached_update_time = cached_info.get('update_time')
            else:
                cached_data = None
                cached_update_time = None
            
            # 獲取資料庫最後更新時間
            db_update_time = self.get_staffs_table_lastupdate_time()
            
            # 判斷是否需要更新緩存
            need_update = False
            
            if not cached_data or not cached_update_time:
                # 緩存不存在
                need_update = True
            elif db_update_time:
                # 比較更新時間
                cached_time = datetime.fromisoformat(cached_update_time)
                if db_update_time > cached_time:
                    need_update = True
            
            if not need_update:
                print("Using redis cached staffs data")
                return cached_data
            else:
            # 從資料庫獲取數據並更新緩存
                """由資料庫中獲取所有師傅列表"""
                connection = self.db_config.get_connection()
                if not connection:
                    return []                
                try:
                    cursor = connection.cursor(dictionary=True)
                    query = """
                        SELECT id, name, `desc`, profit, staff, line_userid, 
                            storeid, enable, isAdmin, max_pr, createdate, 
                            showpublic, publicno, instores, pic0, pic1, pic2
                        FROM Staffs 
                        WHERE enable = 1 and storeid = 1 and (name != '無')
                        ORDER BY id
                    """
                    cursor.execute(query)
                    staffs = cursor.fetchall()
                    
                    # 將 datetime 欄位轉換為字串以便 JSON 序列化
                    for staff in staffs:
                        if staff.get('createdate') and isinstance(staff['createdate'], datetime):
                            staff['createdate'] = staff['createdate'].isoformat()
                    
                    #將staffs整合 update_time ,放入json格式，與我們要存放在redis的資料一致
                    update_time = db_update_time.isoformat() if db_update_time else None
                    data_to_cache = {
                        "update_time": update_time,
                        "data": staffs
                    }
                    redis_client.set('staffs_data', json.dumps(data_to_cache))  
                    
                    return staffs


                except Exception as e:
                    print(f"獲取師傅列表錯誤: {e}")
                    return []
                finally:
                    if connection.is_connected():
                        cursor.close()
                        connection.close()

        except Exception as e1:
            print(f"更新緩存錯誤: {e1}") 
            return []

            
    
    def get_staff_by_id(self, staff_id: int) -> Optional[Dict]:
        """根據ID獲取師傅資訊"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, name, `desc`, profit, staff, line_userid, 
                       storeid, enable, isAdmin, max_pr, createdate, 
                       showpublic, publicno, instores, pic0, pic1, pic2
                FROM Staffs 
                WHERE id = %s AND enable = 1
            """
            cursor.execute(query, (staff_id,))
            staff = cursor.fetchone()
            
            if staff and staff.get('createdate'):
                staff['createdate'] = staff['createdate'].isoformat()
            
            return staff
            
        except Exception as e:
            print(f"獲取師傅資訊錯誤: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_staff_by_name(self, name: str) -> Optional[Dict]:
        """根據姓名獲取師傅資訊"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, name, `desc`, profit, staff, line_userid, 
                       storeid, enable, isAdmin, max_pr, createdate, 
                       showpublic, publicno, instores, pic0, pic1, pic2
                FROM Staffs 
                WHERE name = %s AND storeid = 1 AND enable = 1
            """
            cursor.execute(query, (name,))
            staff = cursor.fetchone()
            
            if staff and staff.get('createdate'):
                staff['createdate'] = staff['createdate'].isoformat()
            
            return staff
            
        except Exception as e:
            print(f"獲取師傅資訊錯誤: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_staff_id_by_name(self, name: str) -> Optional[int]:
        """根據姓名獲取師傅ID"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = "SELECT id FROM Staffs WHERE name = %s AND storeid = 1 AND enable = 1 LIMIT 1"
            cursor.execute(query, (name,))
            result = cursor.fetchone()
            
            if result:
                return result['id']
            return None
            
        except Exception as e:
            print(f"獲取師傅ID錯誤: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_public_staff_names_by_store(self, store_id: int) -> List[str]:
        """獲取指定店家的公開師傅名字列表"""
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT name 
                FROM Staffs 
                WHERE storeid = %s AND storeid=1AND enable = 1 AND showpublic = 1
                ORDER BY name
            """
            cursor.execute(query, (store_id,))
            results = cursor.fetchall()
            
            # 返回師傅名字列表
            return [staff['name'] for staff in results]
            
        except Exception as e:
            print(f"獲取店家公開師傅名字列表錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
