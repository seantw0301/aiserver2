import re
from datetime import datetime

def format_date_string_1(date_str):
    """
    將日期字串格式化為 YYYY-MM-DD 格式
    """
    # 檢查解析字串date_str是否為isoformat YYYY-MM-DD ,若不是則進行進一步解析
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        # 已是 YYYY-MM-DD 格式
        return date_str
    elif re.match(r'\d{4}/\d{1,2}/\d{1,2}', date_str):
        # YYYY/MM/DD 轉為 YYYY-MM-DD
        parts = date_str.split('/')
        return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    elif re.match(r'\d{1,2}/\d{1,2}', date_str):
        # MM/DD 轉為 YYYY-MM-DD，使用當前年份
        current_year = datetime.now().year
        parts = date_str.split('/')
        return f"{current_year}-{int(parts[0]):02d}-{int(parts[1]):02d}"
    elif re.match(r'\d{1,2}-\d{1,2}', date_str):
        # MM-DD 轉為 YYYY-MM-DD，使用當前年份
        current_year = datetime.now().year
        parts = date_str.split('-')
        return f"{current_year}-{int(parts[0]):02d}-{int(parts[1]):02d}"
    else:
        # 如果不匹配任何格式，返回原字串
        return date_str