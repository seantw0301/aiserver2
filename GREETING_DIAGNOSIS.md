# Greeting Message 診斷指南

## ✅ 確認狀態

系統檢查結果：
```
✅ Redis latest       : 已清空
✅ 資料庫 visitdate   : 全部改為昨天 (2025-12-15)  
✅ greeting.py 邏輯   : 正常工作
✅ integration.py     : 正確整合
```

## 🔍 可能的問題

### 問題 1：LINE user ID 不匹配

**症狀**：greeting message 沒有出現

**原因**：LINE user ID 格式不同

**檢查方法**：
```python
# 在 parse.py 中添加 debug 輸出
print(f"DEBUG: LINE user ID = {request.key}")
print(f"DEBUG: visitdate = {user_info.get('visitdate')}")
print(f"DEBUG: greeting_message = {greeting_message}")
```

**LINE user ID 格式**：
- 應為 **36 字符長** 的字符串
- 範例：`U389ffbad3d225902613851d9663deacd`
- **不是** `U389ffbad3` 這樣的截短版本

---

### 問題 2：沒有看到訊息

**可能的原因**：

#### A. response_message 為空
如果用戶的訊息不是預約、不是關鍵字，`response_message` 會是空的

```python
# parse.py 第 220 行的註釋代碼
# if not parsed_data.get('response_message'):
#     parsed_data['response_message'] = ""
```

**解決**：當 response_message 為空時，仍應顯示 greeting message

當前邏輯（✓ 正確）：
```python
if greeting_message and response_message:
    integrated_message = f"{greeting_message}\n\n{response_message}"
elif greeting_message:
    integrated_message = greeting_message  # ✓ greeting 單獨會被顯示
```

#### B. line_messages 為空
當 `integrated_message` 為空時，`line_messages` 會是空列表

```python
if integrated_message:
    line_messages.append(formatter.format_text_message(integrated_message))
# 如果 integrated_message 為空，不會添加任何訊息
```

**檢查**：
```python
print(f"DEBUG: integrated_message = '{integrated_message}'")
print(f"DEBUG: line_messages = {line_messages}")
```

---

### 問題 3：greeting 被顯示但格式不對

**檢查**：
- greeting message 是否真的包含用戶名和 ID？
- 格式是否為：`親愛的會員{display_name}({id})您好!`

---

## 🛠️ 完整診斷步驟

### 步驟 1：確認清除成功
```bash
# Redis 應為空
redis-cli KEYS "*_lastest"
# 結果：(empty array)

# 資料庫應都是昨天
python3 << EOF
from core.database import db_config
conn = db_config.get_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT DISTINCT DATE(visitdate) as dates FROM line_users")
for r in cursor.fetchall():
    print(f"Date: {r['dates']}")
cursor.close()
conn.close()
EOF
```

預期結果：
```
Date: 2025-12-15
```

### 步驟 2：測試 greeting.py
```python
python3 << EOF
import sys
sys.path.insert(0, '/Volumes/aiserver2')
from modules import greeting

# 獲取真實的 line_id
from core.database import db_config
conn = db_config.get_connection()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT line_id FROM line_users LIMIT 1")
result = cursor.fetchone()
test_user = result['line_id']
cursor.close()
conn.close()

print(f"測試用戶：{test_user}")

greeting_msg, user_info = greeting.check_daily_greeting(test_user)

print(f"User Info：{user_info}")
print(f"Greeting：{greeting_msg}")

if greeting_msg:
    print("✅ greeting 正常工作")
else:
    print("❌ greeting 未工作")
EOF
```

### 步驟 3：測試完整的 parse 流程
```python
# 手動調用 parse 端點
curl -X POST "http://localhost:8000/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "真實的LINE_USER_ID",
    "message": "hello"
  }'
```

檢查返回的 JSON：
```json
{
  "line_messages": [
    {
      "type": "text",
      "text": "親愛的會員ANDY(931)您好!"
    }
  ]
}
```

### 步驟 4：在 LINE 上測試
1. 清除資料：`python clearredis.py` (選項 6 + 7)
2. 用戶發送訊息
3. 應該看到：`親愛的會員{name}({id})您好!`

---

## 📋 添加 Debug 輸出

在 `parse.py` 的第 169 行後添加：

```python
# 2. 每日問候語 (Greeting Module) - 必需階段
greeting_message, user_info = greeting.check_daily_greeting(request.key)

# DEBUG OUTPUT
print(f"[DEBUG GREETING]")
print(f"  request.key: {request.key}")
print(f"  user_info: {user_info}")
print(f"  greeting_message: {greeting_message}")
```

在 `integration.py` 的第 387 行後添加：

```python
integrated_message = response_message
if greeting_message and response_message:
    integrated_message = f"{greeting_message}\n\n{response_message}"
elif greeting_message:
    integrated_message = greeting_message

# DEBUG OUTPUT
print(f"[DEBUG INTEGRATION]")
print(f"  greeting_message: {greeting_message}")
print(f"  response_message: {response_message}")
print(f"  integrated_message: {integrated_message}")
print(f"  line_messages count: {len(line_messages)}")
```

---

## 🎯 快速檢查清單

- [ ] Redis latest key 已清空？ (`redis-cli KEYS "*_lastest"` 應為空)
- [ ] 資料庫 visitdate 全是昨天？ (2025-12-15)
- [ ] 用的是完整的 36 字符 LINE user ID？
- [ ] 服務器已重啟以加載最新代碼？
- [ ] 用戶訊息確實被系統接收？
- [ ] greeting message 在代碼測試中能產生？

---

## 📞 尋求幫助

如果仍然無法解決，提供：
1. 用戶發送的訊息
2. 系統返回的 JSON 完整內容
3. 上面 debug 輸出的結果

