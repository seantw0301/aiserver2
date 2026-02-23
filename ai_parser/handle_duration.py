# handle_duration.py
# 療程時長解析模塊
# 負責從用戶輸入中判讀並提取療程時長

import re
from typing import Optional


def _normalize_chinese_numerals(text: str) -> str:
    """
    將中文數字轉換為阿拉伯數字
    例如: "九十分鐘" → "90分鐘"
    """
    # 中文數字映射
    chinese_to_arabic = {
        '零': '0', '一': '1', '二': '2', '三': '3', '四': '4',
        '五': '5', '六': '6', '七': '7', '八': '8', '九': '9',
        '十': '10', '兩': '2'
    }
    
    result = text
    
    # 處理 "九十"、"六十" 等複合數字
    for chinese_num in ['一', '二', '三', '四', '五', '六', '七', '八', '九']:
        # 處理 "X十" 格式（如 "九十" → "90"）
        result = re.sub(f'{chinese_num}十', f'{chinese_to_arabic[chinese_num]}0', result)
    
    # 處理 "兩小時"、"兩小時半" 等
    result = result.replace('兩', '2')
    
    # 處理 "一小時"、"一個半小時" 等單個數字
    for chinese_num, arabic_num in chinese_to_arabic.items():
        result = result.replace(chinese_num, arabic_num)
    
    return result


def extract_duration(text: str) -> Optional[int]:
    """
    從文本中提取療程時長（單位：分鐘）
    
    支持的格式：
    - 中文：60分鐘、90分、120分鐘、一小時、兩小時、一小時半、九十分鐘、六十分鐘
    - 英文：60 mins、90mins、120 mins、1.5hours、1.5 hours
    - 混合：90 mins、60mins
    
    若文本中有多個時長，只返回第一個。
    
    Args:
        text: 用戶輸入的文本
        
    Returns:
        療程時長（分鐘），如果未找到則返回 None
    
    Examples:
        >>> extract_duration("明天90分鐘可以嗎？")
        90
        >>> extract_duration("預約60分鐘")
        60
        >>> extract_duration("一小時的療程")
        60
        >>> extract_duration("120 mins available")
        120
        >>> extract_duration("60分鐘或90分鐘都可以")
        60
    """
    # Debug: 顯示原始輸入
    print(f"[handle_duration] 原始輸入: {text[:100]}...")
    
    # 先移除預設的提示文字，避免誤判
    # 移除各種可能的變體：(90/120mins)、(90/120 mins)、(90/120MINS) 等
    cleaned_text = re.sub(r'\([^\)]*90[^\)]*120[^\)]*mins?\)', '', text, flags=re.IGNORECASE)
    # 也移除單獨的 (90/120mins) 格式
    cleaned_text = re.sub(r'\(90/120\s*mins?\)', '', cleaned_text, flags=re.IGNORECASE)
    
    # Debug: 顯示清理後的文字
    if cleaned_text != text:
        print(f"[handle_duration] 清理後: {cleaned_text[:100]}...")
    
    # 首先標準化中文數字
    normalized_text = _normalize_chinese_numerals(cleaned_text)
    
    # 定義所有支持的時長模式，按優先級排序（最特定的放在前面）
    # 這些模式與 appointment_analysis.py 中的 _extract_project_duration() 保持一致
    patterns = [
        # 特殊格式：冒號後的數字（例如 "project:90", "課程:90", "project:60", "project:120"）
        # 這個要放在最前面，因為是最明確的格式
        # 支援 60, 90, 120 以及其他合理的時長
        (r'(?:project|課程|療程|时长|時長|duration)[:：]\s*(\d+)', lambda m: int(m.group(1))),
        
        # 120 分鐘相關（最長的具體數字，要先匹配以避免被通用模式截取）
        (r'\b120\s*mins?\b', 120),
        (r'\b120分鐘\b', 120),
        (r'\b120分\b', 120),
        (r'\b兩小時\b', 120),
        (r'\b2小時\b', 120),
        # 90 分鐘相關
        (r'\b90\s*mins?\b', 90),
        (r'\b90分鐘\b', 90),
        (r'\b90分\b', 90),
        (r'\b一個半小時\b', 90),
        (r'\b1\.5小時\b', 90),
        # 60 分鐘相關
        (r'\b60\s*mins?\b', 60),
        (r'\b60分鐘\b', 60),
        (r'\b60分\b', 60),
        (r'\b一小時\b', 60),
        (r'\b1小時\b', 60),
        # 其他通用格式（後匹配）
        (r'\b(\d+(?:\.\d+)?)\s*hours?\b', lambda m: int(float(m.group(1)) * 60)),
        (r'\b(\d+)\s*mins?\b', lambda m: int(m.group(1))),
        (r'(\d+)\s*分鐘', lambda m: int(m.group(1))),
        (r'(\d+)\s*分(?!鐘)', lambda m: int(m.group(1))),
        (r'(\d+)\s*小時', lambda m: int(m.group(1)) * 60),
        (r'(\d+)\s*小時\s*半', lambda m: int(m.group(1)) * 60 + 30),
    ]
    
    # 逐個嘗試匹配模式，返回第一個找到的
    for pattern, duration_or_converter in patterns:
        if callable(duration_or_converter):
            # 如果是 lambda 轉換器
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                try:
                    duration = duration_or_converter(match)
                    # 驗證時長在合理範圍內（30-240分鐘）
                    if 30 <= duration <= 240:
                        print(f"[handle_duration] ✓ 找到時長: {duration}分鐘 (pattern: {pattern[:50]}..., matched: {match.group()})")
                        return duration
                except (ValueError, IndexError):
                    continue
        else:
            # 如果直接是分鐘數
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                print(f"[handle_duration] ✓ 找到時長: {duration_or_converter}分鐘 (pattern: {pattern[:50]}..., matched: {match.group()})")
                return duration_or_converter
    
    return None


def is_duration_mentioned(text: str) -> bool:
    """
    檢查文本中是否提到療程時長
    
    Args:
        text: 用戶輸入的文本
        
    Returns:
        True 如果文本中提到療程時長，否則返回 False
    
    Examples:
        >>> is_duration_mentioned("90分鐘療程")
        True
        >>> is_duration_mentioned("明天有空嗎")
        False
    """
    return extract_duration(text) is not None


def get_duration_keyword(text: str) -> Optional[str]:
    """
    獲取文本中提到的療程時長關鍵詞
    
    Args:
        text: 用戶輸入的文本
        
    Returns:
        療程時長關鍵詞（如 "90分鐘"、"120 mins"），未找到則返回 None
    
    Examples:
        >>> get_duration_keyword("我要預約60分鐘")
        "60分鐘"
        >>> get_duration_keyword("120 mins 療程可以嗎")
        "120 mins"
    """
    # 首先標準化中文數字
    normalized_text = _normalize_chinese_numerals(text)
    
    # 所有可能的時長關鍵詞模式
    keyword_patterns = [
        r'\d+(?:\.\d+)?\s*hours?',
        r'\d+\s*mins?',
        r'\d+\s*分鐘',
        r'\d+\s*分(?!鐘)',
        r'\d+\s*小時',
        r'\d+\s*小時\s*半',
        r'一個半小時',
        r'\d+\.?\d*小時',
    ]
    
    for pattern in keyword_patterns:
        match = re.search(pattern, normalized_text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    
    return None


def extract_all_durations(text: str) -> list:
    """
    從文本中提取所有提到的療程時長
    
    Args:
        text: 用戶輸入的文本
        
    Returns:
        療程時長列表（分鐘），如果未找到則返回空列表
    
    Examples:
        >>> extract_all_durations("60分鐘或90分鐘都可以")
        [60, 90]
        >>> extract_all_durations("明天有空嗎")
        []
    """
    durations = []
    
    # 首先標準化中文數字
    normalized_text = _normalize_chinese_numerals(text)
    
    # 定義所有支持的時長模式
    patterns = [
        (r'\b(\d+(?:\.\d+)?)\s*hours?\b', lambda m: int(float(m.group(1)) * 60)),
        (r'\b(\d+)\s*mins?\b', lambda m: int(m.group(1))),
        (r'(\d+)\s*分鐘', lambda m: int(m.group(1))),
        (r'(\d+)\s*分(?!鐘)', lambda m: int(m.group(1))),
        (r'(\d+)\s*小時', lambda m: int(m.group(1)) * 60),
        (r'(\d+)\s*小時\s*半', lambda m: int(m.group(1)) * 60 + 30),
        (r'一個半小時', lambda m: 90),
        (r'1\.5小時', lambda m: 90),
    ]
    
    # 尋找所有匹配
    for pattern, converter in patterns:
        matches = re.finditer(pattern, normalized_text, re.IGNORECASE)
        for match in matches:
            try:
                duration = converter(match)
                # 驗證時長在合理範圍內
                if 30 <= duration <= 240 and duration not in durations:
                    durations.append(duration)
            except (ValueError, IndexError):
                continue
    
    # 按升序排序
    return sorted(durations)


def format_duration(minutes: int) -> str:
    """
    將分鐘轉換為易讀的格式
    
    Args:
        minutes: 分鐘數
        
    Returns:
        格式化的時長字符串（如 "90分鐘"、"1.5小時"）
    
    Examples:
        >>> format_duration(60)
        "1小時"
        >>> format_duration(90)
        "1.5小時"
        >>> format_duration(120)
        "2小時"
    """
    if minutes % 60 == 0:
        hours = minutes // 60
        return f"{hours}小時"
    elif minutes == 90:
        return "1.5小時"
    else:
        return f"{minutes}分鐘"
