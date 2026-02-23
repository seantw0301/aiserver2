from typing import List, Dict, Optional
from datetime import datetime
from .database import db_config


class StoreManager:
    """店家管理模塊"""
    
    def __init__(self):
        self.db_config = db_config
        self._task_manager = None
    
    @property
    def task_manager(self):
        """延遲初始化 TaskManager 以避免循環導入"""
        if self._task_manager is None:
            from .tasks import TaskManager
            self._task_manager = TaskManager()
        return self._task_manager
     

    def get_store_table_lastupdate_time(self) -> Optional[datetime]:
        """獲取Store表的最後更新時間"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
            SELECT UPDATE_TIME 
            FROM information_schema.tables 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'Store'
            """
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result and result.get('UPDATE_TIME'):
                #確認轉成datetime格式
                update_time = result['UPDATE_TIME']
                if isinstance(update_time, str):
                    update_time = datetime.fromisoformat(update_time)
                return update_time
            else:
                return None
            
        except Exception as e:
            print(f"獲取Store表更新時間錯誤: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
            connection.close()

        return
    
    
    def get_all_stores(self) -> List[Dict]:
        """獲取所有店家列表"""
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT *
                FROM Store 
                ORDER BY id
            """
            cursor.execute(query)
            stores = cursor.fetchall()
            
            # 處理 bit 類型的 maskname 欄位
            for store in stores:
                if store.get('maskname') is not None:
                    # 將 bytes 轉換為 boolean
                    store['maskname'] = bool(store['maskname'])
            
            return stores
            
        except Exception as e:
            print(f"獲取店家列表錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_store_by_id(self, store_id: int) -> Optional[Dict]:
        """根據ID獲取店家資訊"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, name, `key`, open, close, maskname, 
                       memdb, mainstore, rooms, address, pics
                FROM Store 
                WHERE id = %s
            """
            cursor.execute(query, (store_id,))
            store = cursor.fetchone()
            
            if store and store.get('maskname') is not None:
                # 將 bytes 轉換為 boolean
                store['maskname'] = bool(store['maskname'])
            
            return store
            
        except Exception as e:
            print(f"獲取店家資訊錯誤: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_store_by_name(self, name: str) -> Optional[Dict]:
        """根據店家名稱獲取店家資訊"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, name, `key`, open, close, maskname, 
                       memdb, mainstore, rooms, address, pics
                FROM Store 
                WHERE name = %s
            """
            cursor.execute(query, (name,))
            store = cursor.fetchone()
            
            if store and store.get('maskname') is not None:
                # 將 bytes 轉換為 boolean
                store['maskname'] = bool(store['maskname'])
            
            return store
            
        except Exception as e:
            print(f"獲取店家資訊錯誤: {e}")
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def create_store(self, store_data: Dict) -> Optional[int]:
        """創建新店家"""
        connection = self.db_config.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor()
            query = """
                INSERT INTO Store (name, `key`, open, close, maskname, 
                                 memdb, mainstore, rooms, address, pics)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            values = (
                store_data.get('name'),
                store_data.get('key'),
                store_data.get('open', 9),
                store_data.get('close', 22),
                store_data.get('maskname', False),
                store_data.get('memdb', 0),
                store_data.get('mainstore'),
                store_data.get('rooms', 4),
                store_data.get('address'),
                store_data.get('pics')
            )
            
            cursor.execute(query, values)
            connection.commit()
            store_id = cursor.lastrowid
            
            return store_id
            
        except Exception as e:
            print(f"創建店家錯誤: {e}")
            connection.rollback()
            return None
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def update_store(self, store_id: int, store_data: Dict) -> bool:
        """更新店家資訊"""
        connection = self.db_config.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # 建立動態更新查詢
            update_fields = []
            values = []
            
            for field in ['name', 'key', 'open', 'close', 'maskname', 
                         'memdb', 'mainstore', 'rooms', 'address', 'pics']:
                if field in store_data:
                    if field == 'key':
                        update_fields.append("`key` = %s")
                    else:
                        update_fields.append(f"{field} = %s")
                    values.append(store_data[field])
            
            if not update_fields:
                return False
            
            query = f"""
                UPDATE Store 
                SET {', '.join(update_fields)}
                WHERE id = %s
            """
            values.append(store_id)
            
            cursor.execute(query, values)
            connection.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"更新店家錯誤: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def delete_store(self, store_id: int) -> bool:
        """刪除店家"""
        connection = self.db_config.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            query = "DELETE FROM Store WHERE id = %s"
            cursor.execute(query, (store_id,))
            connection.commit()
            
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"刪除店家錯誤: {e}")
            connection.rollback()
            return False
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
    
    def get_store_summary(self) -> Dict:
        """獲取店家摘要資訊"""
        stores = self.get_all_stores()
        
        summary = {
            'total_stores': len(stores),
            'total_rooms': sum(store.get('rooms', 0) for store in stores),
            'stores_with_address': len([s for s in stores if s.get('address')]),
            'stores_with_pics': len([s for s in stores if s.get('pics')])
        }
        
        return summary
    
    def search_stores(self, keyword: str) -> List[Dict]:
        """搜索店家（根據名稱或地址）"""
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            query = """
                SELECT id, name, `key`, open, close, maskname, 
                       memdb, mainstore, rooms, address, pics
                FROM Store 
                WHERE name LIKE %s OR address LIKE %s
                ORDER BY id
            """
            search_term = f"%{keyword}%"
            cursor.execute(query, (search_term, search_term))
            stores = cursor.fetchall()
            
            # 處理 bit 類型的 maskname 欄位
            for store in stores:
                if store.get('maskname') is not None:
                    store['maskname'] = bool(store['maskname'])
            
            return stores
            
        except Exception as e:
            print(f"搜索店家錯誤: {e}")
            return []
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def get_store_occupied_block_by_date_24H(self, target_date: str) -> Dict:
        block_len  =288 +6  
        # 初始所有師傅工作表，預設其288+6 個時間塊為False（False表示該時間段無工作）
        result = {
                'date': target_date,
                'data': {}
            }
        all_stores = self.get_all_stores()
        for store in all_stores:
            store_id = store['id']
            # 統一使用字符串作為鍵，避免 Redis JSON 序列化問題
            result['data'][str(store_id)] = {
                'store_name': store['name'],
                'blocks': [0] * block_len  #預設為佔用0間
            }

        #取出當日所有師傅的工作時段，並標記在對應的時間塊中
        all_tasks = self.task_manager.get_tasks_by_date(target_date)
        for task in all_tasks:
            store_id = task['storeid']
            # 使用字符串鍵
            store_id_key = str(store_id)
            if store_id_key in result['data']:
                # 標記該店鋪的佔用時間塊
                start_time = task['start']
                end_time = task['end']
                # 轉換時間為block索引的邏輯需要實現
                # 這裡暫時假設有一個函數convert_time_to_block_index
                start_block = self.task_manager.convert_time_to_block_index(start_time)
                #結束時間必需給予15分鐘準備，緩衝時間
                end_block = self.task_manager.convert_time_to_block_index(end_time) + 3
                #將有工作的block,數字加1,表示用了一間房間
                for i in range(start_block, min(end_block, block_len)):
                    result['data'][store_id_key]['blocks'][i] += 1
        
        return result
    
