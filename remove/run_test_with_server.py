#!/usr/bin/env python3
"""
自動化測試腳本 - 啟動 API 伺服器並運行測試
"""

import subprocess
import time
import os
import signal
import platform
import sys

def run_server_and_test():
    """啟動伺服器並運行測試，然後關閉伺服器"""
    # 確定當前操作系統
    is_windows = platform.system() == "Windows"
    
    # 儲存當前工作目錄
    current_dir = os.getcwd()
    print(f"當前工作目錄: {current_dir}")
    
    # 啟動伺服器進程
    print("\n1. 啟動 API 伺服器...")
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
            start_new_session=True  # 使用 start_new_session 代替 preexec_fn
        )
    
    try:
        # 等待服務器啟動
        print("   等待服務器啟動 (5 秒)...")
        time.sleep(5)
        
        # 檢查服務器是否成功啟動
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
                print("   繼續測試，但可能會失敗...")
        except subprocess.SubprocessError as e:
            print(f"   警告: 健康檢查失敗: {e}")
        
        # 運行測試腳本
        print("\n2. 運行 Python 測試腳本...")
        test_process = subprocess.run(
            ["python", "test_api.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # 輸出測試結果
        print("\n=== Python 測試腳本輸出 ===")
        print(test_process.stdout)
        
        if test_process.stderr:
            print("\n=== 錯誤輸出 ===")
            print(test_process.stderr)
        
        # 運行 PHP 測試腳本
        print("\n3. 運行 PHP 測試腳本...")
        php_test_process = subprocess.run(
            ["php", "test_spabot.php"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # 輸出 PHP 測試結果
        print("\n=== PHP 測試腳本輸出 ===")
        print(php_test_process.stdout)
        
        if php_test_process.stderr:
            print("\n=== 錯誤輸出 ===")
            print(php_test_process.stderr)
        
        # 測試總結
        print("\n4. 測試總結")
        python_success = test_process.returncode == 0
        php_success = php_test_process.returncode == 0
        
        print(f"   Python 測試: {'✓ 成功' if python_success else '✗ 失敗'}")
        print(f"   PHP 測試: {'✓ 成功' if php_success else '✗ 失敗'}")
        print(f"   總體結果: {'✓ 成功' if python_success and php_success else '✗ 失敗'}")
    
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
        print("\n5. 關閉伺服器...")
        try:
            if is_windows:
                # Windows 使用特定信號
                os.kill(server_process.pid, signal.SIGTERM)
            else:
                # Unix/Linux/Mac 使用進程組 ID
                pgid = os.getpgid(server_process.pid)
                os.killpg(pgid, signal.SIGTERM)
            
            # 等待伺服器關閉
            server_process.wait(timeout=5)
            print("   服務器已成功關閉 ✓")
        except OSError as e:
            print(f"   關閉服務器時發生錯誤: {e}")
            print("   嘗試強制終止...")
            try:
                server_process.kill()
                print("   服務器已強制終止 ✓")
            except OSError as kill_error:
                print(f"   無法終止服務器進程: {kill_error}")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("自動化測試 - LINE Bot 自然語言處理")
    print("=" * 60)
    
    success = run_server_and_test()
    
    print("\n測試執行" + ("成功 ✓" if success else "失敗 ✗"))
    sys.exit(0 if success else 1)
