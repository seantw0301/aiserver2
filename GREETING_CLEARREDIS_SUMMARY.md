# Greeting Message 清除方案 - 執行摘要

## 📌 問題及解決方案

### 原始問題
當執行 `clearredis` 清除用戶快取後，系統仍不會將下次登入視為「本日第一句」，因此不會產生 greeting message。

### 根本原因
Greeting message 的顯示取決於**兩層檢查**：
1. **Redis 層**：`{line_user_id}_lastest` 是否等於今日
2. **資料庫層**：`line_users.visitdate` 是否等於今日

只清除其中一層還不夠。

---

## 🔴 應清除的 Redis Key

### Key 格式
```
{line_user_id}_lastest
```

### Key 詳細信息
```
格式：    {line_user_id}_lastest
值類型：  字符串（日期：YYYY-MM-DD）
值範例：  "2025-12-16"
過期時間：36 小時（自動失效）
數量：    等於線上用戶數量
作用：    記錄用戶最後訪問日期，用於快速判斷
```

### 查看 Redis Key
```bash
# 列出所有首次登入標記
redis-cli KEYS "*_lastest"

# 結果示例
U1234567890abcdef1234567890abcdef_lastest
U9876543210abcdef9876543210abcdef_lastest
...
```

---

## 🟦 涉及的資料庫欄位

### 表名
```
line_users
```

### 欄位
```
visitdate (DATE)
└─ 作用：記錄用戶最後一次訪問的日期
   範例：2025-12-16
```

### SQL 查詢
```sql
-- 查看用戶 visitdate
SELECT id, line_id, display_name, visitdate 
FROM line_users 
WHERE line_id = 'U1234567890abcdef1234567890abcdef';

-- 修改 visitdate 為昨天（用於測試）
UPDATE line_users 
SET visitdate = '2025-12-15' 
WHERE line_id = 'U1234567890abcdef1234567890abcdef';

-- 批量修改為昨天
UPDATE line_users 
SET visitdate = DATE_SUB(CURDATE(), INTERVAL 1 DAY);
```

---

## ✅ 完整清除流程

### 方案：使用 clearredis.py 工具（推薦）

#### 步驟 1：重設資料庫 visitdate
```bash
cd /Volumes/aiserver2
python clearredis.py
```
然後選擇 **選項 6**：重設所有用戶 visitdate 為昨天

**執行內容**：
```
- 查詢資料庫中有多少用戶
- 確認操作
- 更新所有用戶 visitdate = 昨天
- 顯示修改結果
```

**資料庫變化**：
```
Before: visitdate = 2025-12-16
After:  visitdate = 2025-12-15
```

#### 步驟 2：清除 Redis latest 標記
```bash
python clearredis.py
```
然後選擇 **選項 7**：清除所有用戶的 Redis 首次登入標記

**執行內容**：
```
- 列出所有 *_lastest 的 key
- 確認刪除
- 刪除所有標記
- 顯示刪除結果
```

**Redis 變化**：
```
Before: U1234567890abcdef1234567890abcdef_lastest = "2025-12-16"
After:  (不存在)
```

#### 步驟 3：驗證清除成功
```bash
# 檢查 Redis 是否還有 latest 標記
redis-cli KEYS "*_lastest"
# 預期結果：(empty array)

# 檢查資料庫 visitdate
mysql -u root -p senspa_db
SELECT visitdate FROM line_users LIMIT 1;
# 預期結果：2025-12-15（如果今天是 12-16）
```

---

## 🎯 清除後的效果

### 用戶再次登入時的流程
```
1. 用戶發送訊息
   ↓
2. 系統檢查 Redis latest
   └─ 不存在（已清除）
   ↓
3. 系統更新資料庫 visitdate = 今日 (2025-12-16)
   ↓
4. 系統比較舊 visitdate (2025-12-15) ≠ 今日 (2025-12-16)
   └─ 不相等 ✓
   ↓
5. 系統產生 greeting message ✅
   "親愛的會員{display_name}({id})您好!"
   ↓
6. 系統寫入 Redis: latest = 2025-12-16（TTL: 36小時）
```

### 用戶同一天再次登入時
```
1. 用戶發送第二條訊息（同一天）
   ↓
2. 系統檢查 Redis latest
   └─ 存在且等於今日 (2025-12-16)
   ↓
3. 系統跳過 greeting 邏輯
   └─ 不產生 greeting message ✗
```

---

## 📊 清除前後對比

### 清除前
| 層級 | Key/欄位 | 值 |
|------|---------|-----|
| **Redis** | `latest` | `2025-12-16` |
| **資料庫** | `visitdate` | `2025-12-16` |
| **結果** | greeting | ❌ 不出現 |

### 清除後（執行步驟 1 + 2）
| 層級 | Key/欄位 | 值 |
|------|---------|-----|
| **Redis** | `latest` | ❌ 不存在 |
| **資料庫** | `visitdate` | `2025-12-15` |
| **結果** | greeting | ✅ 出現 |

---

## 🔧 手動清除方式（進階）

### 方式 A：使用 Redis CLI
```bash
# 清除所有 latest 標記
redis-cli EVAL "return redis.call('del', unpack(redis.call('keys', '*_lastest')))" 0

# 清除特定用戶
redis-cli DEL "U1234567890abcdef1234567890abcdef_lastest"

# 查看結果
redis-cli KEYS "*_lastest"
```

### 方式 B：使用 MySQL
```bash
mysql -u root -p senspa_db

# 查看所有用戶
SELECT id, line_id, display_name, visitdate FROM line_users;

# 修改特定用戶
UPDATE line_users 
SET visitdate = '2025-12-15' 
WHERE line_id = 'U1234567890abcdef1234567890abcdef';

# 批量修改
UPDATE line_users 
SET visitdate = DATE_SUB(CURDATE(), INTERVAL 1 DAY) 
WHERE visitdate IS NOT NULL;

# 驗證
SELECT visitdate FROM line_users WHERE visitdate IS NOT NULL LIMIT 5;
```

---

## 📋 clearredis.py 工具功能表

```
主菜單選項：
1. 列出所有緩存 key                    [查看用途]
2. 清除今天的緩存                      [廣泛清除]
3. 清除指定日期的緩存                  [精確清除]
4. 清除最近 7 天的緩存                 [定期清除]
5. 清除特定類型的緩存                  [細化清除]
6. ⭐ 重設所有用戶 visitdate 為昨天    [greeting 步驟 1]
7. ⭐ 清除所有用戶的 Redis latest      [greeting 步驟 2]
8. 清除所有緩存 (危險！)              [謹慎使用]
0. 退出
```

---

## ⚠️ 常見問題排查

### Q1: 執行完清除後，為什麼用戶還是看不到 greeting？

**檢查清單**：
- [ ] 執行了選項 6（重設 visitdate）？
- [ ] 執行了選項 7（清除 Redis latest）？
- [ ] 兩個都執行了嗎？
- [ ] 執行後用戶重新發送訊息了嗎？

**診斷命令**：
```bash
# 檢查 Redis
redis-cli KEYS "*_lastest"

# 檢查資料庫
mysql -u root -p senspa_db -e "SELECT visitdate FROM line_users LIMIT 1;"
```

### Q2: 只執行了選項 7，為什麼沒有效果？

**原因**：資料庫 visitdate 仍是今日
**解決**：再執行選項 6 重設 visitdate

### Q3: 執行了很久，為什麼還沒完成？

**檢查**：
- 用戶數量很多（>10000）時可能較慢
- 資料庫查詢較慢
- 靜待完成或按 Ctrl+C 中止

### Q4: 如何只清除特定用戶的標記？

**使用 Redis 命令**：
```bash
redis-cli DEL "U1234567890abcdef1234567890abcdef_lastest"
```

**修改特定用戶 visitdate**：
```sql
UPDATE line_users 
SET visitdate = '2025-12-15' 
WHERE line_id = 'U1234567890abcdef1234567890abcdef';
```

---

## 📄 相關文件

| 文件 | 內容 | 用途 |
|------|------|------|
| `GREETING_MESSAGE_GUIDE.md` | 詳細技術指南 | 深入理解系統 |
| `GREETING_REDIS_KEYS.md` | 快速參考手冊 | 日常參考 |
| `clearredis.py` | 清除工具 | 實際執行清除 |
| `modules/greeting.py` | greeting 邏輯 | 代碼級了解 |
| `core/common.py` | visitdate 邏輯 | 代碼級了解 |

---

## ✨ 快速開始

### 最簡單的方式（推薦）
```bash
cd /Volumes/aiserver2
python clearredis.py
# 選項 6 → Enter → yes
# 選項 7 → Enter → yes
# 0 → 退出
# ✓ 完成，用戶再次登入時會看到 greeting ✓
```

### 驗證清除成功
```bash
# 用戶發送一條訊息，應該看到：
親愛的會員{名字}({ID})您好!

# 用戶再次發送訊息（同一天），應該不看到問候
```

---

## 📞 支援資訊

如有問題，請檢查：
1. Redis 是否正常運作：`redis-cli ping`
2. 資料庫是否可連接：`mysql -u root -p senspa_db -e "SELECT 1;"`
3. Python 依賴：`python -c "import redis; print('OK')"`
4. 查看詳細指南：`cat GREETING_MESSAGE_GUIDE.md`

