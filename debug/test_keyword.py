#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
關鍵字匹配功能測試腳本
測試 keywords 資料表匹配邏輯及回覆訊息
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.keyword import check_keywords_match
from core.database import db_config

def test_keyword_matching():
    """測試關鍵字匹配功能"""
    print("=" * 70)
    print("🧪 關鍵字匹配功能測試")
    print("=" * 70)
    
    # 測試案例：[測試文字, 預期是否匹配, 描述]
    test_cases = [
        # ============================================================
        # 精確匹配 (exact) 測試
        # ============================================================
        {
            "input": "到了",
            "should_match": True,
            "description": "精確匹配：「到了」",
            "expected_keywords": ["按門鈴"]
        },
        {
            "input": "我到了",
            "should_match": False,
            "description": "精確匹配失敗：「我到了」不是「到了」",
            "expected_keywords": None
        },
        
        # ============================================================
        # 包含匹配 (contains) 測試
        # ============================================================
        {
            "input": "請問有60分鐘嗎？",
            "should_match": True,
            "description": "包含匹配：「有60分鐘嗎」",
            "expected_keywords": ["60分鐘", "NT1300"]
        },
        {
            "input": "我到樓下了",
            "should_match": True,
            "description": "包含匹配：「我到樓下」",
            "expected_keywords": ["按門鈴", "師傅"]
        },
        {
            "input": "直接上6樓嗎",
            "should_match": True,
            "description": "包含匹配：「直接上6樓嗎」",
            "expected_keywords": ["準時", "提前5分鐘"]
        },
        {
            "input": "想舒服一點",
            "should_match": True,
            "description": "包含匹配：「想舒服」（色色問題）",
            "expected_keywords": ["正規", "拉黑"]
        },
        
        # ============================================================
        # 正則匹配 (regex) 測試 - 營業時間
        # ============================================================
        {
            "input": "請問營業時間是？",
            "should_match": True,
            "description": "正則匹配：「營業時間」",
            "expected_keywords": ["早上11點", "凌晨"]
        },
        {
            "input": "請問最早時間是幾點？",
            "should_match": True,
            "description": "正則匹配：「最早時間」",
            "expected_keywords": ["早上11點"]
        },
        {
            "input": "開到幾點？",
            "should_match": True,
            "description": "正則匹配：「開到幾點」",
            "expected_keywords": ["凌晨"]
        },
        
        # ============================================================
        # 正則匹配 (regex) 測試 - 價格
        # ============================================================
        {
            "input": "請問價格多少？",
            "should_match": True,
            "description": "正則匹配：「價格」",
            "expected_keywords": ["NT$1,300", "NT$1,600", "NT$2,000"]
        },
        {
            "input": "消費多少錢？",
            "should_match": True,
            "description": "正則匹配：「消費」",
            "expected_keywords": ["NT$1,300"]
        },
        {
            "input": "價錢怎麼算？",
            "should_match": True,
            "description": "正則匹配：「價錢」",
            "expected_keywords": ["60分鐘"]
        },
        
        # ============================================================
        # 正則匹配 (regex) 測試 - 色色問題
        # ============================================================
        {
            "input": "有b2b服務嗎？",
            "should_match": True,
            "description": "正則匹配：「b2b」（優先級10）",
            "expected_keywords": ["正規", "拉黑"]
        },
        {
            "input": "有body to body嗎？",
            "should_match": True,
            "description": "正則匹配：「body to body」",
            "expected_keywords": ["正規", "拉黑"]
        },
        {
            "input": "有額外服務嗎？",
            "should_match": True,
            "description": "正則匹配：「額外服務」",
            "expected_keywords": ["正規", "拉黑"]
        },
        
        # ============================================================
        # 正則匹配 (regex) 測試 - 支付方式
        # ============================================================
        {
            "input": "可以刷卡嗎？",
            "should_match": True,
            "description": "正則匹配：「刷卡」",
            "expected_keywords": ["信用卡", "5%手續費"]
        },
        {
            "input": "收Line Pay嗎？",
            "should_match": True,
            "description": "正則匹配：「linepay」（不分大小寫）",
            "expected_keywords": ["Line Pay", "5%"]
        },
        
        # ============================================================
        # 正則匹配 (regex) 測試 - 師傅資訊
        # ============================================================
        {
            "input": "師傅身高多少？",
            "should_match": True,
            "description": "正則匹配：「身高」",
            "expected_keywords": ["simon", "171", "camper", "180"]
        },
        {
            "input": "師傅體重？",
            "should_match": True,
            "description": "正則匹配：「體重」",
            "expected_keywords": ["68", "78", "72"]
        },
        
        # ============================================================
        # 正則匹配 (regex) 測試 - 優惠折扣
        # ============================================================
        {
            "input": "有學生優惠嗎？",
            "should_match": True,
            "description": "正則匹配：「學生」",
            "expected_keywords": ["100", "折扣"]
        },
        {
            "input": "健身房會員有折扣嗎？",
            "should_match": True,
            "description": "正則匹配：「健身會員」",
            "expected_keywords": ["NTD -100"]
        },
        
        # ============================================================
        # 正則匹配 (regex) 測試 - 按摩內容
        # ============================================================
        {
            "input": "按摩內容包含什麼？",
            "should_match": True,
            "description": "正則匹配：「按摩內容」（優先級50）",
            "expected_keywords": ["指壓", "油壓"]
        },
        {
            "input": "可以只做油壓嗎？",
            "should_match": True,
            "description": "正則匹配：「只做油」",
            "expected_keywords": ["指壓", "油壓", "溝通"]
        },
        
        # ============================================================
        # 英文關鍵字測試
        # ============================================================
        {
            "input": "How much is the price?",
            "should_match": True,
            "description": "英文正則匹配：「price」",
            "expected_keywords": ["NT$1,300", "60Mins"]
        },
        {
            "input": "Do you accept walk in?",
            "should_match": True,
            "description": "英文包含匹配：「walk in」",
            "expected_keywords": ["dont accept", "appointment"]
        },
        {
            "input": "outcall service?",
            "should_match": True,
            "description": "英文包含匹配：「outcall」",
            "expected_keywords": ["無外出服務"]
        },
        
        # ============================================================
        # 無匹配測試
        # ============================================================
        {
            "input": "今天天氣真好",
            "should_match": False,
            "description": "無匹配：一般對話",
            "expected_keywords": None
        },
        {
            "input": "謝謝",
            "should_match": False,
            "description": "無匹配：禮貌用語",
            "expected_keywords": None
        },
    ]
    
    # 執行測試
    passed = 0
    failed = 0
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 70}")
        print(f"📝 測試 {i}: {test['description']}")
        print(f"{'=' * 70}")
        print(f"輸入文字: 「{test['input']}」")
        
        result = check_keywords_match(test['input'])
        
        # 判斷是否匹配
        is_matched = result is not None
        
        print(f"預期匹配: {'是' if test['should_match'] else '否'}")
        print(f"實際匹配: {'是' if is_matched else '否'}")
        
        # 驗證結果
        test_pass = is_matched == test['should_match']
        
        # 如果預期匹配，檢查回覆內容
        if test['should_match'] and is_matched:
            print(f"\n📬 回覆訊息:")
            print(f"{'-' * 70}")
            print(result)
            print(f"{'-' * 70}")
            
            # 檢查是否包含預期關鍵字
            if test['expected_keywords']:
                keywords_found = all(kw in result for kw in test['expected_keywords'])
                if keywords_found:
                    print(f"\n✓ 回覆包含預期關鍵字: {test['expected_keywords']}")
                else:
                    print(f"\n✗ 回覆缺少部分預期關鍵字: {test['expected_keywords']}")
                    test_pass = False
        
        if test_pass:
            print(f"\n✅ 測試 {i} 通過")
            passed += 1
        else:
            print(f"\n❌ 測試 {i} 失敗")
            if is_matched and result:
                print(f"   實際回覆: {result[:100]}...")
            failed += 1
        
        results.append({
            "id": i,
            "description": test['description'],
            "pass": test_pass
        })
    
    # ============================================================
    # 測試總結
    # ============================================================
    print("\n" + "=" * 70)
    print("📊 測試總結")
    print("=" * 70)
    
    for result in results:
        status = "✅" if result['pass'] else "❌"
        print(f"{status} 測試 {result['id']}: {result['description']}")
    
    total = len(test_cases)
    print(f"\n通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有測試通過！")
        print("\n💡 關鍵字功能驗證:")
        print("   • 精確匹配 (exact) 正常運作")
        print("   • 包含匹配 (contains) 正常運作")
        print("   • 正則匹配 (regex) 正常運作")
        print("   • 優先級排序正確（priority DESC）")
        print("   • 中英文關鍵字皆支援")
        return 0
    else:
        print(f"\n⚠️  有 {failed} 個測試失敗")
        return 1

def check_database_status():
    """檢查資料庫連線和 keywords 表狀態"""
    print("\n" + "=" * 70)
    print("🔍 資料庫連線檢查")
    print("=" * 70)
    
    try:
        connection = db_config.get_connection()
        if not connection:
            print("❌ 無法連接到資料庫")
            return False
        
        cursor = connection.cursor(dictionary=True)
        
        # 檢查 keywords 表
        cursor.execute("SELECT COUNT(*) as total FROM keywords")
        total = cursor.fetchone()['total']
        print(f"✓ keywords 表總筆數: {total}")
        
        cursor.execute("SELECT COUNT(*) as enabled FROM keywords WHERE enabled = 1")
        enabled = cursor.fetchone()['enabled']
        print(f"✓ 啟用中的關鍵字: {enabled}")
        
        cursor.execute("SELECT COUNT(*) as disabled FROM keywords WHERE enabled = 0")
        disabled = cursor.fetchone()['disabled']
        print(f"✓ 停用中的關鍵字: {disabled}")
        
        # 顯示各類型匹配的數量
        cursor.execute("""
            SELECT match_type, COUNT(*) as count 
            FROM keywords 
            WHERE enabled = 1 
            GROUP BY match_type
        """)
        types = cursor.fetchall()
        print(f"\n匹配類型分布:")
        for t in types:
            print(f"  • {t['match_type']}: {t['count']} 筆")
        
        # 顯示優先級分布
        cursor.execute("""
            SELECT priority, COUNT(*) as count 
            FROM keywords 
            WHERE enabled = 1 
            GROUP BY priority 
            ORDER BY priority DESC
        """)
        priorities = cursor.fetchall()
        print(f"\n優先級分布:")
        for p in priorities:
            print(f"  • 優先級 {p['priority']}: {p['count']} 筆")
        
        cursor.close()
        connection.close()
        
        print("\n✅ 資料庫連線正常")
        return True
        
    except Exception as e:
        print(f"❌ 資料庫檢查失敗: {e}")
        return False

if __name__ == '__main__':
    # 先檢查資料庫狀態
    if not check_database_status():
        print("\n⚠️  資料庫連線失敗，無法執行測試")
        sys.exit(1)
    
    # 執行關鍵字匹配測試
    sys.exit(test_keyword_matching())
