# 模組化遷移說明

## 目標

將啟動流程與應用組裝邏輯由單檔拆分為可維護、可測試、可重用模組。

## 本次調整

### 1. 新增 `api/bootstrap` 子模組

- `application.py`
  - `create_app()`：統一建立 FastAPI 應用、掛載 middleware、註冊 routers、設定首頁與錯誤處理器。
  - `app`：模組級 app 實例（供 uvicorn 載入）。
- `settings.py`
  - `ApiSettings`：集中管理啟動設定（host/port/debug/workers）。
  - `get_settings()`：快取設定讀取，避免重複解析。
- `runner.py`
  - `run_api_server()`：統一 uvicorn 啟動流程與啟動輸出訊息。

### 2. `app.py` 改為薄入口

- 不再直接承載全部組裝與啟動細節。
- 改為：匯出 `app`，並在 script 模式呼叫 `run_api_server()`。

### 3. `start_server.py` 改為薄入口

- 僅呼叫 `run_api_server()`。
- 消除與 `app.py` 的重複設定與重複邏輯。

### 4. 依賴更新

- 新增 `pydantic-settings`，支援型別化環境設定。

### 5. 根目錄腳本分層

- 將工具腳本依用途拆分到 `scripts/`：
  - `scripts/debug/`（`debug_*.py`）
  - `scripts/verify/`（`verify_*.py`）
  - `scripts/check/`（`check_*.py`）
  - `scripts/tools/`（批次測試、模擬、範例）
- 使根目錄聚焦在服務入口、設定與核心模組。

## 效益

- 降低重複程式碼與設定分散風險。
- 可獨立測試 app 建立邏輯與啟動器邏輯。
- 後續擴充（例如分環境設定、測試配置）更容易。

## 建議下一步（可選）

- 將根目錄工具腳本依用途搬移至 `scripts/`（debug/verify/migration）。
- 增加 `tests/bootstrap/` 針對 `create_app()` 與 `settings` 的單元測試。
- 導入 `pre-commit`（format/lint/import sort）。
