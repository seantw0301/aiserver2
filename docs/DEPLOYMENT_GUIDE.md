# LINE Bot 部署指南

## 當前架構問題

**問題：** 遠端伺服器 `https://www.twn.pw/line/spa/spabot_new.php` 無法連接到本地 API `http://localhost:5001/parse`

## 解決方案

### 選項 1：將 Python API 部署到公開伺服器（推薦）

1. **在遠端伺服器上部署 Python API**
   ```bash
   # 上傳整個專案到遠端伺服器
   scp -r /Volumes/aiserver2/* user@www.twn.pw:/path/to/api/
   
   # SSH 連接到遠端伺服器
   ssh user@www.twn.pw
   
   # 安裝依賴
   cd /path/to/api
   pip install -r requirements.txt
   
   # 啟動 API 服務（使用 systemd 或 supervisor）
   python3 app.py
   ```

2. **修改 spabot_new.php 的 API URL**
   ```php
   // 在 callNaturalLanguageAPI 函數中
   $url = 'http://localhost:5001/parse';  // 修改前
   $url = 'http://127.0.0.1:5001/parse';  // 修改後（如果 API 在同一台伺服器）
   // 或
   $url = 'https://api.twn.pw:5001/parse'; // 如果 API 在不同伺服器
   ```

3. **更新防火牆設定**
   ```bash
   # 如果 API 和 PHP 在同一台伺服器，只需開放內部訪問
   # 如果在不同伺服器，需要開放 5001 port
   sudo firewall-cmd --add-port=5001/tcp --permanent
   sudo firewall-cmd --reload
   ```

### 選項 2：使用 ngrok 臨時測試（開發用）

1. **安裝 ngrok**
   ```bash
   brew install ngrok  # macOS
   ```

2. **啟動 ngrok 隧道**
   ```bash
   # 啟動 Python API
   python3 app.py
   
   # 在另一個終端啟動 ngrok
   ngrok http 5001
   ```

3. **使用 ngrok 提供的公開 URL**
   ```
   Forwarding: https://xxxx-xxx-xxx-xxx.ngrok.io -> http://localhost:5001
   ```

4. **修改 spabot_new.php**
   ```php
   $url = 'https://xxxx-xxx-xxx-xxx.ngrok.io/parse';
   ```

### 選項 3：將 API 和 PHP 部署在同一台伺服器

**最佳實踐架構：**

```
遠端伺服器 (www.twn.pw)
├── Web Server (Apache/Nginx)
│   └── /line/spa/spabot_new.php (Port 80/443)
│
└── Python API (FastAPI/Uvicorn)
    └── app.py (Port 5001)
    └── 只監聽 127.0.0.1（內部訪問）
```

**配置步驟：**

1. 在 `.env` 中設定只監聽本地：
   ```
   API_HOST=127.0.0.1
   API_PORT=5001
   ```

2. 在 `spabot_new.php` 中使用本地地址：
   ```php
   $url = 'http://127.0.0.1:5001/parse';
   ```

## 檢查清單

- [ ] Python API 已部署並運行
- [ ] API 可以從 PHP 伺服器訪問
- [ ] PHP 中的 API URL 已更新
- [ ] 防火牆規則已配置
- [ ] LINE webhook URL 已設定為 `https://www.twn.pw/line/spa/spabot_new.php`
- [ ] 已測試完整流程（LINE → PHP → Python API → PHP → LINE）

## 測試步驟

1. **測試 Python API**
   ```bash
   curl -X POST http://localhost:5001/parse \
     -H "Content-Type: application/json" \
     -d '{"key": "test_user", "message": "明天22:47西門90分鐘"}'
   ```

2. **測試 PHP 調用 API**
   ```bash
   php test_php_integration.php
   ```

3. **測試 LINE Bot**
   - 在 LINE 中發送訊息
   - 檢查 `/Volumes/aiserver2/line_bot_log.txt`（或遠端伺服器上的對應日誌）

## 當前狀態

✅ Python API 本地運行正常 (localhost:5001)
✅ API 返回正確的 line_messages 格式
❌ 遠端 spabot_new.php 無法連接本地 API
❓ 需要確認遠端伺服器配置

## 下一步行動

1. 確認遠端伺服器環境
2. 部署 Python API 到遠端伺服器
3. 更新 spabot_new.php 的 API URL
4. 測試完整流程
