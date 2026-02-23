
import requests
import re
import html
import logging
import json
import uuid
import os

class MultiLanguage:
    logger = logging.getLogger(__name__)
    google_key = os.getenv("GOOGLE_TRANSLATE_API_KEY", "")

    @classmethod
    def translate_to_traditional_chinese(cls, text: str) -> tuple:
        """
        使用Google翻譯API將文本翻譯成繁體中文
        如果文本已經是中文或翻譯失敗，則返回原文本
        """
        source_language = "zh-TW"  # 默認值為繁體中文

        try:
            # 判斷是否需要翻譯 (包含非中文字符)
            # if is_chinese_text(text):
            #    return text,source_language
            text = text.replace("tmr", "tomorrow")
            text = re.sub(r"(\d+)\.(\d+)", r"\1:\2", text)
            text = (
                text.strip().replace(",", "").replace("!", "").replace(".", "")
            )  # 去除首尾空格和換行符

            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": "auto",  # 自動檢測源語言
                "tl": "zh-TW",  # 繁體中文
                "dt": "t",
                "q": text,
            }

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            # 解析Google翻譯的響應
            result = response.json()
            translated_text = ""

            # 提取翻譯文本
            if result and len(result) > 0 and result[0]:
                for segment in result[0]:
                    if segment and len(segment) > 0:
                        translated_text += segment[0]

            # 如果翻譯成功，返回翻譯後的文本，否則返回原文本
            if translated_text:
                cls.logger.info("翻譯成功: '%s' -> '%s'", text, translated_text)
                translated_text = (
                    translated_text.lower()
                    .replace("tonight", "今晚")
                    .replace("ximen", "西門")
                    .replace("yanji", "延吉")
                )
                return html.unescape(translated_text), source_language  # 解碼HTML實體
            else:
                cls.logger.warning("翻譯失敗，使用原始文本: '%s'", text)
                return text, source_language

        except Exception as e:
            cls.logger.error("翻譯過程發生錯誤: %s", str(e))
            return text, source_language  # 出錯時返回原文本

    @classmethod
    def translate_to_target_language(cls, text: str, target_language: str = "en") -> str:
        try:
            print(f"翻譯文本: {text} 到 {target_language}")
            # 如果目標語言是繁體中文，直接返回原文本，假設已經是中文
            subscription_key = os.getenv("AZURE_TRANSLATOR_KEY", "")
            endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com")
            location = os.getenv("AZURE_TRANSLATOR_LOCATION", "global")

            if not subscription_key:
                cls.logger.warning("缺少 AZURE_TRANSLATOR_KEY，返回原文")
                return text

            # API 路徑與參數
            path = '/translate?api-version=3.0'
            params = f'&to={target_language}'
            constructed_url = endpoint + path + params

            # HTTP 標頭
            headers = {
                'Ocp-Apim-Subscription-Key': subscription_key,
                'Ocp-Apim-Subscription-Region': location,
                'Content-type': 'application/json',
                'X-ClientTraceId': str(uuid.uuid4())
            }

            # 請求主體
            body = [{
                'text': text
            }]

            # 發送 POST 請求
            response = requests.post(constructed_url, headers=headers, json=body)

            # 顯示翻譯結果
            result = response.json()

            # 可擷取翻譯文字
            translated_text = result[0]['translations'][0]['text']
            return translated_text
        except Exception as e:
            print(f"翻譯過程發生錯誤: {str(e)}")
            return text  # 出錯時返回原文本