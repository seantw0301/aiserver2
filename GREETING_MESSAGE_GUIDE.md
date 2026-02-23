# Greeting Message 出現時機與 Redis 清除指南

## 1. Greeting Message 出現的時機

### 條件判斷流程
```
用戶發送訊息
    ↓
檢查 Redis: {line_user_id}_lastest
    ↓
├─ 有值且等於今日 → 返回 None（不顯示問候）
└─ 無值或不是今日 → 執行資料庫邏輯
    ↓
更新資料庫 visitdate 為今日
    ↓
比較「舊的 visitdate」是否等於今日
    ↓
├─ 等於今日 → 返回 None（不顯示問候）
└─ 不等於或為 NULL → 返回 Greeting Message ✓
```

### Greeting Message 內容
```
親愛的會員{display_name}({user_id})您好!
```
其中：
- `display_name`: 來自 line_users.display_name
- `user_id`: 來自 line_users.id（自增主鍵，非 line_id）

### 出現的具體時機
1. **新用戶首次登入** → visitdate 為 NULL → **顯示問候** ✓
2. **昨日登入的用戶今日首次登入** → 舊 visitdate ≠ 今日 → **顯示問候** ✓
3. **今日已登入的用戶再次登入** → 舊 visitdate = 今日 → **不顯示** ✗
4. **同一天多次訊息** → Redis 已有 latest 記錄 → **不顯示** ✗

---

## 2. 涉及的 Redis Key

### 主要 Key（需要清除的）
```
{line_user_id}_lastest
```

**說明**：
- 存儲用戶**最後訪問的日期**（格式: YYYY-MM-DD）
- **過期時間**：36 小時（確保跨日後失效）
- **作用**：快速判斷用戶是否在今日已訪問過

**範例**：
```
U1234567890abcdef1234567890abcdef_lastest = "2025-12-16"
```

### 其他相關的 Redis Key（如有）
```
{line_user_id}              # 用戶的預約資料快取
{line_user_id}_workday      # 工作日資料快取
{line_user_id}_language     # 用戶語系設定
```

---

## 3. 資料庫字段

### line_users 表
```sql
CREATE TABLE line_users (
    id INT PRIMARY KEY AUTO_INCREMENT,      -- 自增主鍵（greeting 使用）
    line_id VARCHAR(255) UNIQUE,            -- LINE 用戶 ID（greeting 使用）
    display_name VARCHAR(255),              -- 用戶顯示名稱（greeting 使用）
    visitdate DATE,                         -- 最後訪問日期（greeting 判斷依據）
    language VARCHAR(10),
    ...
);
```

### visitdate 的作用
- 記錄用戶**最後一次訪問的日期**
- 與 Redis `{line_user_id}_lastest` 的日期進行比對
- 若資料庫 visitdate 被更新為今日，則下次登入不會顯示問候

---

## 4. 清除指南

### 方案 A：只清除 Redis（只針對今日）
```bash
# 清除特定用戶的 latest 標記
redis-cli DEL "{line_user_id}_lastest"

# 清除所有用戶的 latest 標記（使用 clearredis.py 選項 7）
python clearredis.py
# 選擇選項 7
```

**效果**：
- ✓ Redis 中的 latest 被清除
- ✗ 資料庫 visitdate 仍是今日
- **結果**：用戶再次登入時**仍不會**顯示問候（因為資料庫 visitdate = 今日）

### 方案 B：同時修改資料庫和 Redis（完全測試）
```bash
# 使用 clearredis.py 工具
python clearredis.py

# 選擇選項 6：重設所有用戶 visitdate 為昨天
#   → 資料庫 visitdate 改為昨天

# 選擇選項 7：清除所有用戶的 Redis latest 標記
#   → Redis latest 被刪除

# 結果：用戶再次登入時**會顯示**問候 ✓
```

### 方案 C：手動清除特定用戶
```bash
# 1. 清除 Redis
redis-cli DEL "U1234567890abcdef1234567890abcdef_lastest"

# 2. 修改資料庫（使用 MySQL）
mysql -u root -p senspa_db
UPDATE line_users SET visitdate = '2025-12-15' WHERE line_id = 'U1234567890abcdef1234567890abcdef';

# 結果：該用戶再次登入時會顯示問候 ✓
```

---

## 5. 測試清除後的效果

### 驗證清除成功
```bash
# 查看 Redis 中是否還有 latest 記錄
redis-cli KEYS "*_lastest"

# 查看資料庫中用戶的 visitdate
mysql -u root -p senspa_db
SELECT line_id, display_name, visitdate FROM line_users WHERE line_id = 'YOUR_USER_ID';
```

### 測試流程
1. 執行清除：
   ```bash
   python clearredis.py
   選項 6 → 重設 visitdate 為昨天
   選項 7 → 清除 Redis latest
   ```

2. 用戶傳送訊息：
   ```
   用戶輸入任意文字 → 系統應顯示 greeting message
   ```

3. 驗證資料被更新：
   ```
   用戶再次傳送訊息 → 系統不再顯示 greeting message（Redis 已記錄今日訪問）
   ```

---

## 6. 關鍵代碼位置

### greeting.py
- [第 16-87 行](modules/greeting.py#L16-L87)：`check_daily_greeting()` 核心邏輯

### core/common.py
- [第 2664-2700 行](core/common.py#L2664-L2700)：`update_user_visitdate()` 更新邏輯

### api/routes/parse.py
- [第 100-120 行](api/routes/parse.py#L100-L120)：呼叫 greeting 邏輯

### clearredis.py
- [第 170-210 行](clearredis.py#L170-L210)：`reset_all_visitdate_to_yesterday()` 資料庫清除
- [第 215-250 行](clearredis.py#L215-L250)：`clear_daily_greeting_flags()` Redis 清除

---

## 7. 常見問題

### Q1: 為什麼只清除 Redis 還是看不到 greeting？
**A**: 因為資料庫的 visitdate 已是今日。需要同時清除：
1. Redis 的 `{line_user_id}_lastest`
2. 資料庫的 visitdate（改為昨天或 NULL）

### Q2: clearredis 命令會不會重新觸發 greeting？
**A**: 會。執行 `clearredis` 訊息時系統會：
1. 清除該用戶的 Redis 資料
2. 呼叫 `greeting.check_daily_greeting()`
3. 更新該用戶的 visitdate 為今日
4. 但不會返回 greeting message

### Q3: 如何確認清除成功？
**A**: 
```bash
# Redis 應為空
redis-cli KEYS "*_lastest"
# 結果應為 (empty array)

# 資料庫 visitdate 應為昨天
mysql> SELECT visitdate FROM line_users WHERE line_id = 'YOUR_ID';
# 結果應為 2025-12-15（如果今天是 12-16）
```

### Q4: greeting 是否會在系統重啟後重新出現？
**A**: 不會。除非：
1. 手動刪除資料庫的 visitdate（改為昨天或 NULL）
2. 刪除 Redis 的 `{line_user_id}_lastest`

---

## 8. Redis Key 清除命令快速參考

```bash
# 清除所有 latest 標記
redis-cli EVAL "return redis.call('del', unpack(redis.call('keys', '*_lastest')))" 0

# 清除特定用戶
redis-cli DEL "{line_user_id}_lastest"

# 查看所有相關的 key
redis-cli KEYS "*_lastest"
redis-cli KEYS "*{line_user_id}*"
```

---

## 總結

| 操作 | Redis Key | 資料庫 visitdate | 結果 |
|------|-----------|------------------|------|
| 不清除 | latest = 今日 | 今日 | ✗ 不顯示問候 |
| 只清除 Redis | 無 | 今日 | ✗ 不顯示問候 |
| 只改 visitdate | latest = 今日 | 昨天 | ✗ 不顯示問候 |
| **同時清除兩者** | **無** | **昨天** | **✓ 顯示問候** |

使用 `python clearredis.py` 的選項 6 + 7 可一次完成所有清除操作！
