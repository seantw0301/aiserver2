# API 測試命令 - checkRoomCanBook 和 checkStaffCanBook 黑名單功能

## 使用 curl 測試 API

### 1. 測試 checkRoomCanBook - 正常用戶

```bash
curl -X GET "http://localhost:8000/api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=U1234567890abcdef" \
  -H "Content-Type: application/json"
```

**預期響應**：
- 如果用戶不在黑名單中，會返回房間可用性信息
- 如果沒有可用房間，會返回 `"result": false`

---

### 2. 測試 checkRoomCanBook - 超級黑名單用戶

```bash
curl -X GET "http://localhost:8000/api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=U9999999999999999" \
  -H "Content-Type: application/json"
```

**預期響應**：
```json
{
  "result": false
}
```

---

### 3. 測試 checkStaffCanBook - 正常用戶

```bash
curl -X GET "http://localhost:8000/api/rooms/checkStaffCanBook?date=2025-12-20&time=14:00&guest=1&duration=90&storeid=1&lineid=U1234567890abcdef" \
  -H "Content-Type: application/json"
```

**預期響應**：
```json
{
  "result": true,
  "available_staffs": [
    {"name": "蒙", "stores": [1, 2, 3]},
    {"name": "兔", "stores": [1, 2, 3]},
    {"name": "聖", "stores": [1, 2, 3]}
  ],
  "count": 3
}
```

或如果沒有可用師傅：
```json
{
  "result": false,
  "available_staffs": []
}
```

---

### 4. 測試 checkStaffCanBook - 超級黑名單用戶

```bash
curl -X GET "http://localhost:8000/api/rooms/checkStaffCanBook?date=2025-12-20&time=14:00&guest=1&duration=90&storeid=1&lineid=U9999999999999999" \
  -H "Content-Type: application/json"
```

**預期響應**：
```json
{
  "result": false,
  "available_staffs": []
}
```

---

### 5. 測試缺少必需參數 lineid

```bash
curl -X GET "http://localhost:8000/api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1" \
  -H "Content-Type: application/json"
```

**預期響應**：
```json
{
  "detail": [
    {
      "loc": ["query", "lineid"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```
HTTP 狀態碼：422 (Unprocessable Entity)

---

## 使用 Python requests 測試

```python
import requests
import json

# 測試 checkRoomCanBook
response = requests.get(
    "http://localhost:8000/api/rooms/checkRoomCanBook",
    params={
        'date': '2025-12-20',
        'time': '14:00',
        'guest': 2,
        'duration': 90,
        'storeid': '1',
        'lineid': 'U1234567890abcdef'
    }
)

print("狀態碼:", response.status_code)
print("響應:", json.dumps(response.json(), indent=2, ensure_ascii=False))
```

---

## 參數說明

| 參數 | 類型 | 必需 | 說明 |
|------|------|------|------|
| date | string | ✅ | 預約日期，格式: YYYY-MM-DD |
| time | string | ✅ | 預約開始時間，格式: HH:MM |
| guest | integer | ✅ | 客人數量（必須 >= 1） |
| duration | integer | ✅ | 預約時長（分鐘，必須 >= 1） |
| storeid | string | ❌ | 店家ID（可選） |
| lineid | string | ✅ | **新增** - LINE 用戶 ID（必需） |

---

## 黑名單流程說明

1. **用戶提交預約請求**，包含 `lineid`
2. **API 檢查黑名單**：
   - 如果 `lineid` 是超級黑名單 → 直接返回 `{"result": false}`
   - 如果不是黑名單 → 繼續正常檢查邏輯
3. **返回結果**

### 重要特性：
- 🔒 **安全**：不返回錯誤訊息，避免透露黑名單信息
- ⚡ **高效**：在早期階段阻止黑名單用戶，減少資料庫查詢
- 🔍 **無特征**：黑名單用戶無法判斷是被拒絕還是無可用資源

---

## 調試提示

### 如何確認黑名單檢查正常運作？

1. **檢查資料庫黑名單表**：
```sql
SELECT * FROM blacklist WHERE staff_name = '超級黑名單';
```

2. **檢查 line_users 表**：
```sql
SELECT id, line_id, display_name FROM line_users WHERE line_id = 'U9999999999999999';
```

3. **查看 API 服務器日誌**：
```bash
tail -f /Volumes/aiserver2/server.log
```

### 常見問題

**Q: 為什麼超級黑名單用戶的請求沒有被拒絕？**
A: 檢查：
- `line_users` 表中是否存在該 `line_id`
- `blacklist` 表中是否存在 `staff_name='超級黑名單'` 的記錄
- 兩個表的關聯是否正確（通過 `line_user_id`）

**Q: 為什麼返回 422 錯誤？**
A: 缺少必需參數 `lineid`。所有客戶端都需要升級以包含此參數。

**Q: 黑名單檢查會影響性能嗎？**
A: 會進行一次資料庫查詢，但通常很快。如果需要更好的性能，可以考慮在 Redis 中快取黑名單。
