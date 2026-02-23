"""
測試多國語系翻譯模組
驗證第五階段：文字輸出階段 (MultiLang Module)
"""

import sys
import os

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.multilang import translate_message, translate_response_fields, MultiLangTranslator


def test_translate_message():
    """測試單一訊息翻譯"""
    print("=" * 60)
    print("測試 1: 單一訊息翻譯")
    print("=" * 60)
    
    test_message = "親愛的會員，您的預約已成功！"
    
    # 測試翻譯成英文
    en_result = translate_message(test_message, "en")
    print(f"原文 (zh-TW): {test_message}")
    print(f"英文 (en): {en_result}")
    print()
    
    # 測試翻譯成泰文
    th_result = translate_message(test_message, "th")
    print(f"泰文 (th): {th_result}")
    print()
    
    # 測試翻譯成日文
    ja_result = translate_message(test_message, "ja")
    print(f"日文 (ja): {ja_result}")
    print()
    
    # 測試翻譯成韓文
    ko_result = translate_message(test_message, "ko")
    print(f"韓文 (ko): {ko_result}")
    print()
    
    # 測試保持繁體中文
    tw_result = translate_message(test_message, "zh-TW")
    print(f"繁體中文 (zh-TW): {tw_result}")
    print()


def test_translate_response_fields():
    """測試回應欄位翻譯"""
    print("=" * 60)
    print("測試 2: 回應欄位翻譯")
    print("=" * 60)
    
    # 模擬 parsed_data
    test_data = {
        "branch": "西門店",
        "masseur": ["鞋老師", "川老師"],
        "date": "2025/11/28",
        "time": "14:00",
        "project": 90,
        "count": 2,
        "isReservation": True,
        "response_message": "已為您找到 2 位師傅的空檔時間",
        "greeting_message": "親愛的會員 John(U1234567890) 您好!",
        "success": True
    }
    
    # 測試翻譯成英文
    print("\n英文版本 (en):")
    en_data = translate_response_fields(test_data.copy(), "en")
    print(f"response_message: {en_data.get('response_message')}")
    print(f"greeting_message: {en_data.get('greeting_message')}")
    
    # 測試翻譯成泰文
    print("\n泰文版本 (th):")
    th_data = translate_response_fields(test_data.copy(), "th")
    print(f"response_message: {th_data.get('response_message')}")
    print(f"greeting_message: {th_data.get('greeting_message')}")
    
    # 測試翻譯成日文
    print("\n日文版本 (ja):")
    ja_data = translate_response_fields(test_data.copy(), "ja")
    print(f"response_message: {ja_data.get('response_message')}")
    print(f"greeting_message: {ja_data.get('greeting_message')}")
    
    # 測試保持繁體中文
    print("\n繁體中文版本 (zh-TW):")
    tw_data = translate_response_fields(test_data.copy(), "zh-TW")
    print(f"response_message: {tw_data.get('response_message')}")
    print(f"greeting_message: {tw_data.get('greeting_message')}")
    print()


def test_error_message_translation():
    """測試錯誤訊息翻譯"""
    print("=" * 60)
    print("測試 3: 錯誤訊息翻譯")
    print("=" * 60)
    
    error_data = {
        "isReservation": False,
        "success": False,
        "error": "自然語言解析失敗: 找不到可用的師傅",
        "message": "系統錯誤，請稍後再試"
    }
    
    # 測試翻譯成英文
    print("\n英文版本 (en):")
    en_error = translate_response_fields(error_data.copy(), "en")
    print(f"error: {en_error.get('error')}")
    print(f"message: {en_error.get('message')}")
    
    # 測試翻譯成泰文
    print("\n泰文版本 (th):")
    th_error = translate_response_fields(error_data.copy(), "th")
    print(f"error: {th_error.get('error')}")
    print(f"message: {th_error.get('message')}")
    print()


def test_multiple_languages_batch():
    """批次測試多種語言"""
    print("=" * 60)
    print("測試 4: 批次測試常見問候語")
    print("=" * 60)
    
    greetings = [
        "您好！歡迎光臨",
        "謝謝您的預約",
        "預約成功！期待您的到來",
        "很抱歉，目前沒有可用的時段"
    ]
    
    languages = [
        ("en", "英文"),
        ("th", "泰文"),
        ("ja", "日文"),
        ("ko", "韓文")
    ]
    
    for greeting in greetings:
        print(f"\n原文: {greeting}")
        for lang_code, lang_name in languages:
            translated = translate_message(greeting, lang_code)
            print(f"  {lang_name} ({lang_code}): {translated}")


if __name__ == "__main__":
    print("\n🌐 多國語系翻譯模組測試開始\n")
    
    try:
        # 執行各項測試
        test_translate_message()
        test_translate_response_fields()
        test_error_message_translation()
        test_multiple_languages_batch()
        
        print("\n" + "=" * 60)
        print("✅ 所有測試完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
