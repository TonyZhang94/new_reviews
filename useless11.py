# -*- coding: utf-8 -*-

"""
2019/04/22
情感模糊的情感词（依据target）
"""

# 很小，较小，非常小，特别小，小，不小，更小
# 小，大，高，少，多，辣

prefixes = ["很", "较", "非常", "特别", "", "不", "更"]  # "超"
keys = ["大", "小", "高", "低", "多", "少", "长", "短",
        "酸", "甜", "苦", "辣", "咸", "淡",
        "软", "硬", "松", "紧", "粗", "细", "厚", "薄", "深", "浅",
        "瘦"
        ]  # "胖"

words = list()
for key in keys:
    for prefix in prefixes:
        words.append(prefix+key)

with open("lexicon/vague.txt", mode="w", encoding="utf-8") as fp:
    for word in words:
        fp.write(f"{word}\n")

poss = ["真"]
words = list()
for key in keys:
    for pos in poss:
        words.append(pos+key)

with open("lexicon/opi_pos_pre.txt", mode="w", encoding="utf-8") as fp:
    for word in words:
        fp.write(f"{word}\n")


negs = ["太", "偏", "过"]
words = list()
for key in keys:
    for neg in negs:
        words.append(neg+key)

with open("lexicon/opi_neg_pre.txt", mode="w", encoding="utf-8") as fp:
    for word in words:
        fp.write(f"{word}\n")
