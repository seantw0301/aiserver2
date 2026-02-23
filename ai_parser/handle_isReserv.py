import re
import traceback

def isReservation(text, debug=False):
    """
    判斷自然語言是否為預約的需求
    
    參數:
        text: 用戶輸入的自然語言文本
        debug: 是否打印調試信息
        
    返回:
        bool: 如果是預約需求則返回 True，否則返回 False
    """
    try:
        # 將文本轉換為小寫，以便於不區分大小寫進行匹配
        text_lower = text.lower()
        
        # 預約相關的關鍵詞
        reservation_keywords = [
            '預約', '約', '訂', '排', '安排', '登記', 
            '預訂', '預定', '預排', '空位', '時段',
            '幾點', '什麼時候', '哪個時間', '幾號',
            '可以來', '要來', '想來', '安排時間','還有時間','分鐘可以','分可以',
            '不指定','都可以',"都可","任何師","會按","按比較","比較會","重"
        ]
        
        # 服務相關的關鍵詞
        service_keywords = [
            '按摩', '推拿', '泰式', '腳底', '足底', '課程',
            '精油', '芳療', '身體', '全身', '局部', '足療',
            '護理', '療程', '體驗', '臉部', '美容', '紓壓',
            '舒壓', '放鬆', '疏通', '穴位', '指壓'
        ]
              
        # 計算關鍵詞匹配數量
        reservation_score = 0
        matched_reservation_keywords = []
        for keyword in reservation_keywords:
            if keyword in text_lower:
                reservation_score += 1
                matched_reservation_keywords.append(keyword)
        
        service_score = 0
        matched_service_keywords = []
        for keyword in service_keywords:
            if keyword in text_lower:
                service_score += 1
                matched_service_keywords.append(keyword)
        
        
        # 根據各類關鍵詞得分判斷是否為預約需求
        # 預約關鍵詞至少1個 + (時間關鍵詞或日期關鍵詞至少1個) + 服務關鍵詞至少1個
        is_reservation = (reservation_score > 0 or service_score > 0)
               
        # 處理問詢可用時段的情況
        availability_keywords = ['有空', '有位', '可以預約', '還有位', '還有空', '時段', '可以嗎']
        availability_score = 0
        matched_availability_keywords = []
        for keyword in availability_keywords:
            if keyword in text_lower:
                availability_score += 1
                matched_availability_keywords.append(keyword)
        
        if availability_score > 0 :
            is_reservation = True
            
        # 處理查詢師傅可用性的情況
        staff_keywords = ['師傅', '師父', '老師']
        time_keywords = ['點', '時', '下午', '上午', '晚上', '中午', '早上', '凌晨']
        has_staff = any(keyword in text_lower for keyword in staff_keywords)
        has_time = any(keyword in text_lower for keyword in time_keywords)
        
        # 如果包含師傅+時間+可以，則視為預約查詢
        if has_staff and has_time and '可以' in text_lower:
            is_reservation = True
            
        # 處理週一/特定時間+服務的情況
        weekday_patterns = [r'週一|週二|週三|週四|週五|週六|週日|星期一|星期二|星期三|星期四|星期五|星期六|星期日']
        has_weekday = any(re.search(pattern, text_lower) for pattern in weekday_patterns)
        if has_weekday and service_score > 0 and ("可以" in text_lower or "嗎" in text_lower):
            is_reservation = True
            
        # 處理包含具體時間數字+服務的情況
        time_number_pattern = r'\d{3,4}'  # 匹配 "1830", "330" 等數字時間
        has_time_number = bool(re.search(time_number_pattern, text_lower))
        if has_time_number and service_score > 0 and ("可以" in text_lower or "嗎" in text_lower):
            is_reservation = True
            
        
        return is_reservation
    
    except Exception as e:
        print(f"判斷預約需求時發生錯誤: {e}")
        traceback.print_exc()
        return False


# 測試函數
def test_isReservation():
    test_cases = [
        # 明確的預約請求
        "我想預約明天下午3點的按摩",
        "請幫我安排週五晚上的足底按摩",
        "我要訂後天早上的精油按摩",
        "有沒有明天的空位？我想做全身按摩",
        "下週三有沒有泰式按摩的時段？",
        
        # 非預約請求
        "按摩的價格是多少？",
        "你們提供什麼服務？",
        "營業時間是幾點到幾點？",
        "請問在哪裡可以停車？",
        "你們接受信用卡嗎？",
        
        # 我們的測試用例
        "唐師父，週一還有按摩時間嗎？",
        "週一可以安排1830的足底按摩嗎？",
        "西門店預約鞋或川師傅的精油按摩",
        "60分鐘的全身按摩可以嗎?"
    ]
    
    print("=== 預約判斷測試 ===")
    for i, case in enumerate(test_cases):
        result = isReservation(case, debug=True)
        print(f"{i+1}. 輸入: '{case}'")
        print(f"   結果: {'是預約需求' if result else '不是預約需求'}")
    
    print("=== 測試完成 ===")


if __name__ == "__main__":
    # 執行測試
    test_isReservation()
