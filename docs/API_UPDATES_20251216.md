# API 更新文檔 - 2025-12-16

## 概述
為 `checkRoomCanBook` 和 `checkStaffCanBook` API 端點添加了 LINE 用戶黑名單驗證功能。

---

## 更新詳情

### 1. `checkRoomCanBook` API

#### 新增參數：
- **lineid** (string, 必需)
  - LINE 用戶 ID
  - 用於檢查用戶是否為超級黑名單

#### 新增邏輯：
- API 在處理請求前，會先檢查 `lineid` 是否為超級黑名單
- 如果用戶是超級黑名單，直接返回 `{'result': False}`
- **重要**：不返回任何錯誤訊息（error key），以避免透露黑名單信息

#### 使用範例：
```
GET /api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=U1234567890abcdef
```

#### 返回範例：

**超級黑名單**：
```json
{
  "result": false
}
```

**正常用戶**：（同原有邏輯）
```json
{
  "result": true,
  "store_id": 1,
  "available_rooms": [101, 102, 103],
  ...
}
```

---

### 2. `checkStaffCanBook` API

#### 新增參數：
- **lineid** (string, 必需)
  - LINE 用戶 ID
  - 用於檢查用戶是否為超級黑名單

#### 新增邏輯：
- API 在處理請求前，會先檢查 `lineid` 是否為超級黑名單
- 如果用戶是超級黑名單，直接返回 `{'result': False, 'available_staffs': []}`
- **重要**：不返回任何錯誤訊息（error key），以避免透露黑名單信息

#### 使用範例：
```
GET /api/rooms/checkStaffCanBook?date=2025-12-20&time=14:00&guest=1&duration=90&storeid=1&lineid=U1234567890abcdef
```

#### 返回範例：

**超級黑名單**：
```json
{
  "result": false,
  "available_staffs": []
}
```

**正常用戶**：（同原有邏輯）
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

---

## 黑名單檢查流程

### 檢查邏輯：
1. 接收 `lineid` 參數
2. 呼叫 `BlacklistManager.is_super_blacklist(lineid)`
3. 該方法會：
   - 在 `line_users` 表單中查找對應的 LINE 用戶
   - 在 `blacklist` 表單中查找是否存在 `staff_name='超級黑名單'` 的記錄
   - 返回 `True` 或 `False`
4. 如果返回 `True`，直接返回失敗響應，不執行後續邏輯

### 優勢：
- **安全性高**：不返回錯誤訊息，避免透露黑名單信息
- **性能好**：在早期階段阻止請求，減少後續資源消耗
- **用戶體驗**：黑名單用戶無法判斷是系統拒絕還是無可用資源

---

## 技術實現

### 涉及的文件修改：
- `/Volumes/aiserver2/api/routes/rooms.py`
  - `check_room_can_book()` 函數
  - `check_staff_can_book()` 函數

### 新增導入：
```python
from core.blacklist import BlacklistManager
```

### 檢查代碼片段：
```python
from core.blacklist import BlacklistManager
blacklist_manager = BlacklistManager()
if blacklist_manager.is_super_blacklist(lineid):
    return {'result': False}  # 或 {'result': False, 'available_staffs': []}
```

---

## 後向兼容性

- **舊 API 調用**：如果沒有提供 `lineid` 參數，API 會返回 400 錯誤（缺少必需參數）
- **升級建議**：所有調用這兩個 API 的客戶端都需要更新，添加 `lineid` 參數

---

## 測試用例

### 測試場景 1：超級黑名單用戶請求房間
```
URL: /api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=blacklist_user_id
Expected Response: {"result": false}
```

### 測試場景 2：正常用戶請求房間
```
URL: /api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=normal_user_id
Expected Response: {"result": true, "store_id": 1, ...}
```

### 測試場景 3：超級黑名單用戶請求師傅
```
URL: /api/rooms/checkStaffCanBook?date=2025-12-20&time=14:00&guest=1&duration=90&storeid=1&lineid=blacklist_user_id
Expected Response: {"result": false, "available_staffs": []}
```

### 測試場景 4：正常用戶請求師傅
```
URL: /api/rooms/checkStaffCanBook?date=2025-12-20&time=14:00&guest=1&duration=90&storeid=1&lineid=normal_user_id
Expected Response: {"result": true, "available_staffs": [...], "count": 3}
```

---

## 注意事項

1. **安全性**：不要在任何返回訊息中洩露黑名單狀態
2. **性能**：黑名單檢查會進行一次資料庫查詢，考慮添加快取以提高性能
3. **日誌記錄**：建議在黑名單攔截時記錄日誌用於審計
4. **錯誤處理**：如果黑名單檢查失敗（DB 錯誤），目前會返回 `False`，即拒絕請求

---

## 相關文件

- 黑名單管理：`/Volumes/aiserver2/core/blacklist.py`
- LINE 用戶表：`line_users` (在資料庫中)
- 黑名單表：`blacklist` (在資料庫中)
