#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日問侯語功能實現總結

功能說明：
當客人傳送訊息文字時，系統會：
1. 更新 line_users 表中的 visitdate 欄位為當下日期
2. 比較客人上次訪問的 visitdate 和今日日期
3. 若日期不同（或 visitdate 為 null），在返回訊息中加上問侯語：
   "親愛的會員{display_name}({id})您好!"

其中：
- display_name：來自 line_users 表的 display_name 欄位
- id：來自 line_users 表的 id 欄位（自增主鍵），不是 line_id

修改的文件：
=========================================

1. /Volumes/aiserver2/core/common.py
   - 修改 update_user_visitdate() 函數：
     * 返回更新前的用戶信息（包含舊的 visitdate）
     * 用於在 app.py 中進行日期比較
   
   - 確保 get_user_info() 函數返回 id 欄位

2. /Volumes/aiserver2/ai_parser/natural_language_parser.py
   - 在 parse_natural_language() 函數中：
     * 調用 update_user_visitdate() 獲取更新前的用戶信息
     * 在所有返回結果中添加 user_info 字段

3. /Volumes/aiserver2/app.py
   - 修改 /parse 端點：
     * 從 parse_natural_language() 的返回結果中提取 user_info
     * 比較 visitdate：處理包含時間戳記的格式（例如 "2025-11-19T00:00:00"）
     * 只提取日期部分進行比較（前 10 個字符）
     * 若 visitdate 為 null 或不等於今日，生成問侯語
     * 將 greeting_message 添加到返回結果中

4. /Volumes/aiserver2/spabot_demo.php
   - 添加邏輯處理 greeting_message：
     * 在非預約相關訊息處理後
     * 檢查返回結果中是否有 greeting_message 字段
     * 若存在且不為空，將其添加到顯示消息中

工作流程：
=========================================

1. 客人發送訊息到 LINE Bot
   
2. spabot_demo.php 收到消息
   
3. 調用 /parse 端點
   - Python backend (app.py)
   
4. /parse 端點：
   a. 調用 parse_natural_language(input_json)
      - 更新 visitdate 為今日
      - 返回用戶的舊 visitdate
      - 返回 user_info（包含 id, display_name, 舊的 visitdate）
   
   b. 比較日期：
      - 獲取今日日期
      - 提取 visitdate 的日期部分
      - 若為 null 或不等於今日，生成問侯語
   
   c. 將 greeting_message 添加到返回結果

5. spabot_demo.php 接收結果
   - 提取 greeting_message（如果存在）
   - 添加到 showMessage 中
   - 顯示給用戶

測試用例：
=========================================

測試日期比較邏輯：
- 新用戶（visitdate 為 null）→ 顯示問侯語 ✓
- 時間戳記格式（"2025-11-19T00:00:00"）→ 正確提取日期 ✓
- 純日期格式（"2025-11-19"）→ 正確比較 ✓
- 今天已訪問（visitdate = 今日）→ 不顯示問侯語 ✓

Debug 輸出驗證：
=========================================

在 spabot_demo.php 的 debug 輸出中，應該看到：
- "greeting_message": "親愛的會員{display_name}({id})您好!"

此消息會被添加到 showMessage 中，最終顯示給用戶。

已知限制和注意事項：
=========================================

1. visitdate 的日期格式：
   - 支援格式：YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS
   - 只比較日期部分（前 10 個字符）

2. 問侯語只在以下情況顯示：
   - 新用戶（visitdate 為 null）
   - 上次訪問日期不等於今日

3. 問侯語在每日內只顯示一次（當 visitdate 被更新為今日後）
   - 同一天再發消息時不會顯示

4. 如果用戶信息不存在（update_user_visitdate 返回 null），
   則不會顯示問侯語

驗證命令：
=========================================

# 測試日期比較邏輯
python3 test_date_comparison.py

# 檢查語法
python3 -m py_compile app.py core/common.py ai_parser/natural_language_parser.py
php -l spabot_demo.php
"""

if __name__ == "__main__":
    print(__doc__)
