#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試佔位符系統處理多個相同名稱出現的情況
"""

import sys
import os

# 添加項目根目錄到 Python 路徑
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from modules.multilang import extract_and_replace_names, restore_names

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
    assert modified_text.count("%S1%") == 2, "西門店出現兩次，應該都是 %S1%"
    
    # 還原為中文
    restored_zh = restore_names(modified_text, placeholder_map, "zh-TW")
    print(f"還原中文: {restored_zh}")
    assert restored_zh == text, "還原中文應該與原文相同"
    
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
    assert len([k for k in placeholder_map.keys() if k.startswith("%S")]) == 3, "應該有3個店家佔位符"
    assert len([k for k in placeholder_map.keys() if k.startswith("%W")]) == 3, "應該有3個師傅佔位符"
    
    # 驗證鞋老師出現兩次，都應該是同一個佔位符
    staff_placeholders = [k for k in placeholder_map.keys() if k.startswith("%W")]
    camper_placeholder = [k for k, v in placeholder_map.items() if v[0] == "鞋"][0]
    assert modified_text.count(camper_placeholder) == 2, f"鞋老師出現兩次，應該都是 {camper_placeholder}"
    
    # 還原為英文
    restored_en = restore_names(modified_text, placeholder_map, "en")
    print(f"還原英文: {restored_en}")
    
    # 驗證關鍵詞
    assert "Camper" in restored_en
    assert "Ali" in restored_en
    assert "Ming" in restored_en
    assert "Ximen" in restored_en
    assert "Yanji" in restored_en
    assert "Xinyi" in restored_en
    
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
    
    # 驗證西門店出現2次
    ximen_placeholder = [k for k, v in placeholder_map.items() if v[0] == "西門店"][0]
    assert modified_text.count(ximen_placeholder) == 2, "西門店應該出現2次"
    
    # 驗證延吉店出現2次
    yanji_placeholder = [k for k, v in placeholder_map.items() if v[0] == "延吉店"][0]
    assert modified_text.count(yanji_placeholder) == 2, "延吉店應該出現2次"
    
    # 驗證鞋老師出現2次
    camper_placeholder = [k for k, v in placeholder_map.items() if v[0] == "鞋"][0]
    assert modified_text.count(camper_placeholder) == 2, "鞋老師應該出現2次"
    
    # 還原為中文
    restored_zh = restore_names(modified_text, placeholder_map, "zh-TW")
    print(f"還原中文: {restored_zh}")
    assert restored_zh == text, "還原中文應該與原文相同"
    
    # 還原為英文
    restored_en = restore_names(modified_text, placeholder_map, "en")
    print(f"還原英文: {restored_en}")
    
    # 驗證關鍵詞都存在且出現次數正確
    assert restored_en.count("Camper") == 2, "Camper應該出現2次"
    assert restored_en.count("Ximen") == 2, "Ximen應該出現2次"
    assert restored_en.count("Yanji") == 2, "Yanji應該出現2次"
    
    print("✓ 測試通過")


def main():
    """執行所有測試"""
    print("開始測試佔位符系統處理多個相同名稱的能力...")
    
    try:
        test_multiple_same_store()
        test_multiple_different_stores()
        test_complex_scenario()
        
        print("\n" + "="*50)
        print("✓ 所有測試通過！")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n✗ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
