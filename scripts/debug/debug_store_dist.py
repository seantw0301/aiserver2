#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
調試腳本：檢查store_distribution數據
"""

import json
from modules.appointment_query import _get_staff_store_distribution

def check_store_distribution():
    """檢查師傅店家分佈數據"""
    date = "2025-12-29"  # 今天的日期
    storeid = 1  # 西門店
    
    print("=" * 80)
    print(f"查詢師傅店家分佈 - 日期: {date}, 店ID: {storeid}")
    print("=" * 80)
    
    distribution = _get_staff_store_distribution(date, storeid)
    
    if not distribution:
        print("❌ 無法獲取師傅店家分佈")
        return
    
    print(f"\n總共 {len(distribution)} 位師傅:")
    print("-" * 80)
    for staff_name, store_ids in distribution.items():
        print(f"師傅: {staff_name:<15} -> 店家IDs: {store_ids}")


if __name__ == '__main__':
    check_store_distribution()
