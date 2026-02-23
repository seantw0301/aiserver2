#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試腳本：詳細追蹤 restore_names 問題
"""

from modules.multilang import (
    get_staff_name_mapping, get_store_name_mapping,
    extract_and_replace_names
)
import re

def debug_restore_names(text: str, placeholder_map: dict, target_language: str) -> str:
    """調試版本的 restore_names，帶詳細日誌"""
    if not text or not placeholder_map:
        return text
    
    restored_text = text
    is_chinese = target_language in ['zh-TW', 'zh-tw', 'zh', 'tw']
    
    print(f"\n=== 開始還原 ({target_language}) ===")
    print(f"原始文本: {restored_text}")
    print(f"佔位符映射: {placeholder_map}")
    print(f"是否為中文: {is_chinese}")
    
    iteration = 0
    for placeholder, (chinese_name, english_name) in placeholder_map.items():
        iteration += 1
        # 根據語系選擇中文名或英文名
        name_to_use = chinese_name if is_chinese else english_name
        
        print(f"\n[迭代 {iteration}]")
        print(f"  佔位符: {placeholder}")
        print(f"  中文: {chinese_name}, 英文: {english_name}")
        print(f"  使用: {name_to_use}")
        print(f"  替換前: {restored_text}")
        
        # 直接替換原始佔位符
        restored_text = restored_text.replace(placeholder, name_to_use)
        print(f"  替換後: {restored_text}")
        
        # 也嘗試替換 Azure 可能改變的變種（大小寫轉換、編號改變）
        placeholder_base = placeholder.replace('%W', '%').replace('%S', '%')  # %W1% -> %1%
        pattern = f"(?i)%[Ww]{placeholder_base[1:]}"  # 不區分大小寫匹配 %W1% 或 %w1%
        new_text = re.sub(pattern, name_to_use, restored_text)
        if new_text != restored_text:
            print(f"  正則替換: {new_text}")
            restored_text = new_text
    
    print(f"\n最終結果: {restored_text}")
    return restored_text


def test_problem_case():
    """測試有問題的情況"""
    staff_mapping = get_staff_name_mapping()
    store_mapping = get_store_name_mapping()
    
    text = "川師傅在西門店有空"
    print(f"原始文本: {text}")
    print(f"師傅映射: {staff_mapping}")
    print(f"店家映射: {store_mapping}")
    
    # 提取和替換
    modified, placeholders = extract_and_replace_names(text, staff_mapping, store_mapping)
    
    print(f"\n修改後: {modified}")
    print(f"佔位符映射:")
    for ph, (ch, en) in placeholders.items():
        print(f"  {ph}: ({ch}, {en})")
    
    # 使用調試版本還原
    restored_zh = debug_restore_names(modified, placeholders, "zh-TW")
    print(f"\n預期結果: {text}")
    print(f"實際結果: {restored_zh}")
    print(f"是否匹配: {restored_zh == text}")


if __name__ == '__main__':
    test_problem_case()
