"""
六階段架構使用範例
展示如何使用整合模組 (Integration Module)
"""

import sys
import json
import asyncio

sys.path.insert(0, '/Volumes/aiserver2')

from modules import lang, greeting, appointment, keyword, multilang, integration


# ============================================================
# 範例 1: 完整的六階段流程（預約查詢）
# ============================================================

async def example_1_full_reservation_flow():
    """
    完整的預約查詢流程範例
    展示所有六個階段如何協同工作
    """
    print("\n" + "=" * 60)
    print("範例 1: 完整的預約查詢流程")
    print("=" * 60)
    
    # 模擬用戶輸入
    line_user_id = "U1234567890"
    message = "明天下午2點西門店鞋老師90分鐘2人"
    
    print(f"\n用戶 ID: {line_user_id}")
    print(f"用戶訊息: {message}")
    
    # 第一階段：語系判斷
    print("\n--- 第一階段：語系判斷 ---")
    detected_lang = lang.detect_language(message)
    if not detected_lang:
        lang.initialize_user_language_if_needed(line_user_id, 'zh-TW')
    user_language = lang.get_user_language(line_user_id)
    print(f"用戶語系: {user_language}")
    
    # 第二階段：問候語判斷
    print("\n--- 第二階段：問候語判斷 ---")
    greeting_message, user_info = greeting.check_daily_greeting(line_user_id)
    print(f"問候語: {greeting_message if greeting_message else '無（今日已訪問過）'}")
    
    # 第三階段：預約判斷（這裡使用模擬資料）
    print("\n--- 第三階段：預約判斷 ---")
    parsed_data = {
        "branch": "西門店",
        "masseur": ["鞋老師"],
        "date": "2025/11/28",
        "time": "14:00",
        "project": 90,
        "count": 2,
        "isReservation": True,
        "response_message": "✅ 查詢結果：可以預約\n已為您找到師傅的空檔時間",
        "success": True
    }
    print(f"預約資料: {json.dumps(parsed_data, ensure_ascii=False, indent=2)}")
    
    # 加入問候語
    if greeting_message:
        parsed_data['greeting_message'] = greeting_message
    
    # 第五階段：多國語翻譯
    print("\n--- 第五階段：多國語翻譯 ---")
    parsed_data = multilang.translate_response_fields(parsed_data, user_language)
    print(f"翻譯後語系: {user_language}")
    
    # 第六階段：整合格式化
    print("\n--- 第六階段：整合格式化 ---")
    parsed_data = integration.format_for_line_sdk(parsed_data)
    
    print(f"訊息格式: {parsed_data.get('message_format')}")
    print(f"LINE 訊息數量: {len(parsed_data.get('line_messages', []))}")
    
    # 顯示 LINE 訊息
    print("\nLINE SDK 格式化結果:")
    for idx, msg in enumerate(parsed_data.get('line_messages', [])):
        print(f"\n訊息 {idx + 1}:")
        print(json.dumps(msg, ensure_ascii=False, indent=2))
    
    return parsed_data


# ============================================================
# 範例 2: 關鍵字查詢流程
# ============================================================

def example_2_keyword_flow():
    """
    關鍵字查詢流程範例
    展示非預約訊息如何處理
    """
    print("\n" + "=" * 60)
    print("範例 2: 關鍵字查詢流程")
    print("=" * 60)
    
    line_user_id = "U9876543210"
    message = "營業時間"
    
    print(f"\n用戶 ID: {line_user_id}")
    print(f"用戶訊息: {message}")
    
    # 準備資料（跳過預約階段）
    parsed_data = {
        "isReservation": False,
        "is_keyword_match": True,
        "response_message": "我們的營業時間是週一至週日 10:00-22:00",
        "greeting_message": "親愛的會員 Mary 您好!",
        "success": True
    }
    
    # 直接到第六階段
    print("\n--- 第六階段：整合格式化 ---")
    result = integration.format_for_line_sdk(parsed_data)
    
    print(f"訊息格式: {result.get('message_format')}")
    print("\nLINE 訊息:")
    for idx, msg in enumerate(result.get('line_messages', [])):
        print(f"\n訊息 {idx + 1}: {msg.get('text', msg.get('type'))}")
    
    return result


# ============================================================
# 範例 3: 強制使用 Flex Message
# ============================================================

def example_3_force_flex_format():
    """
    強制使用 Flex Message 格式範例
    """
    print("\n" + "=" * 60)
    print("範例 3: 強制使用 Flex Message")
    print("=" * 60)
    
    # 即使是關鍵字查詢，也可以強制使用 Flex
    parsed_data = {
        "branch": "延吉店",
        "masseur": ["豪老師"],
        "date": "2025/11/27",
        "time": "19:00",
        "project": 60,
        "count": 1,
        "isReservation": True,
        "response_message": "可以預約",
        "success": True
    }
    
    result = integration.format_for_line_sdk(parsed_data, force_format="flex")
    
    print(f"強制格式: flex")
    print(f"實際使用格式: {result.get('message_format')}")
    print(f"訊息類型: {result['line_messages'][0]['type']}")
    
    return result


# ============================================================
# 範例 4: 純文字回應（用於 CLI 測試）
# ============================================================

def example_4_text_response():
    """
    取得純文字回應範例
    用於命令列測試或日誌記錄
    """
    print("\n" + "=" * 60)
    print("範例 4: 取得純文字回應")
    print("=" * 60)
    
    parsed_data = {
        "greeting_message": "親愛的會員 Alice 您好!",
        "response_message": "您的預約已確認\n時間：2025/11/28 14:00\n地點：西門店",
        "isReservation": True
    }
    
    # 先格式化為 LINE SDK 格式
    formatted_data = integration.format_for_line_sdk(parsed_data)
    
    # 取得純文字回應
    text_response = integration.get_text_response(parsed_data)
    
    print("\n純文字回應:")
    print("-" * 60)
    print(text_response)
    print("-" * 60)
    
    return text_response


# ============================================================
# 範例 5: 自訂 Flex Message
# ============================================================

def example_5_custom_flex():
    """
    自訂 Flex Message 範例
    展示如何創建自己的 Flex 樣板
    """
    print("\n" + "=" * 60)
    print("範例 5: 自訂 Flex Message")
    print("=" * 60)
    
    from modules.integration import LineMessageFormatter
    
    formatter = LineMessageFormatter()
    
    # 創建自訂的 Flex Bubble（營業時間資訊）
    custom_bubble = {
        "type": "bubble",
        "hero": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "⏰ 營業時間",
                    "weight": "bold",
                    "size": "xl",
                    "color": "#FFFFFF"
                }
            ],
            "backgroundColor": "#1DB446",
            "paddingAll": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "週一至週日",
                    "weight": "bold",
                    "size": "lg"
                },
                {
                    "type": "text",
                    "text": "10:00 - 22:00",
                    "size": "xxl",
                    "weight": "bold",
                    "color": "#1DB446",
                    "margin": "md"
                },
                {
                    "type": "separator",
                    "margin": "lg"
                },
                {
                    "type": "text",
                    "text": "全年無休，歡迎預約！",
                    "size": "sm",
                    "color": "#999999",
                    "margin": "lg"
                }
            ]
        }
    }
    
    # 格式化為 Flex Message
    flex_message = formatter.format_flex_message(
        alt_text="營業時間資訊",
        contents=custom_bubble
    )
    
    print("\n自訂 Flex Message:")
    print(json.dumps(flex_message, ensure_ascii=False, indent=2))
    
    return flex_message


# ============================================================
# 範例 6: 錯誤處理
# ============================================================

def example_6_error_handling():
    """
    錯誤處理範例
    展示如何處理異常情況
    """
    print("\n" + "=" * 60)
    print("範例 6: 錯誤處理")
    print("=" * 60)
    
    # 空資料
    empty_data = {}
    result1 = integration.format_for_line_sdk(empty_data)
    print(f"\n空資料處理: {len(result1.get('line_messages', []))} 個訊息")
    print(f"預設訊息: {result1['line_messages'][0]['text']}")
    
    # 缺少必要欄位
    incomplete_data = {
        "isReservation": True
        # 缺少其他欄位
    }
    result2 = integration.format_for_line_sdk(incomplete_data, force_format="flex")
    print(f"\n不完整資料處理: {len(result2.get('line_messages', []))} 個訊息")
    
    return result1, result2


# ============================================================
# 範例 7: 多訊息組合（問候語 + Flex）
# ============================================================

def example_7_greeting_with_flex():
    """
    問候語與 Flex Message 組合範例
    展示問候語如何加在 Flex Message 之前
    """
    print("\n" + "=" * 60)
    print("範例 7: 問候語 + Flex Message 組合")
    print("=" * 60)
    
    parsed_data = {
        "branch": "西門店",
        "masseur": ["鞋老師", "川老師"],
        "date": "2025/11/28",
        "time": "14:00",
        "project": 90,
        "count": 2,
        "isReservation": True,
        "greeting_message": "親愛的會員 John(U1234567890) 您好!",
        "response_message": "✅ 已為您找到 2 位師傅的空檔時間",
        "success": True
    }
    
    result = integration.format_for_line_sdk(parsed_data, force_format="flex")
    
    print(f"\n訊息總數: {len(result.get('line_messages', []))}")
    
    for idx, msg in enumerate(result.get('line_messages', [])):
        msg_type = msg.get('type')
        print(f"\n訊息 {idx + 1} - 類型: {msg_type}")
        if msg_type == 'text':
            print(f"  內容: {msg.get('text')[:50]}...")
        elif msg_type == 'flex':
            print(f"  Alt Text: {msg.get('altText')}")
    
    return result


# ============================================================
# 主程式
# ============================================================

async def main():
    """執行所有範例"""
    print("\n" + "=" * 60)
    print("  六階段架構使用範例")
    print("=" * 60)
    
    try:
        # 執行各個範例
        await example_1_full_reservation_flow()
        example_2_keyword_flow()
        example_3_force_flex_format()
        example_4_text_response()
        example_5_custom_flex()
        example_6_error_handling()
        example_7_greeting_with_flex()
        
        print("\n" + "=" * 60)
        print("  ✅ 所有範例執行完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 執行主程式
    asyncio.run(main())
