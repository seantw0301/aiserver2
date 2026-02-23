#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試腳本：檢查師傅名稱映射是否正確
"""

from core.database import db_config
from modules.multilang import get_staff_name_mapping, get_store_name_mapping

def check_database_staffs():
    """直接查詢資料庫檢查Staffs表數據"""
    try:
        connection = db_config.get_connection()
        if not connection:
            print("❌ 無法連接資料庫")
            return
        
        cursor = connection.cursor(dictionary=True)
        
        # 查詢所有師傅
        query = """
            SELECT id, name, staff, storeid, enable 
            FROM Staffs 
            WHERE enable = 1 AND name != ''
            ORDER BY id
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        print("=" * 80)
        print("資料庫中的師傅數據:")
        print("=" * 80)
        print(f"{'ID':<5} {'中文名':<15} {'英文名':<20} {'店ID':<8}")
        print("-" * 80)
        
        for row in results:
            print(f"{row['id']:<5} {row['name']:<15} {str(row['staff']):<20} {row['storeid']:<8}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 查詢資料庫錯誤: {e}")


def check_staff_mapping():
    """檢查 get_staff_name_mapping() 返回的映射"""
    print("\n" + "=" * 80)
    print("get_staff_name_mapping() 返回的映射:")
    print("=" * 80)
    
    mapping = get_staff_name_mapping()
    
    if not mapping:
        print("❌ 無法獲取師傅名稱映射")
        return
    
    print(f"總共 {len(mapping)} 個映射:")
    print("-" * 80)
    for chinese_name, english_name in mapping.items():
        print(f"中文: {chinese_name:<15} -> 英文: {english_name}")


def check_store_mapping():
    """檢查 get_store_name_mapping() 返回的映射"""
    print("\n" + "=" * 80)
    print("get_store_name_mapping() 返回的映射:")
    print("=" * 80)
    
    mapping = get_store_name_mapping()
    
    if not mapping:
        print("❌ 無法獲取店家名稱映射")
        return
    
    print(f"總共 {len(mapping)} 個映射:")
    print("-" * 80)
    for chinese_name, english_name in mapping.items():
        print(f"中文: {chinese_name:<15} -> 英文: {english_name}")


def check_placeholder_mapping():
    """檢查佔位符映射是否混淆師傅和店家"""
    print("\n" + "=" * 80)
    print("檢查佔位符映射（師傅和店家區分）:")
    print("=" * 80)
    
    from modules.multilang import extract_and_replace_names
    
    staff_mapping = get_staff_name_mapping()
    store_mapping = get_store_name_mapping()
    
    # 測試文本包含師傅名和店家名
    test_text = "鞋師傅在西門店有空，獻師傅在延吉店也可以"
    
    print(f"原始文本: {test_text}")
    print(f"\n師傅映射: {staff_mapping}")
    print(f"店家映射: {store_mapping}")
    
    modified_text, placeholder_map = extract_and_replace_names(test_text, staff_mapping, store_mapping)
    
    print(f"\n修改後的文本: {modified_text}")
    print(f"\n佔位符映射:")
    for placeholder, (chinese_name, english_name) in placeholder_map.items():
        print(f"  {placeholder}: 中文={chinese_name}, 英文={english_name}")


if __name__ == '__main__':
    check_database_staffs()
    check_staff_mapping()
    check_store_mapping()
    check_placeholder_mapping()
