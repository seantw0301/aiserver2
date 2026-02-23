#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試黑名單功能
"""

from core.blacklist import BlacklistManager

def test_blacklist():
    """測試黑名單管理功能"""
    
    # 測試的 LINE ID
    test_line_id = 'U705f4d038fdcca7793b27f3076820c27'
    
    print(f"=" * 60)
    print(f"測試 LINE ID: {test_line_id}")
    print(f"=" * 60)
    
    # 初始化黑名單管理器
    blacklist_mgr = BlacklistManager()
    
    # 測試 1: 檢查是否為超級黑名單
    print(f"\n【測試 1】檢查是否為超級黑名單")
    is_super = blacklist_mgr.is_super_blacklist(test_line_id)
    print(f"結果: {'是' if is_super else '否'}")
    
    # 測試 2: 獲取黑名單師傅列表
    print(f"\n【測試 2】獲取黑名單師傅列表")
    blocked_staffs = blacklist_mgr.getBlockedStaffsList(test_line_id)
    
    if blocked_staffs:
        if is_super:
            print(f"此用戶為超級黑名單，所有師傅都將其列為黑名單")
        print(f"黑名單師傅數量: {len(blocked_staffs)}")
        print(f"黑名單師傅列表:")
        for i, staff in enumerate(blocked_staffs, 1):
            print(f"  {i}. {staff}")
    else:
        print(f"此用戶未被任何師傅列為黑名單")
    
    print(f"\n" + "=" * 60)

if __name__ == '__main__':
    test_blacklist()
