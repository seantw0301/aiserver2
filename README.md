# aiserver2

師傅班表管理 API 專案（FastAPI），已完成啟動流程模組化與目錄清理。

## 專案重點

- FastAPI 非同步 API 架構
- 模組化啟動流程（`api/bootstrap`）
- 路由分層（`api/routes`）
- 核心領域邏輯（`core`、`modules`、`ai_parser`）

## 模組化後核心結構

```text
api/
  routes/                # API 路由層
  bootstrap/             # 新增：應用工廠、設定、啟動器
core/                    # 基礎資料與核心業務邏輯
modules/                 # 領域模組（預約、多語言、整合等）
ai_parser/               # 自然語言解析子系統
app.py                   # 薄入口（暴露 app + 啟動）
start_server.py          # 薄入口（僅啟動）
```

## 啟動方式

1. 安裝依賴

```bash
pip install -r requirements.txt
```

2. 啟動 API

```bash
python start_server.py
```

或

```bash
python app.py
```

## 環境變數

可在 `.env` 設定：

- `API_HOST`（預設：`0.0.0.0`）
- `API_PORT`（預設：`5001`）
- `DEBUG`（預設：`True`）
- `WORKERS`（預設：`1`，若非 debug 最少建議 `4`）

## 文件

- [模組化遷移說明](docs/MODULARIZATION.md)
- [清理與刪除策略](docs/CLEANUP.md)

## API 文件

啟動後可用：

- Swagger UI: `/docs`
- ReDoc: `/redoc`
