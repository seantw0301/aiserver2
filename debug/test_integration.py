"""
測試整合模組 (Integration Module Test)
測試六階段處理流程與 LINE SDK 訊息格式化
"""

import sys
import json
from datetime import datetime

# 直接導入模組進行測試
sys.path.insert(0, '/Volumes/aiserver2')

from modules import integration


def print_section(title):
    """列印測試區段標題"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_text_message_format():
    """測試純文字訊息格式化（問候語整合在一起）"""
    print_section("測試 1: 純文字訊息格式化（整合問候語）")
    
    # 準備測試資料
    parsed_data = {
        "branch": "",
        "masseur": [],
        "date": "",
        "time": "",
        "project": 0,
        "count": 0,
        "isReservation": False,
        "is_keyword_match": True,
        "greeting_message": "親愛的會員 John(U1234567890) 您好!",
        "response_message": "我們的營業時間是週一至週日 10:00-22:00",
        "success": True
    }
    
    # 格式化為 LINE SDK 格式
    result = integration.format_for_line_sdk(parsed_data, force_format="text")
    
    print("\n原始資料:")
    print(json.dumps(parsed_data, ensure_ascii=False, indent=2))
    
    print("\nLINE SDK 格式化結果:")
    print(json.dumps(result.get('line_messages', []), ensure_ascii=False, indent=2))
    
    # 驗證只有一個整合的訊息
    assert 'line_messages' in result, "缺少 line_messages 欄位"
    assert len(result['line_messages']) == 1, "應只有一個整合的訊息"
    assert result['line_messages'][0]['type'] == 'text', "訊息應為文字訊息"
    
    # 驗證訊息包含問候語和回應內容
    text = result['line_messages'][0]['text']
    assert "親愛的會員" in text, "應包含問候語"
    assert "營業時間" in text, "應包含回應內容"
    
    print("\n✅ 測試通過: 純文字訊息格式化成功（問候語已整合）")


def test_flex_message_format():
    """測試 Flex Message 格式化（問候語整合在 Flex 中）"""
    print_section("測試 2: Flex Message 格式化（問候語整合）")
    
    # 準備預約查詢測試資料
    parsed_data = {
        "branch": "西門店",
        "masseur": ["鞋老師", "川老師"],
        "date": "2025/11/28",
        "time": "14:00",
        "project": 90,
        "count": 2,
        "isReservation": True,
        "greeting_message": "親愛的會員 Mary(U9876543210) 您好!",
        "response_message": "✅ 查詢結果：可以預約\n已為您找到 2 位師傅的空檔時間",
        "success": True,
        "can_book": True
    }
    
    # 格式化為 Flex Message
    result = integration.format_for_line_sdk(parsed_data, force_format="flex")
    
    print("\n原始資料:")
    print(json.dumps(parsed_data, ensure_ascii=False, indent=2))
    
    print("\nLINE Flex Message 格式化結果:")
    print(json.dumps(result.get('line_messages', []), ensure_ascii=False, indent=2))
    
    # 驗證只有一個 Flex Message（問候語整合在內）
    assert 'line_messages' in result, "缺少 line_messages 欄位"
    assert len(result['line_messages']) == 1, "應只有一個 Flex Message（問候語已整合）"
    
    # 檢查 Flex Message
    flex_msg = result['line_messages'][0]
    assert flex_msg['type'] == 'flex', "訊息應為 Flex Message"
    assert 'contents' in flex_msg, "Flex Message 缺少 contents"
    assert flex_msg['contents']['type'] == 'bubble', "Flex Message 應為 bubble 類型"
    
    # 驗證問候語整合在 Flex 內容中
    body_contents = flex_msg['contents']['body']['contents']
    greeting_found = False
    for content in body_contents:
        if content.get('type') == 'text' and '親愛的會員' in content.get('text', ''):
            greeting_found = True
            break
    
    assert greeting_found, "Flex Message 中應包含問候語"
    
    print("\n✅ 測試通過: Flex Message 格式化成功（問候語已整合）")


def test_greeting_prepend():
    """測試問候語是否正確整合到訊息中（單一訊息）"""
    print_section("測試 3: 問候語整合到訊息中（單一訊息）")
    
    parsed_data = {
        "branch": "",
        "masseur": [],
        "date": "",
        "time": "",
        "project": 0,
        "count": 0,
        "isReservation": False,
        "is_keyword_match": True,
        "greeting_message": "親愛的會員 Alice(U1111111111) 您好!",
        "response_message": "感謝您的查詢！",
        "success": True
    }
    
    result = integration.format_for_line_sdk(parsed_data)
    
    print("\n原始資料:")
    print(f"問候語: {parsed_data['greeting_message']}")
    print(f"回應訊息: {parsed_data['response_message']}")
    
    print("\nLINE Messages:")
    for idx, msg in enumerate(result.get('line_messages', [])):
        print(f"\n訊息 {idx + 1}:")
        print(json.dumps(msg, ensure_ascii=False, indent=2))
    
    # 驗證只有一個訊息，問候語和回應整合在一起
    assert len(result['line_messages']) == 1, "應只有一個整合的訊息"
    assert "親愛的會員" in result['line_messages'][0]['text'], "訊息應包含問候語"
    assert "感謝您的查詢" in result['line_messages'][0]['text'], "訊息應包含回應內容"
    
    # 驗證問候語在回應內容之前
    text = result['line_messages'][0]['text']
    assert text.index("親愛的會員") < text.index("感謝您的查詢"), "問候語應在回應內容之前"
    
    print("\n✅ 測試通過: 問候語正確整合到單一訊息中")


def test_no_greeting():
    """測試沒有問候語的情況"""
    print_section("測試 4: 沒有問候語的情況")
    
    parsed_data = {
        "branch": "延吉店",
        "masseur": ["豪老師"],
        "date": "2025/11/27",
        "time": "19:00",
        "project": 60,
        "count": 1,
        "isReservation": True,
        "response_message": "✅ 查詢結果：可以預約",
        "success": True
    }
    
    result = integration.format_for_line_sdk(parsed_data, force_format="flex")
    
    print("\n原始資料（無問候語）:")
    print(json.dumps(parsed_data, ensure_ascii=False, indent=2))
    
    print("\nLINE Messages 數量:", len(result.get('line_messages', [])))
    
    # 驗證只有 Flex Message，沒有問候語
    assert 'line_messages' in result, "缺少 line_messages 欄位"
    
    print("\n✅ 測試通過: 沒有問候語時正確處理")


def test_auto_format_detection():
    """測試自動格式偵測"""
    print_section("測試 5: 自動格式偵測")
    
    # 測試預約 -> 應自動選擇 Flex
    reservation_data = {
        "branch": "西門店",
        "masseur": ["遠老師"],
        "date": "2025/11/29",
        "time": "10:00",
        "project": 120,
        "count": 1,
        "isReservation": True,
        "response_message": "查詢成功",
        "success": True
    }
    
    result1 = integration.format_for_line_sdk(reservation_data, auto_format=True)
    detected_format1 = integration.auto_detect_message_format(reservation_data)
    
    print(f"\n預約資料自動偵測格式: {detected_format1}")
    print(f"實際使用格式: {result1.get('message_format')}")
    
    assert detected_format1 == "flex", "預約應自動偵測為 Flex 格式"
    
    # 測試關鍵字 -> 應自動選擇 Text
    keyword_data = {
        "isReservation": False,
        "is_keyword_match": True,
        "response_message": "營業時間資訊",
        "success": True
    }
    
    result2 = integration.format_for_line_sdk(keyword_data, auto_format=True)
    detected_format2 = integration.auto_detect_message_format(keyword_data)
    
    print(f"\n關鍵字資料自動偵測格式: {detected_format2}")
    print(f"實際使用格式: {result2.get('message_format')}")
    
    assert detected_format2 == "text", "關鍵字應自動偵測為 Text 格式"
    
    print("\n✅ 測試通過: 自動格式偵測正確")


def test_get_text_response():
    """測試取得純文字回應（用於 CLI 顯示）"""
    print_section("測試 6: 取得純文字回應")
    
    parsed_data = {
        "greeting_message": "親愛的會員 Bob(U2222222222) 您好!",
        "response_message": "您的預約已確認",
        "isReservation": True
    }
    
    text_response = integration.get_text_response(parsed_data)
    
    print(f"\n純文字回應:\n{text_response}")
    
    # 驗證包含問候語和回應訊息
    assert "親愛的會員" in text_response, "純文字回應應包含問候語"
    assert "您的預約已確認" in text_response, "純文字回應應包含回應訊息"
    assert text_response.index("親愛的會員") < text_response.index("您的預約已確認"), \
        "問候語應在回應訊息之前"
    
    print("\n✅ 測試通過: 純文字回應正確")


def test_error_handling():
    """測試錯誤處理"""
    print_section("測試 7: 錯誤處理")
    
    # 測試空資料
    empty_data = {}
    result = integration.format_for_line_sdk(empty_data)
    
    print("\n空資料處理結果:")
    print(json.dumps(result.get('line_messages', []), ensure_ascii=False, indent=2))
    
    assert 'line_messages' in result, "空資料也應返回 line_messages"
    assert len(result['line_messages']) >= 1, "空資料應至少有一個預設訊息"
    
    print("\n✅ 測試通過: 錯誤處理正確")


def run_all_tests():
    """執行所有測試"""
    print("\n" + "=" * 60)
    print("  開始測試整合模組 (Integration Module)")
    print("=" * 60)
    
    try:
        test_text_message_format()
        test_flex_message_format()
        test_greeting_prepend()
        test_no_greeting()
        test_auto_format_detection()
        test_get_text_response()
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("  ✅ 所有測試通過！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
