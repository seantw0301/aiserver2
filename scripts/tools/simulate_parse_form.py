#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模擬測試：解析預約表單（不需要資料庫）
展示 appointment_analysis.py 應該如何解析您的輸入
"""

import re
from datetime import datetime

def simulate_parse_reservation_form():
    """模擬解析預約表單"""
    
    message = """📝(寫預約表)Reservation form
🏠(選擇店家)Branch:ximen
💪(選三位)masseur:camper
📅(日期)Date:dec 1
⏰(時間)Time:9:30PM
💆‍♂️(課程)Project(90/120mins):90"""
    
    print("=" * 70)
    print("模擬解析預約表單")
    print("=" * 70)
    
    print("\n📝 輸入文字:")
    print("-" * 70)
    print(message)
    print("-" * 70)
    
    # 模擬解析流程
    result = {
        'raw_data': {},
        'query_data': {},
        'has_update': False
    }
    
    print("\n🔍 開始解析各個欄位...\n")
    
    # 1. 解析分店 (handle_branch)
    print("1️⃣ 解析分店:")
    branch_patterns = [
        r'branch\s*:\s*(\w+)',
        r'店家.*?[:：]\s*(\S+)',
        r'(西門|延吉|家樂福)',
    ]
    
    branch = None
    for pattern in branch_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            branch_raw = match.group(1)
            print(f"   找到: {branch_raw}")
            
            # 映射到中文店名
            branch_mapping = {
                'ximen': '西門',
                '西門': '西門',
                'yanji': '延吉',
                '延吉': '延吉',
                'carrefour': '家樂福',
                '家樂福': '家樂福'
            }
            branch = branch_mapping.get(branch_raw.lower(), '西門')
            break
    
    if not branch:
        branch = '西門'  # 預設值
        print(f"   未找到，使用預設值: {branch}")
    else:
        print(f"   ✅ 解析為: {branch}")
    
    result['raw_data']['branch'] = branch
    result['query_data']['branch'] = branch
    
    # 2. 解析師傅 (handle_staff)
    print("\n2️⃣ 解析師傅:")
    masseur_patterns = [
        r'masseur\s*:\s*(\w+)',
        r'師傅.*?[:：]\s*(\S+)',
        r'選.*?位.*?[:：]\s*(\S+)',
    ]
    
    masseur = []
    for pattern in masseur_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            masseur_raw = match.group(1)
            print(f"   找到: {masseur_raw}")
            
            # 映射到中文師傅名
            staff_mapping = {
                'camper': '鞋',
                'CAMPER': '鞋',
                '鞋': '鞋',
                'richard': '川',
                '川': '川',
                'hao': '豪',
                '豪': '豪'
            }
            chinese_name = staff_mapping.get(masseur_raw, masseur_raw)
            if chinese_name:
                masseur = [chinese_name]
            break
    
    if not masseur:
        print(f"   未找到，使用空陣列: []")
    else:
        print(f"   ✅ 解析為: {masseur}")
    
    result['raw_data']['masseur'] = masseur
    result['query_data']['masseur'] = masseur
    
    # 3. 解析日期 (handle_time)
    print("\n3️⃣ 解析日期:")
    date_patterns = [
        r'date\s*:\s*(\w+\s+\d+)',
        r'日期.*?[:：]\s*(\S+)',
        r'(dec\s+\d+)',
    ]
    
    date = None
    for pattern in date_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            date_raw = match.group(1)
            print(f"   找到: {date_raw}")
            
            # 解析 "dec 1" 為 2025-12-01
            if 'dec' in date_raw.lower():
                day = re.search(r'\d+', date_raw).group()
                current_year = datetime.now().year
                date = f"{current_year}-12-{day.zfill(2)}"
            break
    
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')  # 預設今天
        print(f"   未找到，使用預設值: {date}")
    else:
        print(f"   ✅ 解析為: {date}")
    
    result['raw_data']['date'] = date
    result['query_data']['date'] = date
    
    # 4. 解析時間 (handle_time)
    print("\n4️⃣ 解析時間:")
    time_patterns = [
        r'time\s*:\s*(\d+:\d+\s*(?:AM|PM)?)',
        r'時間.*?[:：]\s*(\d+:\d+)',
        r'(\d+:\d+\s*(?:AM|PM))',
    ]
    
    time = None
    for pattern in time_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            time_raw = match.group(1)
            print(f"   找到: {time_raw}")
            
            # 轉換 9:30PM 為 21:30
            if 'PM' in time_raw.upper():
                time_parts = re.search(r'(\d+):(\d+)', time_raw)
                if time_parts:
                    hour = int(time_parts.group(1))
                    minute = time_parts.group(2)
                    if hour != 12:
                        hour += 12
                    time = f"{hour}:{minute}"
            elif 'AM' in time_raw.upper():
                time_parts = re.search(r'(\d+):(\d+)', time_raw)
                if time_parts:
                    hour = int(time_parts.group(1))
                    if hour == 12:
                        hour = 0
                    minute = time_parts.group(2)
                    time = f"{hour:02d}:{minute}"
            else:
                time = time_raw
            break
    
    if not time:
        print(f"   未找到，設為 null")
    else:
        print(f"   ✅ 解析為: {time}")
    
    result['raw_data']['time'] = time
    result['query_data']['time'] = time
    
    # 5. 解析療程 (handle_duration)
    print("\n5️⃣ 解析療程:")
    project_patterns = [
        r'project.*?[:：]\s*(\d+)',
        r'課程.*?[:：]\s*(\d+)',
        r'(\d+)\s*(?:分鐘|mins)',
        r'\((\d+)/\d+mins\)',
    ]
    
    project = None
    for pattern in project_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            project_raw = match.group(1)
            print(f"   找到: {project_raw}")
            project = int(project_raw)
            break
    
    if not project:
        project = 90  # 預設值
        print(f"   未找到，使用預設值: {project}")
    else:
        print(f"   ✅ 解析為: {project} 分鐘")
    
    result['raw_data']['project'] = project
    result['query_data']['project'] = project
    
    # 6. 解析人數 (handle_customer)
    print("\n6️⃣ 解析人數:")
    count_patterns = [
        r'選.*?(\d+).*?位',
        r'(\d+)\s*位',
        r'(\d+)\s*人',
    ]
    
    count = 1  # 預設值
    for pattern in count_patterns:
        match = re.search(pattern, message)
        if match:
            count_raw = match.group(1)
            print(f"   找到: {count_raw} 位")
            count = int(count_raw)
            break
    
    if count == 1:
        print(f"   使用預設值: {count} 位")
    else:
        print(f"   ✅ 解析為: {count} 位")
    
    result['raw_data']['count'] = count
    result['query_data']['count'] = count
    
    # 7. 判斷是否為預約 (handle_isReserv)
    print("\n7️⃣ 判斷是否為預約:")
    reservation_keywords = ['預約', 'reservation', '寫預約表', '訂位']
    is_reservation = any(keyword in message.lower() for keyword in reservation_keywords)
    
    if is_reservation:
        print(f"   ✅ 是預約訊息（包含關鍵詞）")
    else:
        print(f"   ❌ 非預約訊息")
    
    result['query_data']['isReservation'] = is_reservation
    
    # 顯示最終結果
    print("\n" + "=" * 70)
    print("📊 解析結果")
    print("=" * 70)
    
    print("\n🏠 分店:", result['query_data']['branch'])
    print("💪 師傅:", result['query_data']['masseur'])
    print("📅 日期:", result['query_data']['date'])
    print("⏰ 時間:", result['query_data']['time'])
    print("💆 療程:", result['query_data']['project'], "分鐘")
    print("👥 人數:", result['query_data']['count'], "位")
    print("✅ 預約:", "是" if result['query_data']['isReservation'] else "否")
    
    # 驗證
    print("\n" + "=" * 70)
    print("✔️ 驗證")
    print("=" * 70)
    
    checks = [
        ("分店", result['query_data']['branch'] == '西門', '西門'),
        ("師傅", '鞋' in result['query_data']['masseur'], "['鞋']"),
        ("日期", '2025-12-01' in result['query_data']['date'], '2025-12-01'),
        ("時間", result['query_data']['time'] == '21:30', '21:30'),
        ("療程", result['query_data']['project'] == 90, '90'),
        ("預約", result['query_data']['isReservation'], 'True'),
    ]
    
    success_count = 0
    for field, is_correct, expected in checks:
        status = "✅" if is_correct else "❌"
        print(f"{status} {field:6s}: 期待 {expected}")
        if is_correct:
            success_count += 1
    
    print("\n" + "=" * 70)
    if success_count == len(checks):
        print(f"🎉 完美！所有 {len(checks)} 項檢查都通過！")
    else:
        print(f"⚠️ {success_count}/{len(checks)} 項檢查通過")
    print("=" * 70)
    
    return result

if __name__ == '__main__':
    print("\n🔧 模擬 appointment_analysis.py 解析流程")
    print("（不需要資料庫連接）\n")
    
    result = simulate_parse_reservation_form()
    
    print("\n💡 說明:")
    print("   這是模擬解析流程，展示 appointment_analysis.py 應該如何處理您的輸入。")
    print("   實際運行時會：")
    print("   1. 從資料庫獲取師傅名單進行匹配")
    print("   2. 使用更完整的日期/時間解析邏輯")
    print("   3. 將資料存入 Redis 以便後續查詢")
    print()
