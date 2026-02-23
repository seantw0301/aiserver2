"""
五階段處理架構 - 使用範例
"""

# 範例 1: 用戶首次使用（預設繁體中文）
# =====================================
# 請求:
POST /parse
{
    "key": "U9876543210",
    "message": "我要明天下午2點預約"
}

# 回應（繁體中文）:
{
    "branch": "西門店",
    "masseur": ["鞋老師"],
    "date": "2025/11/28",
    "time": "14:00",
    "isReservation": true,
    "response_message": "已為您找到 1 位師傅的空檔時間",
    "greeting_message": "親愛的會員 John(U9876543210) 您好!",
    "success": true
}


# 範例 2: 用戶切換到英文
# =====================================
# 步驟 1: 發送語系切換訊息
POST /parse
{
    "key": "U9876543210",
    "message": "English"
}

# 步驟 2: 後續訊息都會以英文回應
POST /parse
{
    "key": "U9876543210",
    "message": "我要明天下午2點預約"
}

# 回應（英文）:
{
    "branch": "西門店",
    "masseur": ["鞋老師"],
    "date": "2025/11/28",
    "time": "14:00",
    "isReservation": true,
    "response_message": "Found available time for 1 therapist",
    "greeting_message": "Dear member John(U9876543210), Hello!",
    "success": true
}


# 範例 3: 用戶使用泰文
# =====================================
POST /parse
{
    "key": "U1111111111",
    "message": "Thailand"
}

# 後續預約請求
POST /parse
{
    "key": "U1111111111",
    "message": "我要明天下午2點預約"
}

# 回應（泰文）:
{
    "branch": "西門店",
    "masseur": ["鞋老師"],
    "date": "2025/11/28",
    "time": "14:00",
    "isReservation": true,
    "response_message": "พบความพร้อมของอาจารย์ 1 คนสําหรับคุณแล้ว",
    "greeting_message": "เรียนสมาชิก John(U1111111111) สวัสดี!",
    "success": true
}


# 範例 4: 關鍵字查詢（英文回應）
# =====================================
# 用戶語系已設為英文
POST /parse
{
    "key": "U9876543210",
    "message": "營業時間"
}

# 回應:
{
    "isReservation": false,
    "is_keyword_match": true,
    "response_message": "Business hours: 10:00-22:00",  # 已翻譯成英文
    "success": true
}


# 範例 5: 錯誤處理（日文）
# =====================================
# 用戶語系為日文
POST /parse
{
    "key": "U2222222222",
    "message": "無效的預約請求"
}

# 回應（日文）:
{
    "isReservation": false,
    "success": false,
    "error": "自然言語解析に失敗しました: 利用可能なマスターが見つかりませんでした",
    "message": "システムエラー。後でもう一度やり直してください"
}


# 五階段處理詳細說明
# =====================================

"""
階段 1: 語系判斷 (Language Module)
- 檢查訊息中是否包含語系關鍵字
- 設定或初始化用戶語系
- 從 Redis 取得用戶當前語系
"""

"""
階段 2: 問候語判斷 (Greeting Module)
- 檢查用戶今天是否首次訪問
- 若是首次，生成問候語
- 更新用戶的訪問日期
"""

"""
階段 3: 預約判斷 (Appointment Module)
- 解析自然語言中的預約資訊
- 查詢師傅空檔時間
- 生成預約結果（繁體中文）
"""

"""
階段 4: 關鍵字判斷 (Keyword Module)
- 若非預約，檢查是否為關鍵字查詢
- 從資料庫取得對應回應
- 加入回應訊息（繁體中文）
"""

"""
階段 5: 文字輸出階段 (MultiLang Module) ← 新增
- 根據用戶語系設定翻譯所有文字欄位
- 翻譯 response_message, greeting_message, error, message
- 若為繁體中文，直接返回不翻譯
- 翻譯失敗時返回原文，不中斷服務
"""


# 程式碼範例
# =====================================

from modules import multilang

# 翻譯單一訊息
message = "您的預約已成功"
translated = multilang.translate_message(message, "en")
# 結果: "Your reservation was successful"

# 翻譯整個回應物件
response_data = {
    "response_message": "已為您找到 2 位師傅",
    "greeting_message": "親愛的會員您好",
    "success": True
}

translated_data = multilang.translate_response_fields(response_data, "th")
# 結果:
# {
#     "response_message": "พบอาจารย์ 2 คนให้คุณแล้ว",
#     "greeting_message": "เรียนสมาชิกสวัสดี",
#     "success": True
# }
