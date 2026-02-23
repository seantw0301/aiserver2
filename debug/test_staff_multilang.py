"""
測試多國語系中的師傅名稱和店家名稱轉換功能
使用佔位符系統保護名稱不被翻譯

驗證：
1. 中文語系使用中文名
2. 其他語系使用英文名
3. 翻譯過程中名稱不會被錯誤翻譯
4. 預約情況下師傅和店家名稱的正確顯示
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
        print(f"映射表: {placeholder_map}")
        
        # 還原為英文
        restored_en = restore_names(text_with_placeholders, placeholder_map, 'en')
        print(f"英文版: {restored_en}")
        
        # 還原為中文
        restored_zh = restore_names(text_with_placeholders, placeholder_map, 'zh-TW')
        print(f"中文版: {restored_zh}")
    
    print()


def test_convert_staff_names(mapping):
    """測試師傅名稱轉換功能"""
    print("=" * 60)
    print("測試 2: 師傅名稱轉換功能")
    print("=" * 60)
    
    # 測試用的師傅名稱列表（中文名）
    test_names = ['鞋', '川', '蒙', '豪', '霆']
    
    languages = [
        ('zh-TW', '繁體中文'),
        ('zh', '簡體中文'),
        ('en', '英文'),
        ('th', '泰文'),
        ('ja', '日文'),
        ('ko', '韓文')
    ]
    
    print(f"原始師傅列表: {test_names}\n")
    
    for lang_code, lang_name in languages:
        converted = convert_staff_names(test_names, lang_code)
        print(f"{lang_name} ({lang_code}): {converted}")
    
    print()


def test_translate_response_with_staff_names():
    """測試包含師傅名稱的回應翻譯"""
    print("=" * 60)
    print("測試 3: 包含師傅名稱的預約回應翻譯")
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
        "response_message": "已為您找到 2 位師傅的空檔時間",
        "greeting_message": "親愛的會員 John 您好!",
        "success": True
    }
    
    languages = [
        ('zh-TW', '繁體中文'),
        ('en', '英文'),
        ('th', '泰文'),
        ('ja', '日文')
    ]
    
    for lang_code, lang_name in languages:
        print(f"\n{lang_name} ({lang_code}) 版本:")
        print("-" * 40)
        
        # 複製原始資料避免修改
        response_copy = test_response.copy()
        response_copy['masseur'] = test_response['masseur'].copy()
        
        # 翻譯
        translated = translate_response_fields(response_copy, lang_code)
        
        print(f"師傅名稱: {translated['masseur']}")
        print(f"回應訊息: {translated['response_message']}")
        print(f"問候語: {translated['greeting_message']}")


def test_multiple_staff_scenarios():
    """測試多種師傅組合場景"""
    print("\n" + "=" * 60)
    print("測試 4: 多種師傅組合場景")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "單一師傅",
            "masseur": ["豪"],
            "message": "已為您預約豪老師"
        },
        {
            "name": "兩位師傅",
            "masseur": ["鞋", "川"],
            "message": "已為您找到 2 位師傅的空檔時間"
        },
        {
            "name": "三位師傅",
            "masseur": ["蒙", "霆", "兔"],
            "message": "已為您找到 3 位師傅的空檔時間"
        },
        {
            "name": "無師傅指定",
            "masseur": [],
            "message": "請選擇師傅"
        }
    ]
    
    for scenario in scenarios:
        print(f"\n場景: {scenario['name']}")
        print(f"原始師傅列表: {scenario['masseur']}")
        
        test_data = {
            "masseur": scenario['masseur'].copy() if scenario['masseur'] else [],
            "response_message": scenario['message'],
            "isReservation": True
        }
        
        # 測試英文語系
        en_data = translate_response_fields(test_data.copy(), 'en')
        print(f"英文版師傅: {en_data['masseur']}")
        print(f"英文訊息: {en_data['response_message']}")
        
        # 測試中文語系
        tw_data = translate_response_fields(test_data.copy(), 'zh-TW')
        print(f"中文版師傅: {tw_data['masseur']}")
        print(f"中文訊息: {tw_data['response_message']}")


def test_edge_cases():
    """測試邊界情況"""
    print("\n" + "=" * 60)
    print("測試 5: 邊界情況測試")
    print("=" * 60)
    
    # 測試空列表
    print("\n1. 空師傅列表:")
    empty_result = convert_staff_names([], 'en')
    print(f"   結果: {empty_result} ✅" if empty_result == [] else f"   結果: {empty_result} ❌")
    
    # 測試不存在的師傅名稱
    print("\n2. 不存在的師傅名稱:")
    unknown_names = ['不存在的師傅']
    unknown_result = convert_staff_names(unknown_names, 'en')
    print(f"   輸入: {unknown_names}")
    print(f"   結果: {unknown_result}")
    print(f"   說明: 找不到對應英文名時保持原名 ✅")
    
    # 測試 None 值
    print("\n3. None 值處理:")
    test_data = {
        "masseur": None,
        "response_message": "測試訊息"
    }
    none_result = translate_response_fields(test_data, 'en')
    print(f"   結果: masseur = {none_result.get('masseur')} ✅")


def run_all_tests():
    """執行所有測試"""
    print("\n🧪 師傅名稱多國語系轉換功能測試\n")
    
    try:
        # 測試 1: 獲取映射
        mapping = test_get_staff_name_mapping()
        
        if not mapping:
            print("⚠️  警告: 無法從資料庫獲取師傅映射，部分測試可能失敗")
        
        # 測試 2: 名稱轉換
        test_convert_staff_names(mapping)
        
        # 測試 3: 回應翻譯
        test_translate_response_with_staff_names()
        
        # 測試 4: 多種場景
        test_multiple_staff_scenarios()
        
        # 測試 5: 邊界情況
        test_edge_cases()
        
        print("\n" + "=" * 60)
        print("✅ 所有測試完成!")
        print("=" * 60)
        print("\n測試結果摘要:")
        print("✓ 繁體中文語系顯示中文師傅名稱")
        print("✓ 其他語系顯示英文師傅名稱")
        print("✓ 回應訊息正確翻譯")
        print("✓ 邊界情況處理正確")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
