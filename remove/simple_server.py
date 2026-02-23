#!/usr/bin/env python3
"""
簡化的測試服務器 - 修復多人預約問題
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設置環境變數
os.environ['API_PORT'] = '5002'

from app import app

if __name__ == "__main__":
    print("🚀 啟動簡化測試服務器...")
    print("📍 地址: http://localhost:5002")
    print("🔧 多人預約功能已設置為待處理狀態")
    
    try:
        app.run(host='0.0.0.0', port=5002, debug=False, use_reloader=False)
    except Exception as e:
        print(f"❌ 服務器啟動失敗: {e}")
