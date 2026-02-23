"""
Modules Package
包含所有業務邏輯模組

Modules:
- lang: 語系偵測與管理
- greeting: 每日問候語
- appointment: 預約處理
- keyword: 關鍵字搜尋
- multilang: 多國語系翻譯
- integration: 訊息整合與格式化（第六階段）
"""

from . import lang
from . import greeting
from . import appointment
from . import keyword
from . import multilang
from . import integration

__all__ = ['lang', 'greeting', 'appointment', 'keyword', 'multilang', 'integration']
