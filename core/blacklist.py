from typing import List, Optional
from .database import db_config

class BlacklistManager:
    """黑名單管理模塊"""
    
    def __init__(self):
        self.db_config = db_config

    def is_super_blacklist(self, lineuserid: str) -> bool:
        """
        檢查用戶是否為超級黑名單
        
        Args:
            lineuserid: LINE 用戶的真實 line_id (字串格式，例如 'U1234567890abcdef')
            
        Returns:
            bool: True 表示是超級黑名單，False 表示不是
        """
        print(f"[DEBUG] is_super_blacklist - 檢查 lineuserid: {lineuserid}")
        connection = self.db_config.get_connection()
        if not connection:
            print(f"[DEBUG] is_super_blacklist - 無法獲取資料庫連接")
            return False
        
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            
            # 先從 line_users 表單找到對應的 id
            query_line_user = """
            SELECT id FROM line_users WHERE line_id = %s
            """
            print(f"[DEBUG] is_super_blacklist - 執行查詢: {query_line_user} with {lineuserid}")
            cursor.execute(query_line_user, (lineuserid,))
            line_user_result = cursor.fetchone()
            print(f"[DEBUG] is_super_blacklist - line_users 查詢結果: {line_user_result}")
            
            if not line_user_result:
                print(f"[DEBUG] is_super_blacklist - {lineuserid} 不在 line_users 中")
                return False
            
            line_user_id = line_user_result['id']
            print(f"[DEBUG] is_super_blacklist - 找到 line_user_id: {line_user_id}")
            
            # 在 blacklist 表單中查找是否為超級黑名單
            query_blacklist = """
            SELECT staff_name FROM blacklist 
            WHERE line_user_id = %s AND staff_name = '超級黑名單'
            """
            print(f"[DEBUG] is_super_blacklist - 執行黑名單查詢")
            cursor.execute(query_blacklist, (line_user_id,))
            blacklist_result = cursor.fetchone()
            print(f"[DEBUG] is_super_blacklist - 黑名單查詢結果: {blacklist_result}")
            
            result = blacklist_result is not None
            print(f"[DEBUG] is_super_blacklist - 最終結果: {result}")
            return result
            
        except Exception as e:
            print(f"[ERROR] 檢查超級黑名單錯誤: {e}")
            return False
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def getBlockedStaffsList(self, lineuserid: str) -> List[str]:
        """
        獲取將此用戶列為黑名單的師傅名稱列表
        
        Args:
            lineuserid: LINE 用戶的真實 line_id (字串格式，例如 'U1234567890abcdef')
            
        Returns:
            List[str]: 師傅名稱陣列
                      - 如果是超級黑名單，返回所有師傅名稱
                      - 如果不是超級黑名單，返回將其列為黑名單的師傅名稱
                      - 如果找不到用戶或沒有黑名單記錄，返回空陣列
        """
        connection = self.db_config.get_connection()
        if not connection:
            return []
        
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            
            # 先從 line_users 表單找到對應的 id
            query_line_user = """
            SELECT id FROM line_users WHERE line_id = %s 
            """
            cursor.execute(query_line_user, (lineuserid,))
            line_user_result = cursor.fetchone()
            
            if not line_user_result:
                return []
            
            line_user_id = line_user_result['id']
            
            # 檢查是否為超級黑名單
            if self.is_super_blacklist(lineuserid):
                # 如果是超級黑名單，返回所有師傅名稱
                query_all_staffs = """
                SELECT name FROM Staffs 
                WHERE enable = 1 AND name != '無' AND storeid=1
                ORDER BY id
                """
                cursor.execute(query_all_staffs)
                all_staffs = cursor.fetchall()
                return [staff['name'] for staff in all_staffs]
            else:
                # 如果不是超級黑名單，查找將其列為黑名單的師傅
                query_blocked_staffs = """
                SELECT staff_name FROM blacklist 
                WHERE line_user_id = %s AND staff_name != '超級黑名單'
                """
                cursor.execute(query_blocked_staffs, (line_user_id,))
                blocked_staffs = cursor.fetchall()
                return [staff['staff_name'] for staff in blocked_staffs]
            
        except Exception as e:
            print(f"獲取黑名單師傅列表錯誤: {e}")
            return []
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
