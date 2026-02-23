#!/bin/bash
# Ubuntu 專用調試腳本 - AI Server 2 服務

echo "===== 系統信息 ====="
echo "主機名稱: $(hostname)"
echo "發行版: $(lsb_release -d 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME)"
echo "內核版本: $(uname -r)"
echo ""

echo "===== 服務狀態 ====="
systemctl status aiserver2.service
echo ""

echo "===== systemd 日誌信息 ====="
journalctl -u aiserver2.service -n 50 --no-pager
echo ""

echo "===== Python 環境 ====="
which python3
python3 --version
echo ""

echo "===== 工作目錄檢查 ====="
SERVICE_DIR=$(grep WorkingDirectory /etc/systemd/system/aiserver2.service | cut -d= -f2)
echo "服務配置的工作目錄: $SERVICE_DIR"
if [ -d "$SERVICE_DIR" ]; then
  echo "目錄存在"
  ls -la "$SERVICE_DIR"
else
  echo "錯誤: 目錄不存在!"
fi
echo ""

echo "===== 關鍵文件檢查 ====="
if [ -f "$SERVICE_DIR/start_server.py" ]; then
  echo "start_server.py 存在"
else
  echo "錯誤: start_server.py 不存在!"
fi

if [ -f "$SERVICE_DIR/app.py" ]; then
  echo "app.py 存在"
else
  echo "錯誤: app.py 不存在!"
fi

if [ -f "$SERVICE_DIR/.env" ]; then
  echo ".env 文件存在"
else
  echo "警告: .env 文件不存在!"
fi
echo ""

echo "===== 權限檢查 ====="
if id www-data &>/dev/null; then
  echo "www-data 用戶存在"
  echo "工作目錄權限:"
  ls -ld "$SERVICE_DIR"
  echo "工作目錄擁有者:"
  stat -c "%U:%G" "$SERVICE_DIR"
else
  echo "錯誤: www-data 用戶不存在!"
fi
echo ""

echo "===== Redis 檢查 ====="
if systemctl is-active redis-server &>/dev/null || systemctl is-active redis &>/dev/null; then
  echo "Redis 服務正在運行"
else
  echo "警告: Redis 服務未運行!"
fi
echo ""

echo "===== 手動測試運行 ====="
echo "嘗試以 www-data 用戶身份運行服務..."
cd "$SERVICE_DIR"
sudo -u www-data python3 -c "import sys; print(f'Python 版本: {sys.version}')"
echo ""
echo "嘗試導入主要模塊..."
sudo -u www-data python3 -c "
try:
    import fastapi, uvicorn, pydantic, dotenv
    print('✓ 核心依賴導入成功')
except ImportError as e:
    print(f'✗ 依賴導入錯誤: {e}')
"
echo ""

echo "===== 解決方案建議 ====="
echo "1. 確保工作目錄正確且存在"
echo "2. 確保 www-data 用戶擁有適當的權限"
echo "3. 確保所有必要的 Python 依賴已安裝"
echo "4. 檢查 .env 文件是否存在且配置正確"
echo "5. 檢查 Redis 服務是否運行"
echo ""

echo "===== 命令參考 ====="
echo "重啟服務: sudo systemctl restart aiserver2"
echo "查看服務狀態: sudo systemctl status aiserver2"
echo "查看服務日誌: sudo journalctl -u aiserver2 -f"
echo "安裝依賴: sudo pip3 install -r $SERVICE_DIR/requirements.txt"
echo "檢查權限: sudo chown -R www-data:www-data $SERVICE_DIR"
