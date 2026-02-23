#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
預約確認訊息解析模塊

用於從預約確認訊息中提取療程時長等資訊
支持中英文混合的確認訊息格式

支持的格式：
- "90 mins" / "90分鐘"
- "療程：90分鐘"
- "60 mins" / "60分鐘"
- "120 mins" / "120分鐘"
等等
"""

import re
from typing import Optional, Dict, Any


def extract_duration_from_confirmation(message: str) -> Optional[int]:
    """
    從預約確認訊息中提取療程時長（分鐘）
    
    支持格式：
    - "90 mins"
    - "90分鐘"
    - "療程：90分鐘"
    - "療程：90 mins"
    
    Args:
        message: 預約確認訊息
        
    Returns:
        療程時長（分鐘），如果找不到則返回 None
        
    Example:
        >>> msg = "Booking Confirmed✅Ximen Store\n11/28 Fri 16:15 / 90 mins / 彬 / NT$ 1600"
        >>> extract_duration_from_confirmation(msg)
        90
    """
    if not message:
        return None
    
    # 模式1：英文格式 "90 mins" 或 "90mins"
    match = re.search(r'(\d+)\s*mins\b', message, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # 模式2：中文格式 "90分鐘" 或 "90分"
    match = re.search(r'(\d+)\s*分(?:鐘)?', message)
    if match:
        return int(match.group(1))
    
    # 模式3：帶冒號的格式 "療程：90分鐘" 或 "療程：90 mins"
    match = re.search(r'療程[：:]\s*(\d+)\s*(?:mins|分(?:鐘)?)', message, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # 模式4：斜線分隔的格式 "/ 90 mins /" 或 "/ 90分鐘 /"
    match = re.search(r'/\s*(\d+)\s*(?:mins|分(?:鐘)?)\s*/', message, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    return None


def extract_booking_info(message: str) -> Dict[str, Any]:
    """
    從預約確認訊息中提取完整的預約資訊
    
    Args:
        message: 預約確認訊息
        
    Returns:
        包含以下欄位的字典：
        - duration: 療程時長（分鐘）
        - store: 店家名稱
        - time: 預約時間
        - staff: 師傅名稱
        - price: 價格
        
    Example:
        >>> msg = "Booking Confirmed✅Ximen Store\n11/28 Fri 16:15 / 90 mins / 彬 / NT$ 1600"
        >>> info = extract_booking_info(msg)
        >>> info['duration']
        90
        >>> info['staff']
        '彬'
    """
    result = {
        'duration': None,
        'store': None,
        'time': None,
        'staff': None,
        'price': None
    }
    
    # 提取療程時長
    result['duration'] = extract_duration_from_confirmation(message)
    
    # 提取店家名稱（從 "Ximen Store" 或其他格式）
    store_match = re.search(r'(Ximen|西門|延吉|家樂福)\s*Store?', message, re.IGNORECASE)
    if store_match:
        store_name = store_match.group(1)
        # 統一為中文名稱
        store_mapping = {
            'Ximen': '西門',
            '西門': '西門',
            '延吉': '延吉',
            '家樂福': '家樂福'
        }
        result['store'] = store_mapping.get(store_name, store_name)
    
    # 提取時間（格式如 "11/28 Fri 16:15"）
    time_match = re.search(r'(\d+/\d+\s+\w+\s+\d+:\d+)', message)
    if time_match:
        result['time'] = time_match.group(1)
    
    # 提取師傅名稱（單個中文字或英文名）
    # 在斜線分隔的格式中，師傅名通常在時間和價格之間
    staff_match = re.search(r'/\s*([^\s/]+)\s*/', message)
    if staff_match:
        potential_staff = staff_match.group(1)
        # 過濾掉非師傅名的內容（如時間、price等）
        if not any(x in potential_staff for x in ['mins', 'Fri', 'Mon', 'Tue', 'Wed', 'Thu', 'Sat', 'Sun', '分鐘', '分']):
            result['staff'] = potential_staff
    
    # 提取價格（格式如 "NT$ 1600"）
    price_match = re.search(r'NT\$\s*[\d,]+', message)
    if price_match:
        result['price'] = price_match.group(0)
    
    return result


def validate_booking_duration(confirmation_msg: str, expected_duration: int) -> bool:
    """
    驗證預約確認訊息中的療程時長是否與預期相符
    
    Args:
        confirmation_msg: 預約確認訊息
        expected_duration: 預期的療程時長（分鐘）
        
    Returns:
        True 如果療程時長相符，False 否則
        
    Example:
        >>> msg = "Booking Confirmed✅Ximen Store\n11/28 Fri 16:15 / 90 mins / 彬 / NT$ 1600"
        >>> validate_booking_duration(msg, 90)
        True
        >>> validate_booking_duration(msg, 60)
        False
    """
    actual_duration = extract_duration_from_confirmation(confirmation_msg)
    if actual_duration is None:
        return False
    return actual_duration == expected_duration


if __name__ == '__main__':
    # 測試
    test_msg = """Booking Confirmed✅Ximen Store
11/28 Fri 16:15 / 90 mins / 彬 / NT$ 1600
Please arrive 5 minutes early or on time
Please ring the doorbell upon arrival, then go upstairs directly
For address inquiry, please type "address" 

This store is by appointment only. There are no staff on site, so please do not arrive too early to avoid waiting. Thank you"""
    
    print("=" * 80)
    print("預約確認訊息解析測試")
    print("=" * 80)
    print()
    
    # 測試1: 提取療程時長
    duration = extract_duration_from_confirmation(test_msg)
    print(f"提取的療程時長: {duration} 分鐘")
    assert duration == 90, f"應該是 90 分鐘，但得到 {duration}"
    print("✅ PASS")
    print()
    
    # 測試2: 提取完整資訊
    booking_info = extract_booking_info(test_msg)
    print(f"提取的預約資訊:")
    print(f"  - 店家: {booking_info['store']}")
    print(f"  - 時間: {booking_info['time']}")
    print(f"  - 療程: {booking_info['duration']} 分鐘")
    print(f"  - 師傅: {booking_info['staff']}")
    print(f"  - 價格: {booking_info['price']}")
    print()
    
    # 測試3: 驗證療程時長
    is_valid = validate_booking_duration(test_msg, 90)
    print(f"驗證療程時長 (期望 90 分鐘): {is_valid}")
    assert is_valid, "應該驗證通過"
    print("✅ PASS")
    print()
    
    # 測試4: 驗證錯誤的療程時長
    is_valid = validate_booking_duration(test_msg, 60)
    print(f"驗證療程時長 (期望 60 分鐘): {is_valid}")
    assert not is_valid, "應該驗證失敗"
    print("✅ PASS")
