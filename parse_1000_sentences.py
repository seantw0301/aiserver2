import sys
import re
sys.path.append('/Volumes/aiserver2/ai_parser')

from handle_time2025 import parser_date_time

# 讀取 test_1000_output.txt 並解析每句
def parse_sentences():
    with open('/Volumes/aiserver2/test_1000_output.txt', 'r') as f:
        content = f.read()

    # 分割成每句的塊
    blocks = re.split(r'\n\n', content.strip())

    for block in blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            sentence_line = lines[0]
            date_line = lines[1]
            time_line = lines[2]

            # 提取句子
            sentence_match = re.search(r'句子: (.+)', sentence_line)
            if sentence_match:
                sentence = sentence_match.group(1)
                print(f"句子: {sentence}")

                # 調用 parser_date_time
                try:
                    result = parser_date_time(sentence)
                    print(f"解析結果: {result}")
                except Exception as e:
                    print(f"解析錯誤: {e}")

                print()

if __name__ == "__main__":
    parse_sentences()