import re
from datetime import datetime, timedelta

def format_date_string_4(date_str):
    """
    處理 "下週" "下星期" "上週" "上星期" "下下週" "下下星期" 相關字串，轉為標準日期格式。
    若無法解析則原樣返回。
    """
    now = datetime.now()
    original_text = date_str
    cleaned_text = date_str.replace(' ', '')

    weekday_patterns = [
        r'下下\s*(?:星期|週|周)([一二三四五六日天1234567])',  # 下下星期X
        r'下\s*(?:星期|週|周)([一二三四五六日天1234567])',     # 下星期X
        r'上\s*(?:星期|週|周)([一二三四五六日天1234567])',     # 上星期X
        r'(?:這|这|本)\s*(?:星期|週|周)([一二三四五六日天1234567])',  # 這星期X/本週X
        r'(?:星期|週|周)([一二三四五六日天1234567])',  # 星期X/週X/周X（無前綴）
        r'禮拜([一二三四五六日天1234567])',  # 禮拜X
    ]
    weekday_map = {
        '一': 0, '1': 0,
        '二': 1, '2': 1,
        '三': 2, '3': 2,
        '四': 3, '4': 3,
        '五': 4, '5': 4,
        '六': 5, '6': 5,
        '日': 6, '天': 6, '7': 6
    }
    for pattern in weekday_patterns:
        weekday_match = re.search(pattern, original_text) or re.search(pattern, cleaned_text)
        if weekday_match:
            match_text = weekday_match.group(0)
            weekday_char = weekday_match.group(1)
            target_weekday = weekday_map.get(weekday_char)
            if target_weekday is not None:
                current_weekday = now.weekday()
                # 下下星期
                if "下下星期" in match_text or "下下周" in match_text or "下下週" in match_text:
                    days_to_sunday = (6 - current_weekday) % 7
                    if days_to_sunday == 0:
                        days_to_sunday = 7
                    weekday_offset = 7 + target_weekday + 1
                    days_ahead = days_to_sunday + weekday_offset
                # 下星期
                elif "下星期" in match_text or "下周" in match_text or "下週" in match_text:
                    # 計算到下星期目標星期的天數
                    days_ahead = (target_weekday - current_weekday + 7) % 7
                    if days_ahead == 0:
                        days_ahead = 7  # 如果是同一天，則是下一週的同一天
                # 上星期
                elif "上星期" in match_text or "上周" in match_text or "上週" in match_text:
                    days_behind = (current_weekday - target_weekday) % 7
                    if days_behind == 0:
                        days_behind = 7
                    days_ahead = -days_behind
                else:
                    # 默認本週
                    days_ahead = (target_weekday - current_weekday) % 7
                result_date = now + timedelta(days=days_ahead)
                return result_date.strftime('%Y-%m-%d')
    return date_str
