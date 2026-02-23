import redis
from core.database import db_config
from typing import Optional

# Redis Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Language Mapping
LANGUAGE_MAPPING = {
    'English': 'en',
    'Thailand': 'th',
    'Taiwan': 'zh-TW',
    '英文': 'en',
    '中文': 'zh-TW',
    '泰文': 'th',
    '日文': 'ja',
    'Japanese': 'ja',
    'Korean': 'ko',
    '韓文': 'ko'
}

def get_redis_connection():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def detect_language(text: str) -> Optional[str]:
    """
    Detect language from text based on keywords.
    Returns language code if found, else None.
    """
    for keyword, lang_code in LANGUAGE_MAPPING.items():
        if keyword.lower() in text.lower():
            return lang_code
    return None

def set_user_language(line_user_id: str, language: str) -> bool:
    """
    Set user language in DB and Redis.
    """
    try:
        # Update Redis
        r = get_redis_connection()
        r.set(f"{line_user_id}_lang", language)
        
        # Update DB - 使用 INSERT ... ON DUPLICATE KEY UPDATE 確保用戶不存在時也能寫入
        connection = db_config.get_connection()
        if connection:
            cursor = connection.cursor()
            # 先檢查用戶是否存在
            cursor.execute("SELECT line_id FROM line_users WHERE line_id = %s", (line_user_id,))
            exists = cursor.fetchone()
            
            if exists:
                # 用戶存在，執行更新
                query = "UPDATE line_users SET language = %s WHERE line_id = %s"
                cursor.execute(query, (language, line_user_id))
            else:
                # 用戶不存在，插入新記錄
                query = "INSERT INTO line_users (line_id, language) VALUES (%s, %s)"
                cursor.execute(query, (line_user_id, language))
            
            connection.commit()
            cursor.close()
            connection.close()
            return True
    except Exception as e:
        print(f"Error setting user language: {e}")
        return False
    return False

def get_user_language(line_user_id: str) -> str:
    """
    Get user language from Redis, default to 'zh-TW'.
    """
    try:
        r = get_redis_connection()
        lang = r.get(f"{line_user_id}_lang")
        if lang:
            return lang
    except Exception as e:
        print(f"Error getting user language from Redis: {e}")
    
    return 'zh-TW'

def initialize_user_language_if_needed(line_user_id: str, default_lang: str = 'zh-TW') -> str:
    """
    Check if user language is set in Redis. If not, set it to default_lang.
    Returns the current (or new) language.
    """
    try:
        r = get_redis_connection()
        lang = r.get(f"{line_user_id}_lang")
        if not lang:
            set_user_language(line_user_id, default_lang)
            return default_lang
        return lang
    except Exception as e:
        print(f"Error initializing user language: {e}")
        return default_lang
