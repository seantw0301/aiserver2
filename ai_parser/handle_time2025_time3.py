import datetime

def format_time_string_3(date_str, time_str, time_format_type):
    """
    根據日期與時間組合，判斷是否為過去時間，若是則將時間+12小時直到大於等於現在時間。
    若已是未來時間則不修改，直接返回。
    """
    try:
        if time_format_type == 3:
            dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        else:
            dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    except Exception:
        # 格式不符，直接返回原值
        return date_str, time_str

    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")

    # 僅當日期為今天時才進行+12小時調整
    if date_str == today_str:
        if dt >= now:
            return date_str, time_str
        while dt < now:
            dt += datetime.timedelta(hours=12)
        date_str = dt.strftime("%Y-%m-%d")
        if time_format_type == 3:
            time_str = dt.strftime("%H:%M:%S")
        else:
            time_str = dt.strftime("%H:%M")
        return date_str, time_str
    else:
        # 非今天的日期，原封不動返回
        return date_str, time_str
