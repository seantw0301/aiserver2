#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然語言解析模組
整合 handle_customer.py, handle_staff.py, handle_time.py 的功能
提供統一的自然語言解析接口
"""

import re
import json
import time
import datetime
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Union
import redis
import mysql.connector
import sys
import os

# 獲取當前腳本所在目錄
current_dir = os.path.dirname(os.path.abspath(__file__))

# 確保當前目錄在路徑中，這樣可以正確導入同目錄下的模塊
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from handle_customer import getCustomerCount
from handle_staff import getStaffNames
from handle_time import parse_datetime_phrases

import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import os
import sys
import time
import redis
import mysql.connector

# 添加當前目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# 添加父目錄到 Python 路徑
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# 導入資料庫配置
from core.database import db_config

# 導入現有的處理模組
from handle_customer import getCustomerCount
from handle_staff import getStaffNames
from handle_time import parse_datetime_phrases
from staff_utils import getStaffMapping
from handle_isReserv import isReservation

# 導入 common 模組中的函數
from core.common import update_user_visitdate, get_user_info

# Redis 連接設定
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_EXPIRY = 12 * 60 * 60  # 12小時過期時間（以秒為單位）

# 店家名稱映射
BRANCH_MAPPING = {
    '西門': '西門',
    '延吉': '延吉',
    '西門店': '西門',
    '延吉店': '延吉',
    '西': '西門',
    '延': '延吉',
    '大巨蛋': '延吉',
    '家樂福': '家樂福',
    '西門二店': '家樂福',
    '西寧店':'家樂福'
}

# 項目時間映射
PROJECT_MAPPING = {
    '60': 60, '一小時': 60, '1小時': 60, '60分': 60, '60分鐘': 60,
    '90': 90, '一個半小時': 90, '1.5小時': 90, '90分': 90, '90分鐘': 90,
    '120': 120, '兩小時': 120, '2小時': 120, '120分': 120, '120分鐘': 120
}

def check_keywords_match(text: str) -> Optional[str]:
    """
    檢查文本是否匹配資料庫中的關鍵詞
    
    Args:
        text (str): 用戶輸入的自然語言文本
        
    Returns:
        Optional[str]: 匹配到的關鍵詞回應，如果沒有匹配則返回 None
    """
    try:
        # 獲取資料庫連接
        connection = db_config.get_connection()
        if not connection:
            print("警告：無法連接到資料庫")
            return None
            
        cursor = connection.cursor(dictionary=True)
        
        # 查詢所有啟用的關鍵詞，按優先級排序
        query = """
        SELECT keyword, match_type, response_message 
        FROM keywords 
        WHERE enabled = 1 
        ORDER BY priority DESC, id ASC
        """
        
        cursor.execute(query)
        keywords = cursor.fetchall()
        
        # 檢查每個關鍵詞是否匹配
        for keyword_data in keywords:
            keyword = keyword_data['keyword']
            match_type = keyword_data['match_type']
            response = keyword_data['response_message']
            
            # 根據匹配類型進行匹配
            is_match = False
            if match_type == 'exact':
                # 精確匹配
                if text.strip() == keyword:
                    is_match = True
            elif match_type == 'contains':
                # 包含匹配
                if keyword in text:
                    is_match = True
            elif match_type == 'regex':
                # 正則表達式匹配
                keywords_list = keyword.split('|')
                for k in keywords_list:
                    if k.strip() and re.search(k.strip(), text, re.IGNORECASE):
                        is_match = True
                        break
            
            # 如果匹配成功，返回回應消息
            if is_match:
                cursor.close()
                connection.close()
                return response
                
        cursor.close()
        connection.close()
        return None
        
    except mysql.connector.Error as err:
        print(f"資料庫查詢錯誤: {err}")
        return None
    except Exception as e:
        print(f"檢查關鍵詞匹配時發生錯誤: {e}")
        return None

class NaturalLanguageParser:
    """自然語言解析器"""
    
    def __init__(self):
        self.branch_mapping = BRANCH_MAPPING
        self.project_mapping = PROJECT_MAPPING
        # 獲取師傅映射
        try:
            self.staff_mapping = getStaffMapping()
        except Exception as e:
            print(f"警告：無法獲取師傅映射：{e}")
            self.staff_mapping = {}
    
    def parse_text(self, text: str, line_key: str = None) -> Dict[str, Any]:
        """
        解析自然語言文本，提取預約資訊
        
        Args:
            text (str): 用戶輸入的自然語言文本
            line_key (str): 會話 key（LINE user ID），如果提供則會將結果保存到 Redis
            
        Returns:
            Dict[str, Any]: 解析結果的 JSON 格式
        """
        print(f"\n{'='*60}")
        print(f"DEBUG [Parser]: 開始解析訊息")
        print(f"DEBUG [Parser]: line_key={line_key}")
        print(f"DEBUG [Parser]: message={text}")
        print(f"{'='*60}")
        
        # 先檢查是否匹配關鍵詞
        print(f"DEBUG [Parser]: Step 1 - 檢查關鍵詞匹配...")
        keyword_response = check_keywords_match(text)
        if keyword_response:
            # 如果匹配到關鍵詞，返回帶有回應消息的結果
            print(f"DEBUG [Parser]: ✅ 匹配到關鍵詞: {keyword_response[:50]}...")
            result = {
                "is_keyword_match": True,
                "response_message": keyword_response
            }
            return result
        print(f"DEBUG [Parser]: 未匹配到關鍵詞，繼續解析...")
        
        # 重置預約相關參數
        is_reservation = False
        print(f"DEBUG [Parser]: Step 2 - 開始解析預約資訊...")
        
        # 預處理：移除表單標籤
        print(f"DEBUG [Parser]: Step 2.1 - 移除表單標籤...")
        form_labels = [
            "📝(寫預約表)Reservation form",
            "🏠(選擇店家)Branch:",
            "💪(依喜歡順序選三位按摩師)masseur:):",
            "📅(日期)Date:",
            "⏰(時間)Time:",
            "💆‍♂️(課程)Project:"
        ]
        
        for label in form_labels:
            text = text.replace(label, "")
        print(f"DEBUG [Parser]: 移除標籤後的文字: {text}")
        
        # 判別是否與預約相關
        print(f"DEBUG [Parser]: Step 2.2 - 判別是否為預約訊息...")
        try:
            print(f"DEBUG [Parser]: 嘗試解析日期時間...")
            datetime_result = parse_datetime_phrases(text)
            print(f"DEBUG [Parser]: 日期時間解析結果: {datetime_result}")
            if datetime_result and (
                ('日期' in datetime_result and datetime_result['日期'] and datetime_result['日期'] != "null") or
                ('時間' in datetime_result and datetime_result['時間'] and datetime_result['時間'] != "null")
            ):
                print(f"DEBUG [Parser]: ✅ 找到日期或時間，判定為預約訊息")
                print(f"DEBUG [Parser]: 日期時間詳情: {datetime_result}")
                is_reservation = True
        except Exception as e:
            print(f"⚠️  警告：日期時間解析失敗：{e}")
            import traceback
            traceback.print_exc()
            datetime_result = {}
        
        # 分鐘數判斷
        if not is_reservation:
            print(f"DEBUG [Parser]: Step 2.3 - 檢查是否包含療程時間...")
            for project_key in PROJECT_MAPPING.keys():
                if project_key in text:
                    print(f"DEBUG [Parser]: ✅ 找到療程關鍵字: {project_key}")
                    is_reservation = True
                    break
            if not is_reservation:
                print(f"DEBUG [Parser]: 未找到療程關鍵字")
        
        # 店家判斷
        if not is_reservation:
            print(f"DEBUG [Parser]: Step 2.4 - 檢查是否包含店家...")
            for branch in BRANCH_MAPPING.keys():
                if branch in text:
                    print(f"DEBUG [Parser]: ✅ 找到店家: {branch}")
                    is_reservation = True
                    break
            if not is_reservation:
                print(f"DEBUG [Parser]: 未找到店家關鍵字")
        
        # 師傅判斷
        if not is_reservation:
            print(f"DEBUG [Parser]: Step 2.5 - 檢查是否包含師傅名稱...")
            staff_names = getStaffNames(text)
            print(f"DEBUG [Parser]: 找到的師傅: {staff_names}")
            if staff_names and len(staff_names) > 0:
                print(f"DEBUG [Parser]: ✅ 找到 {len(staff_names)} 位師傅")
                is_reservation = True
            else:
                print(f"DEBUG [Parser]: 未找到師傅")
        
        # 若前項為 isAboutReservation=false則進行，則進行handle_isReserv.py裡的判斷
        if not is_reservation:
            print(f"DEBUG [Parser]: Step 2.6 - 使用 isReservation() 再次確認...")
            is_reservation = isReservation(text)
            print(f"DEBUG [Parser]: isReservation() 結果: {is_reservation}")
        
        # 最後總結判定
        print(f"\nDEBUG [Parser]: ========== 預約判定結果 ===========")
        print(f"DEBUG [Parser]: is_reservation = {is_reservation}")
        if not is_reservation:
            print(f"DEBUG [Parser]: ✅ 非預約訊息，結束解析")
            print(f"{'='*60}\n")
            return {'isReservation': False}
        
        print(f"DEBUG [Parser]: ✅ 確認為預約訊息，繼續提取資訊...")
        print(f"{'='*60}\n")
            
        # 先從 Redis 載入現有狀態（如果有的話）
        existing_data = {}
        if line_key:
            print(f"DEBUG [Parser]: Step 3 - 從 Redis 載入現有資料...")
            existing_data = _get_data_from_redis(line_key) or {}
            print(f"DEBUG [Redis]: 載入的資料: {existing_data}")
        
        # 若 isAboutReservation=true 則進行原本的後續行為
        # 先提取新的解析結果
        print(f"DEBUG [Parser]: Step 4 - 提取預約資訊...")
        print(f"DEBUG [Parser]: Step 4.1 - 提取店家...")
        new_branch = self._extract_branch(text)
        print(f"DEBUG [Parser]: 新提取的店家: {new_branch}")
        
        print(f"DEBUG [Parser]: Step 4.2 - 提取師傅...")
        new_masseur = self._extract_staff_names(text)
        print(f"DEBUG [Parser]: 新提取的師傅: {new_masseur}")
        
        print(f"DEBUG [Parser]: Step 4.3 - 提取療程時間...")
        new_project = self._extract_project(text)
        print(f"DEBUG [Parser]: 新提取的療程: {new_project}")
        
        print(f"DEBUG [Parser]: Step 4.4 - 提取人數...")
        new_count = self._extract_customer_count(text)
        print(f"DEBUG [Parser]: 新提取的人數: {new_count}")
        
        # 合併現有資料和新解析結果
        print(f"DEBUG [Parser]: Step 5 - 合併現有和新資料...")
        # 只有當新解析出的資料非空/非None或有明確意圖清空時，才更新對應欄位
        # 強制比對分店與時間
        branch_val = new_branch if new_branch is not None else existing_data.get("branch", "")
        print(f"DEBUG [Parser]: 店家合併結果: {branch_val}")
        if not branch_val:
            print(f"DEBUG [Parser]: 店家為空，嘗試從文字中匹配...")
            for branch_key in sorted(self.branch_mapping.keys(), key=len, reverse=True):
                if branch_key in text:
                    branch_val = self.branch_mapping[branch_key]
                    print(f"DEBUG [Parser]: 匹配到店家: {branch_key} -> {branch_val}")
                    break
        
        print(f"DEBUG [Parser]: Step 6 - 建立最終結果...")
        
        # 提取日期和時間，確保是字串格式
        date_val = ""
        time_val = ""
        if datetime_result:
            # 從 datetime_result 提取日期
            if '日期' in datetime_result and datetime_result['日期'] and datetime_result['日期'] != 'null':
                date_val = str(datetime_result['日期'])  # 確保是字串
                # 轉換格式 YYYY-MM-DD 為 YYYY/MM/DD
                if '-' in date_val:
                    date_val = date_val.replace('-', '/')
            # 從 datetime_result 提取時間
            if '時間' in datetime_result and datetime_result['時間'] and datetime_result['時間'] != 'null':
                time_val = str(datetime_result['時間'])  # 確保是字串
        
        # 如果新解析沒有值，使用現有值
        if not date_val:
            date_val = existing_data.get("date", "")
        if not time_val:
            time_val = existing_data.get("time", "")
        
        result = {
            "branch": branch_val,
            "masseur": new_masseur if new_masseur or self._should_clear_masseur(text) else existing_data.get("masseur", []),
            "date": date_val,
            "time": time_val,
            "project": new_project if new_project > 0 else existing_data.get("project", 0),
            "count": new_count if new_count > 0 else existing_data.get("count", 1),
            "isReservation": True
        }
        
        print(f"\nDEBUG [Parser]: ========== 最終解析結果 ===========")
        print(f"DEBUG [Parser]: 店家: {result['branch']}")
        print(f"DEBUG [Parser]: 師傅: {result['masseur']}")
        print(f"DEBUG [Parser]: 日期: {result['date']}")
        print(f"DEBUG [Parser]: 時間: {result['time']}")
        print(f"DEBUG [Parser]: 療程: {result['project']}")
        print(f"DEBUG [Parser]: 人數: {result['count']}")
        print(f"{'='*60}\n")

        # 如果提供了 line_key，則保存到 Redis
        if line_key and is_reservation:
            print(f"DEBUG [Parser]: Step 7 - 保存結果到 Redis...")
            _save_data_to_redis(line_key, result)
        
        print(f"DEBUG [Parser]: 解析完成\n")
        return result
    
    def _extract_branch(self, text: str) -> str:
        """提取分店名稱"""
        # 檢查是否有明確指出不去分店的表述
        if "不去" in text or "不指定分店" in text or "不要分店" in text or re.search(r'(無|没有|没).*分店', text, re.IGNORECASE):
            return ""
        # 直接比對 BRANCH_MAPPING 關鍵字
        for branch_key in sorted(self.branch_mapping.keys(), key=len, reverse=True):
            if branch_key in text:
                return self.branch_mapping[branch_key]
        return None
    
    def _extract_staff_names(self, text: str) -> List[str]:
        """提取師傅名稱列表"""
        # 檢查是否有"無老師"或"沒有老師"等表示不需要指定師傅的詞
        if "無老師" in text or "沒有老師" in text or "不指定老師" in text or "無特定老師" in text:
            return []
        
        # 檢查一般的"不指定"、"都可以"、"隨便"等表示不需要指定師傅的詞
        if "不指定" in text or "有那些" in text or "誰可以" in text or "誰比較" in text or "推蔫" in text or "都可以" in text or "隨便" in text:
            return []
            
        try:
            # 使用 handle_staff.py 的 getStaffNames 函數
            staff_names = getStaffNames(text)
            # 過濾掉可能的"無"作為師傅名
            staff_names = [name for name in staff_names if name != "無"]
            return staff_names
        except Exception as e:
            print(f"警告：師傅名稱提取失敗：{e}")
            return []
    '''
    def _extract_date(self, text: str, datetime_result=None) -> str:
        """提取日期"""
        try:
            # 使用已經解析好的日期時間結果
            if datetime_result and isinstance(datetime_result, dict) and '日期' in datetime_result:
                # 將日期格式轉換為 YYYY/MM/DD
                date_str = datetime_result['日期']
                if date_str and date_str != "null":
                    return date_str.replace("-", "/")
            
            # 如果傳入的結果無效，則重新解析（向後兼容）
            if not datetime_result:
                result = parse_datetime_phrases(text)
                if result and isinstance(result, dict) and '日期' in result:
                    date_str = result['日期']
                    if date_str and date_str != "null":
                        return date_str.replace("-", "/")
            
            # 如果沒有找到日期，返回空字符串
            return ""
            
        except (ImportError, ValueError, TypeError, KeyError) as e:
            print(f"警告：日期提取失敗：{e}")
            # 如果解析失敗，返回空字符串
            return ""
            return ""
            today = datetime.now().strftime("%Y/%m/%d")
            return today
    
    def _extract_time(self, text: str, datetime_result=None) -> str:
        """提取時間"""
        try:
            # 優先使用 parse_datetime_phrases 結果
            if datetime_result and isinstance(datetime_result, dict) and '時間' in datetime_result:
                time_str = datetime_result['時間']
                if time_str and time_str != "null":
                    # 如果時間格式是 HH:MM:SS，截取前 5 個字符獲得 HH:MM
                    if re.match(r"^\d{2}:\d{2}", time_str):
                        return time_str[:5]
                    if len(time_str) >= 5:
                        return time_str[:5]
                    return time_str
            # 如果傳入的結果無效，則重新解析
            if not datetime_result:
                result = parse_datetime_phrases(text)
                if result and isinstance(result, dict) and '時間' in result:
                    time_str = result['時間']
                    if time_str and time_str != "null":
                        if re.match(r"^\d{2}:\d{2}", time_str):
                            return time_str[:5]
                        if len(time_str) >= 5:
                            return time_str[:5]
                        return time_str
            return ""
        except Exception as e:
            print(f"警告：時間提取失敗：{e}")
            return ""
    '''
    
    def _extract_project(self, text: str) -> int:
        """提取項目時間"""
        # 檢查項目時間關鍵字
        for project_key, value in self.project_mapping.items():
            if project_key in text:
                return value
        
        # 檢查數字模式
        time_patterns = [
            r'(\d+)\s*分鐘',
            r'(\d+)\s*分',
            r'(\d+)\s*小時',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, text)
            if match:
                time_value = int(match.group(1))
                if '小時' in match.group(0):
                    time_value *= 60
                
                # 標準化到 60, 90, 120
                if time_value <= 60:
                    return 60
                elif time_value <= 90:
                    return 90
                else:
                    return 120
        
        # 預設項目時間0
        return 0
    
    def _extract_customer_count(self, text: str) -> int:
        """提取客人數量"""
        try:
            # 使用 handle_customer.py 的 getCustomerCount 函數
            count = getCustomerCount(text)
            return count
        except Exception as e:
            print(f"警告：客人數量提取失敗：{e}")
            # 提取失敗時返回預設值 1
            return 1
    
    def _should_clear_branch(self, text: str) -> bool:
        """判斷是否應該清空分店欄位"""
        return ("不去" in text or "不指定分店" in text or "不要分店" in text or 
                re.search(r'(無|没有|没).*分店', text, re.IGNORECASE))
    
    def _should_clear_masseur(self, text: str) -> bool:
        """判斷是否應該清空師傅欄位"""
        return ("無老師" in text or "沒有老師" in text or "不指定老師" in text or 
                "無特定老師" in text or "不指定" in text or "都可以" in text or "隨便" in text)

# 創建全域解析器實例
parser = NaturalLanguageParser()

def _get_redis_client():
    """獲取 Redis 客戶端連接"""
    try:
        return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    except Exception as e:
        print(f"Redis 連接失敗: {e}")
        return None

def _get_data_from_redis(line_key):
    """從 Redis 獲取資料，檢查是否過期"""
    try:
        r = _get_redis_client()
        if r is None:
            return None
        
        data_str = r.get(line_key)
        if not data_str:
            return None
        
        data = json.loads(data_str)
        
        # 檢查資料是否過期 (12小時)
        if "update" in data:
            update_time = float(data["update"])
            current_time = time.time()
            if current_time - update_time > REDIS_EXPIRY:
                return None  # 資料已過期
        else:
            return None  # 沒有時間戳記，視為無效
        
        return data
    except Exception as e:
        print(f"從 Redis 獲取資料失敗: {e}")
        return None

def _save_data_to_redis(line_key, data):
    """儲存資料到 Redis"""
    try:
        r = _get_redis_client()
        if r is None:
            print(f"DEBUG [Redis]: 無法連接 Redis，跳過儲存")
            return False
        
        # 添加時間戳記
        data["update"] = time.time()
        
        # 將所有 datetime/date 物件轉換為字串
        def convert_datetime(obj):
            import datetime as dt
            # 處理 datetime.datetime 物件
            if isinstance(obj, dt.datetime):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            # 處理 datetime.date 物件
            elif isinstance(obj, dt.date):
                return obj.strftime('%Y-%m-%d')
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            return obj
        
        # 轉換資料
        data_to_save = convert_datetime(data)
        
        print(f"DEBUG [Redis]: 準備儲存到 Redis key={line_key}")
        print(f"DEBUG [Redis]: 資料內容: {data_to_save}")
        
        # 儲存資料
        r.set(line_key, json.dumps(data_to_save, ensure_ascii=False))
        print(f"DEBUG [Redis]: ✅ 儲存成功")
        return True
    except Exception as e:
        print(f"❌ 儲存資料到 Redis 失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def _delete_data_from_redis(line_key):
    """從 Redis 刪除指定 key 的資料"""
    try:
        r = _get_redis_client()
        if r is None:
            return False
        
        # 刪除資料
        r.delete(line_key)
        return True
    except Exception as e:
        print(f"從 Redis 刪除資料失敗: {e}")
        return False

def _extract_branch_only(text: str) -> str:
    """僅提取分店名稱，不進行完整解析"""
    # 檢查是否有明確指出不去分店的表述
    if "不去" in text or "不指定分店" in text or "不要分店" in text or re.search(r'(無|没有|没).*分店', text, re.IGNORECASE):
        return ""
    
    # 檢查是否有指定分店
    for branch_key, value in BRANCH_MAPPING.items():
        if branch_key in text:
            return value
    
    # 注意：單純的"不指定"、"都可以"、"隨便"不應該清空分店
    # 只有明確提到分店相關的"不指定"才會清空分店
    # 這些詞彙主要是用於師傅選擇，不應影響分店
            
    # 預設分店，如果真的沒有找到任何分店信息
    return ""  # 當找不到分店時，回傳空白字串


def parse_natural_language(text: str) -> Dict[str, Any]:
    """
    解析自然語言的主要函數，僅接受 JSON 格式的輸入 {"key":"key value","message":"message text"}
    
    Args:
        text (str): 用戶輸入的 JSON 格式文本
        
    Returns:
        Dict[str, Any]: 解析結果，包括用戶每日問侯相關信息
    """
    try:
        # 嘗試解析 JSON
        data = json.loads(text)
        
        # 檢查是否符合預期格式
        if not isinstance(data, dict) or "key" not in data or "message" not in data:
            return {"error": "輸入格式必須為 JSON 且包含 key 和 message 欄位"}
        
        line_key = data["key"]
        message = data["message"]
        
        if not line_key or line_key.strip() == "":
            return {"error": "key 不能為空"}
        
        # 更新用戶的 visitdate 為當前日期，並獲取更新前的用戶信息
        # 返回的 user_info 包含更新前的 visitdate，用於判斷是否需要顯示問侯語
        old_user_info = update_user_visitdate(line_key)
        
        # 如果更新成功，使用舊的用戶信息；否則獲取當前用戶信息
        if old_user_info:
            user_info = old_user_info
        else:
            user_info = get_user_info(line_key)
        
        # 檢查是否是清除 Redis 的命令
        if message.strip().lower() == "clean redis":
            # 清除 Redis 中與該 key 相關的資料
            success = _delete_data_from_redis(line_key)
            return {
                "branch": "",
                "masseur": [],
                "date": datetime.now().strftime("%Y/%m/%d"),
                "time": datetime.now().strftime("%H:%M"),
                "project": 0,
                "count": 0,
                "isReservation": False,
                "success": success,
                "message": f"已成功清除 Redis 中 key 為 '{line_key}' 的資料" if success else f"清除 Redis 中 key 為 '{line_key}' 的資料時發生錯誤",
                "user_info": user_info
            }
        
        # 判定是否與預約相關
        is_mod_reservation = False
        is_reservation = False

        result = _get_data_from_redis(line_key)
        #如果有先前的資料，則我們判定是否要修改內容
        if result:
            # 移除之前的關鍵詞匹配狀態，每次都重新判斷
            if 'is_keyword_match' in result:
                del result['is_keyword_match']
            if 'response_message' in result:
                del result['response_message']
            # 日期判斷
            try:
                datetime_result = parse_datetime_phrases(message)
                if datetime_result and (
                    ('日期' in datetime_result and datetime_result['日期'] and datetime_result['日期'] != "null") or
                    ('時間' in datetime_result and datetime_result['時間'] and datetime_result['時間'] != "null")
                ):
                    if datetime_result['日期'] and datetime_result['日期'] != "null":
                        result['date'] = datetime_result['日期'].replace("-", "/")  
                    if datetime_result['時間'] and datetime_result['時間'] != "null":
                        result['time'] = datetime_result['時間']
                        if result['date'] =='' or result['date'] == "null":
                            #設置為今天日期
                            result['date'] = datetime.now().strftime("%Y/%m/%d")
                    is_mod_reservation = True
            except Exception as e:
                print(f"警告：日期時間解析失敗：{e}")
                datetime_result = {}

            # 按照長度排序，先檢查較長的關鍵詞
            sorted_branches = sorted(BRANCH_MAPPING.keys(), key=len, reverse=True)
            for branch in sorted_branches:
                if branch in message:
                    result['branch'] = BRANCH_MAPPING[branch]
                    is_mod_reservation = True
                    break
            
            # 師傅判斷
            try:
                staff_names = getStaffNames(message)
                if staff_names and len(staff_names) > 0:
                    result['masseur'] = staff_names
                    is_mod_reservation = True
            except Exception as e:
                print(f"警告：師傅判斷失敗：{e}")
                staff_names = []


            # 項目時間判斷
            for key_word in PROJECT_MAPPING.keys():
                if key_word in message:
                    result['project'] = PROJECT_MAPPING[key_word]
                    is_mod_reservation = True
                    break

            # 客人数量判断 - 使用统一入口
            try:
                customer_count, is_explicit = getCustomerCount(message, return_details=True)
                current_count = result.get('count', 1)
                
                # 检查是否有连接模式
                has_connection_patterns = any(pattern in message for pattern in [
                    "我和", "我跟", "我與", "我們", "一起", "家人", "朋友", "夫妻", "情侶"
                ])
                
                # 只有在有明确人数相关表达时才考虑更新人数
                if is_explicit or has_connection_patterns:
                    if customer_count != current_count:
                        result['count'] = customer_count
                        is_mod_reservation = True
                        print(f"更新人数：从 {current_count} 变更为 {customer_count}")
            except Exception as e:
                print(f"警告：人数判断失败：{e}")

            # 新增：只要同時解析出日期、時間、分店就判斷為預約
            if result.get('date') and result.get('time') and result.get('branch'):
                is_mod_reservation = True

            if is_mod_reservation:
                # 確保修改後的資料是正常預約資料，不帶關鍵詞匹配狀態
                result['isReservation'] = True
                result['user_info'] = user_info
                _save_data_to_redis(line_key, result)
                return result
            
        #當is_mod_reservation為False，會執行到此
        #判別新語句是否為預約相關
        is_reservation = isReservation(message)
        
        # 如果不是预约相关，但有明确的人数表达，也视为预约相关的修改
        if not is_reservation:
            _, is_explicit = getCustomerCount(message, return_details=True)
            if is_explicit:
                is_reservation = True
            result = parse_datetime_phrases(message)
            datetime_result = parse_datetime_phrases(message)
            if datetime_result and (
                    ('日期' in datetime_result and datetime_result['日期'] and datetime_result['日期'] != "null") or
                    ('時間' in datetime_result and datetime_result['時間'] and datetime_result['時間'] != "null")
            ):
                is_reservation = True

        # 最後總結判定
        if not is_reservation:
            # 如果不是預約相關，檢查是否匹配關鍵詞
            keyword_response = check_keywords_match(message)
            if keyword_response:
                # 如果匹配到關鍵詞，返回帶有回應消息的結果
                return {
                    "branch": "",
                    "masseur": [],
                    "date": datetime.now().strftime("%Y/%m/%d"),
                    "time": datetime.now().strftime("%H:%M"),
                    "project": 0,
                    "count": 0,
                    "isReservation": False,
                    "is_keyword_match": True,
                    "response_message": keyword_response,
                    "user_info": user_info
                }

            result = {
                "branch": "",
                "masseur": [],
                "date": datetime.now().strftime("%Y/%m/%d"),
                "time": datetime.now().strftime("%H:%M"),
                "project": 0,
                "count": 0,
                "isReservation": False,
                "user_info": user_info
            }
            # 不是預約相關的訊息，不保存到 Redis
            return result
        
        # 沒有之前的資料或資料已過期，處理新訊息
        result = parser.parse_text(message, line_key)
        # 強制比對分店與時間
        if not result.get("branch"):
            for branch_key in sorted(BRANCH_MAPPING.keys(), key=len, reverse=True):
                if branch_key in message:
                    result["branch"] = BRANCH_MAPPING[branch_key]
                    break
        if not result.get("time"):
            m = re.search(r"(\d{1,2}):(\d{2})", message)
            if m:
                result["time"] = f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"
        # 只有當結果是預約相關時，才儲存到 Redis
        if result.get("isReservation", False):
            _save_data_to_redis(line_key, result)
        # 添加用戶信息到結果中
        result['user_info'] = user_info
        return result
    
    except json.JSONDecodeError:
        # 返回帶有所有必需字段的錯誤響應
        return {
            "branch": "",
            "masseur": [],
            "date": datetime.now().strftime("%Y/%m/%d"),
            "time": datetime.now().strftime("%H:%M"),
            "project": 0,
            "count": 0,
            "isReservation": False,
            "is_keyword_match": False,
            "response_message": None,
            "success": False,
            "message": None,
            "error": "輸入必須為有效的 JSON 格式",
            "user_info": None
        }
    except Exception as e:
        print(f"處理 JSON 輸入時出錯: {e}")
        # 返回帶有所有必需字段的錯誤響應
        return {
            "branch": "",
            "masseur": [],
            "date": datetime.now().strftime("%Y/%m/%d"),
            "time": datetime.now().strftime("%H:%M"),
            "project": 0,
            "count": 0,
            "isReservation": False,
            "is_keyword_match": False,
            "response_message": None,
            "success": False,
            "message": None,
            "error": f"處理輸入時發生錯誤: {str(e)}",
            "user_info": None
        }

