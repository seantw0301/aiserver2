#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
師傅工具模組
提供師傅名稱映射功能
"""

from core.database import db_config

def getNameMapping():
    """
    獲取師傅名稱映射
    從資料庫查詢師傅資料，返回中文名稱列表和對應的英文名稱列表
    """
    try:
        connection = db_config.get_connection()
        if not connection:
            print("DEBUG [staff_utils]: 無法連接資料庫，使用空列表")
            return [], []
        
        cursor = connection.cursor(dictionary=True)
        
        # 查詢所有啟用的師傅，使用 GROUP BY 確保唯一性和一致性
        query = """
            SELECT name, staff 
            FROM Staffs 
            WHERE enable = 1 AND staff IS NOT NULL AND staff != ''
            GROUP BY staff, name
            ORDER BY staff
        """
        cursor.execute(query)
        staffs = cursor.fetchall()
        
        print(f"DEBUG [staff_utils]: 從資料庫查詢到 {len(staffs)} 位師傅")
        
        # 建立映射 - 所有英文名稱統一轉為大寫
        staff_mapping = {}
        for staff in staffs:
            chinese_name = staff['name']
            english_name = staff['staff']
            # 統一使用大寫英文名稱作為 key
            staff_mapping[english_name.upper()] = chinese_name
        
        cursor.close()
        connection.close()
        
        chinese_names = list(set(staff_mapping.values()))  # 去重
        english_names = list(staff_mapping.keys())
        
        print(f"DEBUG [staff_utils]: 中文名稱列表: {chinese_names}")
        print(f"DEBUG [staff_utils]: 英文名稱列表: {english_names}")
        
        return chinese_names, english_names
        
    except Exception as e:
        print(f"DEBUG [staff_utils]: 查詢師傅資料錯誤: {e}")
        import traceback
        traceback.print_exc()
        return [], []

def getStaffMapping():
    """
    獲取師傅名稱映射字典
    """
    chinese_names, english_names = getNameMapping()
    
    # 重新查詢建立完整映射
    try:
        connection = db_config.get_connection()
        if not connection:
            return {}
        
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT name, staff 
            FROM Staffs 
            WHERE enable = 1 AND staff IS NOT NULL AND staff != ''
            GROUP BY staff, name
            ORDER BY staff
        """
        cursor.execute(query)
        staffs = cursor.fetchall()
        
        staff_mapping = {}
        for staff in staffs:
            chinese_name = staff['name']
            english_name = staff['staff']
            # 統一使用大寫英文名稱作為 key
            staff_mapping[english_name.upper()] = chinese_name
        
        cursor.close()
        connection.close()
        
        return staff_mapping
        
    except Exception as e:
        print(f"DEBUG [staff_utils]: 建立師傅映射錯誤: {e}")
        return {}
