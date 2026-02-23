"""
多國語系翻譯模組
整合 Azure Translator API 和 Google Translate API
支援繁體中文到多國語系的翻譯
使用佔位符系統保護師傅名稱和店家名稱不被翻譯
"""

import requests
import uuid
import logging
import re
import os
from typing import Optional, List, Dict, Tuple
from core.database import db_config

logger = logging.getLogger(__name__)


# ==================== 佔位符系統 ====================

def get_staff_name_mapping() -> Dict[str, str]:
    """
    從資料庫獲取師傅名稱映射（中文名 -> 英文名）
    
    Returns:
        Dict[str, str]: 中文名到英文名的映射字典
    """
    try:
        connection = db_config.get_connection()
        if not connection:
            logger.error("無法連接資料庫獲取師傅名稱映射")
            return {}
        
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT DISTINCT name, staff 
            FROM Staffs 
            WHERE enable = 1 AND name != '' AND staff != ''
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        # 建立中文名到英文名的映射
        mapping = {}
        for row in results:
            chinese_name = row['name']
            english_name = row['staff'] or chinese_name  # 如果英文名為空，使用中文名
            if chinese_name:
                mapping[chinese_name] = english_name
        
        cursor.close()
        connection.close()
        
        logger.info(f"成功載入 {len(mapping)} 位師傅的名稱映射")
        return mapping
        
    except Exception as e:
        logger.error(f"獲取師傅名稱映射時發生錯誤: {str(e)}")
        return {}


def get_store_name_mapping() -> Dict[str, str]:
    try:
        connection = db_config.get_connection()
        if not connection:
            logger.error("無法連接資料庫獲取店家名稱映射")
            return {}
        
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT name, enname 
            FROM Store 
            WHERE name IS NOT NULL AND enname IS NOT NULL
        """
        cursor.execute(query)
        results = cursor.fetchall()
        
        # 建立中文名到英文名的映射
        mapping = {}
        for row in results:
            chinese_name = row['name']
            english_name = row['enname'] or chinese_name  # 如果英文名為空，使用中文名
            if chinese_name:
                mapping[chinese_name] = english_name
        
        cursor.close()
        connection.close()
        
        logger.info(f"成功載入 {len(mapping)} 間店家的名稱映射")
        return mapping
        
    except Exception as e:
        logger.error(f"獲取店家名稱映射時發生錯誤: {str(e)}")
        return {}


def extract_and_replace_names(text: str, staff_mapping: Dict[str, str], store_mapping: Dict[str, str]) -> Tuple[str, Dict[str, Tuple[str, str]]]:
    """
    從文本中提取師傅名稱和店家名稱，並用佔位符替換
    支援多個師傅和多個店家同時出現
    
    Args:
        text: 原始文本
        staff_mapping: 師傅名稱映射（中文 -> 英文）
        store_mapping: 店家名稱映射（中文 -> 英文）
        
    Returns:
        Tuple[str, Dict]: (替換後的文本, 佔位符映射字典)
        佔位符映射格式: {"%w1%": ("鞋", "Camper"), "%S1%": ("西門", "Ximen")}
    """
    if not text:
        return text, {}
    
    placeholder_map = {}
    modified_text = text
    
    # 步驟 1: 按長度排序，優先替換較長的名稱（避免部分匹配問題）
    # 例如："西門店" 應該在 "西門" 之前被替換
    all_store_names = sorted(store_mapping.keys(), key=len, reverse=True)
    all_staff_names = sorted(staff_mapping.keys(), key=len, reverse=True)
    
    # 步驟 2: 替換店家名稱
    store_counter = 1
    for chinese_name in all_store_names:
        if chinese_name in modified_text:
            # 為每個唯一的店家名稱分配一個佔位符
            placeholder = f"%S{store_counter}%"
            english_name = store_mapping[chinese_name]
            
            # 替換所有出現的該店家名稱
            modified_text = modified_text.replace(chinese_name, placeholder)
            placeholder_map[placeholder] = (chinese_name, english_name)
            store_counter += 1
    
    # 步驟 3: 替換師傅名稱
    staff_counter = 1
    for chinese_name in all_staff_names:
        if chinese_name in modified_text:
            # 為每個唯一的師傅名稱分配一個佔位符
            placeholder = f"%W{staff_counter}%"
            english_name = staff_mapping[chinese_name]
            
            # 替換所有出現的該師傅名稱
            modified_text = modified_text.replace(chinese_name, placeholder)
            placeholder_map[placeholder] = (chinese_name, english_name)
            staff_counter += 1
    
    if placeholder_map:
        logger.info(f"提取並替換了 {len(placeholder_map)} 個唯一名稱: {list(placeholder_map.keys())}")
    
    return modified_text, placeholder_map


def restore_names(text: str, placeholder_map: Dict[str, Tuple[str, str]], target_language: str) -> str:
    """
    將文本中的佔位符還原為正確語言的名稱
    
    Args:
        text: 包含佔位符的文本
        placeholder_map: 佔位符映射字典
        target_language: 目標語系
        
    Returns:
        還原後的文本
    """
    if not text or not placeholder_map:
        return text
    
    restored_text = text
    is_chinese = target_language in ['zh-TW', 'zh-tw', 'zh', 'tw']
    
    for placeholder, (chinese_name, english_name) in placeholder_map.items():
        # 根據語系選擇中文名或英文名
        name_to_use = chinese_name if is_chinese else english_name
        
        # 直接替換原始佔位符
        restored_text = restored_text.replace(placeholder, name_to_use)
        
        # 也嘗試替換 Azure 可能改變的變種（大小寫轉換、編號改變）
        # 例如 %W1% 可能變成 %w1%, %W2% 可能變成 %w9% 等
        # 修正：正確區分師傅佔位符（%W）和店家佔位符（%S）
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
    
    logger.info(f"還原了 {len(placeholder_map)} 個名稱（語系: {target_language}, 使用{'中文' if is_chinese else '英文'}名）")
    return restored_text


def convert_staff_names(staff_names: List[str], target_language: str) -> List[str]:
    """
    根據目標語系轉換師傅名稱列表
    - 繁體中文 (zh-TW, zh) -> 使用中文名
    - 其他語系 -> 使用英文名
    
    Args:
        staff_names: 師傅中文名稱列表
        target_language: 目標語系代碼
        
    Returns:
        轉換後的師傅名稱列表
    """
    if not staff_names:
        return staff_names
    
    # 如果是繁體中文，保持中文名
    if target_language in ['zh-TW', 'zh-tw', 'zh', 'tw']:
        return staff_names
    
    # 其他語系使用英文名
    name_mapping = get_staff_name_mapping()
    converted_names = []
    
    for chinese_name in staff_names:
        # 如果找到對應的英文名，使用英文名；否則保持原名
        english_name = name_mapping.get(chinese_name, chinese_name)
        converted_names.append(english_name)
    
    logger.info(f"轉換師傅名稱: {staff_names} -> {converted_names} (語系: {target_language})")
    return converted_names


class MultiLangTranslator:
    """多國語系翻譯器"""
    
    # Azure Translator 設定
    AZURE_SUBSCRIPTION_KEY = os.getenv('AZURE_TRANSLATOR_KEY', '')
    AZURE_ENDPOINT = os.getenv('AZURE_TRANSLATOR_ENDPOINT', 'https://api.cognitive.microsofttranslator.com')
    AZURE_LOCATION = os.getenv('AZURE_TRANSLATOR_LOCATION', 'global')
    
    # Google Translate 設定（備用）
    GOOGLE_TRANSLATE_URL = 'https://translate.googleapis.com/translate_a/single'
    
    @classmethod
    def translate_to_target_language(cls, text: str, target_language: str = "en") -> str:
        """
        使用 Azure Translator API 將繁體中文翻譯成目標語系
        
        Args:
            text: 要翻譯的文字（假設為繁體中文）
            target_language: 目標語系代碼 (en, th, ja, ko 等)
            
        Returns:
            翻譯後的文字，若翻譯失敗則返回原文
        """
        try:
            # 如果目標語言是繁體中文，直接返回原文本
            if target_language in ['zh-TW', 'zh-tw', 'tw']:
                logger.info(f"目標語言為繁體中文，返回原文: {text}")
                return text
            
            logger.info(f"開始翻譯文本: '{text}' -> {target_language}")

            if not cls.AZURE_SUBSCRIPTION_KEY:
                logger.warning("缺少 AZURE_TRANSLATOR_KEY，返回原文")
                return text
            
            # API 路徑與參數
            path = '/translate?api-version=3.0'
            params = f'&to={target_language}'
            constructed_url = cls.AZURE_ENDPOINT + path + params
            
            # HTTP 標頭
            headers = {
                'Ocp-Apim-Subscription-Key': cls.AZURE_SUBSCRIPTION_KEY,
                'Ocp-Apim-Subscription-Region': cls.AZURE_LOCATION,
                'Content-type': 'application/json',
                'X-ClientTraceId': str(uuid.uuid4())
            }
            
            # 請求主體
            body = [{'text': text}]
            
            # 發送 POST 請求
            response = requests.post(constructed_url, headers=headers, json=body, timeout=10)
            response.raise_for_status()
            
            # 解析翻譯結果
            result = response.json()
            translated_text = result[0]['translations'][0]['text']
            
            logger.info(f"翻譯成功: '{text}' -> '{translated_text}'")
            return translated_text
            
        except requests.exceptions.Timeout:
            logger.error(f"翻譯請求超時: {text}")
            return text
        except requests.exceptions.RequestException as e:
            logger.error(f"翻譯 API 請求失敗: {str(e)}")
            return text
        except (KeyError, IndexError) as e:
            logger.error(f"翻譯結果解析失敗: {str(e)}")
            return text
        except Exception as e:
            logger.error(f"翻譯過程發生未知錯誤: {str(e)}")
            return text
    
    @classmethod
    def translate_to_google(cls, text: str, target_language: str = "en") -> str:
        """
        使用 Google Translate API 作為備用翻譯方案
        
        Args:
            text: 要翻譯的文字
            target_language: 目標語系代碼
            
        Returns:
            翻譯後的文字，若翻譯失敗則返回原文
        """
        try:
            if target_language in ['zh-TW', 'zh-tw', 'tw']:
                return text
            
            params = {
                'client': 'gtx',
                'sl': 'zh-TW',  # 來源語言：繁體中文
                'tl': target_language,  # 目標語言
                'dt': 't',
                'q': text
            }
            
            response = requests.get(cls.GOOGLE_TRANSLATE_URL, params=params, timeout=5)
            response.raise_for_status()
            
            # 解析 Google 翻譯的響應
            result = response.json()
            translated_text = ""
            
            if result and len(result) > 0 and result[0]:
                for segment in result[0]:
                    if segment and len(segment) > 0:
                        translated_text += segment[0]
            
            if translated_text:
                logger.info(f"Google 翻譯成功: '{text}' -> '{translated_text}'")
                return translated_text
            else:
                logger.warning(f"Google 翻譯失敗，使用原始文本: '{text}'")
                return text
                
        except Exception as e:
            logger.error(f"Google 翻譯過程發生錯誤: {str(e)}")
            return text


def translate_message(message: str, target_language: str) -> str:
    """
    翻譯訊息到目標語系（主要入口函數）
    使用佔位符系統保護師傅名稱和店家名稱
    
    Args:
        message: 要翻譯的訊息（繁體中文）
        target_language: 目標語系代碼 (en, th, ja, ko, zh-TW 等)
        
    Returns:
        翻譯後的訊息
    """
    if not message:
        return ""
    
    # 如果目標語系是繁體中文，直接返回
    if target_language in ['zh-TW', 'zh-tw', 'tw', 'zh']:
        return message
    
    # 獲取映射
    staff_mapping = get_staff_name_mapping()
    store_mapping = get_store_name_mapping()
    
    # 步驟 1: 提取並替換名稱為佔位符
    text_with_placeholders, placeholder_map = extract_and_replace_names(
        message, staff_mapping, store_mapping
    )
    
    # 步驟 2: 翻譯包含佔位符的文本
    translated_text = MultiLangTranslator.translate_to_target_language(
        text_with_placeholders, target_language
    )
    
    # 步驟 3: 將佔位符還原為正確語言的名稱
    final_text = restore_names(translated_text, placeholder_map, target_language)
    
    return final_text


def translate_response_fields(parsed_data: dict, target_language: str) -> dict:
    """
    翻譯 parsed_data 中的文字欄位到目標語系
    師傅名稱和店家名稱會自動使用正確的語言（不翻譯）
    
    Args:
        parsed_data: 包含回應訊息的字典
        target_language: 目標語系代碼
        
    Returns:
        翻譯後的 parsed_data
    """
    if not parsed_data:
        return parsed_data
    
    # 處理師傅名稱：直接轉換為對應語言的名稱
    if 'masseur' in parsed_data and parsed_data['masseur']:
        parsed_data['masseur'] = convert_staff_names(
            parsed_data['masseur'], 
            target_language
        )
    
    # 如果是繁體中文，其他欄位也不需要翻譯
    if target_language in ['zh-TW', 'zh-tw', 'tw', 'zh']:
        return parsed_data
    
    # 翻譯文字欄位（translate_message 會自動保護名稱）
    text_fields = ['response_message', 'greeting_message', 'error', 'message']
    
    for field in text_fields:
        if field in parsed_data and parsed_data[field]:
            parsed_data[field] = translate_message(
                parsed_data[field], 
                target_language
            )
    
    return parsed_data
