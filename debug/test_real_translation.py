#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試真實的多國語系翻譯 - 調用實際的 Azure Translator API
"""

import sys
import os

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from modules.multilang import translate_message, MultiLangTranslator

def test_real_translation():
    """測試真實的翻譯API調用"""
    
    print("="*80)
    print("🌍 真實多國語系翻譯測試（調用 Azure Translator API）")
    print("="*80)
    
    # 測試案例
    test_cases = [
        {
            "name": "營業時間查詢",
            "text": "西門店的營業時間是早上11點到晚上10點",
            "languages": ["en", "ja", "ko", "th"]
        },
        {
            "name": "師傅休假通知",
            "text": "鞋老師本週四休假，您可以改約阿力老師或選擇其他時間",
            "languages": ["en", "ja", "ko"]
        },
        {
            "name": "多店家比較",
            "text": "西門店和延吉店今天下午都有空檔，信義店已經客滿",
            "languages": ["en", "ja", "ko"]
        },
        {
            "name": "價格查詢",
            "text": "90分鐘按摩在西門店是2500元，延吉店是2800元",
            "languages": ["en", "ja"]
        },
        {
            "name": "複雜句型",
            "text": "鞋老師明天在西門店，後天在延吉店。如果您要找鞋老師，建議選西門店比較方便",
            "languages": ["en", "ja"]
        },
    ]
    
    for idx, case in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"📋 測試 {idx}: {case['name']}")
        print(f"{'─'*80}")
        print(f"\n🇹🇼 中文原文:")
        print(f"   {case['text']}")
        
        for lang in case['languages']:
            print(f"\n🌐 翻譯為 {lang.upper()}:")
            try:
                translated = translate_message(case['text'], lang)
                print(f"   {translated}")
                
                # 檢查翻譯質量
                if translated == case['text']:
                    print(f"   ⚠️  警告: 翻譯結果與原文相同，可能翻譯失敗")
                elif any('\u4e00' <= c <= '\u9fff' for c in translated):
                    # 檢查是否還有中文字（除了可能保留的專有名詞）
                    chinese_chars = [c for c in translated if '\u4e00' <= c <= '\u9fff']
                    print(f"   ℹ️  含有中文字符: {''.join(set(chinese_chars))}")
                else:
                    print(f"   ✓ 翻譯成功，無未翻譯的中文")
                    
            except Exception as e:
                print(f"   ✗ 翻譯失敗: {str(e)}")
    
    print(f"\n{'='*80}")
    print("✅ 測試完成")
    print(f"{'='*80}\n")


def test_simple_translation():
    """測試簡單的翻譯（不含師傅/店家名稱）"""
    
    print("\n" + "="*80)
    print("🔍 簡單翻譯測試（驗證 Azure API 連接）")
    print("="*80)
    
    simple_texts = [
        "今天天氣很好",
        "您的預約已確認",
        "請問需要什麼服務？",
    ]
    
    target_langs = ["en", "ja", "ko"]
    
    for text in simple_texts:
        print(f"\n原文: {text}")
        for lang in target_langs:
            try:
                result = MultiLangTranslator.translate_to_target_language(text, lang)
                print(f"  {lang}: {result}")
            except Exception as e:
                print(f"  {lang}: ✗ 錯誤 - {str(e)}")
    
    print()


if __name__ == "__main__":
    print("\n")
    
    # 先測試簡單翻譯，確認 API 連接正常
    test_simple_translation()
    
    # 再測試完整的翻譯流程（含佔位符系統）
    test_real_translation()
