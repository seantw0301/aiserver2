from datetime import datetime, timedelta

def format_date_string_2(date_str):
    relative_dates = {
        "大前天": -3,
        "前天": -2 , "前日" : -2, 
        "昨天": -1, "昨日": -1, "昨兒": -1, "昨兒個": -1, 
        "今天": 0, "今兒": 0, "今兒個": 0, "本日": 0, "這天": 0, "本天": 0, "今日": 0, "近日": 0, "近日內": 0, "現在": 0, "立刻": 0, "馬上": 0, "等下": 0, "等一下": 0,
        "明天": 1, "明日": 1, "明兒": 1, "明兒個": 1,
        "後天": 2, "後日": 2,
        "大後天": 3
    }
    if date_str in relative_dates:
        days = relative_dates[date_str]
        target_date = datetime.now() + timedelta(days=days)
        return target_date.strftime('%Y-%m-%d')
    else:
        return date_str