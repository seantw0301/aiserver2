#!/bin/bash
# CentOS 7 專用修復腳本 - AI Server 2 服務

# 檢查是否以 root 運行
if [ "$EUID" -ne 0 ]; then
  echo "請以 root 用戶身份運行此腳本"
  exit 1
fi

echo "==== AI Server 2 服務修復腳本 (CentOS 7) ===="

WORK_DIR="/home/aiserver2"
cd "$WORK_DIR"

# 首先檢查可用的 Python 解釋器
echo "檢查系統 Python..."
SYSTEM_PYTHON=$(which python3 2>/dev/null)

if [ -z "$SYSTEM_PYTHON" ]; then
    echo "系統中未找到 python3，嘗試安裝..."
    yum install -y python3 python3-pip
    SYSTEM_PYTHON=$(which python3)
    
    if [ -z "$SYSTEM_PYTHON" ]; then
        echo "無法安裝 python3，使用默認 python..."
        SYSTEM_PYTHON=$(which python)
    fi
fi

echo "使用 Python 路徑: $SYSTEM_PYTHON"
$SYSTEM_PYTHON --version

# 確保 www-data 可以訪問 Python
# CentOS 通常使用 apache 而不是 www-data
if ! id -u www-data &>/dev/null; then
    echo "在 CentOS 上創建 www-data 用戶..."
    useradd -r -M -s /sbin/nologin www-data
fi

# 設置權限
echo "設置目錄權限..."
chown -R www-data:www-data "$WORK_DIR"
chmod -R 755 "$WORK_DIR"

# 確保 Python 可執行
if [[ "$SYSTEM_PYTHON" == "/root"* ]]; then
    echo "警告: Python 在 /root 目錄下，www-data 用戶無法訪問"
    echo "嘗試為 www-data 用戶安裝 Python..."
    
    # 使用系統 Python
    SYSTEM_PYTHON="/usr/bin/python3"
    if [ ! -f "$SYSTEM_PYTHON" ]; then
        echo "安裝系統 Python 3..."
        yum install -y python3 python3-pip
    fi
fi

# 安裝 Python 依賴
echo "安裝 Python 依賴..."
$SYSTEM_PYTHON -m pip install -r "$WORK_DIR/requirements.txt"

# 更新服務文件，使用系統 Python
echo "更新服務文件..."
cat > /etc/systemd/system/aiserver2.service << EOL
[Unit]
Description=AI Server 2 Service
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$WORK_DIR
ExecStart=$SYSTEM_PYTHON $WORK_DIR/start_server.py
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

# 重新載入 systemd 配置
echo "重新載入 systemd 配置..."
systemctl daemon-reload

# 重啟服務
echo "重啟服務..."
systemctl restart aiserver2.service
sleep 2

# 檢查服務狀態
echo "服務狀態:"
systemctl status aiserver2.service

echo "==== 修復完成 ===="
echo "如果服務仍有問題，請檢查日誌: journalctl -u aiserver2 -f"
