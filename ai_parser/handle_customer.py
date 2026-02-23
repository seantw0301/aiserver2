#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客人數量判斷處理模組

匯整所有判斷自然語言中"客人數量"的條件
從原始程式碼中整理而來，不改動任何原始程式碼
"""

import re
import sys
import os
from typing import Optional

# 添加當前目錄到路徑以便導入 staff_utils
sys.path.append(os.path.dirname(__file__))
from staff_utils import getNameMapping


def getCustomerCount(text: str, return_details: bool = False):
    """
    從文本中提取客人數量
    
    Args:
        text (str): 用戶輸入的文本
        return_details (bool): 是否返回详细信息（包括是否明确表达）
        
    Returns:
        如果 return_details=False: int - 客人數量
        如果 return_details=True: tuple[int, bool] - (客人數量, 是否明确表达)
    """
    #原始句字中的 "選三位"取代為"選"
    text = re.sub(r"選[一二兩三四五六七八九十]位", "選", text)

    # 嘗試提取明確的數字表達
    person_count = _extract_explicit_person_count(text)
    if person_count is not None:
        return (person_count, True) if return_details else person_count
    
    # 嘗試通過師傅名字組合判斷人數
    person_count = _extract_person_count_by_staff_names(text)
    if person_count is not None:
        return (person_count, True) if return_details else person_count
    
    # 嘗試通過其他模式判斷人數
    person_count = _extract_person_count_by_patterns(text)
    if person_count is not None:
        return (person_count, True) if return_details else person_count
    
    # 如果無法取得數量，返回 None
    return (None, False) if return_details else None


def _extract_explicit_person_count(text: str) -> Optional[int]:
    """
    從文本中提取明確的數字表達客人數量
    
    此函數整合自 main.py 的 extract_person_count 函數的數字匹配部分
    
    Args:
        text (str): 用戶輸入的文本
        
    Returns:
        Optional[int]: 提取到的客人數量，如果沒有找到則返回None
    """

    #原始句字中的 "選三位"取代為"選"
    text = re.sub(r"選[一二兩三四五六七八九十]位", "選", text)

    # 先檢查中文數字+人的模式（避免被後續阿拉伯數字規則干擾）
    chinese_number_map = {
        '一': 1, '二': 2, '兩': 2, '两': 2, '三': 3, '四': 4, 
        '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
        '壹': 1, '貳': 2, '參': 3, '叁': 3, '肆': 4, '伍': 5,
        '陸': 6, '柒': 7, '捌': 8, '玖': 9, '拾': 10
    }
    
    # 中文數字 + 人/位/個人 等的模式
    chinese_person_pattern = r"([一二兩两三四五六七八九十壹貳參叁肆伍陸柒捌玖拾]+)\s*(?:个人|個人|人|位|客人|客戶)"
    match = re.search(chinese_person_pattern, text)
    
    if match:
        chinese_num = match.group(1)
        # 轉換中文數字為阿拉伯數字
        count = _convert_chinese_to_number(chinese_num, chinese_number_map)
        if count and 1 <= count <= 20:
            return count
    
    # 數字+人的模式（來自 main.py extract_person_count 函數）
    person_pattern = r"(\d+)\s*(?:个人|個人|人|位)"
    match = re.search(person_pattern, text)
    
    if match:
        try:
            count = int(match.group(1))
            # 基本合理性檢查，避免過大的數字
            if 1 <= count <= 20:  # 假設最多20人的預約
                return count
        except ValueError:
            pass
    
    return None


def _convert_chinese_to_number(chinese_str: str, number_map: dict) -> Optional[int]:
    """
    將中文數字字符串轉換為阿拉伯數字
    
    Args:
        chinese_str: 中文數字字符串（如 "三"、"十"、"二十"）
        number_map: 中文數字到阿拉伯數字的映射
        
    Returns:
        Optional[int]: 轉換後的數字，如果無法轉換則返回None
    """
    # 處理單個中文數字
    if len(chinese_str) == 1:
        return number_map.get(chinese_str)
    
    # 處理 "十X" 的情況（如 "十一" = 11, "十二" = 12）
    if chinese_str.startswith('十') or chinese_str.startswith('拾'):
        if len(chinese_str) == 1:
            return 10
        second_char = chinese_str[1]
        second_num = number_map.get(second_char, 0)
        return 10 + second_num
    
    # 處理 "X十" 或 "X十Y" 的情況（如 "二十" = 20, "二十三" = 23）
    if '十' in chinese_str or '拾' in chinese_str:
        parts = chinese_str.replace('拾', '十').split('十')
        if len(parts) == 2:
            tens = number_map.get(parts[0], 0) if parts[0] else 1  # "十" = "一十"
            ones = number_map.get(parts[1], 0) if parts[1] else 0
            return tens * 10 + ones
    
    # 如果無法處理，嘗試直接查表
    return number_map.get(chinese_str)


def _extract_person_count_by_staff_names(text: str) -> Optional[int]:
    """
    通過師傅名字組合判斷人數
    
    此函數整合自 main.py 的 extract_person_count 函數的師傅名字匹配部分
    
    NOTE: 客人數量不應該等於按摩師數量，這個函數主要檢查是否有多人通過連接詞組合表達
    
    Args:
        text (str): 用戶輸入的文本
        
    Returns:
        Optional[int]: 提取到的客人數量，如果沒有找到則返回None
    """
    try:
        # 獲取師傅名字列表
        staff_names, english_names = getNameMapping()
        
        # 中文師傅名字模式
        staff_pattern_cn = "|".join(staff_names)
        
        # 英文師傅名字模式 (包括小寫和首字母大寫)
        staff_pattern_en = "|".join(
            [name.lower() for name in english_names]
            + [name.capitalize() for name in english_names]
        )
        
        # 完整師傅名字模式
        staff_pattern = f"({staff_pattern_cn}|{staff_pattern_en})"
        
        # 連接詞
        connect_words = ["和", "跟", "與", "and", "&"]
        connect_pattern = "|".join(connect_words)
        
        # 組合模式：師傅名1 + 連接詞 + 師傅名2
        pattern = f"{staff_pattern}(?:{connect_pattern}){staff_pattern}"
        
        # 檢查是否有師傅名字通過連接詞連接
        if re.search(pattern, text, re.IGNORECASE):
            return 2
        
        # 不再使用師傅數量來推斷客人數量
        # 除非有明確的連接詞表示多人
        
    except Exception as e:
        print(f"通過師傅名字判斷人數時發生錯誤: {e}")
    
    return None


def _extract_person_count_by_patterns(text: str) -> Optional[int]:
    """
    通過其他模式判斷人數
    
    整合自 handle_reserv.php 中的人數相關模式和其他啟發式規則
    
    Args:
        text (str): 用戶輸入的文本
        
    Returns:
        Optional[int]: 提取到的客人數量，如果沒有找到則返回None
    """
    #原始句字中的 "選三位"取代為"選"
    text = re.sub(r"選[一二兩三四五六七八九十]位", "選", text)

    # 來自 handle_reserv.php 的人數模式
    person_patterns = [
        r'\d+\s*(?:个人|個人|人|位)',
        r'\d+人'
    ]
    
    for pattern in person_patterns:
        match = re.search(pattern, text)
        if match:
            # 提取數字
            number_match = re.search(r'\d+', match.group())
            if number_match:
                try:
                    count = int(number_match.group())
                    if 1 <= count <= 20:  # 基本合理性檢查
                        return count
                except ValueError:
                    continue
    
    # 檢查「我和...」「我跟...」「我與...」這種連詞表達方式（明確表示2人）
    connection_patterns = [
        r"我和(?:朋友|家人|同事|伙伴|親友|同學|同窗|夫人|先生|老公|老婆|女友|男友)",
        r"我跟(?:朋友|家人|同事|伙伴|親友|同學|同窗|夫人|先生|老公|老婆|女友|男友)",
        r"我與(?:朋友|家人|同事|伙伴|親友|同學|同窗|夫人|先生|老公|老婆|女友|男友)"
    ]
    
    for pattern in connection_patterns:
        if re.search(pattern, text):
            return 2
    
    # 不再使用模糊的複數表達或家庭詞彙來推斷人數
    # 只有明確的數字表達才返回數量
    
    return None


def analyzeCustomerCountText(text: str) -> dict:
    """
    詳細分析文本，返回匹配的客人數量相關信息（用於調試）
    
    Args:
        text (str): 用戶輸入的文本
        
    Returns:
        dict: 包含分析結果的字典
    """
    result = {
        'final_count': getCustomerCount(text),
        'explicit_count': _extract_explicit_person_count(text),
        'staff_name_count': _extract_person_count_by_staff_names(text),
        'pattern_count': _extract_person_count_by_patterns(text),
        'analysis': {}
    }
    
    # 分析各種模式的匹配情況
    analysis = result['analysis']
    
    # 數字模式分析
    person_pattern = r"(\d+)\s*(?:个人|個人|人|位)"
    if re.search(person_pattern, text):
        analysis['explicit_number_pattern'] = re.findall(person_pattern, text)
    
    # 師傅名字模式分析
    try:
        staff_names, english_names = getNameMapping()
        staff_pattern = "|".join(staff_names + [name.lower() for name in english_names])
        staff_matches = re.findall(f"({staff_pattern})", text, re.IGNORECASE)
        if staff_matches:
            analysis['staff_names_found'] = staff_matches
    except Exception as e:
        analysis['staff_mapping_error'] = str(e)
    
    # 連詞模式分析
    connection_patterns = [
        r"我和(?:朋友|家人|同事|伙伴|親友|同學|同窗|夫人|先生|老公|老婆|女友|男友)",
        r"我跟(?:朋友|家人|同事|伙伴|親友|同學|同窗|夫人|先生|老公|老婆|女友|男友)",
        r"我與(?:朋友|家人|同事|伙伴|親友|同學|同窗|夫人|先生|老公|老婆|女友|男友)"
    ]
    
    for pattern in connection_patterns:
        if re.search(pattern, text):
            if 'connection_patterns' not in analysis:
                analysis['connection_patterns'] = []
            analysis['connection_patterns'].append(re.search(pattern, text).group())
    
    # 複數表達分析
    plural_patterns = ["我們", "我们", "大家", "一起", "一群", "我和朋友", "我跟朋友"]
    found_plurals = [pattern for pattern in plural_patterns if pattern in text]
    if found_plurals:
        analysis['plural_expressions'] = found_plurals
    
    # 家庭相關詞彙分析
    family_patterns = ["家人", "家庭", "夫妻", "情侶", "朋友們"]
    found_family = [pattern for pattern in family_patterns if pattern in text]
    if found_family:
        analysis['family_expressions'] = found_family
    
    return result


def getCustomerCountKeywords() -> dict:
    """
    獲取客人數量判斷關鍵詞列表（用於測試和調試）
    
    Returns:
        dict: 包含所有客人數量相關關鍵詞的字典
    """
    return {
        'explicit_patterns': [
            r"(\d+)\s*(?:个人|個人|人|位)",
            r"\d+人",
            r"兩\s*(?:个人|個人|人|位|客人|客戶)",
            r"三\s*(?:个人|個人|人|位|客人|客戶)",
            r"四\s*(?:个人|個人|人|位|客人|客戶)"
        ],
        'staff_connection_words': ["和", "跟", "與", "and", "&"],
        'connection_patterns': [
            r"我和(?:朋友|家人|同事|伙伴|親友|同學|同窗|夫人|先生|老公|老婆|女友|男友)",
            r"我跟(?:朋友|家人|同事|伙伴|親友|同學|同窗|夫人|先生|老公|老婆|女友|男友)",
            r"我與(?:朋友|家人|同事|伙伴|親友|同學|同窗|夫人|先生|老公|老婆|女友|男友)"
        ],
        'plural_expressions': [
            "我們", "我们", "大家", "一起", "一群", 
            "幾個", "几个", "多個", "多个", "好幾個", "好几个",
            "我和朋友", "我和家人", "我跟朋友", "我與朋友"
        ],
        'family_expressions': [
            "家人", "家庭", "夫妻", "夫婦", "夫妇", 
            "情侶", "情侣", "朋友們", "朋友们", "同事們", "同事们"
        ],
        'chinese_numbers': {
            "兩": 2, "二": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9, "十": 10
        }
    }


# 測試函數
def test_getCustomerCount():
    """
    測試 getCustomerCount 函數的各種情況
    """
    test_cases = [
        # 明確數字表達
        ("我要預約3個人", 3),
        ("5位客人要預約", 5),
        ("兩個人要預約", 2),
        ("三位要預約", 3),
        
        # 師傅名字組合
        ("我要預約鞋和豪", 2),
        ("camper跟simon有空嗎", 2),
        ("鞋師傅與蒙師傅", 2),
        
        # 複數表達
        ("我們要預約", 2),
        ("大家一起去", 2),
        ("朋友們要預約", 2),
        
        # 家庭相關
        ("夫妻要預約", 2),
        ("情侶按摩", 2),
        ("家人要理髮", 2),
        
        # 無明確數量（應該返回1）
        ("我要預約", 1),
        ("明天有空嗎", 1),
        ("想要理髮", 1),
        
        # 邊界情況
        ("", 1),
        ("100個人", 1),  # 超出合理範圍，應該返回預設值
    ]
    
    print("=== 客人數量判斷測試 ===")
    for text, expected in test_cases:
        result = getCustomerCount(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (預期: {expected})")
    
    print("\n=== 詳細分析測試 ===")
    test_text = "我們兩個人要預約鞋和豪師傅"
    analysis = analyzeCustomerCountText(test_text)
    print(f"測試文本: '{test_text}'")
    print(f"最終數量: {analysis['final_count']}")
    print(f"明確數量: {analysis['explicit_count']}")
    print(f"師傅名字數量: {analysis['staff_name_count']}")
    print(f"模式數量: {analysis['pattern_count']}")
    print(f"分析詳情: {analysis['analysis']}")


if __name__ == "__main__":
    test_getCustomerCount()
