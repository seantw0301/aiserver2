# 多語言佔位符系統 Bug 修復報告

## 問題總結

**問題描述**: 在預約查詢結果中，「可約師傅」欄位返回的是店家英文名（如 `Ximen`）而不是師傅名字（如 `川`、`獻`）。

**受影響的功能**:
- 多語言預約查詢結果
- 跨語系翻譯系統
- 所有使用佔位符保護機制的翻譯流程

## 根本原因

**位置**: `modules/multilang.py` 的 `restore_names()` 函數（第153-192行）

**問題分析**:

佔位符系統使用以下格式：
- 師傅佔位符: `%W1%`, `%W2%`, ... （W = Worker）
- 店家佔位符: `%S1%`, `%S2%`, ... （S = Store）

原始代碼在還原佔位符時，對每個佔位符執行相同的正則替換模式：

```python
# 缺陷邏輯
placeholder_base = placeholder.replace('%W', '%').replace('%S', '%')  # %W1% -> %1%
pattern = f"(?i)%[Ww]{placeholder_base[1:]}"  # "(?i)%[Ww]1%"
restored_text = re.sub(pattern, name_to_use, restored_text)
```

**具體問題**:

當 `placeholder = "%S1%"` 時：
- `placeholder_base = "%1%"`
- `pattern = "(?i)%[Ww]1%"`
- 此正則式會匹配 `%W1%` 和 `%w1%`（因為字符類 `[Ww]` 包含了 W 和 w）
- 結果：替換店家名「西門」時，正則式錯誤地也替換掉了師傅名「川」

## 修復方案

更新 `restore_names()` 函數，正確區分師傅和店家佔位符：

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
    logger.warning(f"未知佔位符格式: {placeholder}")
    continue

restored_text = re.sub(pattern, name_to_use, restored_text)
```

## 修改的文件

- **modules/multilang.py**: `restore_names()` 函數（第153-192行）

## 測試結果

✅ **所有回歸測試通過** (10/10)

### 測試用例

| 原始文本 | 還原(中文) | 還原(英文) | 狀態 |
|---------|-----------|---------|------|
| 可約師傅：川、獻 | ✓ 可約師傅：川、獻 | ✓ 可約師傅：River、ryan | ✅ PASS |
| 川師傅在西門店有空 | ✓ 川師傅在西門店有空 | ✓ River師傅在Ximen店有空 | ✅ PASS |
| 西門的川 | ✓ 西門的川 | ✓ Ximen的River | ✅ PASS |
| 川、獻、豪在西門有空 | ✓ 川、獻、豪在西門有空 | ✓ River、ryan、Lance在Ximen有空 | ✅ PASS |
| 西門、延吉、家樂福三間分店的師傅川、獻都有空 | ✓ 西門、延吉、家樂福三間分店的師傅川、獻都有空 | ✓ Ximen、Yanji(Taipei Dome)、Ximen2(Xining Carrefour)三間分店的師傅River、ryan都有空 | ✅ PASS |
| 可約師傅：川 | ✓ 可約師傅：川 | ✓ 可約師傅：River | ✅ PASS |
| 只有店家：西門 | ✓ 只有店家：西門 | ✓ 只有店家：Ximen | ✅ PASS |
| 師傅川 | ✓ 師傅川 | ✓ 師傅River | ✅ PASS |
| 店家西門 | ✓ 店家西門 | ✓ 店家Ximen | ✅ PASS |
| 川和川一樣，在西門和西門 | ✓ 川和川一樣，在西門和西門 | ✓ River和River一樣，在Ximen和Ximen | ✅ PASS |

### 回歸測試命令

```bash
python test_multilang_regression.py
```

## 影響範圍

此修復影響所有使用多語言翻譯系統的功能：

1. **預約查詢**: 師傅和店家名稱正確顯示
2. **多語言翻譯**: 跨語系翻譯時名稱保持正確
3. **佔位符系統**: 所有涉及名稱提取和還原的流程

## 建議

1. ✅ 在 CI/CD 管道中增加多語言系統的單元測試
2. ✅ 定期運行 `test_multilang_regression.py` 檢測迴歸
3. ✅ 為佔位符系統增加詳細的日誌記錄，便於除錯
4. ✅ 考慮實現更強大的佔位符驗證機制

## 版本信息

- **修復日期**: 2025-12-29
- **修復者**: AI Assistant
- **相關文件**: modules/multilang.py
- **變更行數**: 第153-192行

## 驗證方式

執行以下命令確認修復成功：

```bash
# 1. 運行多語言回歸測試
python test_multilang_regression.py

# 2. 測試完整的預約查詢流程
python debug_query_only.py

# 3. 驗證多語言系統
python debug_multilang.py
```
