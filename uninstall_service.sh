  #!/bin/bash
# AI Server 2 服務卸載腳本
# 此腳本將從systemd中卸載aiserver2服務

# 檢查是否以root運行
if [ "$EUID" -ne 0 ]; then
  echo "請以root用戶或使用sudo運行此腳本"
  exit 1
fi

# 服務檔案路徑
SERVICE_NAME="aiserver2"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

# 檢查服務是否存在
if [ ! -f "$SERVICE_FILE" ]; then
    echo "服務 $SERVICE_NAME 未安裝，無需卸載。"
    exit 0
fi

# 停止服務
echo "停止 $SERVICE_NAME 服務..."
systemctl stop $SERVICE_NAME.service

# 禁用服務
echo "禁用 $SERVICE_NAME 服務..."
systemctl disable $SERVICE_NAME.service

# 刪除服務檔案
echo "刪除服務檔案..."
rm -f "$SERVICE_FILE"

# 重新加載systemd配置
echo "重新加載systemd配置..."
systemctl daemon-reload
systemctl reset-failed

echo "=========================================="
echo "$SERVICE_NAME 服務已成功卸載！"
echo "=========================================="
