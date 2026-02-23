# handle_time_date.py
# 日期解析主要模組

import re
from datetime import datetime, timedelta
try:
    from .handle_time_utils import convert_chinese_numerals_to_arabic
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from handle_time_utils import convert_chinese_numerals_to_arabic


def parse_date(text):
    """解析各種日期格式"""
    now_year = datetime.now().year
    current_year_last_two = now_year % 100

    try:
        # 處理英文月份日期格式: DD Month YYYY 或 DD Mon YYYY
        english_months = {
            'Jan': 1, 'January': 1, 'Feb': 2, 'February': 2, 'Mar': 3, 'March': 3,
            'Apr': 4, 'April': 4, 'May': 5, 'Jun': 6, 'June': 6,
            'Jul': 7, 'July': 7, 'Aug': 8, 'August': 8, 'Sep': 9, 'Sept': 9, 'September': 9,
            'Oct': 10, 'October': 10, 'Nov': 11, 'November': 11, 'Dec': 12, 'December': 12
        }
        english_pattern = r'(\d{1,2})\s+([A-Za-z]+)(?:\s+|,\s*)(\d{4})'
        m = re.search(english_pattern, text)
        if m:
            day = int(m.group(1))
            month_name = m.group(2).capitalize()
            year = int(m.group(3))
            
            # 檢查月份是否有效
            if month_name in english_months:
                month = english_months[month_name]
                if 1 <= day <= 31 and 1 <= month <= 12:
                    try:
                        parsed_date = datetime(year, month, day)
                        print(f"找到英文日期格式: {day} {month_name} {year}，解析為: {year}-{month:02d}-{day:02d}")
                        return parsed_date
                    except ValueError:
                        print(f"無效英文日期: {day} {month_name} {year}")
        
        # 處理ISO格式日期 YYYY-MM-DD
        m = re.search(r"\d{4}-\d{1,2}-\d{1,2}", text)
        if m:
            return datetime.strptime(m.group(), "%Y-%m-%d")

        # 處理標準斜線日期 YYYY/MM/DD
        m = re.search(r"\d{4}/\d{1,2}/\d{1,2}", text)
        if m:
            return datetime.strptime(m.group(), "%Y/%m/%d")
        
        # 處理歐式日期格式 DD/MM/YY 或 DD/MM/YYYY (年份在最後)
        m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{2}|\d{4})(?!\d)", text)
        if m:
            day = int(m.group(1))
            month = int(m.group(2))
            year_str = m.group(3)
            
            # 處理二位數年份 - 只接受與當前年份最後兩位相同的情況
            if len(year_str) == 2:
                year = int(year_str)
                # 嚴格比對：只有當年份與當前年份的最後兩位相同時才接受
                if year == current_year_last_two:
                    year = now_year  # 使用完整的當前年份
                    print(f"檢測到歐式日期格式 {day}/{month}/{year_str}，年份與當前年份最後兩位相符，解析為: {year}-{month:02d}-{day:02d}")
                else:
                    # 年份不匹配，不將其視為歐式日期
                    print(f"檢測到疑似歐式日期格式 {day}/{month}/{year_str}，但年份不與當前年份最後兩位({current_year_last_two})相符，拒絕解析")
                    return None
            else:  # 四位數年份直接使用
                year = int(year_str)
            
            # 確保日期有效
            if 1 <= day <= 31 and 1 <= month <= 12:
                try:
                    date_obj = datetime(year, month, day)
                    print(f"找到歐式日期格式: {day}/{month}/{year}，解析為: {year}-{month:02d}-{day:02d}")
                    return date_obj
                except ValueError:
                    print(f"無效日期: {day}/{month}/{year}")
                    return None

        # 處理常規MM/DD或DD/MM格式 (假設年份為當前年)
        m = re.search(r"\d{1,2}/\d{1,2}(?!/)", text)
        if m:
            # 確保這不是一個被截斷的歐式日期格式
            if not re.search(r"\d{1,2}/\d{1,2}/", text):
                date_parts = m.group().split('/')
                first = int(date_parts[0])
                second = int(date_parts[1])
                
                # 判斷是 MM/DD 還是 DD/MM
                # 如果第一個數字 > 12，肯定是日期，第二個才是月份（DD/MM）
                if first > 12:
                    # DD/MM 格式
                    day = first
                    month = second
                    try:
                        date_obj = datetime(now_year, month, day)
                        print(f"檢測到 DD/MM 格式: {day}/{month}，解析為: {now_year}-{month:02d}-{day:02d}")
                        return date_obj
                    except ValueError:
                        print(f"無效日期: {day}/{month}/{now_year}")
                        return None
                else:
                    # MM/DD 格式（默認美式）
                    month = first
                    day = second
                    try:
                        date_obj = datetime(now_year, month, day)
                        print(f"檢測到 MM/DD 格式: {month}/{day}，解析為: {now_year}-{month:02d}-{day:02d}")
                        return date_obj
                    except ValueError:
                        print(f"無效日期: {month}/{day}/{now_year}")
                        return None

        # 處理中文日期格式
        m = re.search(r"\d{1,2}月\d{1,2}(?:[號日]?)", text)
        if m:
            mm = re.match(r"(\d{1,2})月(\d{1,2})(?:[號日]?)", m.group())
            month = int(mm.group(1))
            day = int(mm.group(2))
            return datetime(now_year, month, day)

    except Exception as e:
        print(f"日期解析錯誤: {e}")
        pass

    return None


def parse_date_component(original_text, cleaned_text, now):
    """處理並解析文本中的日期信息，返回日期字符串或 None """
    
    # 檢查今日相關表達式
    if is_today_expression(original_text, cleaned_text):
        date_result = now.date().strftime('%Y-%m-%d')
        print(f"找到今天相關表達式，設置日期為: {date_result}")
        return date_result
    
    # 嘗試解析日期格式
    parsed_date = parse_date(cleaned_text)
    if parsed_date:
        date_result = parsed_date.strftime('%Y-%m-%d')
        print(f"找到日期: {date_result}")
        return date_result
    
    # 處理星期表達式
    weekday_result = parse_weekday_expression(original_text, cleaned_text, now)
    if weekday_result:
        return weekday_result
    
    # 處理日期格式 MM/DD 或 M/D
    date_format_result = parse_date_format(original_text, cleaned_text, now)
    if date_format_result:
        return date_format_result
    
    # 處理中文日期格式 X月X日
    chinese_date_result = parse_chinese_date_format(cleaned_text, now)
    if chinese_date_result:
        return chinese_date_result
    
    # 檢查關鍵日期詞
    keyword_date_result = parse_date_keywords(original_text, cleaned_text, now)
    if keyword_date_result:
        return keyword_date_result
    
    return None


def is_today_expression(original_text, cleaned_text):
    """檢查是否含有今天相關表達式"""
    today_expressions = [
        r'今\s*[天日]?\b', r'今天', r'今日', r'today',
        r'今\s*[早上午晚夜]', r'今晚', r'今早', r'今上午', r'今下午', r'今夜',  # 今 + 時間限定詞
        r'現在', r'目前', r'當前', r'当前', r'now'
    ]
    
    for pattern in today_expressions:
        if re.search(pattern, cleaned_text, re.IGNORECASE) or re.search(pattern, original_text, re.IGNORECASE):
            return True
    return False


def parse_weekday_expression(original_text, cleaned_text, now):
    """處理星期表達式，返回日期字符串或 None"""
    weekday_patterns = [
        r'下下\s*(?:星期|週|周)([一二三四五六日天1234567])',  # 下下星期X
        r'下\s*(?:星期|週|周)([一二三四五六日天1234567])',     # 下星期X
        r'(?:這|这|本)\s*(?:星期|週|周)([一二三四五六日天1234567])',  # 這星期X/本週X
        r'(?:星期|週|周)([一二三四五六日天1234567])',  # 星期X/週X/周X（無前綴）
        r'禮拜([一二三四五六日天1234567])',  # 禮拜X
    ]
    
    for pattern in weekday_patterns:
        weekday_match = re.search(pattern, original_text) or re.search(pattern, cleaned_text)
        
        if weekday_match:
            matched_text = weekday_match.group(0)
            weekday_char = weekday_match.group(1)
            
            # 將中文星期或阿拉伯數字轉換為數字（0=星期一，6=星期日）
            weekday_map = {
                '一': 0, '1': 0,
                '二': 1, '2': 1,
                '三': 2, '3': 2,
                '四': 3, '4': 3,
                '五': 4, '5': 4,
                '六': 5, '6': 5,
                '日': 6, '天': 6, '7': 6
            }
            target_weekday = weekday_map.get(weekday_char)
            
            if target_weekday is not None:
                current_weekday = now.weekday()
                match_text = weekday_match.group(0)
                
                # 計算日期
                date_result = calculate_weekday_date(match_text, current_weekday, target_weekday, now)
                
                # 返回字符串格式的日期
                return date_result.strftime('%Y-%m-%d')
    
    return None


def calculate_weekday_date(match_text, current_weekday, target_weekday, now):
    """計算星期幾對應的日期"""
    if "下下星期" in match_text or "下下周" in match_text or "下下週" in match_text:
        # 計算到最近的星期天的天數
        days_to_sunday = (6 - current_weekday) % 7
        if days_to_sunday == 0:
            days_to_sunday = 7
        
        weekday_offset = 7 + target_weekday + 1
        days_ahead = days_to_sunday + weekday_offset
    elif "下星期" in match_text or "下周" in match_text or "下週" in match_text:
        days_to_sunday = (6 - current_weekday) % 7
        if days_to_sunday == 0:
            days_to_sunday = 7
        
        weekday_offset = target_weekday + 1
        days_ahead = days_to_sunday + weekday_offset
    else:
        days_ahead = (target_weekday - current_weekday) % 7
        
        if current_weekday > target_weekday:
            days_ahead = 7 - (current_weekday - target_weekday)
        else:
            days_ahead = target_weekday - current_weekday
    
    return (now + timedelta(days=days_ahead)).date()


def parse_date_format(original_text, cleaned_text, now):
    """處理日期格式 MM/DD 或 M/D，返回日期字符串或 None"""
    date_pattern = r'(\d{1,2})[/\-](\d{1,2})'
    date_match = re.search(date_pattern, original_text) or re.search(date_pattern, cleaned_text)
    
    if date_match:
        try:
            month = int(date_match.group(1))
            day = int(date_match.group(2))
            
            if 1 <= month <= 12 and 1 <= day <= 31:
                year = now.year
                
                try:
                    parsed_date = datetime(year, month, day).date()
                    
                    if parsed_date < now.date():
                        parsed_date = datetime(year + 1, month, day).date()
                        print(f"日期 {month}/{day} 小於今日，調整為下一年: {parsed_date}")
                    
                    print(f"找到日期格式 {month}/{day}，解析為: {parsed_date}")
                    return parsed_date.strftime('%Y-%m-%d')
                    
                except ValueError:
                    print(f"無效日期: {month}/{day}")
        except ValueError:
            print(f"日期解析失敗: {date_match.group(0)}")
    
    return None


def parse_chinese_date_format(cleaned_text, now):
    """處理中文日期格式 X月X日"""
    text_with_arabic = convert_chinese_numerals_to_arabic(cleaned_text)
    
    chinese_date_pattern = r'(\d{1,2})月(\d{1,2})日?'
    chinese_date_match = re.search(chinese_date_pattern, text_with_arabic)
    
    if chinese_date_match:
        try:
            month = int(chinese_date_match.group(1))
            day = int(chinese_date_match.group(2))
            
            if 1 <= month <= 12 and 1 <= day <= 31:
                year = now.year
                
                try:
                    parsed_date = datetime(year, month, day).date()
                    
                    if parsed_date < now.date():
                        parsed_date = datetime(year + 1, month, day).date()
                        print(f"日期 {month}月{day}日 小於今日，調整為下一年: {parsed_date}")
                    
                    print(f"找到中文日期格式 {month}月{day}日，解析為: {parsed_date}")
                    return parsed_date.strftime('%Y-%m-%d')
                    
                except ValueError:
                    print(f"無效日期: {month}月{day}日")
        except ValueError:
            print(f"日期解析失敗: {chinese_date_match.group(0)}")
    
    return None


def parse_date_keywords(original_text, cleaned_text, now):
    """檢查關鍵日期詞"""
    # 處理純日期關鍵詞 (包括 今天/今晚/今早/今上午/今下午 等)
    if re.search(r'今[天日晚早上午下夜]|今\b|目前', original_text) or re.search(r'今[天日晚早上午下夜]|今\b|目前', cleaned_text):
        date_result = now.date().strftime('%Y-%m-%d')
        print(f"找到'今天'关键词，日期设为: {date_result}")
        return date_result
    elif re.search(r'明[天日]|明天\b', original_text) or re.search(r'明[天日]|明天\b', cleaned_text):
        date_result = (now + timedelta(days=1)).date().strftime('%Y-%m-%d')
        print(f"找到'明天'关键词，日期设为: {date_result}")
        return date_result
    elif re.search(r'昨[天日]|昨\b', original_text) or re.search(r'昨[天日]|昨\b', cleaned_text):
        date_result = (now - timedelta(days=1)).date().strftime('%Y-%m-%d')
        print(f"找到'昨天'关键词，日期设为: {date_result}")
        return date_result
    elif re.search(r'後[天日]|后[天日]', original_text) or re.search(r'後[天日]|后[天日]', cleaned_text):
        date_result = (now + timedelta(days=2)).date().strftime('%Y-%m-%d')
        print(f"找到'後天'关键词，日期设为: {date_result}")
        return date_result
    # 處理英文日期關鍵詞
    elif re.search(r'\btomorrow\b|tmr\b', original_text, re.IGNORECASE) or re.search(r'\btomorrow\b|tmr\b', cleaned_text, re.IGNORECASE):
        date_result = (now + timedelta(days=1)).date().strftime('%Y-%m-%d')
        print(f"找到'tomorrow/tmr'关键词，日期设为: {date_result}")
        return date_result
    elif re.search(r'\byesterday\b', original_text, re.IGNORECASE) or re.search(r'\byesterday\b', cleaned_text, re.IGNORECASE):
        date_result = (now - timedelta(days=1)).date().strftime('%Y-%m-%d')
        print(f"找到'yesterday'关键词，日期设为: {date_result}")
        return date_result
    elif re.search(r'\bthe day after tomorrow\b', original_text, re.IGNORECASE) or re.search(r'\bthe day after tomorrow\b', cleaned_text, re.IGNORECASE):
        date_result = (now + timedelta(days=2)).date().strftime('%Y-%m-%d')
        print(f"找到'the day after tomorrow'关键词，日期设为: {date_result}")
        return date_result
    
    return None


def parse_direct_datetime_date_part(original_text, cleaned_text, now):
    """解析直接日期+時間表達式中的日期部分"""
    # 日期关键词模式
    date_patterns = [
        (r'(今[天日]|今\b|目前|现在)', 0),
        (r'(明[天日]|明天\b)', 1),
        (r'(昨[天日]|昨\b)', -1),
        (r'(後[天日]|后[天日])', 2),
        (r'(\btomorrow\b|tmr\b)', 1),
        (r'(\byesterday\b)', -1),
        (r'(\bthe day after tomorrow\b)', 2),
    ]
    
    for pattern, days_offset in date_patterns:
        match = re.search(pattern, original_text, re.IGNORECASE) or re.search(pattern, cleaned_text, re.IGNORECASE)
        if match:
            date_result = (now + timedelta(days=days_offset)).date()
            return date_result, days_offset
    
    return None, None


def parse_direct_datetime_combination(original_text, cleaned_text, now, format_datetime_result_func):
    """
    直接解析包含日期+时间数字的表达式，如"今天1400"或"明天9點"
    這是 handle_time_date.py 和 handle_time_time.py 的協作函數
    """
    try:
        from .handle_time_time import parse_direct_datetime_time_part
    except ImportError:
        from handle_time_time import parse_direct_datetime_time_part
    
    # 日期关键词+数字时间模式
    date_time_patterns = [
        # 日期词+4位数字时间 (今天1400)
        (r'(今[天日]|今\b|目前|现在)[\s]*(\d{4})(?!\d)', 0),
        (r'(明[天日]|明天\b)[\s]*(\d{4})(?!\d)', 1),
        (r'(昨[天日]|昨\b)[\s]*(\d{4})(?!\d)', -1),
        (r'(後[天日]|后[天日])[\s]*(\d{4})(?!\d)', 2),
        # 日期词+时间限定词+数字时间 (今晚10pm, 今早8点)
        (r'(今[晚早上午下夜])[\s]*(\d{1,2})(?:\s*(?:pm|PM|點|点|时|時))?', 0),
        (r'(明[晚早上午下夜])[\s]*(\d{1,2})(?:\s*(?:pm|PM|點|点|时|時))?', 1),
        (r'(昨[晚早上午下夜])[\s]*(\d{1,2})(?:\s*(?:pm|PM|點|点|时|時))?', -1),
        (r'(後[晚早上午下夜])[\s]*(\d{1,2})(?:\s*(?:pm|PM|點|点|时|時))?', 2),
        # 日期词+1-2位数字时间 (今天2點)
        (r'(今[天日]|今\b|目前|现在)[\s]*(\d{1,2})(?!\d)(?![/\-\.:：點点時时分])', 0),
        (r'(明[天日]|明天\b)[\s]*(\d{1,2})(?!\d)(?![/\-\.:：點点時时分])', 1),
        (r'(昨[天日]|昨\b)[\s]*(\d{1,2})(?!\d)(?![/\-\.:：點点時时分])', -1),
        (r'(後[天日]|后[天日])[\s]*(\d{1,2})(?!\d)(?![/\-\.:：點点時时分])', 2),
    ]
    
    for pattern, days_offset in date_time_patterns:
        match = re.search(pattern, original_text) or re.search(pattern, cleaned_text)
        if match:
            # 处理日期部分
            date_result = (now + timedelta(days=days_offset)).date()
            time_str = match.group(2)
            
            # 根据关键词设置输出信息
            date_desc = "未知日期"  # 初始化默认值
            if days_offset == 0:
                date_desc = "今天"
            elif days_offset == 1:
                date_desc = "明天"
            elif days_offset == -1:
                date_desc = "昨天"
            elif days_offset == 2:
                date_desc = "后天"
            
            # 处理时间部分 - 使用標準化後的文本
            time_value = parse_direct_datetime_time_part(
                cleaned_text, cleaned_text, now, date_result, time_str
            )
            
            if time_value is not None:
                print(f"找到'{date_desc}'+时间'{time_str}'，解析为: {date_result} {time_value}")
            
            # 创建并返回结果
            result = format_datetime_result_func(
                original_text, date_result, time_value, now
            )
            return result
    
    return None