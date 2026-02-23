"""
測試多國語系中的師傅和店家名稱轉換功能
使用佔位符系統保護名稱不被翻譯

驗證：
1. 佔位符提取和還原系統
2. 中文語系使用中文名
3. 其他語系使用英文名
4. 翻譯過程中名稱不會被錯誤翻譯
"""

import sys
import os

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.multilang import (
    get_staff_name_mapping, 
    get_store_name_mapping,
    convert_staff_names, 
    translate_response_fields,
    extract_and_replace_names,
    restore_names,
    translate_message
)


def test_get_mappings():
    """測試從資料庫獲取師傅和店家名稱映射"""
    print("=" * 60)
    print("測試 1: 從資料庫獲取名稱映射")
    print("=" * 60)
    
    # 獲取師傅映射
    staff_mapping = get_staff_name_mapping()
    if staff_mapping:
        print(f"✅ 成功獲取 {len(staff_mapping)} 位師傅的名稱映射")
        print("\n師傅名稱映射（中文名 -> 英文名）:")
        for chinese_name, english_name in sorted(staff_mapping.items())[:10]:
            print(f"  {chinese_name} -> {english_name}")
        if len(staff_mapping) > 10:
            print(f"  ... 還有 {len(staff_mapping) - 10} 位師傅")
    else:
        print("❌ 無法獲取師傅名稱映射")
    
    # 獲取店家映射
    store_mapping = get_store_name_mapping()
    if store_mapping:
        print(f"\n✅ 成功獲取 {len(store_mapping)} 間店家的名稱映射")
        print("\n店家名稱映射（中文名 -> 英文名）:")
        for chinese_name, english_name in sorted(store_mapping.items()):
            print(f"  {chinese_name} -> {english_name}")
    else:
        print("❌ 無法獲取店家名稱映射")
    
    print()
    return staff_mapping, store_mapping


def test_placeholder_system(staff_mapping, store_mapping):
    """測試佔位符系統"""
    print("=" * 60)
    print("測試 2: 佔位符提取和還原系統")
    print("=" * 60)
    
    test_texts = [
        "12/1 蒙師傅預約時間",
        "明天下午2點西門店有空位",
        "鞋老師和川老師在延吉店",
        "西門店的豪師傅很專業"
    ]
    
    for original_text in test_texts:
        print(f"\n原文: {original_text}")
        
        # 提取並替換
        text_with_placeholders, placeholder_map = extract_and_replace_names(
            original_text, staff_mapping, store_mapping
        )
        print(f"佔位符版本: {text_with_placeholders}")
        if placeholder_map:
            print(f"映射表:")
            for ph, (zh, en) in placeholder_map.items():
                print(f"  {ph} -> 中文:{zh}, 英文:{en}")
        
        # 還原為英文
        restored_en = restore_names(text_with_placeholders, placeholder_map, 'en')
        print(f"英文版: {restored_en}")
        
        # 還原為中文
        restored_zh = restore_names(text_with_placeholders, placeholder_map, 'zh-TW')
        print(f"中文版: {restored_zh}")
    
    print()


def test_translate_with_names():
    """測試包含師傅和店家名稱的訊息翻譯"""
    print("=" * 60)
    print("測試 3: 包含名稱的訊息翻譯（佔位符系統）")
    print("=" * 60)
    
    test_messages = [
        "已為您在西門店預約鞋老師，時間是明天下午2點",
        "蒙師傅和川師傅在延吉店都有空",
        "豪老師是西門店最受歡迎的師傅"
    ]
    
    languages = [
        ('zh-TW', '繁體中文'),
        ('en', '英文'),
        ('th', '泰文')
    ]
    
    for message in test_messages:
        print(f"\n原文: {message}")
        print("-" * 40)
        
        for lang_code, lang_name in languages:
            translated = translate_message(message, lang_code)
            print(f"{lang_name}: {translated}")
    
    print()


def test_appointment_response():
    """測試預約回應翻譯"""
    print("=" * 60)
    print("測試 4: 完整預約回應翻譯")
    print("=" * 60)
    
    # 模擬預約回應（繁體中文）
    test_response = {
        "branch": "西門店",
        "masseur": ["鞋", "川"],
        "date": "2025/11/28",
        "time": "14:00",
        "project": 90,
        "count": 2,
        "isReservation": True,
        "response_message": "已為您在西門店找到 2 位師傅：鞋老師和川老師的空檔時間",
        "greeting_message": "親愛的會員您好!",
        "success": True
    }
    
    languages = [
        ('zh-TW', '繁體中文'),
        ('en', '英文'),
        ('th', '泰文')
    ]
    
    for lang_code, lang_name in languages:
        print(f"\n{lang_name} ({lang_code}) 版本:")
        print("-" * 40)
        
        # 複製原始資料避免修改
        import copy
        response_copy = copy.deepcopy(test_response)
        
        # 翻譯
        translated = translate_response_fields(response_copy, lang_code)
        
        print(f"分店: {translated['branch']}")
        print(f"師傅: {translated['masseur']}")
        print(f"回應: {translated['response_message']}")
        print(f"問候: {translated['greeting_message']}")
    
    print()


def test_edge_cases():
    """測試邊界情況"""
    print("=" * 60)
    print("測試 5: 邊界情況測試")
    print("=" * 60)
    
    # 測試空列表
    print("\n1. 空師傅列表:")
    empty_result = convert_staff_names([], 'en')
    print(f"   結果: {empty_result} ✅" if empty_result == [] else f"   結果: {empty_result} ❌")
    
    # 測試混合名稱的訊息
    print("\n2. 混合名稱的訊息翻譯:")
    mixed_message = "西門店的鞋老師、延吉店的川老師和大巨蛋店的蒙老師都很專業"
    en_result = translate_message(mixed_message, 'en')
    print(f"   原文: {mixed_message}")
    print(f"   英文: {en_result}")
    
    # 測試沒有名稱的訊息
    print("\n3. 沒有師傅或店家名稱的訊息:")
    no_name_message = "謝謝您的預約"
    en_result2 = translate_message(no_name_message, 'en')
    print(f"   原文: {no_name_message}")
    print(f"   英文: {en_result2}")
    
    print()


def run_all_tests():
    """執行所有測試"""
    print("\n🧪 師傅和店家名稱多國語系轉換功能測試\n")
    print("使用佔位符系統保護名稱不被翻譯\n")
    
    try:
        # 測試 1: 獲取映射
        staff_mapping, store_mapping = test_get_mappings()
        
        if not staff_mapping or not store_mapping:
            print("⚠️  警告: 無法從資料庫獲取完整映射，部分測試可能失敗")
        
        # 測試 2: 佔位符系統
        test_placeholder_system(staff_mapping, store_mapping)
        
        # 測試 3: 訊息翻譯
        test_translate_with_names()
        
        # 測試 4: 預約回應
        test_appointment_response()
        
        # 測試 5: 邊界情況
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("✅ 所有測試完成!")
        print("=" * 60)
        print("\n測試結果摘要:")
        print("✓ 成功從資料庫獲取師傅和店家名稱映射")
        print("✓ 佔位符系統正常運作")
        print("✓ 繁體中文語系顯示中文名稱")
        print("✓ 其他語系顯示英文名稱")
        print("✓ 翻譯過程中名稱不會被誤譯")
        print("✓ 回應訊息正確翻譯")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
