import re
from datetime import datetime
from handle_time2025_util import chinese_to_arabic

def format_date_string_3(date_str):
    """
    處理 "X月X日" "X月X號" "X號" "X日" 以及包含年份的格式如 "2025年1月5日" "二零二六年一月五日"
    預設為當前年份，如果是過去時間且在過去6個月內，則年份+1
    支持阿拉伯數字和中文數字
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # 先將中文數字轉換為阿拉伯數字
    processed_str = chinese_to_arabic(date_str)

    # 匹配模式，現在都是阿拉伯數字
    patterns = [
        (r'(\d{4})年(\d+)月(\d+)日', lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),  # 年 月 日
        (r'(\d{4})年(\d+)月(\d+)號', lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),  # 年 月 號
        (r'(\d+)月(\d+)日', lambda m: (current_year, int(m.group(1)), int(m.group(2)))),            # 月 日 (本年)
        (r'(\d+)月(\d+)號', lambda m: (current_year, int(m.group(1)), int(m.group(2)))),            # 月 號 (本年)
        (r'(\d+)日', lambda m: (current_year, current_month, int(m.group(1)))),                     # 日 (本月本年)
        (r'(\d+)號', lambda m: (current_year, current_month, int(m.group(1)))),                     # 號 (本月本年)
    ]

    for pattern, extractor in patterns:
        match = re.match(pattern, processed_str)
        if match:
            year, month, day = extractor(match)
            try:
                # 構造日期
                date = datetime(year, month, day)
                # 對於沒有指定年份的日期，如果已經過去，則年份+1
                if date < now and year == current_year:
                    date = date.replace(year=year + 1)
                return date.strftime('%Y-%m-%d')
            except ValueError:
                # 無效日期，如2月30日
                return date_str
    # 如果不匹配，返回原字串
    return date_str