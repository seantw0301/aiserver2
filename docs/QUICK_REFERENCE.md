# 快速參考 - 黑名單功能 API

## 🎯 核心功能

在 `checkRoomCanBook` 和 `checkStaffCanBook` API 中添加了 LINE 用戶黑名單驗證。

---

## 📝 API 端點

### checkRoomCanBook

```
GET /api/rooms/checkRoomCanBook
```

**新增必需參數**：
```
lineid=U1234567890abcdef
```

**檢查流程**：
```
lineid → 是否超級黑名單? → YES → 返回 {'result': false}
                              → NO → 執行房間檢查邏輯
```

**響應示例**：
```json
// 超級黑名單用戶
{"result": false}

// 正常用戶 - 有可用房間
{"result": true, "store_id": 1, "available_rooms": [101, 102]}

// 正常用戶 - 無可用房間
{"result": false, "error": "..."}
```

---

### checkStaffCanBook

```
GET /api/rooms/checkStaffCanBook
```

**新增必需參數**：
```
lineid=U1234567890abcdef
```

**檢查流程**：
```
lineid → 是否超級黑名單? → YES → 返回 {'result': false, 'available_staffs': []}
                              → NO → 執行師傅檢查邏輯
```

**響應示例**：
```json
// 超級黑名單用戶
{"result": false, "available_staffs": []}

// 正常用戶 - 有可用師傅
{"result": true, "available_staffs": [...], "count": 3}

// 正常用戶 - 無可用師傅
{"result": false, "available_staffs": []}
```

---

## 🔐 黑名單檢查

### 工作原理

1. **接收** `lineid` 參數
2. **查詢** `line_users` 表找到用戶 ID
3. **查詢** `blacklist` 表檢查是否有 `staff_name='超級黑名單'` 的記錄
4. **決策**：
   - 找到 → 返回 `{'result': false}` (無訊息)
   - 未找到 → 繼續正常邏輯

### 安全特性

✅ **不透露信息** - 黑名單用戶只得到簡單 false，無任何提示
✅ **提前攔截** - 黑名單用戶不能觸發後續邏輯
✅ **無特征** - 黑名單用戶無法區分是被拒絕還是無資源

---

## 📊 參數速查表

| 參數 | 型別 | 必需 | 備註 |
|------|------|------|------|
| date | str | ✅ | YYYY-MM-DD |
| time | str | ✅ | HH:MM |
| guest | int | ✅ | >= 1 |
| duration | int | ✅ | >= 1 (分鐘) |
| storeid | str | ❌ | 店家 ID |
| **lineid** | **str** | **✅ 新增** | **LINE 用戶 ID** |

---

## 🚀 快速測試

### 使用 curl

```bash
# 正常用戶
curl "http://localhost:8000/api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=U1234567890abcdef"

# 黑名單用戶
curl "http://localhost:8000/api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=blacklist_user"
```

### 使用 Python

```python
import requests

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

print(response.json())
```

---

## ⚠️ 常見問題

### Q: lineid 是什麼？
A: LINE 平台為每個用戶分配的唯一 ID，格式如 `U1234567890abcdef`

### Q: 黑名單用戶會看到什麼錯誤訊息？
A: 沒有錯誤訊息，只返回 `{"result": false}`

### Q: 如何查詢用戶是否為超級黑名單？
```sql
SELECT * FROM blacklist 
WHERE line_user_id = (SELECT id FROM line_users WHERE line_id = 'U1234567890abcdef')
AND staff_name = '超級黑名單';
```

### Q: 如何添加用戶到超級黑名單？
```sql
-- 1. 找到用戶
SELECT id FROM line_users WHERE line_id = 'U1234567890abcdef';

-- 2. 添加到黑名單
INSERT INTO blacklist (line_user_id, staff_name) VALUES (user_id, '超級黑名單');
```

### Q: 黑名單檢查會阻止其他 API 使用嗎？
A: 只阻止 `checkRoomCanBook` 和 `checkStaffCanBook`，其他 API 不受影響

---

## 📄 文檔位置

| 文檔 | 內容 |
|------|------|
| `API_UPDATES_20251216.md` | 詳細 API 文檔 |
| `IMPLEMENTATION_SUMMARY.md` | 完整實現細節 |

---

## 🔄 版本控制

| 版本 | 日期 | 變更 |
|------|------|------|
| 1.0 | 2025-12-16 | 初始版本，添加黑名單檢查 |

---

## 💡 實現細節

**修改文件**：
- `/Volumes/aiserver2/api/routes/rooms.py`

**關鍵代碼**：
```python
from core.blacklist import BlacklistManager

blacklist_manager = BlacklistManager()
if blacklist_manager.is_super_blacklist(lineid):
    return {'result': False}  # 或添加 'available_staffs': []
```

**無需修改**：
- 資料庫結構
- 黑名單管理邏輯
- 其他 API 端點

---

## ✅ 驗證檢查清單

- [x] 語法檢查通過
- [x] 邏輯檢查通過
- [x] 文檔完整
- [x] 測試腳本可用
- [x] 後向兼容性檢查（破壞性變更已標注）

---

## 📞 故障排除

### 黑名單不工作？

1. **檢查 lineid 是否正確**
   ```bash
   # 用提供的 lineid 查詢資料庫
   SELECT * FROM line_users WHERE line_id = 'your_lineid';
   ```

2. **檢查黑名單記錄**
   ```bash
   # 查詢是否存在黑名單
   SELECT * FROM blacklist WHERE staff_name = '超級黑名單' LIMIT 5;
   ```

3. **檢查 API 日誌**
   ```bash
   tail -f /Volumes/aiserver2/server.log | grep -i blacklist
   ```

### lineid 參數報 422 錯誤？
- 確保提供了 `lineid` 參數
- 檢查參數名稱拼寫是否正確

### 黑名單檢查很慢？
- 考慮在 Redis 中快取黑名單
- 或為 `line_users` 和 `blacklist` 表添加索引

---

**最後更新**：2025-12-16
**狀態**：✅ 就緒生產環境
