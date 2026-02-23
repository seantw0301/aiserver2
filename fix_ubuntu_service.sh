#!/bin/bash
# Ubuntu 環境下 AI Server 2 服務修復腳本

# 檢查是否以 root 運行
if [ "$EUID" -ne 0 ]; then
  echo "請以 root 用戶或使用 sudo 運行此腳本"
  exit 1
fi

# 獲取腳本所在目錄的絕對路徑
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "==== AI Server 2 服務修復腳本 ===="
echo "工作目錄: $SCRIPT_DIR"

# 確保存在 www-data 用戶
if ! id -u www-data &>/dev/null; then
    echo "創建 www-data 用戶..."
    useradd -r -s /bin/false www-data
fi

# 確保權限正確
echo "設置目錄權限..."
chown -R www-data:www-data "$SCRIPT_DIR"
chmod -R 755 "$SCRIPT_DIR"

# 檢查 Python 環境
echo "檢查 Python 環境..."
if ! command -v python3 &>/dev/null; then
    echo "錯誤: 找不到 python3。請先安裝 Python 3"
    echo "運行: sudo apt update && sudo apt install -y python3 python3-pip"
    exit 1
fi

# 確保 pip 已安裝
if ! command -v pip3 &>/dev/null; then
    echo "安裝 pip3..."
    apt update && apt install -y python3-pip
fi

# 安裝/更新 Python 依賴
echo "安裝 Python 依賴..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

# 檢查 Redis
if ! systemctl is-active redis-server &>/dev/null && ! systemctl is-active redis &>/dev/null; then
    echo "安裝並啟動 Redis..."
    apt update && apt install -y redis-server
    systemctl enable redis-server
    systemctl start redis-server
fi

# 更新服務文件
echo "更新服務文件..."
cat > /etc/systemd/system/aiserver2.service << EOL
[Unit]
Description=AI Server 2 Service
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$SCRIPT_DIR
ExecStart=$(which python3) $SCRIPT_DIR/start_server.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=aiserver2
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOL

echo "服務文件已更新，內容如下:"
cat /etc/systemd/system/aiserver2.service

# 確保 .env 文件存在
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "創建默認 .env 文件..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    chown www-data:www-data "$SCRIPT_DIR/.env"
fi

# 重新載入 systemd 配置
echo "重新載入 systemd 配置..."
systemctl daemon-reload

# 重啟服務
echo "重啟服務..."
systemctl restart aiserver2.service

# 檢查服務狀態
echo "服務狀態:"
systemctl status aiserver2.service

echo "==== 修復完成 ===="
echo "如果服務仍有問題，請運行 debug_ubuntu.sh 獲取詳細診斷信息"
