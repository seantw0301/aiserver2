from datetime import datetime

def validate_date_format(date_str: str, format_str: str = '%Y-%m-%d') -> bool:
    """驗證日期格式是否正確"""
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False

def validate_datetime_format(datetime_str: str) -> bool:
    """驗證日期時間格式是否正確（ISO格式）"""
    try:
        datetime.fromisoformat(datetime_str)
        return True
    except ValueError:
        return False
