#!/bin/bash
# AI Server 2 服務調試腳本

# 檢查服務狀態
echo "====== 服務狀態 ======"
systemctl status aiserver2.service
echo ""

# 檢查日誌
echo "====== 服務日誌 (最近 50 行) ======"
journalctl -u aiserver2.service -n 50 --no-pager
echo ""

# 檢查環境
echo "====== 服務環境變數 ======"
systemctl show-environment
echo ""

# 檢查服務配置文件
echo "====== 服務配置文件 ======"
cat /etc/systemd/system/aiserver2.service
echo ""

# 嘗試手動運行
echo "====== 嘗試手動運行 ======"
cd $(grep WorkingDirectory /etc/systemd/system/aiserver2.service | cut -d= -f2)
echo "工作目錄: $(pwd)"
echo "Python 版本: $(python3 --version)"

# 檢查文件存在
echo "====== 關鍵文件檢查 ======"
ls -la start_server.py
ls -la app.py
ls -la requirements.txt
echo ""

# 檢查 .env 文件
echo "====== .env 文件檢查 ======"
if [ -f .env ]; then
    echo ".env 文件存在"
    grep -v "PASSWORD" .env | grep -v "SECRET" # 不顯示敏感信息
else
    echo ".env 文件不存在！"
fi
echo ""

echo "調試完成。如果服務仍有問題，請檢查上述信息是否有錯誤提示。"
