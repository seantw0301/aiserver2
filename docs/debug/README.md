# Debug 目錄

此目錄存放除錯與診斷工具，不包含測試腳本。

## 目前檔案

```text
debug/
├── README.md
├── debug_api.php
├── debug_detailed.php
├── debug_service.sh
├── debug_ubuntu.sh
└── integration_examples.py
```

## 用途

- `debug_api.php`：API 請求除錯
- `debug_detailed.php`：詳細診斷輸出
- `debug_service.sh`：服務狀態與啟停檢查
- `debug_ubuntu.sh`：Ubuntu 環境診斷
- `integration_examples.py`：整合呼叫範例

## 使用建議

- 先確認 API 服務已啟動
- 優先在開發或 staging 環境操作
- 涉及 Redis / DB 的腳本請先備份關鍵資料
