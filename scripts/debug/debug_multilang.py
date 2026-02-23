#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試腳本：測試多語言佔位符系統
"""

from modules.multilang import (
    get_staff_name_mapping, get_store_name_mapping,
    extract_and_replace_names, restore_names
)

def test_multilang_system():
    """測試多語言系統的師傅和店家名分別"""
    
    staff_mapping = get_staff_name_mapping()
    store_mapping = get_store_name_mapping()
    
    print("=" * 80)
    print("多語言系統測試")
    print("=" * 80)
    
    # 測試文本包含師傅名和店家名，以及可約師傅的回應
    test_cases = [
        ("可約師傅：川、獻", "師傅列表中的名字"),
        ("川師傅在西門店有空", "師傅和店家名混合"),
        ("西門的川", "店家和師傅名"),
        ("川、獻、豪在西門有空", "多個師傅和店家"),
    ]
    
    for text, description in test_cases:
        print(f"\n測試: {description}")
        print(f"原始文本: {text}")
        
        # 提取和替換
        modified, placeholders = extract_and_replace_names(text, staff_mapping, store_mapping)
        print(f"修改後: {modified}")
        print(f"佔位符映射:")
        for placeholder, (chinese, english) in placeholders.items():
            name_type = "店家" if placeholder.startswith("%S") else "師傅"
            print(f"  - {placeholder}: {name_type} 中文={chinese}, 英文={english}")
        
        # 還原為中文
        restored_zh = restore_names(modified, placeholders, "zh-TW")
        print(f"還原(中文): {restored_zh}")
        
        # 還原為英文
        restored_en = restore_names(modified, placeholders, "en")
        print(f"還原(英文): {restored_en}")
        
        # 檢查是否有錯誤
        for staff_name in staff_mapping.keys():
            if staff_name not in text and staff_name in restored_en:
                print(f"⚠️ 警告: {staff_name} 被添加到了結果中")
        
        for store_name in store_mapping.keys():
            if store_name not in text and store_name in restored_en:
                print(f"⚠️ 警告: {store_name} 被添加到了結果中")


if __name__ == '__main__':
    test_multilang_system()
