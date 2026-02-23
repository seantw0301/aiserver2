# 清理與刪除策略

## 已刪除項目（本次）

- Python 快取目錄：`__pycache__/`（全專案）
- 本機虛擬環境：`venv/`
- 歷史快照資料夾：`.history/`
- 過時備援程式：`app_old.py`
- 日期快照 JSON：
  - `room_status_2025-12-01.json`
  - `room_status_2025-12-02.json`
  - `room_status_2025-12-03.json`
  - `workday_status_2025-12-03.json`
  - `workday_status_2025-12-04.json`
- 除錯輸出 JSON：
  - `debug_occupied_status.json`
  - `debug_room_status.json`
- 執行與測試輸出：
  - `server.log`
  - `line_bot_log.txt`
  - `parse_results*.txt`
  - `test_*output*.txt`

## 已新增忽略規則

新增 `.gitignore`，避免再次提交：

- 快取與測試快取
- 虛擬環境
- `.env`
- log 與輸出檔
- 打包產物

## 保留原則

- 保留所有核心程式碼（`api/`, `core/`, `modules/`, `ai_parser/`）
- 保留現有測試檔與除錯腳本（便於回歸驗證）
- 不刪除資料庫 SQL 與部署腳本

## 後續可人工確認再刪除

以下類型通常可再進一步整理，但建議先確認仍有無運維需求：

- 根目錄 `debug_*.py` / `verify_*.py`
- 舊版教學或一次性修復報告
- 過期日期快照 `room_status_*.json`, `workday_status_*.json`
