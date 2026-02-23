# 中文數字轉阿拉伯數字的工具函數
# 用於 handle_time2025 系列文件

# 中文數字對應表
CHINESE_NUMERAL_MAP = {
    '零': 0, '〇': 0, '一': 1, '二': 2, '兩': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
    '十': 10, '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15, '十六': 16, '十七': 17, '十八': 18, '十九': 19,
    '二十': 20, '廿': 20, '卅': 30, '參': 3, '玖': 9
}

def chinese_to_arabic(text):
    """
    將中文數字轉換為阿拉伯數字

    Args:
        text (str): 包含中文數字的字串

    Returns:
        str: 轉換後的字串，中文數字被替換為阿拉伯數字
    """
    if not isinstance(text, str):
        return text

    # 先處理複合數字
    compound_numbers = [
        ('十一', 11), ('十二', 12), ('十三', 13), ('十四', 14), ('十五', 15),
        ('十六', 16), ('十七', 17), ('十八', 18), ('十九', 19), ('二十', 20),
        ('廿', 20), ('卅', 30)
    ]
    for zh, num in compound_numbers:
        text = text.replace(zh, str(num))

    # 單字替換
    for zh, num in CHINESE_NUMERAL_MAP.items():
        text = text.replace(zh, str(num))

    return text