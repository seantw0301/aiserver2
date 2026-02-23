import redis
from typing import List, Optional
from datetime import datetime
from core.database import db_config

# Redis Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Redis Keys
SKIP_KEYWORDS_KEY = 'skip_keywords'
SKIP_KEYWORDS_TIMESTAMP_KEY = 'skip_keywords_timestamp'


def get_redis_connection():
    """建立 Redis 連接"""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)


def get_table_last_modified_time() -> Optional[float]:
    """
    取得 skip_keywords 資料表最後變更時間
    
    注意：需要資料表使用 MyISAM 引擎才能正確取得 UPDATE_TIME
    
    Returns:
        Optional[float]: Unix timestamp 或 None
    """
    try:
        connection = db_config.get_connection()
        if not connection:
            print("無法建立資料庫連線")
            return None
        
        cursor = connection.cursor(dictionary=True)
        
        # 查詢資料表的最後更新時間
        query = """
            SELECT UPDATE_TIME 
            FROM information_schema.tables 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'skip_keywords'
        """
        cursor.execute(query, (db_config.database,))
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        if result and result.get('UPDATE_TIME'):
            # 將 datetime 轉換為 Unix timestamp
            update_time = result['UPDATE_TIME']
            if isinstance(update_time, datetime):
                return update_time.timestamp()
            elif isinstance(update_time, str):
                dt = datetime.strptime(update_time, '%Y-%m-%d %H:%M:%S')
                return dt.timestamp()
        
        # 如果無法取得 UPDATE_TIME，返回 None（保持 Redis 快取）
        return None
        
    except Exception as e:
        print(f"取得資料表更新時間錯誤: {e}")
        return None


def get_skip_keywords_from_db() -> List[str]:
    """
    從資料庫讀取 skip_keywords
    
    Returns:
        List[str]: 關鍵字列表
    """
    keywords = []
    
    try:
        connection = db_config.get_connection()
        if not connection:
            print("無法建立資料庫連線")
            return keywords
        
        cursor = connection.cursor(dictionary=True)
        
        # 查詢所有 skip_keywords
        query = "SELECT keyword FROM skip_keywords WHERE keyword IS NOT NULL"
        cursor.execute(query)
        results = cursor.fetchall()
        
        # 提取關鍵字
        keywords = [row['keyword'] for row in results if row.get('keyword')]
        
        cursor.close()
        connection.close()
        
        print(f"從資料庫讀取到 {len(keywords)} 個 skip_keywords")
        
    except Exception as e:
        print(f"從資料庫讀取 skip_keywords 錯誤: {e}")
    
    return keywords


def get_skip_keywords() -> List[str]:
    """
    取得 skip_keywords 列表（帶 Redis 快取）
    
    流程：
    1. 比較資料表與 Redis 的更新時間
    2. 若資料表較新，從資料庫重新讀取並更新 Redis
    3. 否則直接使用 Redis 快取的資料
    
    Returns:
        List[str]: 關鍵字列表
    """
    try:
        r = get_redis_connection()
        
        # 1. 取得資料表最後更新時間
        db_update_time = get_table_last_modified_time()
        
        # 2. 取得 Redis 中的更新時間
        redis_update_time_str = r.get(SKIP_KEYWORDS_TIMESTAMP_KEY)
        redis_update_time = float(redis_update_time_str) if redis_update_time_str else 0
        
        # 3. 比較時間，決定是否需要更新
        need_update = False
        
        if db_update_time is None:
            # 無法取得資料庫時間，使用 Redis 快取（若有）
            print("無法取得資料庫更新時間，使用 Redis 快取")
        elif redis_update_time == 0:
            # Redis 沒有快取，需要更新
            print("Redis 無快取，從資料庫載入")
            need_update = True
        elif db_update_time > redis_update_time:
            # 資料庫較新，需要更新
            print(f"資料庫已更新 (DB: {db_update_time}, Redis: {redis_update_time})，重新載入")
            need_update = True
        else:
            # Redis 快取仍有效
            print("使用 Redis 快取資料 skip_keywords")
        
        # 4. 根據需要更新或讀取資料
        if need_update:
            # 從資料庫讀取
            keywords = get_skip_keywords_from_db()
            
            if keywords:
                # 將資料存入 Redis（使用 list）
                r.delete(SKIP_KEYWORDS_KEY)  # 先清空舊資料
                if keywords:  # 確保有資料才寫入
                    r.rpush(SKIP_KEYWORDS_KEY, *keywords)
                
                # 更新時間戳記
                r.set(SKIP_KEYWORDS_TIMESTAMP_KEY, db_update_time or datetime.now().timestamp())
                
                print(f"已更新 Redis 快取: {len(keywords)} 個關鍵字")
                return keywords
            else:
                print("資料庫無資料，返回空列表")
                return []
        else:
            # 從 Redis 讀取
            keywords = r.lrange(SKIP_KEYWORDS_KEY, 0, -1)
            
            if keywords:
                print(f"從 Redis 讀取到 {len(keywords)} 個關鍵字")
                return keywords
            else:
                # Redis 無資料，從資料庫載入
                print("Redis 快取為空，從資料庫載入")
                keywords = get_skip_keywords_from_db()
                
                if keywords:
                    r.rpush(SKIP_KEYWORDS_KEY, *keywords)
                    r.set(SKIP_KEYWORDS_TIMESTAMP_KEY, datetime.now().timestamp())
                
                return keywords
                
    except Exception as e:
        print(f"get_skip_keywords 錯誤: {e}")
        # 發生錯誤時，嘗試直接從資料庫讀取
        print("嘗試直接從資料庫讀取")
        return get_skip_keywords_from_db()
