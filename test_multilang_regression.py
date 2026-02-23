#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多語言佔位符系統的完整回歸測試
"""

from modules.multilang import (
    get_staff_name_mapping, get_store_name_mapping,
    extract_and_replace_names, restore_names
)

def run_tests():
    """運行完整的回歸測試"""
    staff_mapping = get_staff_name_mapping()
    store_mapping = get_store_name_mapping()
    
    # 測試用例：(原始文本, 預期中文還原, 預期英文還原)
    test_cases = [
        # 基本情況
        ("可約師傅：川、獻", "可約師傅：川、獻", "可約師傅：River、ryan"),
        ("川師傅在西門店有空", "川師傅在西門店有空", "River師傅在Ximen店有空"),
        ("西門的川", "西門的川", "Ximen的River"),
        
        # 複雜情況
        ("川、獻、豪在西門有空", "川、獻、豪在西門有空", "River、ryan、Lance在Ximen有空"),
        ("西門、延吉、家樂福三間分店的師傅川、獻都有空", "西門、延吉、家樂福三間分店的師傅川、獻都有空", 
         "Ximen、Yanji(Taipei Dome)、Ximen2(Xining Carrefour)三間分店的師傅River、ryan都有空"),
        
        # 邊界情況
        ("可約師傅：川", "可約師傅：川", "可約師傅：River"),
        ("只有店家：西門", "只有店家：西門", "只有店家：Ximen"),
        ("師傅川", "師傅川", "師傅River"),
        ("店家西門", "店家西門", "店家Ximen"),
        
        # 重複出現
        ("川和川一樣，在西門和西門", "川和川一樣，在西門和西門", "River和River一樣，在Ximen和Ximen"),
    ]
    
    print("=" * 100)
    print("多語言佔位符系統回歸測試")
    print("=" * 100)
    
    passed = 0
    failed = 0
    
    for original_text, expected_zh, expected_en in test_cases:
        # 提取和替換
        modified, placeholders = extract_and_replace_names(original_text, staff_mapping, store_mapping)
        
        # 還原為中文
        restored_zh = restore_names(modified, placeholders, "zh-TW")
        
        # 還原為英文
        restored_en = restore_names(modified, placeholders, "en")
        
        # 驗證
        zh_pass = restored_zh == expected_zh
        en_pass = restored_en == expected_en
        
        if zh_pass and en_pass:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
        
        print(f"\n{status}")
        print(f"  原始文本:  {original_text}")
        
        if not zh_pass:
            print(f"  中文結果:  {restored_zh}")
            print(f"  中文預期:  {expected_zh}")
        else:
            print(f"  中文:      ✓ {restored_zh}")
        
        if not en_pass:
            print(f"  英文結果:  {restored_en}")
            print(f"  英文預期:  {expected_en}")
        else:
            print(f"  英文:      ✓ {restored_en}")
    
    print("\n" + "=" * 100)
    print(f"測試結果: {passed} 通過, {failed} 失敗")
    print("=" * 100)
    
    return failed == 0


if __name__ == '__main__':
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
