#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試佔位符邏輯（獨立測試，不需要導入完整模組）
"""

from typing import Dict, Tuple

def extract_and_replace_names(text: str, staff_mapping: Dict[str, str], store_mapping: Dict[str, str]) -> Tuple[str, Dict[str, Tuple[str, str]]]:
    """
    從文本中提取師傅名稱和店家名稱，並用佔位符替換
    """
    if not text:
        return text, {}
    
    placeholder_map = {}
    modified_text = text
    
    # 步驟 1: 按長度排序，優先替換較長的名稱
    all_store_names = sorted(store_mapping.keys(), key=len, reverse=True)
    all_staff_names = sorted(staff_mapping.keys(), key=len, reverse=True)
    
    # 步驟 2: 替換店家名稱
    store_counter = 1
    for chinese_name in all_store_names:
        if chinese_name in modified_text:
            placeholder = f"%S{store_counter}%"
            english_name = store_mapping[chinese_name]
            
            # 替換所有出現的該店家名稱
            modified_text = modified_text.replace(chinese_name, placeholder)
            placeholder_map[placeholder] = (chinese_name, english_name)
            store_counter += 1
    
    # 步驟 3: 替換師傅名稱
    staff_counter = 1
    for chinese_name in all_staff_names:
        if chinese_name in modified_text:
            placeholder = f"%W{staff_counter}%"
            english_name = staff_mapping[chinese_name]
            
            # 替換所有出現的該師傅名稱
            modified_text = modified_text.replace(chinese_name, placeholder)
            placeholder_map[placeholder] = (chinese_name, english_name)
            staff_counter += 1
    
    return modified_text, placeholder_map


def restore_names(text: str, placeholder_map: Dict[str, Tuple[str, str]], language: str) -> str:
    """
    將佔位符還原為實際名稱
    """
    if not text or not placeholder_map:
        return text
    
    restored_text = text
    
    # 根據語系決定使用中文還是英文名稱
    use_chinese = language in ['zh-TW', 'zh', 'zh-CN', 'zh-HK']
    
    for placeholder, (chinese_name, english_name) in placeholder_map.items():
        name_to_use = chinese_name if use_chinese else english_name
        restored_text = restored_text.replace(placeholder, name_to_use)
    
    return restored_text


def test_multiple_same_store():
    """測試同一個店家出現多次"""
    print("\n=== 測試：同一店家多次出現 ===")
    
    staff_mapping = {"鞋": "Camper"}
    store_mapping = {"西門店": "Ximen", "延吉店": "Yanji"}
    
    text = "西門店的鞋老師在西門店和延吉店都有預約"
    print(f"原文: {text}")
    
    # 提取並替換
    modified_text, placeholder_map = extract_and_replace_names(text, staff_mapping, store_mapping)
    print(f"替換後: {modified_text}")
    print(f"佔位符映射: {placeholder_map}")
    
    # 驗證佔位符數量
    assert "%S1%" in modified_text, "應該包含 %S1%"
    assert "%S2%" in modified_text, "應該包含 %S2%"
    assert "%W1%" in modified_text, "應該包含 %W1%"
    
    # 驗證西門店應該被替換成同一個佔位符
    count_s1 = modified_text.count("%S1%")
    print(f"  %S1% 出現次數: {count_s1}")
    assert count_s1 == 2, f"西門店出現兩次，應該都是 %S1%，實際出現 {count_s1} 次"
    
    # 還原為中文
    restored_zh = restore_names(modified_text, placeholder_map, "zh-TW")
    print(f"還原中文: {restored_zh}")
    assert restored_zh == text, f"還原中文應該與原文相同\n  期望: {text}\n  實際: {restored_zh}"
    
    # 還原為英文
    restored_en = restore_names(modified_text, placeholder_map, "en")
    print(f"還原英文: {restored_en}")
    expected_en = "Ximen的Camper老師在Ximen和Yanji都有預約"
    assert restored_en == expected_en, f"還原英文應該是 '{expected_en}', 實際是 '{restored_en}'"
    
    print("✓ 測試通過")


def test_multiple_different_stores():
    """測試多個不同店家和師傅"""
    print("\n=== 測試：多個不同店家和師傅 ===")
    
    staff_mapping = {
        "鞋": "Camper",
        "阿力": "Ali",
        "小明": "Ming"
    }
    store_mapping = {
        "西門店": "Ximen",
        "延吉店": "Yanji",
        "信義店": "Xinyi"
    }
    
    text = "今天西門店有鞋和阿力，延吉店有小明，信義店也有鞋"
    print(f"原文: {text}")
    
    # 提取並替換
    modified_text, placeholder_map = extract_and_replace_names(text, staff_mapping, store_mapping)
    print(f"替換後: {modified_text}")
    print(f"佔位符映射: {placeholder_map}")
    
    # 驗證佔位符數量
    store_count = len([k for k in placeholder_map.keys() if k.startswith("%S")])
    staff_count = len([k for k in placeholder_map.keys() if k.startswith("%W")])
    print(f"  店家佔位符數量: {store_count}")
    print(f"  師傅佔位符數量: {staff_count}")
    assert store_count == 3, f"應該有3個店家佔位符，實際有 {store_count} 個"
    assert staff_count == 3, f"應該有3個師傅佔位符，實際有 {staff_count} 個"
    
    # 驗證鞋老師出現兩次，都應該是同一個佔位符
    camper_placeholder = [k for k, v in placeholder_map.items() if v[0] == "鞋"][0]
    camper_count = modified_text.count(camper_placeholder)
    print(f"  鞋老師的佔位符 {camper_placeholder} 出現次數: {camper_count}")
    assert camper_count == 2, f"鞋老師出現兩次，應該都是 {camper_placeholder}，實際出現 {camper_count} 次"
    
    # 還原為英文
    restored_en = restore_names(modified_text, placeholder_map, "en")
    print(f"還原英文: {restored_en}")
    
    # 驗證關鍵詞
    assert "Camper" in restored_en, "應該包含 Camper"
    assert "Ali" in restored_en, "應該包含 Ali"
    assert "Ming" in restored_en, "應該包含 Ming"
    assert "Ximen" in restored_en, "應該包含 Ximen"
    assert "Yanji" in restored_en, "應該包含 Yanji"
    assert "Xinyi" in restored_en, "應該包含 Xinyi"
    
    print("✓ 測試通過")


def test_complex_scenario():
    """測試複雜場景：多個店家、師傅混合出現"""
    print("\n=== 測試：複雜場景 ===")
    
    staff_mapping = {
        "鞋": "Camper",
        "阿力": "Ali"
    }
    store_mapping = {
        "西門店": "Ximen",
        "延吉店": "Yanji"
    }
    
    text = "西門店的鞋老師今天休息，請改約延吉店。延吉店的阿力老師也可以服務，或者改天再約西門店的鞋老師。"
    print(f"原文: {text}")
    
    # 提取並替換
    modified_text, placeholder_map = extract_and_replace_names(text, staff_mapping, store_mapping)
    print(f"替換後: {modified_text}")
    print(f"佔位符映射: {placeholder_map}")
    
    # 驗證西門店出現2次
    ximen_placeholder = [k for k, v in placeholder_map.items() if v[0] == "西門店"][0]
    ximen_count = modified_text.count(ximen_placeholder)
    print(f"  西門店佔位符 {ximen_placeholder} 出現次數: {ximen_count}")
    assert ximen_count == 2, f"西門店應該出現2次，實際出現 {ximen_count} 次"
    
    # 驗證延吉店出現2次
    yanji_placeholder = [k for k, v in placeholder_map.items() if v[0] == "延吉店"][0]
    yanji_count = modified_text.count(yanji_placeholder)
    print(f"  延吉店佔位符 {yanji_placeholder} 出現次數: {yanji_count}")
    assert yanji_count == 2, f"延吉店應該出現2次，實際出現 {yanji_count} 次"
    
    # 驗證鞋老師出現2次
    camper_placeholder = [k for k, v in placeholder_map.items() if v[0] == "鞋"][0]
    camper_count = modified_text.count(camper_placeholder)
    print(f"  鞋老師佔位符 {camper_placeholder} 出現次數: {camper_count}")
    assert camper_count == 2, f"鞋老師應該出現2次，實際出現 {camper_count} 次"
    
    # 還原為中文
    restored_zh = restore_names(modified_text, placeholder_map, "zh-TW")
    print(f"還原中文: {restored_zh}")
    assert restored_zh == text, f"還原中文應該與原文相同\n  期望: {text}\n  實際: {restored_zh}"
    
    # 還原為英文
    restored_en = restore_names(modified_text, placeholder_map, "en")
    print(f"還原英文: {restored_en}")
    
    # 驗證關鍵詞都存在且出現次數正確
    camper_en_count = restored_en.count("Camper")
    ximen_en_count = restored_en.count("Ximen")
    yanji_en_count = restored_en.count("Yanji")
    
    print(f"  英文版 Camper 出現次數: {camper_en_count}")
    print(f"  英文版 Ximen 出現次數: {ximen_en_count}")
    print(f"  英文版 Yanji 出現次數: {yanji_en_count}")
    
    assert camper_en_count == 2, f"Camper應該出現2次，實際出現 {camper_en_count} 次"
    assert ximen_en_count == 2, f"Ximen應該出現2次，實際出現 {ximen_en_count} 次"
    assert yanji_en_count == 2, f"Yanji應該出現2次，實際出現 {yanji_en_count} 次"
    
    print("✓ 測試通過")


def main():
    """執行所有測試"""
    print("="*60)
    print("開始測試佔位符系統處理多個相同名稱的能力...")
    print("="*60)
    
    try:
        test_multiple_same_store()
        test_multiple_different_stores()
        test_complex_scenario()
        
        print("\n" + "="*60)
        print("✓ 所有測試通過！佔位符系統可以正確處理多個相同名稱的情況")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n✗ 測試失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
