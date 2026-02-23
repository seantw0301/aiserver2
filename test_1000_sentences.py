import sys
import random
sys.path.append('/Volumes/aiserver2/ai_parser')

from handle_time2025 import extra_date_string, extra_time_string

# 生成1000句測試句子
def generate_sentences():
    dates = [
        "今天", "明天", "後天", "昨天", "前天",
        "下星期一", "下星期二", "下星期三", "下星期四", "下星期五", "下星期六", "下星期日",
        "上星期一", "上星期二", "上星期三", "上星期四", "上星期五", "上星期六", "上星期日",
        "本星期一", "本星期二", "本星期三", "本星期四", "本星期五", "本星期六", "本星期日",
        "下個月1號", "下個月2號", "下個月15號", "下個月30號",
        "上個月1號", "上個月15號", "上個月30號",
        "明年春節", "去年中秋節", "今年五一勞動節", "後年國慶節",
        "明年端午節", "去年重陽節", "今年教師節", "後年元旦",
        "明年聖誕節", "去年萬聖節", "今年感恩節", "後年情人節",
        "明年清明節", "去年元宵節", "今年建黨節", "後年航海日",
        "明年春分", "去年秋分", "今年冬至", "後年夏至",
        "2025年12月15日", "2024年10月1日", "2026年1月1日",
        "12月25日", "10月1日", "5月1日"
    ]

    times = [
        "上午9點", "上午10點", "上午11點",
        "下午1點", "下午2點", "下午3點", "下午4點", "下午5點",
        "晚上6點", "晚上7點", "晚上8點", "晚上9點", "晚上10點",
        "中午12點", "凌晨1點", "凌晨2點", "凌晨3點",
        "清晨5點", "傍晚6點", "深夜11點", "午夜12點",
        "早上7點", "早上8點",
        "上午9點半", "下午3點半", "晚上8點半",
        "中午12點半", "凌晨2點半",
        "9:30", "14:00", "20:15",
        "10am", "3pm"
    ]

    actions = [
        "開會", "吃飯", "上班", "回家", "睡覺", "起床", "跑步", "購物",
        "看電影", "唱歌", "逛街", "旅行", "出差", "聚餐", "散步", "休息",
        "打電話", "見面", "約會", "慶祝", "紀念", "玩耍", "種樹", "賞花",
        "掃墓", "猜燈謎", "吃粽子", "登高", "送花", "放煙火", "拜年", "賞月",
        "遊行", "跨年", "觀測", "吃餃子", "出海", "種樹", "慶祝", "約會"
    ]

    sentences = []
    for i in range(1000):
        date = random.choice(dates)
        time = random.choice(times)
        action = random.choice(actions)
        sentence = f"{date}{time}{action}。"
        sentences.append(sentence)
    return sentences

sentences = generate_sentences()

for i, sentence in enumerate(sentences, 1):
    date = extra_date_string(sentence)
    time = extra_time_string(sentence)
    print(f"{i}. 句子: {sentence}")
    print(f"   日期: '{date}'")
    print(f"   時間: '{time}'")
    print()