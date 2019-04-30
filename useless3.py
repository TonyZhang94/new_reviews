# -*- coding: utf-8 -*-

"""
2019/04/20
整理知网各类词汇
"""


def process(file, dst):
    words = set()
    with open(f"data/{file}", mode="r", encoding="gbk") as fp:
        for line in fp.readlines():
            words.add(line.strip())

    with open(f"lexicon/{dst}", mode="w", encoding="utf-8") as fp:
        for word in words:
            fp.write(f"{word}\n")


if __name__ == '__main__':
    tasks = [
        ["主张词语（中文）.txt", "how_opinion.txt"],
        ["正面情感词语（中文）.txt", "how_pos_sen.txt"],
        ["正面评价词语（中文）.txt", "how_pos_com.txt"],
        ["程度级别词语（中文）.txt", "how_deg.txt"],
        ["负面情感词语（中文）.txt", "how_neg_sen.txt"],
        ["负面评价词语（中文）.txt", "how_neg_com.txt"]
    ]
    for task in tasks:
        process(task[0], task[1])
