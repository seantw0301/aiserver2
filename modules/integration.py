"""
整合模組 (Integration Module) - 第六階段
負責將所有訊息整理成 LINE SDK 可顯示的格式

支援的格式：
1. 純文字格式 (Text Message)
2. 帶有 menu 的格式 (Template Message - Buttons/Carousel)
3. Flex 格式 (Flex Message)

此階段必須將 greeting_message 加在所有訊息的開頭部份
"""

from typing import Dict, List, Any, Optional, Union
from datetime import datetime


class LineMessageFormatter:
    """LINE 訊息格式化器"""
    
    @staticmethod
    def format_text_message(text: str) -> Dict[str, Any]:
        """
        格式化純文字訊息
        
        Args:
            text: 文字內容
            
        Returns:
            LINE 文字訊息格式
        """
        return {
            "type": "text",
            "text": text
        }
    
    @staticmethod
    def format_buttons_template(
        title: str,
        text: str,
        actions: List[Dict[str, Any]],
        alt_text: str = "選單訊息"
    ) -> Dict[str, Any]:
        """
        格式化 Buttons Template 訊息 (Rich Menu)
        
        Args:
            title: 標題
            text: 內容文字
            actions: 按鈕動作列表 (最多4個)
            alt_text: 替代文字（推播通知顯示）
            
        Returns:
            LINE Template 訊息格式
        """
        return {
            "type": "template",
            "altText": alt_text,
            "template": {
                "type": "buttons",
                "title": title,
                "text": text,
                "actions": actions[:4]  # LINE 限制最多4個按鈕
            }
        }
    
    @staticmethod
    def format_carousel_template(
        columns: List[Dict[str, Any]],
        alt_text: str = "選單訊息"
    ) -> Dict[str, Any]:
        """
        格式化 Carousel Template 訊息 (多個 Buttons 組合)
        
        Args:
            columns: 欄位列表 (每個欄位是一個 buttons template)
            alt_text: 替代文字
            
        Returns:
            LINE Carousel Template 訊息格式
        """
        return {
            "type": "template",
            "altText": alt_text,
            "template": {
                "type": "carousel",
                "columns": columns[:10]  # LINE 限制最多10個欄位
            }
        }
    
    @staticmethod
    def format_flex_message(
        alt_text: str,
        contents: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        格式化 Flex Message
        
        Args:
            alt_text: 替代文字
            contents: Flex 內容 (bubble 或 carousel)
            
        Returns:
            LINE Flex Message 格式
        """
        return {
            "type": "flex",
            "altText": alt_text,
            "contents": contents
        }
    
    @staticmethod
    def create_reservation_flex_bubble(
        reservation_data: Dict[str, Any],
        greeting_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        創建預約資訊的 Flex Bubble
        
        Args:
            reservation_data: 預約資料
            greeting_message: 問候語（將整合到 Flex Message 中）
            
        Returns:
            Flex Bubble 格式
        """
        # 建立預約資訊內容
        body_contents = []
        
        # 如果有問候語，先加入問候語
        if greeting_message:
            body_contents.append({
                "type": "text",
                "text": greeting_message,
                "weight": "bold",
                "size": "lg",
                "color": "#1DB446",
                "wrap": True
            })
            body_contents.append({
                "type": "separator",
                "margin": "md"
            })
        
        # 標題
        body_contents.append({
            "type": "text",
            "text": "📋 預約查詢結果",
            "weight": "bold",
            "size": "xl",
            "color": "#1DB446"
        })
        
        body_contents.append({
            "type": "separator",
            "margin": "md"
        })
        
        # 查詢條件
        if reservation_data.get('branch'):
            branch_text = reservation_data.get('branch', '')
            if reservation_data.get('used_default_branch'):
                branch_text += "(默認值)"
            
            body_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": "🏪 店家：",
                        "size": "sm",
                        "color": "#555555",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": branch_text,
                        "size": "sm",
                        "color": "#111111",
                        "flex": 0,
                        "margin": "sm"
                    }
                ]
            })
        
        if reservation_data.get('masseur') and len(reservation_data.get('masseur', [])) > 0:
            body_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": "👨‍⚕️ 師傅：",
                        "size": "sm",
                        "color": "#555555",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": ", ".join(reservation_data.get('masseur', [])),
                        "size": "sm",
                        "color": "#111111",
                        "flex": 0,
                        "margin": "sm",
                        "wrap": True
                    }
                ]
            })
        
        if reservation_data.get('date'):
            body_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": "📅 日期：",
                        "size": "sm",
                        "color": "#555555",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": reservation_data.get('date', ''),
                        "size": "sm",
                        "color": "#111111",
                        "flex": 0,
                        "margin": "sm"
                    }
                ]
            })
        
        if reservation_data.get('time'):
            body_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": "⏰ 時間：",
                        "size": "sm",
                        "color": "#555555",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": reservation_data.get('time', ''),
                        "size": "sm",
                        "color": "#111111",
                        "flex": 0,
                        "margin": "sm"
                    }
                ]
            })
        
        if reservation_data.get('project'):
            project_text = f"{reservation_data.get('project', '')} 分鐘"
            if reservation_data.get('used_default_project'):
                project_text += "(默認值)"
            
            body_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": "⏱️ 療程：",
                        "size": "sm",
                        "color": "#555555",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": project_text,
                        "size": "sm",
                        "color": "#111111",
                        "flex": 0,
                        "margin": "sm"
                    }
                ]
            })
        
        if reservation_data.get('count'):
            body_contents.append({
                "type": "box",
                "layout": "baseline",
                "margin": "sm",
                "contents": [
                    {
                        "type": "text",
                        "text": "👥 人數：",
                        "size": "sm",
                        "color": "#555555",
                        "flex": 0
                    },
                    {
                        "type": "text",
                        "text": f"{reservation_data.get('count', '')} 位",
                        "size": "sm",
                        "color": "#111111",
                        "flex": 0,
                        "margin": "sm"
                    }
                ]
            })
        
        # 查詢結果
        if reservation_data.get('response_message'):
            body_contents.append({
                "type": "separator",
                "margin": "md"
            })
            body_contents.append({
                "type": "text",
                "text": reservation_data.get('response_message', ''),
                "size": "sm",
                "color": "#111111",
                "margin": "md",
                "wrap": True
            })
        
        bubble = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": body_contents
            }
        }
        
        return bubble


def prepend_greeting_to_message(message: str, greeting: Optional[str]) -> str:
    """
    將問候語加到訊息開頭
    
    Args:
        message: 原始訊息
        greeting: 問候語
        
    Returns:
        加上問候語的訊息
    """
    if greeting:
        return f"{greeting}\n\n{message}"
    return message


def integrate_response_messages(
    parsed_data: Dict[str, Any],
    message_format: str = "text"
) -> Dict[str, Any]:
    """
    整合所有回應訊息，並加上問候語
    
    這是第六階段的核心函數，負責：
    1. 檢查是否有 greeting_message
    2. 將 greeting_message 整合到訊息內容中（而非分開多筆）
    3. 根據 message_format 格式化訊息為 LINE SDK 可接受的格式
    
    重要：為了符合 LINE SDK 的最佳實踐，儘量將訊息整合在單一筆回應中
    
    Args:
        parsed_data: 從前五個階段處理後的資料
        message_format: 訊息格式類型 ("text", "buttons", "carousel", "flex")
        
    Returns:
        包含 line_messages 的整合資料
    """
    formatter = LineMessageFormatter()
    greeting_message = parsed_data.get('greeting_message')
    response_message = parsed_data.get('response_message', '')
    
    # 準備 LINE 訊息列表
    line_messages = []
    
    # 將問候語整合到回應訊息中（單一訊息）
    integrated_message = response_message
    if greeting_message and response_message:
        integrated_message = f"{greeting_message}\n\n{response_message}"
    elif greeting_message:
        integrated_message = greeting_message
    
    # 如果是預約查詢，在訊息末尾添加提醒文字
    if parsed_data.get('isReservation', False) and integrated_message:
        reminder_text = "\n\n*提醒您：以上訊息僅為查詢非確認，您可以使用底部選單進行快速預約，二小時內或深夜時段需由客服人員協助預約"
        reminder_text = reminder_text + "\n家樂福店位於西門町西寧南路上，離捷運一號出口約步行6分鐘"
        integrated_message = integrated_message + reminder_text
    
    # 根據不同情況格式化主要訊息
    if message_format == "text":
        # 純文字格式 - 整合問候語和回應訊息在一起
        if integrated_message:
            line_messages.append(formatter.format_text_message(integrated_message))
    
    elif message_format == "flex":
        # Flex Message 格式 - 適用於預約查詢結果
        if parsed_data.get('isReservation', False):
            # 為 Flex Message 添加問候語到內容中
            flex_bubble = formatter.create_reservation_flex_bubble(parsed_data, greeting_message)
            flex_message = formatter.format_flex_message(
                alt_text="預約查詢結果",
                contents=flex_bubble
            )
            line_messages.append(flex_message)
        else:
            # 非預約訊息，使用純文字整合
            if integrated_message:
                line_messages.append(formatter.format_text_message(integrated_message))
    
    elif message_format == "buttons":
        # Buttons Template 格式 - 將問候語整合到 text 欄位中
        if integrated_message:
            # 示例：為關鍵字匹配提供相關選項
            actions = [
                {
                    "type": "message",
                    "label": "查看店家資訊",
                    "text": "店家資訊"
                },
                {
                    "type": "message",
                    "label": "查詢預約",
                    "text": "我要預約"
                }
            ]
            buttons_message = formatter.format_buttons_template(
                title="相關服務",
                text=integrated_message,
                actions=actions,
                alt_text=integrated_message[:20]  # 使用前20字作為替代文字
            )
            line_messages.append(buttons_message)
    
    elif message_format == "carousel":
        # Carousel Template 格式 - 可用於多個選項
        # 這裡可以根據需求自定義欄位內容
        pass  # 暫時保留，可依需求實作
    
    # 如果沒有任何訊息，直接返回空列表（不發送垃圾訊息）
    # 前端 (spabot_demo.php) 會檢查並直接忽略
    
    # 3. 將 LINE 訊息加入到回應資料中
    parsed_data['line_messages'] = line_messages
    parsed_data['message_format'] = message_format
    parsed_data['integration_timestamp'] = datetime.now().isoformat()
    
    return parsed_data


def auto_detect_message_format(parsed_data: Dict[str, Any]) -> str:
    """
    自動偵測應使用的訊息格式
    
    Args:
        parsed_data: 解析後的資料
        
    Returns:
        建議的訊息格式 ("text", "flex", "buttons", "carousel")
    
    注意：預設使用 text 格式以方便剪貼使用
    若需要使用 flex 或其他格式，請在呼叫 format_for_line_sdk 時
    使用 force_format 參數明確指定
    """
    # 預設統一使用純文字格式（方便剪貼使用）
    return "text"


def format_for_line_sdk(
    parsed_data: Dict[str, Any],
    auto_format: bool = True,
    force_format: Optional[str] = None
) -> Dict[str, Any]:
    """
    格式化為 LINE SDK 可用的格式（主要入口函數）
    
    Args:
        parsed_data: 從五階段處理後的資料
        auto_format: 是否自動偵測格式
        force_format: 強制使用指定格式 ("text", "flex", "buttons", "carousel")
        
    Returns:
        包含 line_messages 的整合資料
    """
    # 決定訊息格式
    if force_format:
        message_format = force_format
    elif auto_format:
        message_format = auto_detect_message_format(parsed_data)
    else:
        message_format = "text"
    
    # 整合訊息
    return integrate_response_messages(parsed_data, message_format)


# 便利函數：取得 LINE 訊息列表
def get_line_messages(parsed_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    從整合後的資料中取得 LINE 訊息列表
    
    Args:
        parsed_data: 整合後的資料
        
    Returns:
        LINE 訊息列表
    """
    return parsed_data.get('line_messages', [])


# 便利函數：取得純文字回應（用於 CLI 測試）
def get_text_response(parsed_data: Dict[str, Any]) -> str:
    """
    從整合後的資料中取得純文字回應（用於測試和 CLI 顯示）
    
    注意：此函數整合問候語和回應訊息在一起
    
    Args:
        parsed_data: 整合後的資料
        
    Returns:
        純文字回應（問候語+回應訊息整合在一起）
    """
    parts = []
    
    # 加入問候語
    if parsed_data.get('greeting_message'):
        parts.append(parsed_data['greeting_message'])
    
    # 加入回應訊息
    if parsed_data.get('response_message'):
        parts.append(parsed_data['response_message'])
    
    # 整合在一起，用兩個換行分隔
    return "\n\n".join(parts) if parts else ""
