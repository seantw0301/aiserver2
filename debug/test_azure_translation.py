#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試真實的多國語系翻譯 - 直接調用翻譯API（不依賴完整模組）
"""

import requests
import uuid
import sys
import os

# Azure Translator 設定
AZURE_SUBSCRIPTION_KEY = os.getenv('AZURE_TRANSLATOR_KEY', '')
AZURE_ENDPOINT = os.getenv('AZURE_TRANSLATOR_ENDPOINT', 'https://api.cognitive.microsofttranslator.com')
AZURE_LOCATION = os.getenv('AZURE_TRANSLATOR_LOCATION', 'global')


def translate_with_azure(text: str, target_language: str) -> str:
    """使用 Azure Translator API 翻譯文本"""
    try:
        if not AZURE_SUBSCRIPTION_KEY:
            return "翻譯失敗: 缺少 AZURE_TRANSLATOR_KEY"

        path = '/translate?api-version=3.0'
        params = f'&to={target_language}'
        constructed_url = AZURE_ENDPOINT + path + params
        
        headers = {
            'Ocp-Apim-Subscription-Key': AZURE_SUBSCRIPTION_KEY,
            'Ocp-Apim-Subscription-Region': AZURE_LOCATION,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        
        body = [{'text': text}]
        
        response = requests.post(constructed_url, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        translated_text = result[0]['translations'][0]['text']
        
        return translated_text
        
    except Exception as e:
        return f"翻譯失敗: {str(e)}"


def main():
    """執行翻譯測試"""
    
    print("\n" + "="*80)
    print("🌍 Azure Translator API 真實翻譯測試")
    print("="*80)
    
    # 測試案例（包含佔位符）
    test_cases = [
        {
            "name": "營業時間查詢（含店家佔位符）",
            "text": "%S1%的營業時間是早上11點到晚上10點",
            "note": "佔位符 %S1% 代表：西門店 (Ximen)",
            "languages": ["en", "ja", "ko", "th"]
        },
        {
            "name": "師傅休假通知（含師傅佔位符）",
            "text": "%W1%老師本週四休假，您可以改約%W2%老師或選擇其他時間",
            "note": "佔位符: %W1%=鞋(Camper), %W2%=阿力(Ali)",
            "languages": ["en", "ja", "ko"]
        },
        {
            "name": "多店家比較（多個佔位符）",
            "text": "%S1%和%S2%今天下午都有空檔，%S3%已經客滿",
            "note": "佔位符: %S1%=西門店, %S2%=延吉店, %S3%=信義店",
            "languages": ["en", "ja", "ko"]
        },
        {
            "name": "價格查詢",
            "text": "90分鐘按摩在%S1%是2500元，%S2%是2800元",
            "note": "佔位符: %S1%=西門店, %S2%=延吉店",
            "languages": ["en", "ja"]
        },
        {
            "name": "複雜句型（同一佔位符多次出現）",
            "text": "%W1%老師明天在%S1%，後天在%S2%。如果您要找%W1%老師，建議選%S1%比較方便",
            "note": "佔位符重複出現: %W1%=鞋, %S1%=西門店, %S2%=延吉店",
            "languages": ["en", "ja"]
        },
        {
            "name": "無佔位符（純文本翻譯）",
            "text": "今天天氣很好，歡迎光臨我們的按摩店",
            "note": "無需佔位符保護",
            "languages": ["en", "ja", "ko"]
        },
    ]
    
    success_count = 0
    fail_count = 0
    
    for idx, case in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"📋 測試 {idx}: {case['name']}")
        print(f"{'─'*80}")
        print(f"說明: {case['note']}")
        print(f"\n🇹🇼 中文原文 (含佔位符):")
        print(f"   {case['text']}")
        
        for lang in case['languages']:
            lang_flag = {
                'en': '🇺🇸',
                'ja': '🇯🇵',
                'ko': '🇰🇷',
                'th': '🇹🇭',
                'vi': '🇻🇳'
            }.get(lang, '🌐')
            
            print(f"\n{lang_flag} 翻譯為 {lang.upper()}:")
            translated = translate_with_azure(case['text'], lang)
            
            if "翻譯失敗" in translated:
                print(f"   ✗ {translated}")
                fail_count += 1
            else:
                print(f"   {translated}")
                
                # 檢查翻譯質量
                if translated == case['text']:
                    print(f"   ⚠️  警告: 翻譯結果與原文相同")
                    fail_count += 1
                elif "%W" in translated or "%S" in translated:
                    print(f"   ✓ 佔位符已保留，等待名稱還原")
                    success_count += 1
                elif any('\u4e00' <= c <= '\u9fff' for c in translated):
                    chinese_chars = [c for c in translated if '\u4e00' <= c <= '\u9fff']
                    print(f"   ℹ️  含有中文字符: {''.join(set(chinese_chars))}")
                    success_count += 1
                else:
                    print(f"   ✓ 翻譯成功")
                    success_count += 1
    
    print(f"\n{'='*80}")
    print(f"📊 測試總結")
    print(f"{'='*80}")
    print(f"✓ 成功: {success_count}")
    print(f"✗ 失敗: {fail_count}")
    print(f"總計: {success_count + fail_count}")
    print()
    
    print("💡 重要觀察:")
    print("1. 佔位符（如 %S1%, %W1%）在翻譯後是否保持不變？")
    print("2. 翻譯後的語法是否自然流暢？")
    print("3. 數字、時間等資訊是否正確保留？")
    print("4. 下一步：將翻譯後的佔位符還原為實際名稱（中文/英文）")
    print()


if __name__ == "__main__":
    main()
