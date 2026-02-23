# 部署檢查清單 - 黑名單功能整合

## 版本信息
- **功能**：LINE 用戶超級黑名單驗證
- **版本**：1.0
- **實現日期**：2025-12-16
- **狀態**：✅ 就緒

---

## 部署前檢查

### 代碼準備
- [x] 代碼語法檢查通過
  ```bash
  python3 -m py_compile api/routes/rooms.py
  ```
- [x] 導入檢查通過
  - `from core.blacklist import BlacklistManager`
  - `from fastapi import Query`
- [x] 邏輯驗證
  - 黑名單檢查在函數開始處
  - 超級黑名單用戶返回 false，無錯誤訊息

### 數據庫準備
- [ ] 驗證 `line_users` 表存在
  ```sql
  DESCRIBE line_users;
  ```
- [ ] 驗證 `blacklist` 表存在
  ```sql
  DESCRIBE blacklist;
  ```
- [ ] 驗證黑名單記錄格式
  ```sql
  SELECT * FROM blacklist WHERE staff_name = '超級黑名單' LIMIT 1;
  ```

### 環境準備
- [ ] 備份當前生產環境 `api/routes/rooms.py`
  ```bash
  cp api/routes/rooms.py api/routes/rooms.py.backup.20251216
  ```
- [ ] 準備回滾計劃
- [ ] 通知團隊部署時間

---

## 部署步驟

### 第一步：代碼部署
1. [ ] 上傳新的 `api/routes/rooms.py` 到服務器
2. [ ] 驗證文件權限正確
3. [ ] 驗證文件內容正確

### 第二步：服務重啟
1. [ ] 停止 API 服務
   ```bash
   # 根據實際情況調整
   systemctl stop aiserver2
   # 或
   pkill -f "python.*start_server.py"
   ```
2. [ ] 等待 5-10 秒
3. [ ] 啟動 API 服務
   ```bash
   systemctl start aiserver2
   # 或
   cd /Volumes/aiserver2 && python3 start_server.py
   ```
4. [ ] 驗證服務運行
   ```bash
   curl http://localhost:8000/docs
   ```

### 第三步：測試驗證

#### 功能測試
1. [ ] 正常用戶能正常使用 checkRoomCanBook
   ```bash
   curl "http://localhost:8000/api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=U1234567890abcdef"
   ```

2. [ ] 正常用戶能正常使用 checkStaffCanBook
   ```bash
   curl "http://localhost:8000/api/rooms/checkStaffCanBook?date=2025-12-20&time=14:00&guest=1&duration=90&storeid=1&lineid=U1234567890abcdef"
   ```

3. [ ] 超級黑名單用戶被拒絕（需要實際的黑名單 lineid）

4. [ ] 缺少 lineid 參數返回 422 錯誤
   ```bash
   curl "http://localhost:8000/api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1"
   ```

#### 性能測試
1. [ ] 響應時間在可接受範圍內（< 1s）
2. [ ] 數據庫連接正常
3. [ ] 無內存洩漏（監控內存使用）

#### 日誌檢查
1. [ ] 服務啟動日誌正常
   ```bash
   tail -50 /Volumes/aiserver2/server.log
   ```
2. [ ] 沒有異常錯誤消息
3. [ ] 黑名單檢查正常記錄

---

## API 驗證

### 手動驗證黑名單邏輯
```bash
curl "http://localhost:8000/api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=normal_user"
curl "http://localhost:8000/api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=blacklist_user"
curl "http://localhost:8000/api/rooms/checkStaffCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=normal_user"
curl "http://localhost:8000/api/rooms/checkStaffCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=blacklist_user"
```

**預期結果**：
- 正常用戶：回傳可預約結果
- 黑名單用戶：回傳 403 或禁止預約訊息

---

## 客戶端通知

### 升級警告
⚠️ **重要**：這是破壞性變更

**受影響的客戶端**：
- 所有調用 `/api/rooms/checkRoomCanBook` 的客戶端
- 所有調用 `/api/rooms/checkStaffCanBook` 的客戶端

**必需操作**：
- 所有客戶端必須添加 `lineid` 參數
- 不提供 `lineid` 會收到 422 錯誤
- 升級時間窗口：建議 2-4 週

### 通知內容示例
```
主題：API 更新通知 - checkRoomCanBook 和 checkStaffCanBook

親愛的開發者，

我們將於 2025-12-16 更新以下 API 端點，添加用戶身份驗證功能：
- /api/rooms/checkRoomCanBook
- /api/rooms/checkStaffCanBook

重要變更：
✓ 新增必需參數：lineid (LINE 用戶 ID)
✓ 不提供此參數會收到 422 錯誤
✓ 建議升級時間：2-4 週

詳細文檔見：API_UPDATES_20251216.md

感謝合作！
```

---

## 回滾計劃

### 快速回滾
如果出現嚴重問題，執行以下步驟恢復：

1. [ ] 停止 API 服務
   ```bash
   systemctl stop aiserver2
   ```

2. [ ] 恢復備份
   ```bash
   cp api/routes/rooms.py.backup.20251216 api/routes/rooms.py
   ```

3. [ ] 重啟服務
   ```bash
   systemctl start aiserver2
   ```

4. [ ] 驗證恢復
   ```bash
   curl http://localhost:8000/api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1
   # 應該返回 400 or 422 (缺少 lineid 參數，符合預期)
   ```

### 回滾後行動
- [ ] 記錄問題詳情
- [ ] 分析失敗原因
- [ ] 修復問題
- [ ] 重新安排部署

---

## 部署後檢查

### 24 小時內
- [ ] 監控 API 響應時間
- [ ] 檢查錯誤日誌
- [ ] 驗證數據庫連接
- [ ] 確認客戶端兼容性

### 一週內
- [ ] 分析黑名單攔截統計
- [ ] 驗證沒有誤報
- [ ] 收集用戶反饋
- [ ] 優化性能（如需要）

### 一個月內
- [ ] 評估功能效果
- [ ] 考慮添加快取優化
- [ ] 計劃進一步改進
- [ ] 發布總結報告

---

## 監控指標

### 關鍵指標
| 指標 | 正常範圍 | 警告閾值 |
|------|---------|---------|
| API 響應時間 | < 500ms | > 1000ms |
| 數據庫查詢時間 | < 100ms | > 300ms |
| 黑名單檢查成功率 | > 99% | < 95% |
| 服務可用性 | > 99.9% | < 99% |

### 監控命令
```bash
# 監控 API 響應時間
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/rooms/checkRoomCanBook?date=2025-12-20&time=14:00&guest=2&duration=90&storeid=1&lineid=test

# 監控服務狀態
systemctl status aiserver2

# 監控日誌
tail -f /Volumes/aiserver2/server.log
```

---

## 常見問題排查

### 問題 1: API 啟動失敗
```
症狀：無法啟動服務或啟動時出錯
排查步驟：
1. 檢查 Python 語法：python3 -m py_compile api/routes/rooms.py
2. 檢查導入：grep "from core.blacklist" api/routes/rooms.py
3. 檢查日誌：tail -50 server.log
解決方案：參考日誌錯誤信息或回滾
```

### 問題 2: 黑名單不工作
```
症狀：超級黑名單用戶仍能使用 API
排查步驟：
1. 驗證 lineid 是否存在於 line_users 表
2. 驗證黑名單記錄是否存在
3. 驗證 API 調用包含 lineid 參數
解決方案：檢查數據庫黑名單配置
```

### 問題 3: 性能下降
```
症狀：API 響應變慢
排查步驟：
1. 監控數據庫查詢時間
2. 檢查網絡延遲
3. 檢查服務器資源使用情況
解決方案：考慮添加 Redis 快取
```

---

## 文檔清單

部署前請確認以下文檔已審閱：

- [ ] `API_UPDATES_20251216.md` - API 詳細文檔
- [ ] `IMPLEMENTATION_SUMMARY.md` - 實現細節
- [ ] `QUICK_REFERENCE.md` - 快速參考
- [ ] `DEPLOYMENT_CHECKLIST.md` - 本文件

---

## 簽核

部署前需獲得以下簽核：

| 角色 | 名字 | 簽名 | 日期 |
|------|------|------|------|
| 開發者 | _____ | _____ | _____ |
| 代碼審查 | _____ | _____ | _____ |
| 測試 | _____ | _____ | _____ |
| 運維 | _____ | _____ | _____ |
| 產品 | _____ | _____ | _____ |

---

## 部署時間表

```
時間               活動
─────────────────────────────────────
14:00             會議開始，確認所有人就位
14:05             備份當前代碼和數據
14:10             停止 API 服務
14:15             部署新代碼
14:20             啟動 API 服務
14:25             運行自動化測試
14:35             手動測試關鍵流程
14:45             監控日誌和性能
15:00             部署完成，監控30分鐘
15:30             發送完成通知
```

---

**部署負責人**：_______________
**部署日期**：2025-12-16
**計劃完成時間**：約 1 小時
**預計宕機時間**：< 5 分鐘
