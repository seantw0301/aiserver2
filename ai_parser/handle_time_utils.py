# handle_time_utils.py
# 共用工具函數

import re
from datetime import datetime, timedelta


def convert_chinese_numerals_to_arabic(text: str) -> str:
    """
    將中文數字及全形字符轉換為阿拉伯數字和半形字符
    支持：
    1. 中文數字：一二三四五六七八九十百千萬億、壹貳參肆伍陸柒捌玖拾佰仟萬億、兩
    2. 全形字符：全形數字、英文字母、標點符號、空格等
    """
    # 定義中文數字到阿拉伯數字的映射
    chinese_num_map = {
        '零': '0', '〇': '0',
        '一': '1', '壹': '1',
        '二': '2', '貳': '2', '貮': '2', '兩': '2',
        '三': '3', '參': '3', '叁': '3',
        '四': '4', '肆': '4',
        '五': '5', '伍': '5',
        '六': '6', '陸': '6',
        '七': '7', '柒': '7',
        '八': '8', '捌': '8',
        '九': '9', '玖': '9',
    }
    
    # 定義全形字符到半形字符的映射
    fullwidth_num_map = {
        # 全形數字
        '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
        '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
        # 全形標點符號
        '：': ':', '；': ';', '，': ',', '。': '.', '！': '!', 
        '？': '?', '「': '"', '」': '"', '『': "'", '』': "'",
        '（': '(', '）': ')', '【': '[', '】': ']', '｛': '{', '｝': '}',
        '－': '-', '＿': '_', '＋': '+', '＝': '=', '＊': '*',
        '／': '/', '＼': '\\', '｜': '|', '～': '~', '＾': '^',
        '％': '%', '＄': '$', '＃': '#', '＠': '@', '＆': '&',
        # 全形英文字母 A-Z
        'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F', 'Ｇ': 'G', 'Ｈ': 'H',
        'Ｉ': 'I', 'Ｊ': 'J', 'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N', 'Ｏ': 'O', 'Ｐ': 'P',
        'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T', 'Ｕ': 'U', 'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X',
        'Ｙ': 'Y', 'Ｚ': 'Z',
        # 全形英文字母 a-z
        'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e', 'ｆ': 'f', 'ｇ': 'g', 'ｈ': 'h',
        'ｉ': 'i', 'ｊ': 'j', 'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n', 'ｏ': 'o', 'ｐ': 'p',
        'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't', 'ｕ': 'u', 'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x',
        'ｙ': 'y', 'ｚ': 'z',
        # 全形空格
        '　': ' '
    } 
    
    # 定義中文數量詞
    quantity_map = {
        '十': 10, '拾': 10, 
        '百': 100, '佰': 100, 
        '千': 1000, '仟': 1000,
        '萬': 10000, '万': 10000,
        '億': 100000000, '亿': 100000000
    }
    
    # 先將全形字符轉換為半形字符
    for full, half in fullwidth_num_map.items():
        text = text.replace(full, half)
    
    # 使用正則表達式查找連續的中文數字
    pattern = r'[零〇一壹二貳貮兩三參叁四肆五伍六陸七柒八捌九玖十拾百佰千仟萬万億亿]+'
    
    def replace_chinese_num(match):
        chinese_num = match.group(0)
        
        # 簡單的情況：單個數字
        if len(chinese_num) == 1 and chinese_num in chinese_num_map:
            return chinese_num_map[chinese_num]
        
        # 處理"十"開頭的特殊情況，例如"十三"應為"13"而非"103"
        if chinese_num.startswith('十') or chinese_num.startswith('拾'):
            chinese_num = '一' + chinese_num
        
        # 複雜的情況：數字組合
        result = 0
        temp = 0
        for char in chinese_num:
            if char in chinese_num_map:
                temp = int(chinese_num_map[char])
            elif char in quantity_map:
                if temp == 0:  # 處理如"百"、"千"這樣的情況，前面沒有具體數字
                    temp = 1
                temp *= quantity_map[char]
                result += temp
                temp = 0
            else:
                # 非數字字符，忽略
                pass
        
        # 加上最後剩餘的數字
        result += temp
        
        # 如果結果為0，可能是單個"零"
        if result == 0 and ('零' in chinese_num or '〇' in chinese_num):
            return '0'
        
        return str(result)
    
    # 替換文本中的所有中文數字
    return re.sub(pattern, replace_chinese_num, text)


def preprocess_text(text):
    """預處理文本：移除emoji和特殊符號，但保留括號和有用字符"""
    return re.sub(r'[^\w\s\d:：/\-年月日點点时時分半週周星期\(\)（）上下晚午早]', '', text)