#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
員工姓名處理模組

匯整所有與員工姓名提取相關的程式碼
從原始程式碼中整理而來，不改動任何原始程式碼
主要功能：在自然語言中找出員工們的姓名，包含中文或英文
"""

import re
from typing import List, Dict, Any


def getStaffNames(text: str) -> List[str]:
    """
    在自然語言中找出員工們的姓名，包含中文或英文
    
    此函數整合自 main.py 的 extract_staff_name 函數
    加強中文判斷：確保同一人只回傳一次，且只回傳中文名
    
    特殊處理：若文字包含「不指定」「都可以」「有那些師傅」「有誰可以」「有那些師父」「誰可以」
              則返回所有師傅名單
    
    Args:
        text (str): 用戶輸入的文本
        
    Returns:
        List[str]: 找到的員工姓名列表（中文名稱）
    """
    print(f"DEBUG [StaffNames]: 開始提取師傅名稱，輸入文字: {text}")
    
    # 🔍 優先檢查是否為「不指定師傅」的表達（在查詢資料庫前）
    no_preference_keywords = ['不指定', '那一', '哪一','都可以', '那位師傅','哪位','哪些','那些', '有誰可以', '有那些師父', '誰可以', '其它']
    for keyword in no_preference_keywords:
        if keyword in text:
            print(f"DEBUG [StaffNames]: ⭐️ 檢測到「{keyword}」關鍵詞")
            # 只在檢測到關鍵詞時才查詢資料庫
            try:
                from .staff_utils import getStaffMapping
                staff_mapping = getStaffMapping()
                if staff_mapping:
                    staff_names = list(set(staff_mapping.values()))
                    print(f"DEBUG [StaffNames]: 返回所有 {len(staff_names)} 位師傅")
                    return staff_names
            except Exception as e:
                print(f"DEBUG [StaffNames]: ❗ 獲取師傅名單時發生錯誤: {e}")
            return []
    
    # 獲取師傅名字列表及對應的英文名
    # 來自 staff_utils.py 的 getNameMapping() 函數
    try:
        from .staff_utils import getStaffMapping
        
        # 直接獲取完整的映射字典（英文大寫 -> 中文）
        staff_mapping = getStaffMapping()
        if not staff_mapping:
            print(f"DEBUG [StaffNames]: ❗ 無法獲取師傅名單")
            return []
        
        # 獲取所有中文名稱（去重）
        staff_names = list(set(staff_mapping.values()))
        print(f"DEBUG [StaffNames]: 師傅名單總數: {len(staff_names)} 位")
        print(f"DEBUG [StaffNames]: 中文名: {staff_names}")
    except Exception as e:
        print(f"DEBUG [StaffNames]: ❗ 獲取師傅名單時發生錯誤: {e}")
        return []
    
    # 使用 set 來儲存找到的中文名稱，自動去重
    found_chinese_names = set()
    
    # 查找中文名（直接字符串匹配）
    # 來自 main.py extract_staff_name 函數
    print(f"DEBUG [StaffNames]: Step 1 - 檢查中文名...")
    for name in staff_names:
        if name in text:
            print(f"DEBUG [StaffNames]: ✅ 找到中文名: {name}")
            found_chinese_names.add(name)
    
    # 檢查英文名（統一轉大寫比對）
    print(f"DEBUG [StaffNames]: Step 2 - 檢查英文名（轉大寫比對）...")
    upper_text = text.upper()
    
    # 來自 main.py extract_staff_name 函數的多種匹配模式
    for eng_name, chinese_name in staff_mapping.items():
        # eng_name 已經是大寫，chinese_name 是對應的中文名
        
        # 如果這個人的中文名已經被找到了，跳過英文名匹配
        if chinese_name in found_chinese_names:
            continue
            
        # 使用負向斷言：前後不能是英文字母（避免部分匹配，如 YU 匹配到 YUAN）
        # 這樣可以正確處理中英文混合（中文字符不會干擾匹配）
        pattern = r'(?<![A-Z])' + re.escape(eng_name) + r'(?![A-Z])'
        
        if re.search(pattern, upper_text):
            # 將英文名轉換為對應的中文名，確保只加入中文名
            print(f"DEBUG [StaffNames]: ✅ 找到英文名: {eng_name} -> {chinese_name}")
            found_chinese_names.add(chinese_name)
    
    # 轉換為列表並返回，確保只回傳中文名
    result = list(found_chinese_names)
    print(f"DEBUG [StaffNames]: ✅ 最終找到 {len(result)} 位師傅: {result}")
    return result


def extractStaffNamesByPattern(text: str) -> List[str]:
    """
    通過特定模式提取員工姓名（更嚴格的匹配）
    
    此函數提供更嚴格的員工姓名匹配，適用於需要精確識別的場景
    
    Args:
        text (str): 用戶輸入的文本
        
    Returns:
        List[str]: 找到的員工姓名列表（中文名稱）
    """
    try:
        from .staff_utils import getStaffMapping
        staff_mapping = getStaffMapping()
        if not staff_mapping:
            return []
        # 提取中文名稱列表
        staff_names = list(set(staff_mapping.values()))
    except Exception as e:
        print(f"獲取師傅名單時發生錯誤: {e}")
        return []
    
    found_names = []
    
    # 中文師傅名字模式（完整詞匹配）
    for name in staff_names:
        # 確保是完整的師傅名字，不是部分匹配
        pattern = r"(?:^|[^a-zA-Z\u4e00-\u9fff])" + re.escape(name) + r"(?:[^a-zA-Z\u4e00-\u9fff]|$)"
        if re.search(pattern, text):
            found_names.append(name)
    
    # 英文師傅名字模式（詞邊界匹配）
    for eng_name, chinese_name in staff_mapping.items():
        # 使用詞邊界確保完整匹配
        pattern = r"\b" + re.escape(eng_name) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            found_names.append(chinese_name)
    
    return list(set(found_names))


def extractStaffNamesWithConnections(text: str) -> Dict[str, Any]:
    """
    提取員工姓名並識別連接關係
    
    此函數整合自 handle_customer.py 和 main.py 中的員工名字連接模式識別
    
    Args:
        text (str): 用戶輸入的文本
        
    Returns:
        Dict[str, Any]: 包含員工姓名和連接關係的詳細信息
    """
    try:
        from .staff_utils import getStaffMapping
        staff_mapping = getStaffMapping()
        if not staff_mapping:
            return {'staff_names': [], 'has_connections': False, 'connection_count': 0}
        staff_names = list(set(staff_mapping.values()))
        english_names = list(staff_mapping.keys())
    except Exception as e:
        print(f"獲取師傅名單時發生錯誤: {e}")
        return {'staff_names': [], 'has_connections': False, 'connection_count': 0}
    
    # 獲取所有找到的員工姓名
    found_names = getStaffNames(text)
    
    # 檢查連接詞模式（來自 handle_customer.py 和 main.py）
    # 中文師傅名字模式
    staff_pattern_cn = "|".join(staff_names)
    
    # 英文師傅名字模式 (包括小寫和首字母大寫)
    staff_pattern_en = "|".join(
        [name.lower() for name in english_names]
        + [name.capitalize() for name in english_names]
    )
    
    # 完整師傅名字模式
    staff_pattern = f"({staff_pattern_cn}|{staff_pattern_en})"
    
    # 連接詞（來自 handle_customer.py 和 main.py）
    connect_words = ["和", "跟", "與", "and", "&"]
    connect_pattern = "|".join(connect_words)
    
    # 組合模式：師傅名1 + 連接詞 + 師傅名2
    connection_pattern = f"{staff_pattern}(?:{connect_pattern}){staff_pattern}"
    
    # 檢查是否有師傅名字通過連接詞連接
    has_connections = bool(re.search(connection_pattern, text, re.IGNORECASE))
    
    # 計算連接組合數量
    connection_matches = re.findall(connection_pattern, text, re.IGNORECASE)
    connection_count = len(connection_matches)
    
    # 檢查是否有多個師傅名字（不通過連接詞，但在同一句話中）
    staff_matches = re.findall(staff_pattern, text, re.IGNORECASE)
    unique_staff_in_text = list(set([match.lower() for match in staff_matches]))
    
    return {
        'staff_names': found_names,
        'has_connections': has_connections,
        'connection_count': connection_count,
        'total_staff_mentions': len(staff_matches),
        'unique_staff_mentions': len(unique_staff_in_text),
        'connection_matches': connection_matches
    }


def analyzeStaffNameText(text: str) -> Dict[str, Any]:
    """
    詳細分析文本中的員工姓名信息（用於調試）
    
    Args:
        text (str): 用戶輸入的文本
        
    Returns:
        Dict[str, Any]: 包含詳細分析結果的字典
    """
    try:
        from .staff_utils import getStaffMapping
        staff_mapping = getStaffMapping()
        if not staff_mapping:
            return {'error': '無法獲取員工名單'}
        staff_names = list(set(staff_mapping.values()))
    except Exception as e:
        return {'error': f'獲取師傅名單時發生錯誤: {e}'}
    
    result = {
        'found_staff_names': getStaffNames(text),
        'pattern_based_names': extractStaffNamesByPattern(text),
        'connection_analysis': extractStaffNamesWithConnections(text),
        'detailed_analysis': {}
    }
    
    analysis = result['detailed_analysis']
    
    # 中文名字匹配分析
    chinese_matches = []
    for name in staff_names:
        if name in text:
            chinese_matches.append(name)
    analysis['chinese_name_matches'] = chinese_matches
    
    # 英文名字匹配分析
    english_matches = []
    for eng_name, chinese_name in staff_mapping.items():
        patterns = [
            eng_name.lower(),
            eng_name.capitalize(),
            eng_name.upper()
        ]
        for pattern in patterns:
            if pattern in text:
                english_matches.append({
                    'english_name': eng_name,
                    'chinese_name': chinese_name,
                    'matched_pattern': pattern
                })
                break
    analysis['english_name_matches'] = english_matches
    
    # 連接詞分析
    connect_words = ["和", "跟", "與", "and", "&"]
    found_connections = [word for word in connect_words if word in text]
    analysis['connection_words_found'] = found_connections
    
    return result


def getStaffNamePatterns() -> Dict[str, Any]:
    """
    獲取員工姓名匹配的所有模式（用於測試和調試）
    
    Returns:
        Dict[str, Any]: 包含所有員工姓名相關模式的字典
    """
    try:
        from .staff_utils import getStaffMapping
        staff_mapping = getStaffMapping()
        if not staff_mapping:
            return {'error': '無法獲取員工名單'}
        staff_names = list(set(staff_mapping.values()))
    except Exception as e:
        return {'error': f'獲取師傅名單時發生錯誤: {e}'}
    
    return {
        'chinese_names': list(staff_names),
        'english_names': list(staff_mapping.keys()),
        'name_mapping': staff_mapping,
        'connection_words': ["和", "跟", "與", "and", "&"],
        'matching_patterns': {
            'chinese_direct': '直接字符串匹配',
            'english_patterns': [
                '標準模式：完整單詞匹配',
                '寬松模式：允許是單詞的一部分',
                '特殊模式：大小寫不敏感的完整英文名',
                '首字母大寫模式'
            ]
        }
    }


# 測試函數
def test_getStaffNames():
    """
    測試 getStaffNames 函數的各種情況
    """
    test_cases = [
        # 中文名字
        ("我要預約鞋師傅", ["鞋"]),
        ("豪師傅有空嗎", ["豪"]),
        ("我想找蒙師傅", ["蒙"]),
        
        # 英文名字
        ("I want to book camper", ["鞋"]),  # 假設camper對應鞋
        ("simon老師", ["蒙"]),  # 假設simon對應蒙
        ("Peter師傅", ["兔"]),  # 假設peter對應兔
        
        # 大小寫變化
        ("CAMPER師傅", ["鞋"]),
        ("Camper有空嗎", ["鞋"]),
        ("camper老師", ["鞋"]),
        
        # 多個師傅
        ("我要預約鞋和豪", ["鞋", "豪"]),
        ("camper跟simon", ["鞋", "蒙"]),
        ("鞋師傅與Peter", ["鞋", "兔"]),
        
        # 連接詞測試
        ("鞋and豪", ["鞋", "豪"]),
        ("camper&simon", ["鞋", "蒙"]),
        
        # 無師傅名字
        ("我要預約", []),
        ("明天有空嗎", []),
        ("想要理髮", []),
        
        # 邊界情況
        ("", []),
    ]
    
    print("=== 員工姓名提取測試 ===")
    for text, expected in test_cases:
        result = getStaffNames(text)
        # 因為實際的師傅名字映射可能不同，我們只檢查是否找到了名字
        status = "✓" if (len(result) > 0) == (len(expected) > 0) else "✗"
        print(f"{status} '{text}' -> {result}")
    
    print("\n=== 連接關係分析測試 ===")
    test_text = "我要預約鞋和豪師傅"
    analysis = extractStaffNamesWithConnections(test_text)
    print(f"測試文本: '{test_text}'")
    print(f"找到的師傅: {analysis['staff_names']}")
    print(f"有連接關係: {analysis['has_connections']}")
    print(f"連接數量: {analysis['connection_count']}")
    print(f"總提及次數: {analysis['total_staff_mentions']}")
    
    print("\n=== 詳細分析測試 ===")
    detailed_analysis = analyzeStaffNameText(test_text)
    print(f"基本匹配: {detailed_analysis['found_staff_names']}")
    print(f"模式匹配: {detailed_analysis['pattern_based_names']}")
    print(f"詳細分析: {detailed_analysis['detailed_analysis']}")


if __name__ == "__main__":
    test_getStaffNames()
