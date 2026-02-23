import re
from datetime import datetime, timedelta
from handle_time2025_date1 import format_date_string_1
from handle_time2025_date2 import format_date_string_2
from handle_time2025_date3 import format_date_string_3
from handle_time2025_date4 import format_date_string_4
from handle_time2025_time1 import format_time_string_1
from handle_time2025_time2 import format_time_string_2
from handle_time2025_time3 import format_time_string_3
from handle_time2025_util import chinese_to_arabic


def parser_date_time(input_string, time_format_type=2):
    date_str= extra_date_string(input_string)
    
    
    # 格式化日期字串
    if date_str :
        #有找到時間字串，將字串由input_string中移除，以免誤判
        input_string = input_string.replace(date_str, '')

        date_str = format_date_string_1(date_str)
        if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            #開始處理 "昨天" "前天""今天""明天""後天" "大後天"
            date_str = format_date_string_2(date_str)
        if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            #開始處理 "X月X日" "X月X號" "X號" "X日" "2025年1月5日" "二零二六年一月五日"
            date_str = format_date_string_3(date_str)
        if not re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            #開始處理 "下週" "下星期" "上週" "上星期""下下週" "下下星期" 
            date_str = format_date_string_4(date_str)
    else :
        date_str = '' 


    time_str= extra_time_string(input_string)

    #格式化時間字串
    if time_str :
        #time_format_type==2 時 為 hh:mm ，time_format_type==3時為 hh:mm:ss
        if time_format_type == 2 :
            if not re.match(r'\d{2}:\d{2}',time_str):
                #處理中文時間字串 X點X分  X點半 X時
                time_str = format_time_string_1(time_str,time_format_type)
            if not re.match(r'\d{2}:\d{2}',time_str):
                time_str = format_time_string_2(time_str,time_format_type)
            #檢查是過去時間，還是未來時間
            if date_str:
                date_str,time_str = format_time_string_3(date_str,time_str,time_format_type)

        else:  #time_format_type == 3
            if not re.match(r'\d{2}:\d{2}:\d{2}',time_str):
                time_str = format_time_string_1(time_str,time_format_type)
            if not re.match(r'\d{2}:\d{2}:\d{2}',time_str):
                time_str = format_time_string_2(time_str,time_format_type)
            #檢查是過去時間，還是未來時間
            if date_str:
                date_str,time_str = format_time_string_3(date_str,time_str,time_format_type)
    else :   
        time_str = '' 
    
    # 驗證日期並調整過期日期
    if date_str and re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        date_str = adjust_past_date(date_str)

    #回傳最後解析成果
    return date_str,time_str

    

def adjust_past_date(date_str):
    """
    判讀日期是否為過去的時間，若為過去時間且超過了180天，則在日期年份加一年
    
    Args:
        date_str: 日期字符串，格式為 YYYY-MM-DD
        
    Returns:
        調整後的日期字符串
    """
    try:
        # 解析日期
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        # 獲取當前時間（午夜時刻）
        now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 計算時間差
        time_diff = now - date_obj
        
        # 如果是過去時間且超過了180天
        if time_diff.days > 180:
            # 將年份加一年
            new_year = date_obj.year + 1
            adjusted_date_str = date_str.replace(str(date_obj.year), str(new_year), 1)
            return adjusted_date_str
        
        return date_str
        
    except Exception as e:
        # 如果解析失敗，返回原始日期字符串
        return date_str


def extra_date_string(input_string):
    # 先檢查完全匹配的關鍵字
    exact_keywords = ["大前天", "前天", "昨天", "昨日", "昨兒", "今天", "今兒", "本日", "這天", "本天", "今日", "明日", "明兒", "明天", "後天", "後日", "大後天", "近日", "近日內", "現在", "立刻", "馬上", "等下", "等一下"]
    for kw in exact_keywords:
        if kw in input_string:
            return kw
    # 然後檢查正則表達式，順序從具體到一般
    patterns = [
        r'下下星期[一二三四五六日]',
        r'下下週[一二三四五六日]',
        r'下星期[一二三四五六日]',
        r'下週[一二三四五六日]',
        r'上星期[一二三四五六日]',
        r'上週[一二三四五六日]',
        r'本星期[一二三四五六日]',
        r'本週[一二三四五六日]',
        r'下個月\d+號',
        r'下個月\d+日',
        r'上個月\d+號',
        r'上個月\d+日',
        r'\d{4}年\d+月\d+日',
        r'明年\d+月\d+日',
        r'去年\d+月\d+日',
        r'今年\d+月\d+日',
        r'後年\d+月\d+日',
        r'明年春節',
        r'去年中秋節',
        r'今年五一勞動節',
        r'後年國慶節',
        r'明年端午節',
        r'去年重陽節',
        r'今年教師節',
        r'後年元旦',
        r'明年七夕節',
        r'去年兒童節',
        r'今年植樹節',
        r'後年婦女節',
        r'明年聖誕節',
        r'去年萬聖節',
        r'今年感恩節',
        r'後年情人節',
        r'明年清明節',
        r'去年元宵節',
        r'今年建黨節',
        r'後年航海日',
        r'明年春分',
        r'去年秋分',
        r'今年冬至',
        r'後年夏至',
        r'\d+月\d+日',
        r'\d+月\d+號',
        r'\d{4}/\d{1,2}/\d{1,2}',  # YYYY/MM/DD
        r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
        r'\d{1,2}/\d{1,2}',        # MM/DD
        r'\d{1,2}-\d{1,2}',         # MM-DD
        r'\d+日',
        r'\d+號'
    ]
    for pattern in patterns:
        match = re.search(pattern, input_string)
        if match:
            return match.group(0)
    return ""

def extra_time_string(input_string):
    # 先將整個字串中的中文數字轉換為阿拉伯數字，這樣正則表達式就能匹配
    converted_string = chinese_to_arabic(input_string)
    
    # 提取字串中，有關時間的字串，使用正則表達式匹配，順序從具體到一般
    patterns = [
        r'\d{1,2}:\d{2}',      # 11:30, 21:00
        r'\d{1,2}am',          # 10am
        r'am\d{1,2}',          # am10
        r'\d{1,2}pm',          # 11pm
        r'pm\d{1,2}',          # pm10
        r'早上\d+點半',        # 早上三點半
        r'早上[一二兩三四五六七八九十]+點半',  # 早上三點半 (中文)
        r'上午\d+點半',        # 上午三點半
        r'上午[一二兩三四五六七八九十]+點半',  # 上午三點半 (中文)
        r'中午\d+點半',        # 中午12點半
        r'中午[一二兩三四五六七八九十]+點半',  # 中午十二點半 (中文)
        r'下午\d+點半',        # 下午3點半
        r'下午[一二兩三四五六七八九十]+點半',  # 下午三點半 (中文)
        r'傍晚\d+點半',        # 傍晚6點半
        r'傍晚[一二兩三四五六七八九十]+點半',  # 傍晚六點半 (中文)
        r'晚上\d+點半',        # 晚上七點半, 晚上8點半
        r'晚上[一二兩三四五六七八九十]+點半',  # 晚上七點半 (中文)
        r'凌晨\d+點半',        # 凌晨3點半
        r'凌晨[一二兩三四五六七八九十]+點半',  # 凌晨三點半 (中文)
        r'清晨\d+點半',        # 清晨5點半
        r'清晨[一二兩三四五六七八九十]+點半',  # 清晨五點半 (中文)
        r'深夜\d+點半',        # 深夜12點半
        r'深夜[一二兩三四五六七八九十]+點半',  # 深夜十二點半 (中文)
        r'午夜\d+點半',        # 午夜1點半
        r'午夜[一二兩三四五六七八九十]+點半',  # 午夜一點半 (中文)
        r'早上\d+點',          # 早上三點
        r'早上[一二兩三四五六七八九十]+點',    # 早上三點 (中文)
        r'上午\d+點',          # 上午三點
        r'上午[一二兩三四五六七八九十]+點',    # 上午三點 (中文)
        r'中午\d+點',          # 中午12點
        r'中午[一二兩三四五六七八九十]+點',    # 中午十二點 (中文)
        r'中午',                # 中午（默認12點）
        r'下午\d+點',          # 下午3點
        r'下午[一二兩三四五六七八九十]+點',    # 下午三點 (中文)
        r'傍晚\d+點',          # 傍晚6點
        r'傍晚[一二兩三四五六七八九十]+點',    # 傍晚六點 (中文)
        r'晚上\d+點',          # 晚上七點, 晚上8點
        r'晚上[一二兩三四五六七八九十]+點',    # 晚上七點 (中文)
        r'凌晨\d+點',          # 凌晨3點
        r'凌晨[一二兩三四五六七八九十]+點',    # 凌晨三點 (中文)
        r'清晨\d+點',          # 清晨5點
        r'清晨[一二兩三四五六七八九十]+點',    # 清晨五點 (中文)
        r'深夜\d+點',          # 深夜12點
        r'深夜[一二兩三四五六七八九十]+點',    # 深夜十二點 (中文)
        r'午夜\d+點',          # 午夜1點
        r'午夜[一二兩三四五六七八九十]+點',    # 午夜一點 (中文)
        r'\d+點半',            # 一點半
        r'[一二兩三四五六七八九十]+點半',      # 三點半 (中文)
        r'\d+點',              # 二點, 十一點
        r'[一二兩三四五六七八九十]+點',        # 三點 (中文)
        r'早上',                # 早上（默認9點）
        r'上午',                # 上午（默認9點）
        r'下午',                # 下午（默認13點）
        r'傍晚',                # 傍晚（默認17點）
        r'晚上',                # 晚上（默認18點）
        r'凌晨',                # 凌晨（默認1點）
        r'清晨',                # 清晨（默認6點）
        r'深夜',                # 深夜（默認22點）
        r'午夜',                # 午夜（默認24點）
        # 中文數字時間（在轉換後應該不會匹配了）
        r'(?:^|[^一二兩三四五六七八九十])([一二兩三四五六七八九十]+點半)(?:[^一二兩三四五六七八九十]|$)',  # 一點半, 兩點半
        r'(?:^|[^一二兩三四五六七八九十])([一二兩三四五六七八九十]+點)(?:[^一二兩三四五六七八九十]|$)',    # 一點, 兩點, 十點
    ]
    for pattern in patterns:
        match = re.search(pattern, converted_string)
        if match:
            if pattern.startswith(r'(?:^|[^一二兩三四五六七八九十])') and pattern.endswith(r'(?:[^一二兩三四五六七八九十]|$)'):
                matched_str = match.group(1)  # For patterns with capture groups
            else:
                matched_str = match.group(0)
            if pattern == r'am\d{1,2}':
                num = re.search(r'\d+', matched_str).group(0)
                return num + 'am'
            elif pattern == r'pm\d{1,2}':
                num = re.search(r'\d+', matched_str).group(0)
                return num + 'pm'
            else:
                return matched_str
    return ""