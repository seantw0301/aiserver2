#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BUG 修復總結
============

問題描述
--------
使用者在預約查詢中發現「可約師傅」欄位返回的是店家英文名（Ximen）而不是師傅名字（如川、獻）。

例如：原應顯示「可約師傅：川、獻」，卻顯示成「可約師傅：Ximen, ryan」

根本原因
--------
在 modules/multilang.py 的 restore_names() 函數中，正則表達式邏輯有缺陷：

1. 該函數使用佔位符系統來保護師傅名和店家名不被翻譯
   - 師傅佔位符格式：%W1%, %W2%, ... （W = Worker/師傅）
   - 店家佔位符格式：%S1%, %S2%, ... （S = Store/店家）

2. 原始代碼在還原佔位符時，對每個佔位符執行正則替換：
   ```python
   placeholder_base = placeholder.replace('%W', '%').replace('%S', '%')  # %W1% -> %1%
   pattern = f"(?i)%[Ww]{placeholder_base[1:]}"  # "(?i)%[Ww]1%"
   restored_text = re.sub(pattern, name_to_use, restored_text)
   ```

3. 問題在於：
   - 當 placeholder = "%S1%" 時，pattern = "(?i)%[Ww]1%"
   - 這個正則式會匹配 "%W1%" 和 "%w1%"
   - 結果是：當替換 %S1%（店家「西門」）時，正則式會錯誤地也替換掉 %W1%（師傅「川」）

4. 導致結果：
   - %W1% 和 %S1% 都被替換成 "西門"
   - 最終師傅名被店家名覆蓋

修復方案
--------
更新 restore_names() 函數的正則表達式邏輯，正確區分師傅和店家佔位符：

```python
if placeholder.startswith('%W') or placeholder.startswith('%w'):
    # 師傅佔位符：只匹配 %W 或 %w，不匹配 %S
    placeholder_num = placeholder[2:-1]  # 從 %W1% 提取 1
    pattern = f"(?i)%[Ww]{placeholder_num}%"  # 匹配 %W1% 或 %w1%
elif placeholder.startswith('%S') or placeholder.startswith('%s'):
    # 店家佔位符：只匹配 %S 或 %s，不匹配 %W
    placeholder_num = placeholder[2:-1]  # 從 %S1% 提取 1
    pattern = f"(?i)%[Ss]{placeholder_num}%"  # 匹配 %S1% 或 %s1%
else:
    # 未知佔位符格式，跳過正則替換
    continue
```

修改的文件
----------
- modules/multilang.py: restore_names() 函數（第153-192行）

測試結果
--------
✅ 所有回歸測試通過 (10/10)
- 師傅列表中的名字：正確
- 師傅和店家名混合：正確  
- 店家和師傅名：正確
- 複雜情況（多個師傅和店家）：正確
- 邊界情況：正確
- 重複出現：正確

影響範圍
--------
這個修復影響所有使用多語言翻譯系統的功能，包括：
1. 跨語系的預約查詢結果
2. 多語言的師傅和店家名稱翻譯
3. 任何涉及佔位符替換和還原的翻譯流程

建議
----
1. 在 CI/CD 管道中增加多語言系統的單元測試
2. 定期運行 test_multilang_regression.py 來檢測迴歸
3. 考慮為佔位符系統增加更詳細的日誌，便於除錯
"""

print(__doc__)
