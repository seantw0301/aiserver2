# Scripts 分層說明

此目錄存放非 API 主流程的工具與維運腳本。

## 結構

- `scripts/debug/`：除錯腳本（原 `debug_*.py`）
- `scripts/verify/`：驗證腳本（原 `verify_*.py`）
- `scripts/check/`：檢查腳本（原 `check_*.py`）
- `scripts/tools/`：其他工具腳本（批次處理、模擬、範例）

## 執行方式

建議在專案根目錄執行，例如：

```bash
python3 scripts/debug/debug_full_flow.py
python3 scripts/verify/verify_calculation.py
python3 scripts/check/check_masseur.py
python3 scripts/tools/simulate_parse_form.py
```
