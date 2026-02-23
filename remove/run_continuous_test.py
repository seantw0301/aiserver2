#!/usr/bin/env python3
"""
連續對話測試腳本（帶伺服器管理）
"""

import subprocess
import time
import os
import signal
import platform
import sys

def run_continuous_conversation_test():
    """啟動伺服器並運行連續對話測試"""
    # 確定當前操作系統
    is_windows = platform.system() == "Windows"
    
    print("=" * 70)
    print("連續對話測試 - 帶自動伺服器管理")
    print("=" * 70)
    
    # 啟動伺服器進程
    print("1. 啟動 API 伺服器...")
    if is_windows:
        server_process = subprocess.Popen(
            ["python", "start_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        server_process = subprocess.Popen(
            ["python", "start_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
    
    try:
        # 等待服務器啟動
        print("   等待服務器啟動 (5 秒)...")
        time.sleep(5)
        
        # 檢查服務器狀態
        print("   檢查服務器狀態...")
        try:
            health_check = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "http://localhost:8000/docs"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if health_check.stdout.strip() == "200":
                print("   服務器啟動成功 ✓")
            else:
                print(f"   警告: 服務器可能未正確啟動 (狀態碼: {health_check.stdout.strip()})")
        except subprocess.SubprocessError as e:
            print(f"   警告: 健康檢查失敗: {e}")
        
        # 運行連續對話測試
        print("\n2. 運行連續對話測試...")
        test_process = subprocess.run(
            ["python", "test_continuous_conversation.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # 輸出測試結果
        print("\n=== 連續對話測試輸出 ===")
        print(test_process.stdout)
        
        if test_process.stderr:
            print("\n=== 錯誤輸出 ===")
            print(test_process.stderr)
        
        # 測試總結
        print("\n3. 測試總結")
        test_success = test_process.returncode == 0
        
        print(f"   連續對話測試: {'✓ 成功' if test_success else '✗ 失敗'}")
        
        return test_success
    
    except subprocess.SubprocessError as e:
        print(f"\n❌ 子進程錯誤: {e}")
        return False
    except OSError as e:
        print(f"\n❌ 操作系統錯誤: {e}")
        return False
    except KeyboardInterrupt:
        print("\n❌ 測試被手動中斷")
        return False
    finally:
        # 關閉伺服器進程
        print("\n4. 關閉伺服器...")
        try:
            if is_windows:
                os.kill(server_process.pid, signal.SIGTERM)
            else:
                pgid = os.getpgid(server_process.pid)
                os.killpg(pgid, signal.SIGTERM)
            
            server_process.wait(timeout=5)
            print("   服務器已成功關閉 ✓")
        except OSError as e:
            print(f"   關閉服務器時發生錯誤: {e}")
            try:
                server_process.kill()
                print("   服務器已強制終止 ✓")
            except OSError as kill_error:
                print(f"   無法終止服務器進程: {kill_error}")

if __name__ == "__main__":
    success = run_continuous_conversation_test()
    print(f"\n連續對話測試結果: {'成功 ✓' if success else '失敗 ✗'}")
    sys.exit(0 if success else 1)
