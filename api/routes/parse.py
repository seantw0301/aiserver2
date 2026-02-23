from fastapi import APIRouter
from datetime import datetime
from api.models import NaturalLanguageRequest
from modules import lang, greeting, appointment, keyword, multilang, integration
from utils import run_in_executor
from core.multilanguage import MultiLanguage
from keywords_manager import get_skip_keywords
import redis

router = APIRouter(tags=["Parse"])

# Redis Configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

def get_redis_connection():
    """建立 Redis 連接"""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def clear_user_redis_data(line_user_id: str) -> dict:
    """
    清空 Redis 上所有與特定 line_user_id 相關的資料
    
    Args:
        line_user_id (str): LINE 用戶 ID
        
    Returns:
        dict: 包含清除結果的字典
    """
    try:
        r = get_redis_connection()
        
        # 尋找所有以 line_user_id 開頭的 key
        pattern = f"{line_user_id}*"
        keys = r.keys(pattern)
        
        if keys:
            # 刪除所有找到的 key
            deleted_count = r.delete(*keys)
            print(f"已清除 {deleted_count} 個 Redis keys (pattern: {pattern})")
            return {
                "success": True,
                "deleted_count": deleted_count,
                "keys": keys,
                "message": f"已清除 {deleted_count} 筆 Redis 資料"
            }
        else:
            print(f"未找到任何符合 pattern: {pattern} 的 Redis keys")
            return {
                "success": True,
                "deleted_count": 0,
                "keys": [],
                "message": "未找到任何相關的 Redis 資料"
            }
            
    except Exception as e:
        print(f"清除 Redis 資料錯誤: {e}")
        return {
            "success": False,
            "deleted_count": 0,
            "keys": [],
            "message": f"清除失敗: {str(e)}"
        }

#新增一個function 名為。check_skip_keyword
def check_has_skip_keyword(message: str) -> bool:
    # 在此實現檢查是否跳過關鍵字的邏輯
    # 例如，根據 message 內容判斷是否跳過
    # 從資料庫/Redis 取得最新的 skip_keywords
    skip_keywords = get_skip_keywords()
    for keyword in skip_keywords:
        if keyword in message:
            return True
    return False


@router.post("/parse", summary="自然語言解析")
async def parse_natural_text(request: NaturalLanguageRequest):
    """
    解析客戶輸入的自然語言文字，提取預約資訊
    
    六階段處理流程：
    1. 語系判斷 (Language Module) - 若為設置語系，設置完後跳到第六階段
    2. 問候語判斷 (Greeting Module) - 必需階段，無法跳過
    3. 預約判斷 (Appointment Module) - 若為預約，處理完後跳到第六階段
    4. 關鍵字判斷 (Keyword Module) - 處理完後跳到第六階段
    5. 文字輸出階段 (MultiLang Module) - 必需階段，依用戶語系翻譯回應訊息
    6. 整合階段 (Integration Module) - 必需階段，格式化為 LINE SDK 可顯示的格式
    
    客戶可以輸入自然語言，例如：
    - "我想要明天下午2點在西門預約鞋老師和川老師的90分鐘按摩，2位客人"
    - "今天晚上7點延吉店，豪老師，60分鐘，1人"
    - "8月16日上午10點，西門，遠老師，120分鐘按摩"
    
    系統會自動解析並返回結構化的預約資訊。
    
    每日問侯語功能：
    - 當客人傳送訊息時，系統會更新 line_users 表中的 visitdate 欄位為當下日期
    - 若客人的 visitdate 不是今日，系統會在返回訊息最後面加上問侯語：
      "親愛的會員{display_name}({line_user_id})您好!"
    """
    try:
        # 檢查是否為 clearredis 指令
        if request.message.strip().lower() == "clearredis":
            clear_result = clear_user_redis_data(request.key)
            
            # 取得用戶語系（如果還存在的話，否則使用預設值）
            try:
                user_language = lang.get_user_language(request.key) or 'zh-TW'
            except:
                user_language = 'zh-TW'
            
            parsed_data = {
                "branch": "",
                "masseur": [],
                "date": "",
                "time": "",
                "project": 0,
                "count": 0,
                "isReservation": False,
                "is_keyword_match": False,
                "is_language_setting": False,
                "is_redis_clear": True,
                "response_message": clear_result.get("message", "Redis 資料已清除"),
                "redis_clear_details": {
                    "deleted_count": clear_result.get("deleted_count", 0),
                    "keys": clear_result.get("keys", [])
                },
                "success": clear_result.get("success", True)
            }
            
            # 格式化為 LINE SDK 格式
            parsed_data = integration.format_for_line_sdk(parsed_data)
            return parsed_data
        

        # 1. 判斷語系 (Language Module)
        detected_lang = lang.detect_language(request.message)
        if detected_lang:
            lang.set_user_language(request.key, detected_lang)
            # 語系設置完成，直接跳到第五階段（多國語處理）
            user_language = detected_lang
            parsed_data = {
                "branch": "",
                "masseur": [],
                "date": "",
                "time": "",
                "project": 0,
                "count": 0,
                "isReservation": False,
                "is_keyword_match": False,
                "is_language_setting": True,
                "response_message": f"語系已設定為：{user_language}",
                "success": True
            }
            # 跳到第五階段
            parsed_data = multilang.translate_response_fields(parsed_data, user_language)
            # 第六階段：整合階段 (Integration Module)
            parsed_data = integration.format_for_line_sdk(parsed_data)
            return parsed_data
        else:
            lang.initialize_user_language_if_needed(request.key, 'zh-TW')

        # 取得用戶當前語系設定
        user_language = lang.get_user_language(request.key)

        # 2. 每日問候語 (Greeting Module) - 必需階段
        greeting_message, user_info = greeting.check_daily_greeting(request.key)

        has_skip_keyword = False
        has_skip_keyword = check_has_skip_keyword(request.message)

        # 2.1 將可能的員工名字和分店的名字，用代位符號取代，以免翻譯成繁體中文時出錯
        # 這裡可以根據實際需求實現替換邏輯
        # 使用 core/multilanguage.py 裡的 translate_to_traditional_chinese 把文字變成繁體中文
        request.message, _ = MultiLanguage.translate_to_traditional_chinese(request.message)
        #輸出翻譯後的文字供debug    
        print(f"翻譯後的文字: {request.message}")

        # 3. 預約流程 (Appointment Module)
        if not has_skip_keyword:
            parsed_data = await run_in_executor(appointment.process_appointment, request.key, request.message, user_info)
        else: 
            parsed_data = {}
            parsed_data['isReservation'] = False

        # 將問候語添加到返回結果中
        if greeting_message:
            parsed_data['greeting_message'] = greeting_message

        # 若為預約，直接跳到第五階段
        if parsed_data.get('isReservation', False):
            # 5. 文字輸出階段 (MultiLang Module) - 多國語系翻譯
            parsed_data = multilang.translate_response_fields(parsed_data, user_language)
            # 6. 整合階段 (Integration Module)
            parsed_data = integration.format_for_line_sdk(parsed_data)
            return parsed_data
        
        # 4. 關鍵字搜尋 (Keyword Module) - 只有在非預約時才進行
        keyword_response = keyword.check_keywords_match(request.message)
        if keyword_response:
            parsed_data['is_keyword_match'] = True
            parsed_data['response_message'] = keyword_response
            # 處理完關鍵字後，跳到第五階段
            # 5. 文字輸出階段 (MultiLang Module)
            parsed_data = multilang.translate_response_fields(parsed_data, user_language)
            # 6. 整合階段 (Integration Module)
            parsed_data = integration.format_for_line_sdk(parsed_data)
            return parsed_data

        # 如果沒有匹配任何關鍵字或預約，提供預設回應(不回應)
        #if not parsed_data.get('response_message'):
        #    parsed_data['response_message'] = ""

        # 5. 文字輸出階段 (MultiLang Module) - 多國語系翻譯
        parsed_data = multilang.translate_response_fields(parsed_data, user_language)
        
        # 6. 整合階段 (Integration Module) - 格式化為 LINE SDK 可顯示的格式
        parsed_data = integration.format_for_line_sdk(parsed_data)
        
        return parsed_data
        
    except Exception as e:
        current_time = datetime.now()
        error_data = {
            "branch": "",
            "masseur": [],
            "date": current_time.strftime("%Y/%m/%d"),
            "time": current_time.strftime("%H:%M"),
            "project": 0,
            "count": 0,
            "isReservation": False,
            "is_keyword_match": False,
            "response_message": None,
            "success": False,
            "message": None,
            "error": f"自然語言解析失敗: {str(e)}"
        }
        
        # 即使發生錯誤，也嘗試翻譯錯誤訊息並格式化
        try:
            user_language = lang.get_user_language(request.key)
            error_data = multilang.translate_response_fields(error_data, user_language)
            error_data = integration.format_for_line_sdk(error_data)
        except:
            pass  # 如果翻譯或格式化失敗，返回原始錯誤訊息
        
        return error_data
