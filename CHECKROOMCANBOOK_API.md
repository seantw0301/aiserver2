# checkRoomCanBook API 端點文檔

## 功能說明

`checkRoomCanBook` API 用於檢查指定日期時間條件下是否有足夠的房間可以預約。

## API 端點

```
GET /rooms/checkRoomCanBook
```

## 請求參數

| 參數名 | 型別 | 必需 | 說明 |
|--------|------|------|------|
| `date` | string | ✅ | 預約日期，格式: `YYYY-MM-DD` |
| `time` | string | ✅ | 預約開始時間，格式: `HH:MM`（24小時制） |
| `guest` | integer | ✅ | 需要的房間數量（≥1） |
| `duration` | integer | ✅ | 預約時長（分鐘，≥1） |
| `storeid` | integer | ❌ | 店家ID（可選，不指定則檢查所有店家） |

## 回應格式

### 成功時（可以預約）

```json
{
  "result": true,
  "store_id": 1
}
```

### 失敗時（無法預約或出錯）

```json
{
  "result": false,
  "error": "錯誤訊息說明",
  "store_id": 1
}
```

注意：
- 如果指定了 `storeid` 參數，回應中會包含該 `store_id`
- 如果未指定 `storeid` 且找到可用房間，會返回找到房間的店家ID
- 如果未指定 `storeid` 且未找到任何可用房間，不會包含 `store_id` 欄位

## 使用案例

### 例子 1：查詢明天下午 2 點，1 人預約 30 分鐘（不指定店家）

```bash
curl "http://api.esim168.com:5001/rooms/checkRoomCanBook?date=2025-12-16&time=14:00&guest=1&duration=30"
```

### 例子 2：查詢明天下午 3 點，3 人預約 60 分鐘（不指定店家）

```bash
curl "http://api.esim168.com:5001/rooms/checkRoomCanBook?date=2025-12-16&time=15:00&guest=3&duration=60"
```

### 例子 3：查詢店家 ID 1，明天下午 2 點，1 人預約 30 分鐘

```bash
curl "http://api.esim168.com:5001/rooms/checkRoomCanBook?date=2025-12-16&time=14:00&guest=1&duration=30&storeid=1"
```

### 例子 4：查詢店家 ID 2，明天下午 3 點，3 人預約 60 分鐘

```bash
curl "http://api.esim168.com:5001/rooms/checkRoomCanBook?date=2025-12-16&time=15:00&guest=3&duration=60&storeid=2"
```

## 實現邏輯

1. **驗證輸入參數**
   - 檢查日期格式是否正確（YYYY-MM-DD）
   - 檢查時間格式是否正確（HH:MM）
   - 驗證客人數量和預約時長是否有效
   - 驗證店家ID是否有效（如果提供）

2. **獲取房間狀態**
   - 調用 `WorkdayManager.get_all_room_status()` 獲取指定日期的房間狀態
   - 該方法返回所有店家該日期的可用房間數（以 5 分鐘為單位的時間塊）

3. **時間轉換**
   - 使用 `TaskManager.convert_time_to_block_index()` 將時間轉換為 block 索引
   - 每個 block 代表 5 分鐘
   - 根據預約時長計算需要的 block 數量

4. **房間檢查**
   - 如果指定了 `storeid`，只檢查該特定店家
   - 如果未指定 `storeid`，檢查所有店家直到找到有足夠房間的店家
   - 遍歷指定時間段內的所有 block
   - 檢查每個 block 內的可用房間數
   - 計算指定時間段內的最小可用房間數

5. **返回結果**
   - 如果找到足夠房間，返回 `true` 並包含 `store_id`
   - 否則返回 `false` 並包含錯誤訊息

## 技術實現

### 核心依賴

- `WorkdayManager`: 用於獲取房間狀態
- `TaskManager`: 用於時間轉換和計算
- `run_in_executor`: 用於非同步執行同步函數

### 房間狀態數據結構

```python
{
    "store_id": {
        "store_name": "店家名稱",
        "free_blocks": [房間數1, 房間數2, ..., 房間數294]  # 294 個時間塊（24小時+30分鐘緩衝）
    }
}
```

### 時間塊計算

- 總塊數: 294 (288 塊 + 6 塊緩衝)
- 每塊代表時間: 5 分鐘
- 24 小時: 00:00 - 24:00 = 1440 分鐘 = 288 塊

### 持續時間計算

- 預約持續時間轉換為塊數: `(duration_minutes + 4) // 5`（向上取整）

## 錯誤情況

| 錯誤情況 | 返回訊息 |
|---------|---------|
| 日期格式錯誤 | "日期格式錯誤，應為 YYYY-MM-DD" |
| 時間格式錯誤 | "時間格式錯誤，應為 HH:MM" |
| 客人數量無效 | "客人數量必須大於 0" |
| 預約時長無效 | "預約時長必須大於 0 分鐘" |
| 店家ID無效 | "店家ID必須大於 0" |
| 店家不存在 | "店家ID {storeid} 不存在" |
| 無法獲取房間狀態 | "無法獲取該日期的房間狀態" |
| 時間超過營業時間 | "預約時間超過當日營業時間" |
| 房間不足（指定店家） | "店家 {storeid} 沒有足夠的房間可以預約" |
| 房間不足（未指定店家） | "沒有足夠的房間可以預約" |
| 其他錯誤 | "檢查時發生錯誤: {錯誤詳情}" |

## 測試

可以使用提供的測試腳本 `test_checkRoomCanBook.py` 進行功能測試：

```bash
python test_checkRoomCanBook.py
```

該腳本會測試多個使用案例，包括：
- 正常預約請求
- 邊界情況測試
- 不同日期格式
- 錯誤輸入驗證

## 注意事項

1. **時區**: 時間是按照伺服器時區計算的
2. **房間數量**: 返回值只表示是否有足夠房間，不會返回具體的房間數量
3. **快取**: 房間狀態數據使用 Redis 快取，如果資料庫更新，快取會自動更新
4. **非同步執行**: 為了避免阻塞，長時間操作會使用 `run_in_executor` 在執行緒池中執行

## API 版本信息

- 版本: 1.0.0
- 添加日期: 2025-12-15
- 相關模組: 
  - `api/routes/rooms.py`
  - `modules/workday_manager.py`
  - `core/tasks.py`

---

# checkStaffCanBook API 端點文檔

## 功能說明

`checkStaffCanBook` API 用於檢查指定日期時間段內有哪些師傅可以連續提供服務。該 API 用於在確認房間充足後，進一步尋找可用的師傅。

## API 端點

```
GET /rooms/checkStaffCanBook
```

## 請求參數

| 參數名 | 型別 | 必需 | 說明 |
|--------|------|------|------|
| `date` | string | ✅ | 預約日期，格式: `YYYY-MM-DD` |
| `time` | string | ✅ | 預約開始時間，格式: `HH:MM`（24小時制） |
| `guest` | integer | ✅ | 客人數量（用於參數驗證，此API中不使用） |
| `duration` | integer | ✅ | 預約時長（分鐘，≥1） |
| `storeid` | string | ❌ | 店家ID（可選，若指定則只返回在該店家工作的師傅） |

## 回應格式

### 成功時（有可用師傅）

```json
{
  "result": true,
  "available_staffs": [
    {
      "name": "師傅1",
      "stores": [1, 2]
    },
    {
      "name": "師傅2",
      "stores": [1]
    }
  ],
  "count": 2
}
```

### 失敗時（無可用師傅或出錯）

```json
{
  "result": false,
  "error": "錯誤訊息說明",
  "available_staffs": []
}
```

## 回傳格式說明

### 成功時的欄位說明

- `result`：boolean，是否有可用師傅
- `available_staffs`：array，可提供服務的師傅列表
  - `name`：string，師傅名字
  - `stores`：array of integers，該師傅當天工作的店家ID列表（已排序）
- `count`：integer，可用師傅的數量

### 失敗時的欄位說明

- `result`：boolean，始終為 false
- `error`：string，錯誤訊息說明
- `available_staffs`：array，空陣列

## 使用案例

### 例子 1：查詢明天下午 2 點，30 分鐘內可提供服務的師傅（不指定店家）

```bash
curl "http://api.esim168.com:5001/rooms/checkStaffCanBook?date=2025-12-16&time=14:00&guest=1&duration=30"
```

**回應範例**：
```json
{
  "result": true,
  "available_staffs": [
    {"name": "師傅1", "stores": [1, 2, 3]},
    {"name": "師傅2", "stores": [1]},
    {"name": "師傅3", "stores": [2, 3]}
  ],
  "count": 3
}
```

### 例子 2：查詢明天下午 3 點，60 分鐘內可在店家 1 提供服務的師傅

```bash
curl "http://api.esim168.com:5001/rooms/checkStaffCanBook?date=2025-12-16&time=15:00&guest=3&duration=60&storeid=1"
```

**回應範例**：
```json
{
  "result": true,
  "available_staffs": [
    {"name": "師傅1", "stores": [1, 2]},
    {"name": "師傅2", "stores": [1]}
  ],
  "count": 2
}
```

### 例子 3：查詢該時間沒有可用師傅的情況

```bash
curl "http://api.esim168.com:5001/rooms/checkStaffCanBook?date=2025-12-16&time=23:00&guest=1&duration=120"
```

**回應範例**：
```json
{
  "result": false,
  "error": "預約時間超過當日營業時間",
  "available_staffs": []
}
```

## 實現邏輯

1. **驗證輸入參數**
   - 檢查日期格式是否正確（YYYY-MM-DD）
   - 檢查時間格式是否正確（HH:MM）
   - 驗證預約時長是否有效
   - 驗證店家ID是否為有效的整數（如果提供）

2. **獲取師傅工作狀態和店家分佈**
   - 調用 `WorkdayManager.get_all_work_day_status()` 獲取指定日期的師傅工作狀態
   - 調用 `WorkdayManager.get_all_staff_store_map()` 獲取師傅在各店家的分佈
   - 該方法返回所有師傅該日期的可用時段和所在店家

3. **時間轉換**
   - 使用 `TaskManager.convert_time_to_block_index()` 將時間轉換為 block 索引
   - 每個 block 代表 5 分鐘
   - 根據預約時長計算需要的 block 數量

4. **師傅檢查**
   - 遍歷所有師傅
   - **首先**檢查該師傅在指定時間段內是否有連續的可用 block（有排班且無工作）
   - **其次**檢查該師傅的店家分佈：
     - 如果指定了 `storeid`，檢查師傅是否在該店家工作
     - 如果未指定 `storeid`，則所有符合時間條件的師傅都可以加入名單
   - 返回同時滿足時間和店家條件的師傅

5. **返回結果**
   - 返回所有符合條件的師傅及其工作店家列表
   - 若無符合條件的師傅，返回空列表

## 錯誤情況

| 錯誤情況 | 返回訊息 |
|---------|---------|
| 日期格式錯誤 | "日期格式錯誤，應為 YYYY-MM-DD" |
| 時間格式錯誤 | "時間格式錯誤，應為 HH:MM" |
| 預約時長無效 | "預約時長必須大於 0 分鐘" |
| 無法獲取師傅狀態 | "無法獲取該日期的師傅工作狀態" |
| 時間超過營業時間 | "預約時間超過當日營業時間" |
| 沒有師傅可用 | "沒有師傅可以在指定時間提供服務" |
| 其他錯誤 | "檢查時發生錯誤: {錯誤詳情}" |

## 使用工作流程

通常的使用流程如下：

1. **首先調用 `checkRoomCanBook`**
   - 驗證是否有足夠的房間可以預約
   - 可選地指定 `storeid` 以檢查特定店家

2. **然後調用 `checkStaffCanBook`**
   - 在確認房間可用後，尋找可提供服務的師傅
   - 使用相同的日期、時間和預約時長參數

### 完整工作流程範例

```bash
# 步驟 1：檢查房間
curl "http://api.esim168.com:5001/rooms/checkRoomCanBook?date=2025-12-16&time=14:00&guest=2&duration=60&storeid=1"
# 如果返回 result: true，則繼續

# 步驟 2：檢查師傅
curl "http://api.esim168.com:5001/rooms/checkStaffCanBook?date=2025-12-16&time=14:00&guest=2&duration=60"
# 返回可提供服務的師傅名單
```

## 注意事項

1. **時區**: 時間是按照伺服器時區計算的
2. **師傅可用性**: 只有當師傅在整個指定時間段內都有排班且沒有其他工作時，才被列為可用
3. **店家分佈**: 
   - 若未指定 `storeid`，返回的師傅列表包含所有符合時間條件的師傅及其工作店家
   - 若指定了 `storeid`，只返回在該店家工作的師傅
4. **店家ID轉換**: `storeid` 參數會自動轉換為整數與師傅的店家列表進行比較
5. **快取**: 師傅工作狀態和店家分佈數據使用 Redis 快取，若資料庫更新會自動更新快取
6. **非同步執行**: 為了避免阻塞，長時間操作會使用 `run_in_executor` 在執行緒池中執行

## API 版本信息

- 版本: 1.0.0
- 添加日期: 2025-12-16
- 相關模組: 
  - `api/routes/rooms.py`
  - `modules/workday_manager.py`
  - `core/tasks.py`
