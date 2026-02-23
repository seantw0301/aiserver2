"""
驗證蒙在 2025-12-07 的原始排班資料
"""

from core.database import db_config

def verify_schedule_data():
    """檢查資料庫中蒙的原始排班資料"""
    
    staff_name = "蒙"
    target_date = "2025-12-07"
    
    connection = db_config.get_connection()
    if not connection:
        print("無法連接資料庫")
        return
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        query = """
            SELECT * FROM sch 
            WHERE staff_name = %s AND date = %s
        """
        cursor.execute(query, (staff_name, target_date))
        schedule = cursor.fetchone()
        
        if not schedule:
            print(f"未找到 {staff_name} 在 {target_date} 的排班資料")
            return
        
        print(f"=" * 80)
        print(f"{staff_name} 在 {target_date} 的原始排班資料")
        print(f"=" * 80)
        print(f"\nStaff ID: {schedule.get('staff_id')}")
        print(f"Date: {schedule.get('date')}")
        print(f"Status: {schedule.get('status')}")
        
        # TIME_SLOTS 定義
        TIME_SLOTS = [
            '0800', '0830', '0900', '0930', '1000', '1030',
            '1100', '1130', '1200', '1230', '1300', '1330',
            '1400', '1430', '1500', '1530', '1600', '1630',
            '1700', '1730', '1800', '1830', '1900', '1930',
            '2000', '2030', '2100', '2130', '2200', '2230',
            '2300', '2330'
        ]
        
        print(f"\n排班時段詳情:")
        print(f"{'時段':>6} | {'值':>3} | 狀態")
        print("-" * 30)
        
        scheduled_slots = []
        for slot in TIME_SLOTS:
            value = schedule.get(slot, 0)
            status = "✓ 有排班" if value == 1 else "✗ 無排班"
            print(f"{slot[:2]}:{slot[2:]} | {value:>3} | {status}")
            if value == 1:
                scheduled_slots.append(slot)
        
        print(f"\n總結:")
        print(f"有排班的時段: {len(scheduled_slots)} 個")
        if scheduled_slots:
            first_slot = scheduled_slots[0]
            last_slot = scheduled_slots[-1]
            print(f"第一個排班時段: {first_slot[:2]}:{first_slot[2:]}")
            print(f"最後一個排班時段: {last_slot[:2]}:{last_slot[2:]}")
            print(f"\n最後時段 {last_slot[:2]}:{last_slot[2:]} 涵蓋的時間:")
            
            # 計算最後時段的結束時間
            hour = int(last_slot[:2])
            minute = int(last_slot[2:])
            end_minute = minute + 30
            end_hour = hour
            if end_minute >= 60:
                end_hour += 1
                end_minute -= 60
            print(f"  → {last_slot[:2]}:{last_slot[2:]} - {end_hour:02d}:{end_minute:02d}")
            print(f"\n❌ 問題: 如果要支援到 21:55，需要 2130 時段也有排班")
            print(f"   但資料庫中 2130 = {schedule.get('2130', 0)}")
        
    except Exception as e:
        print(f"錯誤: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    verify_schedule_data()
