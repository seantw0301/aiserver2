#!/bin/bash
# AI Server 2 服務安裝腳本
# 此腳本將安裝aiserver2服務到systemd，以便使用systemctl管理

# 檢查是否以root運行
if [ "$EUID" -ne 0 ]; then
  echo "請以root用戶或使用sudo運行此腳本"
  exit 1
fi

# 獲取腳本所在目錄的絕對路徑
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 服務檔案路徑
SERVICE_FILE="aiserver2.service"
SERVICE_DEST="/etc/systemd/system/aiserver2.service"

# 創建www-data用戶（如果不存在）
if ! id -u www-data &>/dev/null; then
    echo "創建www-data用戶..."
    useradd -r -s /bin/false www-data
fi

# 設置工作目錄的權限
echo "設置目錄權限..."
chown -R www-data:www-data "$SCRIPT_DIR"
chmod -R 755 "$SCRIPT_DIR"

# 檢查服務文件是否存在
if [ ! -f "$SERVICE_FILE" ]; then
    echo "錯誤：服務文件 $SERVICE_FILE 不存在！"
    exit 1
fi

# 檢查python3是否安裝
if ! command -v python3 &>/dev/null; then
    echo "錯誤：找不到python3。請先安裝Python 3。"
    exit 1
fi

# 檢查pip3是否安裝
if ! command -v pip3 &>/dev/null; then
    echo "錯誤：找不到pip3。請先安裝pip。"
    exit 1
fi

# 檢查redis是否安裝
if ! systemctl status redis &>/dev/null && ! systemctl status redis-server &>/dev/null; then
    echo "警告：未找到Redis服務。請確保Redis已安裝並運行。"
    read -p "是否繼續安裝？ (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 安裝Python依賴
echo "安裝Python依賴..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
else
    echo "警告：找不到requirements.txt文件"
fi

# 修改服務文件中的路徑
echo "更新服務文件配置..."
sed -i "s|WorkingDirectory=.*|WorkingDirectory=$SCRIPT_DIR|" "$SERVICE_FILE"

# 確保 Python 路徑正確
PYTHON_PATH=$(which python3)
echo "使用 Python 路徑: $PYTHON_PATH"
sed -i "s|ExecStart=.*|ExecStart=$PYTHON_PATH start_server.py|" "$SERVICE_FILE"

# 複製服務檔案到systemd目錄
echo "安裝systemd服務..."
cp "$SERVICE_FILE" "$SERVICE_DEST"
echo "服務文件內容："
cat "$SERVICE_DEST"

# 重新加載systemd配置
echo "重新加載systemd配置..."
systemctl daemon-reload

# 啟用服務（開機自啟動）
echo "啟用服務開機自啟動..."
systemctl enable aiserver2.service

# 詢問是否立即啟動服務
read -p "是否立即啟動aiserver2服務？ (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "啟動aiserver2服務..."
    systemctl start aiserver2.service
    echo "服務狀態："
    systemctl status aiserver2.service
fi

echo "=========================================="
echo "安裝完成！您現在可以使用以下命令管理服務："
echo "  啟動服務: sudo systemctl start aiserver2"
echo "  停止服務: sudo systemctl stop aiserver2"
echo "  重啟服務: sudo systemctl restart aiserver2"
echo "  查看狀態: sudo systemctl status aiserver2"
echo "  開機自啟: sudo systemctl enable aiserver2"
echo "  禁用自啟: sudo systemctl disable aiserver2"
echo "=========================================="
