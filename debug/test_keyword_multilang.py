#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試關鍵字回應的多國語系轉換
驗證翻譯後的語法是否自然流暢
"""

from typing import Dict, Tuple

def extract_and_replace_names(text: str, staff_mapping: Dict[str, str], store_mapping: Dict[str, str]) -> Tuple[str, Dict[str, Tuple[str, str]]]:
    """從文本中提取師傅名稱和店家名稱，並用佔位符替換"""
    if not text:
        return text, {}
    
    placeholder_map = {}
    modified_text = text
    
    # 按長度排序，優先替換較長的名稱
    all_store_names = sorted(store_mapping.keys(), key=len, reverse=True)
    all_staff_names = sorted(staff_mapping.keys(), key=len, reverse=True)
    
    # 替換店家名稱
    store_counter = 1
    for chinese_name in all_store_names:
        if chinese_name in modified_text:
            placeholder = f"%S{store_counter}%"
            english_name = store_mapping[chinese_name]
            modified_text = modified_text.replace(chinese_name, placeholder)
            placeholder_map[placeholder] = (chinese_name, english_name)
            store_counter += 1
    
    # 替換師傅名稱
    staff_counter = 1
    for chinese_name in all_staff_names:
        if chinese_name in modified_text:
            placeholder = f"%W{staff_counter}%"
            english_name = staff_mapping[chinese_name]
            modified_text = modified_text.replace(chinese_name, placeholder)
            placeholder_map[placeholder] = (chinese_name, english_name)
            staff_counter += 1
    
    return modified_text, placeholder_map


def restore_names(text: str, placeholder_map: Dict[str, Tuple[str, str]], language: str) -> str:
    """將佔位符還原為實際名稱"""
    if not text or not placeholder_map:
        return text
    
    restored_text = text
    use_chinese = language in ['zh-TW', 'zh', 'zh-CN', 'zh-HK']
    
    for placeholder, (chinese_name, english_name) in placeholder_map.items():
        name_to_use = chinese_name if use_chinese else english_name
        restored_text = restored_text.replace(placeholder, name_to_use)
    
    return restored_text


def test_keyword_response(scenario_name: str, original_text: str, staff_mapping: Dict[str, str], 
                         store_mapping: Dict[str, str], target_languages: list):
    """
    測試關鍵字回應在不同語系的表現
    
    Args:
        scenario_name: 測試場景名稱
        original_text: 中文原文
        staff_mapping: 師傅名稱映射
        store_mapping: 店家名稱映射
        target_languages: 目標語系列表
    """
    print(f"\n{'='*70}")
    print(f"測試場景: {scenario_name}")
    print(f"{'='*70}")
    print(f"中文原文: {original_text}")
    print()
    
    # 步驟1: 提取名稱並替換為佔位符
    modified_text, placeholder_map = extract_and_replace_names(original_text, staff_mapping, store_mapping)
    print(f"佔位符版本: {modified_text}")
    print(f"佔位符映射: {placeholder_map}")
    print()
    
    # 步驟2: 模擬翻譯後的結果（實際會調用 Azure Translator）
    # 這裡我們手動提供各語系的翻譯示例
    translations = {
        'en': None,  # 英文版會在下面根據佔位符版本生成
        'ja': None,  # 日文版
        'ko': None,  # 韓文版
        'th': None,  # 泰文版
        'vi': None,  # 越南文版
    }
    
    # 步驟3: 還原名稱
    print("各語系翻譯結果:")
    print("-" * 70)
    
    # 中文（不翻譯，直接還原）
    restored_zh = restore_names(modified_text, placeholder_map, "zh-TW")
    print(f"中文 (zh-TW): {restored_zh}")
    
    # 英文（還原英文名稱）
    # 這裡我們需要模擬翻譯後的結果
    for lang in target_languages:
        if lang == 'zh-TW':
            continue
        
        # 還原名稱（使用英文名）
        if lang in translations and translations[lang]:
            restored = restore_names(translations[lang], placeholder_map, lang)
        else:
            # 如果沒有提供翻譯，直接還原佔位符版本（用英文名）
            restored = restore_names(modified_text, placeholder_map, lang)
        
        print(f"{lang.upper():6s}: {restored}")
    
    print()


def main():
    """執行所有關鍵字測試"""
    
    # 共用的名稱映射
    staff_mapping = {
        "鞋": "Camper",
        "阿力": "Ali",
        "小明": "Ming",
        "Amy": "Amy",
    }
    
    store_mapping = {
        "西門店": "Ximen",
        "延吉店": "Yanji",
        "信義店": "Xinyi",
    }
    
    # 測試目標語系
    target_languages = ['zh-TW', 'en', 'ja', 'ko']
    
    # ============= 測試案例 1: 營業時間查詢 =============
    test_keyword_response(
        scenario_name="營業時間查詢",
        original_text="西門店的營業時間是早上11點到晚上10點",
        staff_mapping=staff_mapping,
        store_mapping=store_mapping,
        target_languages=target_languages
    )
    
    # ============= 測試案例 2: 師傅休假通知 =============
    test_keyword_response(
        scenario_name="師傅休假通知",
        original_text="鞋老師本週四休假，您可以改約阿力老師或選擇其他時間",
        staff_mapping=staff_mapping,
        store_mapping=store_mapping,
        target_languages=target_languages
    )
    
    # ============= 測試案例 3: 多店家比較 =============
    test_keyword_response(
        scenario_name="多店家時段查詢",
        original_text="西門店和延吉店今天下午都有空檔，信義店已經客滿",
        staff_mapping=staff_mapping,
        store_mapping=store_mapping,
        target_languages=target_languages
    )
    
    # ============= 測試案例 4: 師傅技能說明 =============
    test_keyword_response(
        scenario_name="師傅專長介紹",
        original_text="阿力老師擅長深層組織按摩，鞋老師專精運動按摩和舒壓",
        staff_mapping=staff_mapping,
        store_mapping=store_mapping,
        target_languages=target_languages
    )
    
    # ============= 測試案例 5: 價格資訊 =============
    test_keyword_response(
        scenario_name="價格查詢",
        original_text="90分鐘按摩在西門店是2500元，延吉店是2800元",
        staff_mapping=staff_mapping,
        store_mapping=store_mapping,
        target_languages=target_languages
    )
    
    # ============= 測試案例 6: 複雜句型（同一師傅多次出現）=============
    test_keyword_response(
        scenario_name="預約建議（複雜句型）",
        original_text="鞋老師明天在西門店，後天在延吉店。如果您要找鞋老師，建議選西門店比較方便",
        staff_mapping=staff_mapping,
        store_mapping=store_mapping,
        target_languages=target_languages
    )
    
    # ============= 測試案例 7: 服務項目說明 =============
    test_keyword_response(
        scenario_name="服務項目介紹",
        original_text="我們提供全身按摩、腳底按摩、精油SPA等服務，每項服務都有專業師傅負責",
        staff_mapping=staff_mapping,
        store_mapping=store_mapping,
        target_languages=target_languages
    )
    
    print("\n" + "="*70)
    print("✓ 關鍵字多國語系測試完成")
    print("="*70)
    print("\n注意事項：")
    print("1. 以上只顯示佔位符還原後的結果")
    print("2. 實際使用時，佔位符版本會先送到 Azure Translator 翻譯")
    print("3. 翻譯後的文本再進行名稱還原")
    print("4. 師傅和店家名稱在非中文語系都會顯示英文名稱")
    print()


if __name__ == "__main__":
    main()
