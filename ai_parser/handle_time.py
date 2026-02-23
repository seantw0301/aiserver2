# handle_time.py
# 主要入口程式 - 日期時間解析模組

import re
from datetime import datetime, timedelta
try:
    from .handle_time_utils import convert_chinese_numerals_to_arabic, preprocess_text
    from .handle_time_date import parse_date_component
    from .handle_time_time import parse_time_component
except ImportError:
    # 絕對導入作為備選
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from handle_time_utils import convert_chinese_numerals_to_arabic, preprocess_text
    from handle_time_date import parse_date_component
    from handle_time_time import parse_time_component


def round_minutes_to_nearest_five(minutes: int) -> int:
    """
    將分鐘數對齐到最接近的 5 分鐘倍數
    規則：
    - 0-2 → 0
    - 3-7 → 5
    - 8-12 → 10
    - 13-17 → 15
    - 18-22 → 20
    - 23-27 → 25
    - 28-32 → 30
    - 33-37 → 35
    - 38-42 → 40 (特殊：42 → 40，不是 45)
    - 43-47 → 45 (特殊：43 → 45，46 → 45)
    - 48-52 → 50 (特殊：48 → 50，不是 45)
    - 53-57 → 55
    - 58-59 → 0 (下一小時)
    
    Args:
        minutes: 分鐘數 (0-59)
        
    Returns:
        對齐後的分鐘數
    """
    if minutes < 3:
        return 0
    elif minutes < 8:
        return 5
    elif minutes < 13:
        return 10
    elif minutes < 18:
        return 15
    elif minutes < 23:
        return 20
    elif minutes < 28:
        return 25
    elif minutes < 33:
        return 30
    elif minutes < 38:
        return 35
    elif minutes < 43:
        return 40
    elif minutes < 48:
        return 45
    elif minutes < 53:
        return 50
    elif minutes < 58:
        return 55
    else:
        return 0  # 進位到下一小時

def split_into_lines(text):
    """
    前置動作1-3：將要解析的句子，創建一個line array
    將換行符號和空白視為分隔符號，切割為不同單句
    如"11/11 1600",為兩行句子，分別為 "11/11" 及 "1600"
    """
    # 同時考慮換行符號和空白作為分隔符號
    # 先將不同的換行符號標準化為 \n
    normalized = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 將換行符號和空白都視為分隔符號
    # 使用正則表達式分割：連續的空白或換行符號
    lines = re.split(r'[\s\n]+', normalized)
    
    # 移除空白行並返回
    return [line.strip() for line in lines if line.strip()]


def select_best_result(parse_results, now):
    """
    前置動作4：解析的優先權判讀
    日期部分：
    (1) 優先選擇與今天相同的日期
    (2) 若沒有，則選擇未來且最靠近今天的日期（距離越近分數越高）
    
    時間部分：
    (1) 只選擇未過期的時間
    (2) 優先選擇最靠近當前時間的未來時間
    (3) 若結合日期考慮，應該與優選日期相匹配的時間
    
    同時合併多個結果中的日期和時間部分
    """
    if not parse_results:
        return None
    
    today = now.date()
    current_time = now.time()
    
    best_date_result = None
    best_time_result = None
    best_date_score = -1
    best_time_score = -1
    selected_date = None
    
    # 第一步：先選擇最佳日期
    for result in parse_results:
        if result is None:
            continue
        
        # 檢查日期優先級
        if result.get("日期") is not None:
            score = -1
            try:
                date_str = result.get("日期")
                if date_str:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    # 優先權1: 與今天相同的日期
                    if date_obj == today:
                        score = 10000  # 最高分
                    else:
                        # 優先權2: 未來日期中最靠近的
                        days_diff = (date_obj - today).days
                        if days_diff > 0:
                            # 未來日期，天數差越小分數越高
                            # 距離1天 = 5000分，距離2天 = 4999分，以此類推
                            score = 5000 - (days_diff - 1)
                        # 若是過去日期或其他情況，score 保持 -1
                    
                    if score > best_date_score:
                        best_date_score = score
                        best_date_result = result
                        selected_date = date_obj
            except (ValueError, AttributeError):
                pass
    
    # 第二步：根據優選日期，選擇最佳時間
    # 策略：建構日期和時間的邏輯關聯
    # 因為拆分導致日期和時間分開，所以需要查看前後結果以重建關聯
    
    # 構建日期 -> 時間結果的映射
    date_to_times = {}
    date_to_indices = {}  # 記錄日期結果的索引
    time_indices = []  # 記錄時間結果的索引
    
    for idx, result in enumerate(parse_results):
        if result is None:
            continue
        
        date_str = result.get("日期")
        time_str = result.get("時間")
        
        # 將有日期的結果映射起來，並記錄索引
        if date_str is not None:
            if date_str not in date_to_times:
                date_to_times[date_str] = []
                date_to_indices[date_str] = []
            date_to_indices[date_str].append(idx)
        
        # 記錄時間結果的索引
        if time_str is not None:
            time_indices.append(idx)
    
    # 構建時間 -> 最近日期的映射
    time_to_date = {}
    for time_idx in time_indices:
        # 找時間結果之前最近的日期結果
        closest_date = None
        for idx in range(time_idx - 1, -1, -1):
            result = parse_results[idx]
            if result and result.get("日期") is not None:
                closest_date = result.get("日期")
                break
        time_to_date[time_idx] = closest_date
    
    # 優先從優選日期的結果中選擇時間
    selected_date_str = best_date_result.get("日期") if best_date_result else None
    
    # 找所有與優選日期相關聯的時間結果
    candidates_with_date = []
    for time_idx in time_indices:
        if time_to_date.get(time_idx) == selected_date_str:
            candidates_with_date.append(parse_results[time_idx])
    
    # 優先從與優選日期相關聯的時間中選擇；否則從所有時間結果中選擇
    candidates = candidates_with_date if candidates_with_date else [
        parse_results[idx] for idx in time_indices
    ]
    
    for result in candidates:
        if result is None:
            continue
        
        # 檢查時間優先級
        if result.get("時間") is not None:
            score = -1
            try:
                time_str = result.get("時間")
                if time_str:
                    time_obj = datetime.strptime(time_str, '%H:%M:%S').time()
                    
                    # 優先權1: 時間必須有效
                    if 0 <= time_obj.hour <= 23 and 0 <= time_obj.minute <= 59:
                        # 優先權2: 時間未過期
                        is_future = time_obj >= current_time
                        
                        if is_future:
                            # 優先權3: 最靠近當前時間的未來時間
                            time_diff_seconds = (
                                datetime.combine(today, time_obj) - 
                                datetime.combine(today, current_time)
                            ).total_seconds()
                            # 未來時間得分計算：最靠近獲得最高分
                            score = int(10000 / (1 + time_diff_seconds))
                        else:
                            # 時間已過期，不選擇
                            score = -1
                    
                    if score > best_time_score:
                        best_time_score = score
                        best_time_result = result
            except (ValueError, AttributeError):
                pass
    
    # 合併最優日期和時間結果
    if best_date_result or best_time_result:
        final_result = {
            "輸入語句": parse_results[0].get("輸入語句", ""),
        }
        
        # 優先使用最優日期結果
        if best_date_result and best_date_score > -1:
            final_result["日期"] = best_date_result.get("日期")
            final_result["星期"] = best_date_result.get("星期")
        else:
            final_result["日期"] = None
            final_result["星期"] = None
        
        # 使用最優時間結果
        if best_time_result and best_time_score > -1:
            final_result["時間"] = best_time_result.get("時間")
        else:
            final_result["時間"] = None
        
        return final_result
    
    return None
def parse_datetime_phrases_multiline(text):
    """
    解析包含多句的文本
    執行前置動作：
    1. 將要解析的句子，創建一個line array
    2. 將換行符號考慮進來，切割為不同單句
    3. 空白視為換行符號
    4. 解析的優先權判讀
    
    Returns:
        tuple: (result_dict, force_clear_time)
            - result_dict: 包含日期和時間的字典
            - force_clear_time: bool，是否強制清除時間（從最佳結果繼承）
    """
    now = datetime.now()
    
    # 前置動作1-3：分割為多個單句
    lines = split_into_lines(text)
    
    if not lines:
        return None, False
    
    # 解析每一行，收集所有結果
    parse_results = []
    force_clear_time_flags = []
    for line in lines:
        result, force_clear_time = parse_datetime_phrases(line)
        if result:
            parse_results.append(result)
            force_clear_time_flags.append(force_clear_time)
    
    if not parse_results:
        return None, False
    
    # 前置動作4：根據優先權選擇最佳結果
    best_result = select_best_result(parse_results, now)
    
    # 找到最佳結果對應的 force_clear_time
    best_index = parse_results.index(best_result) if best_result in parse_results else 0
    best_force_clear_time = force_clear_time_flags[best_index] if best_index < len(force_clear_time_flags) else False
    
    return best_result, best_force_clear_time


def parse_datetime_phrases(text):
    """解析文本中的日期和時間"""
    original_text = text
    
    # 前置動作1：將所有全型文字轉換成半型文字
    # 前置動作2：將所有中文的數字轉換成阿拉伯數字
    normalized_text = convert_chinese_numerals_to_arabic(text)
    # 進行文本清理
    cleaned_text = preprocess_text(normalized_text)
    now = datetime.now()
    
    # 1. 處理日期部分
    date_result = parse_date_component(
        normalized_text, cleaned_text, now
    )
    
    # 2. 處理時間部分
    time_result = parse_time_component(
        normalized_text, cleaned_text, now, date_result
    )
    
    # 3. 組合最終結果
    result, force_clear_time = format_datetime_result(
        original_text, date_result, time_result, now
    )
    
    # 返回結果和 force_clear_time 標記
    return result, force_clear_time


def format_datetime_result(original_text, date_result, time_result, now):
    """
    格式化並返回解析結果
    
    流程：
    1. 由 handle_time_date.py 取得日期（None 或日期字符串或 date 对象）
    2. 由 handle_time_time.py 取得時間（None 或時間字符串）
    3. 判斷日期是否為今天：
       - 是今天：若time為None，則將time設為現在時間+30分鐘
       - 不是今天：檢查無偏好關鍵詞，決定是否清除時間為None
    
    Returns:
        tuple: (result_dict, force_clear_time)
            - result_dict: 包含日期和時間的字典
            - force_clear_time: bool，是否強制清除時間（日期不是今天且有無偏好關鍵詞）
    """
    # 確保統一格式
    if hasattr(date_result, 'strftime'):  # 如果是 date 对象，转换为字符串
        date_result = date_result.strftime('%Y-%m-%d')
    
    # 日期和時間都是 None，返回空結果（但保持元組格式）
    if date_result is None and time_result is None:
        return None, False  # 返回 (None, False) 而不是單個 None
    
    
    #if date_result is None and time_result is not None:
    #   date_result = now.strftime('%Y-%m-%d')
    #
    
    weekday_names = ['一', '二', '三', '四', '五', '六', '日']
    
    # Step 3: 判斷日期是否為今天
    is_today = False
    if date_result is not None:
        try:
            date_obj = datetime.strptime(date_result, '%Y-%m-%d').date()
            is_today = date_obj == now.date()
        except:
            pass
    else:
        is_today = True
    
    # 初始化 force_clear_time
    force_clear_time = False
    
    if is_today:
        # 是今天：若time為None，則將time設為現在時間+30分鐘
        if time_result is None:
            future_time = now + timedelta(minutes=30)
            # 對齐分鐘到最接近的 5 分鐘倍數
            rounded_minute = round_minutes_to_nearest_five(future_time.minute)
            if rounded_minute == 0 and future_time.minute >= 58:
                future_time = future_time.replace(minute=0) + timedelta(hours=1)
            else:
                future_time = future_time.replace(minute=rounded_minute)
            time_result = future_time.strftime('%H:%M')
    else:
        # 不是今天：檢查無偏好關鍵詞，決定是否清除時間
        
        # 檢查無偏好關鍵詞
        no_preference_keywords = ['班表','排班','不指定', '都可以', '那位師傅','哪位','哪些','那些', '有誰可以', '有那些師父', '誰可以', '其它']
        has_no_preference_keyword = any(keyword in original_text for keyword in no_preference_keywords)
        
        if has_no_preference_keyword and time_result is not None:
            time_result = None
            force_clear_time = True
        elif time_result is not None:
            pass  # 保留具體時間值
        else:
            pass  # time 本來就是 None，保留
    
    # 組裝結果
    result = {
        "輸入語句": original_text,
    }
    
    # 日期處理
    if date_result is not None:
        try:
            date_obj = datetime.strptime(date_result, '%Y-%m-%d').date()
            result["日期"] = date_result
            result["星期"] = f"星期{weekday_names[date_obj.weekday()]}"
        except:
            result["日期"] = None
            result["星期"] = None
    else:
        result["日期"] = None
        result["星期"] = None
        
    # 時間處理：直接使用 time_result（已經是 None 或具體值）
    result["時間"] = time_result
    
    return result, force_clear_time


# ==================== 輔助函數導出（供測試使用） ====================
# 這些函數從內部模組重新導出，以便測試文件可以使用
# 但一般應用程式應該只使用 parse_datetime_phrases 主函數

def is_time_query(text):
    """
    檢測是否為時間查詢相關的關鍵詞
    重新導出自 handle_time_time 模組
    """
    try:
        from .handle_time_time import is_time_query as _is_time_query
        return _is_time_query(text)
    except ImportError:
        from handle_time_time import is_time_query as _is_time_query
        return _is_time_query(text)


def _is_availability_query(text):
    """
    檢測是否為可用性查詢
    重新導出自 handle_time_time 模組
    """
    try:
        from .handle_time_time import _is_availability_query as _is_avail_query
        return _is_avail_query(text)
    except ImportError:
        from handle_time_time import _is_availability_query as _is_avail_query
        return _is_avail_query(text)


def _should_clear_time_for_availability_query(text):
    """
    檢測是否應該為可用性查詢清空時間字段
    重新導出自 handle_time_time 模組
    """
    try:
        from .handle_time_time import _should_clear_time_for_availability_query as _should_clear
        return _should_clear(text)
    except ImportError:
        from handle_time_time import _should_clear_time_for_availability_query as _should_clear
        return _should_clear(text)


# ==================== 內部組件導出（僅供單元測試使用） ====================
# 警告：這些是內部實現細節，不應該在生產代碼中使用
# 僅用於單元測試特定的解析組件

def parse_time_component_test_only(original_text, cleaned_text, now=None, date_result=None):
    """
    時間組件解析函數（僅供測試使用）
    重新導出自 handle_time_time 模組
    
    警告：此函數僅用於單元測試，生產代碼應使用 parse_datetime_phrases
    """
    return parse_time_component(original_text, cleaned_text, now, date_result)


def parse_date_component_test_only(text, now=None):
    """
    日期組件解析函數（僅供測試使用）
    重新導出自 handle_time_date 模組
    
    警告：此函數僅用於單元測試，生產代碼應使用 parse_datetime_phrases
    """
    return parse_date_component(text, now)