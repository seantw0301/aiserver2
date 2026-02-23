from datetime import datetime
from typing import Optional, Dict, Tuple
import redis
from core.common import update_user_visitdate, get_user_info

# Redis Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

def get_redis_connection():
    """建立 Redis 連接"""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def check_daily_greeting(line_user_id: str) -> Tuple[Optional[str], Optional[Dict]]:
    """
    Check if a daily greeting should be sent to the user.
    Uses Redis to cache last visit date for performance.
    
    Args:
        line_user_id (str): The LINE user ID.
        
    Returns:
        Tuple[Optional[str], Optional[Dict]]: 
            - The greeting message if applicable, else None.
            - The user info dictionary.
    """
    greeting_message = None
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 1. 先從 Redis 檢查上次對話日期（快速判斷）
    try:
        r = get_redis_connection()
        last_visit = r.get(f"{line_user_id}_lastest")
        
        # 如果 Redis 有記錄且是今天，則不需要問候語
        if last_visit and last_visit == today:
            # 直接從資料庫獲取 user_info（不更新 visitdate）
            user_info = get_user_info(line_user_id)
            return None, user_info
    except Exception as e:
        print(f"Redis check failed: {e}")
        # Redis 失敗時繼續使用資料庫邏輯
    
    # 2. Redis 無記錄或不是今天，需要檢查並可能產生問候語
    # Update user's visitdate to current date and get old user info
    old_user_info = update_user_visitdate(line_user_id)
    
    # If update successful, use old info; otherwise fetch current info
    if old_user_info:
        user_info = old_user_info
    else:
        user_info = get_user_info(line_user_id)
    
    if user_info:
        old_visitdate = user_info.get('visitdate')
        display_name = user_info.get('display_name', '尊敬的會員')
        user_id = user_info.get('id', line_user_id)
        
        # Handle visitdate format (datetime object or string)
        visitdate_date_str = None
        if old_visitdate:
            if isinstance(old_visitdate, datetime):
                visitdate_date_str = old_visitdate.strftime("%Y-%m-%d")
            elif isinstance(old_visitdate, str):
                visitdate_date_str = old_visitdate[:10] if len(old_visitdate) >= 10 else old_visitdate
            else:
                visitdate_date_str = str(old_visitdate)[:10]
        
        # If visitdate is None or not today, generate greeting
        if old_visitdate is None or visitdate_date_str != today:
            greeting_message = f"親愛的會員{display_name}({user_id})您好!"
        
        # 3. 更新 Redis 快取（記錄今天已訪問）
        try:
            r = get_redis_connection()
            # 設定為今天的日期，過期時間為 36 小時（確保跨日後失效）
            r.setex(f"{line_user_id}_lastest", 36 * 3600, today)
        except Exception as e:
            print(f"Redis update failed: {e}")
            
    return greeting_message, user_info
