# handle_time_time.py
# 時間解析主要模組

import re
from datetime import datetime, timedelta
try:
    from .handle_time_utils import convert_chinese_numerals_to_arabic
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from handle_time_utils import convert_chinese_numerals_to_arabic


def parse_time_component(original_text, cleaned_text, now=None, date_result=None):
    """
    處理並解析文本中的時間信息
    
    統一在最後處理「今天且時間已過需+12小時」的邏輯，簡化各子函數的重複代碼
    
    注意:無偏好關鍵詞的處理已移至 handle_time.py 的 format_datetime_result 函數中
    """
    #將字串中的預設文字去除 '(90/120mins)' 取代為空白''
    # 使用更靈活的正則表達式，匹配可能的變體
    original_text = re.sub(r'\(90/120mins\)', '', original_text, flags=re.IGNORECASE)    
    cleaned_text = re.sub(r'\(90/120mins\)', '', cleaned_text, flags=re.IGNORECASE)

    #如果日期是None 則假定是今天日期
    if date_result is None:
        date_result = datetime.now().date()

    if now is None:
        now = datetime.now()
    
    time_result = None
    
    # 優先處理最具體的時間格式，讓特定格式可以覆蓋通用時間表達式
    # 1. 處理AM/PM格式（最具體，如"10pm"會覆蓋"今晚"）- 已明確指定上下午，不需後續調整
    am_pm_result = parse_am_pm_time(original_text, now, date_result)
    if am_pm_result:
        return am_pm_result
    
    # 2. 處理"X點Y分"格式
    if not time_result:
        time_result = parse_hour_minute_format(cleaned_text, now, date_result)
    
    # 3. 處理標准時間格式 (HH:MM)
    if not time_result:
        time_result = parse_standard_time(original_text, cleaned_text, now, date_result)
    
    # 處理即時時間表達式
    if not time_result:
        time_result = parse_immediate_time(original_text, cleaned_text, now, date_result)
    
    # 處理特定的中文時間表達式模式（通用，如"今晚"會在更具體的格式都失效後才被使用）
    if not time_result:
        time_result = parse_time_period_expression(original_text, cleaned_text, now, date_result)
    
    # 處理特殊時間標籤
    if not time_result:
        time_result = parse_time_label(original_text, now, date_result)
    
    # 處理數字.數字時間格式
    if not time_result:
        time_result = parse_dot_time_format(original_text, cleaned_text, now, date_result)
    
    # 統一處理：如果是今天且時間已過，自動+12小時（僅針對1-11點的時間）
    if time_result:
        time_result = _adjust_time_for_today(time_result, original_text, now, date_result)
    
    return time_result


def _adjust_time_for_today(time_str, original_text, now, date_result):
    """
    統一處理今天已過時間的調整邏輯
    
    邏輯：
    1. 如果時間是1-11點且已過去 → +12小時（如早上10點已過，調整為晚上10點）
    2. 如果時間是12-23點且已過去 → 當前時間+30分鐘（如晚上6點已過，調整為當前+30分）
    
    Args:
        time_str: 時間字符串 (HH:MM 格式)
        original_text: 原始文本
        now: 當前時間
        date_result: 日期結果
        
    Returns:
        調整後的時間字符串
    """
    if not time_str:
        return time_str
    
    # 判斷是否為今天
    is_today = False
    if date_result is not None:
        try:
            if isinstance(date_result, str):
                from datetime import datetime as dt
                date_obj = dt.strptime(date_result, '%Y-%m-%d').date()
                is_today = date_obj == now.date()
            elif hasattr(date_result, 'date'):
                is_today = date_result.date() == now.date()
            else:
                is_today = date_result == now.date()
        except:
            pass
    
    if not is_today:
        return time_str
    
    # 解析時間字符串
    try:
        time_parts = time_str.split(':')
        if len(time_parts) != 2:
            return time_str
        
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        
        current_hour = now.hour
        current_minute = now.minute
        
        # 檢查時間是否已過（考慮小時和分鐘）
        time_has_passed = hour < current_hour or (hour == current_hour and minute <= current_minute)
        
        if not time_has_passed:
            return time_str
        
        # 檢查是否有明確的上下午標記
        has_period_indicator = re.search(r'(下午|晚上|晚間|夜晚|傍晚|早上|早晨|上午|早|凌晨|清晨|今晚|今早|今中午|今下午)', original_text)
        
        # 情況1: 1-11點的時間已過 → +12小時（轉換為下午/晚上）
        if 1 <= hour <= 11:
            # 但如果有明確的上下午標記，不調整（已經是正確的時段）
            if has_period_indicator:
                return time_str
            
            hour += 12
            print(f"[統一調整] 今天{time_str}已過（當前 {current_hour:02d}:{current_minute:02d}），調整為 {hour:02d}:{minute:02d}")
            
            # ⚠️ 重要：+12小時後再次檢查是否仍已過
            # 例如：當前22:55，10:00+12=22:00，但22:00仍<22:55已過
            adjusted_time_has_passed = hour < current_hour or (hour == current_hour and minute <= current_minute)
            if adjusted_time_has_passed:
                # +12小時後仍已過 → 改為當前時間+30分鐘
                from datetime import timedelta
                adjusted_time = now + timedelta(minutes=30)
                final_hour = adjusted_time.hour
                final_minute = adjusted_time.minute
                print(f"[二次調整] {hour:02d}:{minute:02d}仍已過，改為當前時間+30分鐘: {final_hour:02d}:{final_minute:02d}")
                return f"{final_hour:02d}:{final_minute:02d}"
            
            return f"{hour:02d}:{minute:02d}"
        
        # 情況2: 12-23點的時間已過 → 當前時間+30分鐘
        elif 12 <= hour <= 23:
            # 計算當前時間+30分鐘
            from datetime import timedelta
            adjusted_time = now + timedelta(minutes=30)
            adjusted_hour = adjusted_time.hour
            adjusted_minute = adjusted_time.minute
            
            print(f"[統一調整] 今天{time_str}已過（當前 {current_hour:02d}:{current_minute:02d}），調整為當前時間+30分鐘: {adjusted_hour:02d}:{adjusted_minute:02d}")
            return f"{adjusted_hour:02d}:{adjusted_minute:02d}"
        
    except (ValueError, IndexError):
        pass
    
    return time_str


def parse_hour_minute_format(cleaned_text, now, date_result):
    """處理"X點Y分"格式"""
    # 先處理可能包含的中文數字
    text_with_arabic = convert_chinese_numerals_to_arabic(cleaned_text)
    
    # 改進模式，更好地處理中文時間格式
    # 修改：不允許跨行匹配，使用 [^\n\r] 或限制空白字符為非換行符
    # 只允許同一行內的空白字符（不包括換行符）
    hour_minute_pattern = r'(?<!\d)(\d{1,2})(?:點|点|時|时)(?:(?:[ \t]*)(\d{1,2})(?:[ \t]*)(?:分|分鐘)?)?'
    
    # 按行分割文本，逐行尋找第一個合法的時間格式
    lines = text_with_arabic.split('\n')
    
    for line_num, line in enumerate(lines):
        hour_minute_match = re.search(hour_minute_pattern, line)
        
        if hour_minute_match:
            hour = int(hour_minute_match.group(1))
            original_hour = hour
            minute = 0
            
            # 解析分鐘數
            if hour_minute_match.group(2):
                minute_value = int(hour_minute_match.group(2))
                # 檢查分鐘數是否合法（0-59），如果 >= 60 則視為療程時間，不是時間的分鐘數
                if minute_value >= 60:
                    # 分鐘數 >= 60，視為療程時間，時間的分鐘數設為 0
                    minute = 0
                    print(f"檢測到療程時間: {minute_value}分鐘，時間設為 {hour}")
                else:
                    minute = minute_value
            elif '半' in line:
                # 檢查當前行中是否有 "半" 字（如 "十點半"）
                # 確保 "半" 在時間表達式附近
                match_pos = hour_minute_match.start()
                # 在匹配位置前後5個字符內查找 "半"
                search_start = max(0, match_pos - 5)
                search_end = min(len(line), match_pos + len(hour_minute_match.group(0)) + 5)
                context = line[search_start:search_end]
                if '半' in context:
                    minute = 30
                    print(f"檢測到 '半' 字，設置分鐘為30")
            
            # 先檢查是否明確表示了晚上/下午
            evening_indicators = ['晚上', '晚間', '傍晚', '夜晚', '下午']
            for indicator in evening_indicators:
                if indicator in line:
                    # 如果明確是晚上/下午且小時在1-11範圍內，自動調整為24小時制
                    if 1 <= hour <= 11:
                        hour += 12
                        print(f"因為有'{indicator}'標記，將{original_hour}點直接調整為晚上時段: {hour}點")
                    break
            # 其他情況不在這裡調整，統一由 _adjust_time_for_today 處理
            
            # 確保小時在有效範圍內
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                time_result = f"{hour:02d}:{minute:02d}"
                print(f"[第{line_num+1}行] 找到時間點格式: {original_hour}點{minute}分 -> {time_result}")
                return time_result
    
    return None


def parse_immediate_time(original_text, cleaned_text, now, date_result):
    """處理即時時間表達式"""
    immediate_time_patterns = [
        # 等下/稍後時間表達式
        (r'等下\s*(\d{1,2})\s*[點时]', True),
        (r'稍[侯後后]\s*(\d{1,2})\s*[點时]', True),
        (r'等下\s*(\d{2})(\d{2})', False),
        (r'稍[侯後后]\s*(\d{2})(\d{2})', False),
        (r'一會[兒儿]?\s*(\d{1,2})\s*[點时]', True),
        (r'待會[兒儿]?\s*(\d{1,2})\s*[點时]', True),
        (r'馬上\s*(\d{1,2})\s*[點时]', True),
        (r'即刻\s*(\d{1,2})\s*[點时]', True)
    ]
    
    for pattern, is_hour_only in immediate_time_patterns:
        time_match = re.search(pattern, cleaned_text) or re.search(pattern, original_text)
        if time_match:
            if is_hour_only:
                hour = int(time_match.group(1))
                minute = 0
                
                # 根據當前時間判斷應該是上午還是下午
                current_hour = now.hour
                if 1 <= hour <= 11 and current_hour >= 12:
                    hour += 12
                    print(f"基於當前時間為下午/晚上，將即時時間'{time_match.group(0)}'調整為: {hour}")
                
                time_result = f"{hour:02d}:{minute:02d}"
            else:
                # 處理如 "等下0900" 的情況
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                time_result = f"{hour:02d}:{minute:02d}"
            
            print(f"找到即時時間表達式: '{time_match.group(0)}', 解析為: {time_result}")
            return time_result
    
    return None


def parse_standard_time(original_text, cleaned_text, now, date_result):
    """處理標准時間格式 (HH:MM)，也處理直接的四位數時間表示 (如1400)"""
    # 首先處理標準格式 HH:MM，支持更長的分鐘數以檢測療程時間
    std_time_pattern = r'(\d{1,2})[:\：](\d{2,3})(?:\s*(?:am|pm|a\.m\.|p\.m\.|AM|PM|A\.M\.|P\.M\.)|)'
    std_time_match = re.search(std_time_pattern, original_text) or re.search(std_time_pattern, cleaned_text)
    if std_time_match:
        try:
            hour = int(std_time_match.group(1))
            minute_value = int(std_time_match.group(2))
            
            # 檢查分鐘數是否合法（0-59），如果 >= 60 則視為療程時間，不是時間的分鐘數
            if minute_value >= 60:
                # 分鐘數 >= 60，視為療程時間，時間的分鐘數設為 0
                minute = 0
                print(f"檢測到療程時間: {minute_value}分鐘，時間設為 {hour}")
            else:
                minute = minute_value
            
            # 改進 AM/PM 檢測
            match_text = std_time_match.group(0).lower()
            
            # 檢查匹配的文本是否包含 pm/am
            if 'pm' in match_text and hour < 12:
                hour += 12
                print(f"直接檢測到PM標記，將時間調整為: {hour}:{minute:02d}")
            elif 'am' in match_text and hour == 12:
                hour = 0
                print(f"直接檢測到AM標記，將12點調整為: {hour}:{minute:02d}")
            else:
                # 搜索更廣泛的上下文
                search_range = 20
                match_pos = std_time_match.start()
                search_start = max(0, match_pos - search_range)
                search_end = min(len(original_text.lower()), match_pos + std_time_match.end() + search_range)
                search_text = original_text.lower()[search_start:search_end]
                
                # 檢查上下文中是否有 pm/am 標記
                if re.search(r'\b(?:pm|p\.m\.)\b', search_text) and hour < 12:
                    hour += 12
                    print(f"上下文檢測到PM標記，將時間調整為: {hour}:{minute:02d}")
                elif re.search(r'\b(?:am|a\.m\.)\b', search_text) and hour == 12:
                    hour = 0
                    print(f"上下文檢測到AM標記，將12點調整為: {hour}:{minute:02d}")
                else:
                    # 檢查中文晚上/下午標記（與 parse_time_period_expression 保持一致）
                    evening_indicators = ['晚上', '晚間', '傍晚', '夜晚', '下午', '午後', '今晚', '明晚']
                    is_evening = any(indicator in original_text or indicator in cleaned_text for indicator in evening_indicators)
                    
                    if is_evening and 1 <= hour < 12:
                        hour += 12
                        print(f"檢測到中文晚上/下午時段詞，將{hour-12}:{minute:02d}調整為24小時制: {hour}:{minute:02d}")
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                time_result = f"{hour:02d}:{minute:02d}"
                print(f"找到標準時間格式: {time_result}")
                return time_result
        except ValueError:
            pass
    
    # 然後處理直接的四位數時間 (如1400)
    # 確保不是日期格式中的年份數字
    direct_time_pattern = r'(?<![年/\-\d])(\d{4})(?!\d)'
    direct_time_match = re.search(direct_time_pattern, original_text) or re.search(direct_time_pattern, cleaned_text)
    
    if direct_time_match:
        time_str = direct_time_match.group(1)
        try:
            # 檢查是否為合理的時間值
            hour = int(time_str[:2])
            minute = int(time_str[2:])
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                time_result = f"{hour:02d}:{minute:02d}"
                # print(f"找到四位數直接時間表示: {time_str} -> {time_result}")
                return time_result
        except ValueError:
            pass
            
    return None


def parse_am_pm_time(original_text, now, date_result):
    """處理AM/PM格式"""
    am_pm_patterns = [
        r'\b(?:am|a\.m\.|AM|A\.M\.)\s+(\d{1,2})(?::(\d{2}))?',  # AM 10 或 AM 10:30
        r'\b(?:pm|p\.m\.|PM|P\.M\.)\s+(\d{1,2})(?::(\d{2}))?',  # PM 3 或 PM 3:30
        r'(\d{1,2})(?::(\d{2}))?\s+(?:am|a\.m\.|AM|A\.M\.)',    # 10 AM 或 10:30 AM
        r'(\d{1,2})(?::(\d{2}))?\s+(?:pm|p\.m\.|PM|P\.M\.)',    # 3 PM 或 3:30 PM
        r'(\d{1,2})(?:am|a\.m\.|AM|A\.M\.)',                     # 10am 或 10AM（無空格）
        r'(\d{1,2})(?:pm|p\.m\.|PM|P\.M\.)'                      # 10pm 或 10PM（無空格）
    ]
    
    for i, pattern in enumerate(am_pm_patterns):
        am_pm_match = re.search(pattern, original_text)
        if am_pm_match:
            try:
                hour = int(am_pm_match.group(1))
                minute = 0
                # 只有模式 0-3 有第二个分组（分钟）
                if i < 4 and len(am_pm_match.groups()) > 1 and am_pm_match.group(2):
                    minute_value = int(am_pm_match.group(2))
                    # 檢查分鐘數是否合法（0-59），如果 >= 60 則視為療程時間，不是時間的分鐘數
                    if minute_value >= 60:
                        # 分鐘數 >= 60，視為療程時間，時間的分鐘數設為 0
                        minute = 0
                        print(f"檢測到療程時間: {minute_value}分鐘，時間設為 {hour}")
                    else:
                        minute = minute_value
                
                # 判斷是AM還是PM
                # 模式 0, 1: 空格分隔的 AM/PM
                # 模式 2, 3: 空格分隔的時間 AM/PM
                # 模式 4, 5: 無空格的 AM/PM (10am, 10pm)
                is_pm = False
                if i == 1 or i == 3 or i == 5:  # PM格式
                    is_pm = True
                
                # 調整小時數
                if is_pm and hour < 12:
                    hour += 12
                elif not is_pm and hour == 12:
                    hour = 0
                
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    time_result = f"{hour:02d}:{minute:02d}"
                    print(f"找到AM/PM時間格式: {time_result} ({'PM' if is_pm else 'AM'})")
                    return time_result
            except (ValueError, IndexError):
                continue
    
    return None


def parse_time_label(original_text, now, date_result):
    """處理特殊時間標籤格式"""
    time_label_patterns = [
        r'(?:time|Time|TIME|時間|时间)[：:]\s*(\d{1,4})',
        r'(?:time|Time|TIME|時間|时间)\s+(\d{1,4})',
        r'(?:⏰|⌚)?.*?(?:time|Time|TIME|時間|时间).*?(\d{1,4})',
        r'[\(（]?(?:時間|时间|Time|time)[：:]?[\)）]?\s*(\d{1,4})',
    ]
    
    for pattern in time_label_patterns:
        time_match = re.search(pattern, original_text, re.IGNORECASE)
        if time_match:
            time_digits = time_match.group(1)
            
            # 處理時間格式
            try:
                if len(time_digits) == 4:  # 1900 -> 19:00
                    hour = int(time_digits[:2])
                    minute = int(time_digits[2:])
                elif len(time_digits) == 3:  # 900 -> 9:00
                    hour = int(time_digits[0])
                    minute = int(time_digits[1:])
                elif len(time_digits) <= 2:  # 19 -> 19:00 或 9 -> 9:00
                    hour = int(time_digits)
                    minute = 0
                else:
                    continue  # 無效時間格式
                    
                # 確保小時和分鐘在有效範圍內
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    time_result = f"{hour:02d}:{minute:02d}"
                    print(f"找到特殊格式時間: {time_result}")
                    return time_result
            except ValueError:
                continue
    
    return None


def parse_time_period_expression(original_text, cleaned_text, now, date_result):
    """處理時間段詞和複合表達式"""
    # 轉換中文數字成阿拉伯數字
    text_with_arabic = convert_chinese_numerals_to_arabic(cleaned_text)
    
    # 首先檢查標準時間格式，如果存在則優先處理
    # 檢查是否有標準數字時間格式（如XX:XX），支持更長的分鐘數以檢測療程時間
    std_time_pattern = r'(\d{1,2})[:\：](\d{1,3})'
    std_time_match = re.search(std_time_pattern, original_text) or re.search(std_time_pattern, cleaned_text)
    
    # 檢查是否存在時間段詞
    time_period_words = [
        '早上', '早晨', '上午', '中午', '午餐', '午飯', '下午', '晚上', '晚間', 
        '夜晚', '半夜', '凌晨', '傍晚', '今晚', '今早', '今中午', '今下午',
        '明晚', '明天晚上', '明早', '明天早上', '明天中午', '明天下午'
    ]
    has_period_word = any(word in original_text or word in cleaned_text for word in time_period_words)
    
    # 如果同時存在標準時間和時間段詞，優先使用標準時間
    if std_time_match and has_period_word:
        try:
            hour = int(std_time_match.group(1))
            minute_value = int(std_time_match.group(2))
            
            # 檢查分鐘數是否合法（0-59），如果 >= 60 則視為療程時間，不是時間的分鐘數
            if minute_value >= 60:
                # 分鐘數 >= 60，視為療程時間，時間的分鐘數設為 0
                minute = 0
                print(f"檢測到療程時間: {minute_value}分鐘，時間設為 {hour}")
            else:
                minute = minute_value
            
            # 檢查是否有晚上/下午標記，如果有且小時<12則調整為24小時制
            evening_indicators = ['晚上', '晚間', '傍晚', '夜晚', '下午', '午後', '今晚', '明晚']
            is_evening = any(indicator in original_text or indicator in cleaned_text for indicator in evening_indicators)
            
            if is_evening and 1 <= hour < 12:
                hour += 12
                print(f"檢測到晚上/下午時段詞與具體時間{hour-12}:{minute:02d}，調整為24小時制: {hour}:{minute:02d}")
            
            time_result = f"{hour:02d}:{minute:02d}"
            print(f"找到時間段詞與標準時間格式共存，優先使用標準時間: {time_result}")
            return time_result
        except ValueError:
            pass
    
    # 處理中文時間表示，直接搜索"兩點"或"兩點半"等
    chinese_time_pattern = r'(下午|晚上).*?(兩點|兩時|二點|二時)(?:半)?'
    chinese_time_match = re.search(chinese_time_pattern, original_text)
    
    if chinese_time_match:
        time_period = chinese_time_match.group(1)
        hour = 2  # 基本時間是2點
        minute = 0
        
        # 處理半點
        if '半' in chinese_time_match.group(0):
            minute = 30
            
        # 調整為24小時制
        if time_period in ['下午', '晚上']:
            hour += 12
            
        time_result = f"{hour:02d}:{minute:02d}"
        print(f"找到中文時間表達式: {chinese_time_match.group(0)}, 時間={time_result}")
        return time_result
    
    # 處理"晚上X點"格式 (優先於默認時間處理)
    evening_time_pattern = r'(晚上|晚間|夜晚|傍晚|下午|午後).*?([\d一二兩三四五六七八九十]+)(?:點|点|時|时)(?:(?:(\d{1,2})(?:分|分鐘)?)|半)?'
    evening_match = re.search(evening_time_pattern, text_with_arabic)
    
    if evening_match:
        try:
            hour_str = evening_match.group(2)
            minute = 0
            
            # 處理中文數字
            if not hour_str.isdigit():
                # 將中文數字轉換為阿拉伯數字
                if '兩' in hour_str:
                    hour = 2
                elif '一' in hour_str or '壹' in hour_str:
                    hour = 1
                elif '二' in hour_str or '貳' in hour_str:
                    hour = 2
                elif '三' in hour_str or '參' in hour_str:
                    hour = 3
                elif '四' in hour_str or '肆' in hour_str:
                    hour = 4
                elif '五' in hour_str or '伍' in hour_str:
                    hour = 5
                elif '六' in hour_str or '陸' in hour_str:
                    hour = 6
                elif '七' in hour_str or '柒' in hour_str:
                    hour = 7
                elif '八' in hour_str or '捌' in hour_str:
                    hour = 8
                elif '九' in hour_str or '玖' in hour_str:
                    hour = 9
                elif '十' in hour_str or '拾' in hour_str:
                    hour = 10
                else:
                    print(f"未認識的中文數字: {hour_str}")
                    raise ValueError(f"Unrecognized Chinese numeral: {hour_str}")
            else:
                hour = int(hour_str)
            
            # 處理分鐘數
            if evening_match.group(3):
                minute_value = int(evening_match.group(3))
                # 檢查分鐘數是否合法（0-59），如果 >= 60 則視為療程時間，不是時間的分鐘數
                if 0 <= minute_value <= 59:
                    minute = minute_value
                else:
                    # 分鐘數 >= 60，視為療程時間，時間的分鐘數設為 0
                    minute = 0
                    print(f"檢測到分鐘數 {minute_value} >= 60，視為療程時間而非時間分鐘數")
            elif '半' in evening_match.group(0):
                minute = 30
                
            # 如果是晚上/下午且小時在1-11範圍內，自動調整為24小時制
            if 1 <= hour < 12:
                hour += 12
                
            # 檢查原始字符串中是否明確提到分鐘數
            has_explicit_minutes = False
            if evening_match.group(3) or '半' in evening_match.group(0):
                has_explicit_minutes = True
            
            # 如果只說"X點"而沒有提到分鐘，則將分鐘設為00
            if not has_explicit_minutes:
                minute = 0
                
            # 設置時間
            time_result = f"{hour:02d}:{minute:02d}"
            print(f"找到晚上/下午時間表達式: {evening_match.group(0)}, 時間={time_result}")
            return time_result
        except (ValueError, IndexError) as e:
            print(f"處理晚上/下午時間格式時出錯: {e}")
            # 繼續嘗試其他時間格式
    
    # 處理複合日期時間表達式
    composite_patterns = [
        # 今晚/今天晚上 + 時間
        (r'今(?:天|日)?(?:晚上|晚間|晚|夜[晚間]?).*?(\d{1,2})(?:點|点|時|时)(?:(\d{1,2})(?:分|分鐘)?|半)?', now.date()),
        # 明晚/明天晚上 + 時間
        (r'明(?:天|日)?(?:晚上|晚間|晚|夜[晚間]?).*?(\d{1,2})(?:點|点|時|时)(?:(\d{1,2})(?:分|分鐘)?|半)?', (now + timedelta(days=1)).date()),
        # 後天晚上 + 時間
        (r'[後后](?:天|日)?(?:晚上|晚間|晚|夜[晚間]?).*?(\d{1,2})(?:點|点|時|时)(?:(\d{1,2})(?:分|分鐘)?|半)?', (now + timedelta(days=2)).date()),
    ]
    
    for pattern, _ in composite_patterns:
        match = re.search(pattern, text_with_arabic) or re.search(pattern, original_text)
        if match:
            # 解析時間
            hour = int(match.group(1))
            minute = 0
            
            # 處理分鐘數
            if match.group(2):
                minute = int(match.group(2))
            elif '半' in match.group(0):
                minute = 30
            
            # 檢查原始字符串中是否明確提到分鐘數
            has_explicit_minutes = False
            if match.group(2) or '半' in match.group(0):
                has_explicit_minutes = True
            
            # 如果只說"X點"而沒有提到分鐘，則將分鐘設為00
            if not has_explicit_minutes:
                minute = 0
            
            # 將時間調整為晚上時段 (12小時制 -> 24小時制)
            if 1 <= hour < 12:
                hour += 12
            
            # 設置時間
            time_result = f"{hour:02d}:{minute:02d}"
            print(f"找到複合日期時間表達式: {match.group(0)}, 時間={time_result}")
            return time_result
    
    # 處理時間段詞 - 修改為最低優先級
    # 只有在沒有找到具體時間的情況下，才使用默認時間
    if not std_time_match:  # 確保沒有標準時間格式存在
        time_defaults = {
            '早上': '08:00', '早晨': '07:00', '上午': '10:00', 
            '中午': '12:00', '午餐': '12:00', '午飯': '12:00',
            '下午': '13:00', '晚上': '18:00', '晚間': '19:00', 
            '夜晚': '20:00', '半夜': '00:00', '凌晨': '03:00',
            '傍晚': '17:00', '今晚': '18:00', '今早': '08:00', 
            '今中午': '12:00', '今下午': '13:00',
            '明晚': '18:00', '明天晚上': '18:00', 
            '明早': '08:00', '明天早上': '08:00',
            '明天中午': '12:00', '明天下午': '13:00'
        }
        
        for period, default_time in time_defaults.items():
            if period in original_text or period in cleaned_text:
                # print(f"找到時間段關鍵詞'{period}'，且無具體時間，設置默認時間: {default_time}")
                return default_time
    
    return None


def parse_dot_time_format(original_text, cleaned_text, now, date_result):
    """處理數字.數字格式的時間 (如 6.40 → 06:40)"""
    dot_time_pattern = r'(?<!\d)(\d{1,2})\.(\d{1,2})(?!\d)'
    dot_time_match = re.search(dot_time_pattern, original_text) or re.search(dot_time_pattern, cleaned_text)
    
    if dot_time_match:
        try:
            hour = int(dot_time_match.group(1))
            minute_str = dot_time_match.group(2)
            original_hour = hour
            
            # 處理分鐘格式
            if len(minute_str) == 1:  # 如 "6.4" → "06:40"
                minute = int(minute_str) * 10
            else:  # 如 "6.40" → "06:40"
                minute = int(minute_str)
                if minute > 59:
                    minute = minute % 60
                    print(f"分鐘數超過59，調整為: {minute}")
            
            # 智能判斷上午/下午
            hour = adjust_am_pm(hour, original_text, cleaned_text, now, date_result)
            
            # 確保時間在有效範圍內
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                time_result = f"{hour:02d}:{minute:02d}"
                print(f"找到數字.數字時間格式: {original_hour}.{minute_str} -> {time_result}")
                return time_result
                
        except ValueError:
            pass
    
    return None


def adjust_am_pm(hour, original_text, cleaned_text, now, date_result, appointment_query=None):
    """智能判斷並調整時間為上午或下午"""
    original_hour = hour
    
    # 檢查文本中是否有明確的上下午標記
    am_pm_indicator = None
    if re.search(r'(下午|晚上|晚間|夜晚|傍晚)', original_text) or re.search(r'(下午|晚上|晚間|夜晚|傍晚)', cleaned_text):
        am_pm_indicator = 'pm'
    elif re.search(r'(早上|早晨|上午|早|凌晨|清晨)', original_text) or re.search(r'(早上|早晨|上午|早|凌晨|清晨)', cleaned_text):
        am_pm_indicator = 'am'
    
    # 如果沒有傳入appointment_query參數，自行檢測
    if appointment_query is None:
        appointment_query = re.search(r'有約|有人|有客人|有客戶|有空|有時間|可以|能約|能預約|有沒有', original_text)
    
    # 應用上下午邏輯
    if am_pm_indicator == 'pm' and 1 <= hour <= 11:
        hour += 12
        print(f"根據明確的下午/晚上標記，將{original_hour}點調整為: {hour}點")
    elif am_pm_indicator == 'am':
        # 對於明確的上午標記，保持原小時數
        print(f"根據明確的上午/早上標記，保持時間為: {hour}點")
    # 根據當前時間和日期智能推斷
    else:
        # 將 date_result 轉換為 date 對象進行比較
        is_today = False
        if date_result is not None:
            try:
                if isinstance(date_result, str):
                    from datetime import datetime as dt
                    date_obj = dt.strptime(date_result, '%Y-%m-%d').date()
                    is_today = date_obj == now.date()
                elif hasattr(date_result, 'date'):
                    is_today = date_result.date() == now.date()
                else:
                    is_today = date_result == now.date()
            except:
                pass
        
        if is_today:  # 今天
            current_hour = now.hour
            current_minute = now.minute
            
            # 檢查時間是否已過（小時已過或同小時但分鐘已過）
            if 1 <= hour <= 11:
                # 如果指定的小時已經過了（如現在是14:00，說"10點"）
                if hour < current_hour or (hour == current_hour and 0 < current_minute):
                    hour += 12
                    print(f"今天{original_hour}點已過（當前時間 {current_hour:02d}:{current_minute:02d}），自動調整為晚上時段: {hour}點")
                elif appointment_query:
                    # 有預約查詢關鍵字，即使時間未過也可能是下午
                    hour += 12
                    print(f"詢問預約且為今天，將{original_hour}點調整為晚上時段: {hour}點")
            elif current_hour >= 12 and 1 <= hour <= 11:  # 當前下午，輸入早上時間
                hour += 12
                print(f"當前為下午/晚上，將{original_hour}點調整為晚上時段: {hour}點")
        else:  # 非今天
            # 根據常規時間習慣判斷
            if appointment_query and 1 <= hour <= 6:  # 1-6點更可能指下午/晚上
                hour += 12
                print(f"非今天的預約查詢，將{original_hour}點調整為晚上時段: {hour}點")
    
    return hour
    
    return hour


def parse_direct_datetime_time_part(original_text, cleaned_text, now, date_result, time_str):
    """解析直接日期+時間表達式中的時間部分"""
    time_value = None
    
    if len(time_str) == 4:  # 四位数 (1400)
        hour = int(time_str[:2])
        minute = int(time_str[2:])
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            time_value = f"{hour:02d}:{minute:02d}"
    elif len(time_str) <= 2:  # 一或二位数 (14 或 2)
        hour = int(time_str)
        # 调整时间（上下文判断）
        hour = adjust_am_pm(hour, original_text, cleaned_text, now, date_result)
        if 0 <= hour <= 23:
            time_value = f"{hour:02d}:00"
    
    return time_value


def is_time_query(text):
    """
    檢測是否為時間查詢相關的關鍵詞
    當檢測到這些關鍵詞時，表示用戶在詢問時間相關的資訊
    
    Args:
        text: 用戶輸入的文本
        
    Returns:
        bool: 如果是時間查詢關鍵詞則返回 True，否則返回 False
    """
    time_query_keywords = ['幾點可', '什麼時候', '什麼時侯', '什麼時間', '什時', '幾時']
    return any(keyword in text for keyword in time_query_keywords)


def _is_availability_query(text):
    """
    檢測是否為可用性查詢 (如 "有...時間嗎?")
    
    Args:
        text: 用戶輸入的文本
        
    Returns:
        bool: 如果是可用性查詢則返回 True
    """
    # 檢測 "有...時間嗎?" 的模式
    availability_pattern = r'有.*時間\s*嗎'
    return bool(re.search(availability_pattern, text))


def _should_clear_time_for_availability_query(text):
    """
    檢測是否應該為可用性查詢清空時間字段
    
    如果是模糊的日期查詢（如 "有明日時間嗎?"），清空時間以查詢整天
    如果是明確的時間查詢（如 "有19:00時間嗎?"），保留時間
    
    Args:
        text: 用戶輸入的文本
        
    Returns:
        bool: 如果應該清空時間則返回 True
    """
    # 先檢測是否為可用性查詢
    if not _is_availability_query(text):
        return False
    
    # 優先檢測明確時間的模式 - 這些情況下應該保留時間（先檢測以避免被模糊模式匹配）
    explicit_time_patterns = [
        r'\d{1,2}:\d{2}',  # HH:MM 格式，如 19:00
        r'\d{1,2}\s*(am|pm)',  # 10am, 10pm (不區分大小寫)
        r'\d{1,2}\s*(點|时)',  # 10點、10时
    ]
    
    # 檢查是否有明確的時間表示
    for pattern in explicit_time_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            print(f"DEBUG [可用性查詢]: 檢測到明確時間查詢，保留時間: {text}")
            return False
    
    # 檢測模糊日期/時期的模式 - 這些情況下應該清空時間
    vague_patterns = [
        r'有.*明(天|日|早|晚).*時間',  # 有明天時間、有明日時間、有明早時間、有明晚時間
        r'有.*\d{1,2}/\d{1,2}(?!\:).*時間',  # 有11/30時間 (不包含 11/30:XX 格式)
        r'有.*[周星]期.*時間',  # 有週一時間、有星期一時間
        r'有.*下午(?!\d).*時間',  # 有下午時間 (不包含 下午3:00)
        r'有.*上午(?!\d).*時間',  # 有上午時間 (不包含 上午10:00)
        r'有.*晚上(?!\d).*時間',  # 有晚上時間 (不包含 晚上8:00)
        r'有.*今(天|日)(?!\d).*時間',  # 有今天時間、有今日時間 (不包含 今天10:00)
        r'有.*時間\s*嗎\s*$',  # 純粹的 "有時間嗎?" (最後帶問號)
    ]
    
    # 檢查是否匹配任何模糊模式
    for pattern in vague_patterns:
        if re.search(pattern, text):
            print(f"DEBUG [可用性查詢]: 檢測到模糊日期/時期查詢: {text}")
            return True
    
    # 其他 "有...時間嗎?" 模式預設為清空時間
    return True


def handle_time_query_with_date(text, detected_date=None, now=None):
    """
    當檢測到時間查詢關鍵詞時，根據日期設置適當的時間
    - 如果日期是今天/今日，設置時間為目前時間 + 30 分鐘
    - 如果日期是未來日期（如明天），返回空字符串（表示查詢整天的時段）
    - 如果沒有檢測到日期，返回 None（由調用者決定如何處理）
    
    特別處理可用性查詢（"有...時間嗎?"）：
    - 對於模糊的日期（如"有明日時間嗎?"），清空時間以查詢整天
    - 對於明確的時間（如"有19:00時間嗎?"），保留時間
    
    Args:
        text: 用戶輸入的文本
        detected_date: 解析出的日期字符串 (格式: YYYY/MM/DD 或 YYYY-MM-DD)
        now: 當前時間 (datetime 對象)，默認為 datetime.now()
        
    Returns:
        str: 設置的時間字符串 (格式: HH:MM) 或空字符串，如果無需設置則返回 None
    """
    if now is None:
        now = datetime.now()
    
    # 檢查是否為時間查詢
    if not is_time_query(text):
        return None
    
    # 檢查是否為可用性查詢，且應該清空時間
    if _should_clear_time_for_availability_query(text):
        print(f"DEBUG [時間查詢]: 檢測到可用性查詢 (有...時間嗎?)，清空時間以查詢整天")
        return ""
    
    # 取得今天的日期（支持兩種格式）
    today_yyyymmdd = now.strftime("%Y-%m-%d")
    today_yyyyslashmmdd = now.strftime("%Y/%m/%d")
    
    # 標準化 detected_date 格式（將 / 轉換為 -）
    if detected_date:
        detected_date_normalized = detected_date.replace('/', '-')
    else:
        detected_date_normalized = None
    
    # 檢查日期是否為今天
    is_today = (detected_date == today_yyyymmdd or 
                detected_date == today_yyyyslashmmdd or
                detected_date_normalized == today_yyyymmdd)
    
    # 檢查日期是否明確包含今天、今日等關鍵詞
    today_keywords = ['今天', '今日', '目前', '現在']
    is_today_from_text = any(keyword in text for keyword in today_keywords)
    
    # 如果是今天或文本中有今天相關詞彙，設置時間為目前時間 + 30 分鐘
    if is_today or is_today_from_text:
        future_time = now + timedelta(minutes=30)
        time_str = future_time.strftime("%H:%M")
        print(f"DEBUG [時間查詢]: 檢測到今天查詢，設置時間為: {time_str}")
        return time_str
    
    # 如果日期是未來日期（不是今天），返回空字符串
    if detected_date and not is_today and not is_today_from_text:
        print(f"DEBUG [時間查詢]: 檢測到未來日期查詢 {detected_date}，時間清空")
        return ""
    
    # 如果沒有檢測到日期，返回 None（由調用者決定如何處理）
    return None