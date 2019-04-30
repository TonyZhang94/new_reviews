# -*- coding: utf-8 -*-

"""
2019/04/24
找到错误的情感词

用lexicon文件夹把zhuicanw_web/new_reviews下的lexicon文件夹换掉
"""

from new_reviews.process.public import *


def analysis():
    df = pd.read_csv("data/opinions.csv", encoding=UTF8, index_col=0)
    df["grade"] = df["grade"].astype("Int32")
    pos, neu, neg = set(), set(), set()
    for k, v in df.iterrows():
        if 1 == v["grade"]:
            pos.add(v["word"])
        elif 0 == v["grade"]:
            neu.add(v["word"])
        else:
            neg.add(v["word"])

    # print(len(df))  # 3124
    # print(len(pos))  # 1559
    # print(len(neu))  # 878
    # print(len(neg))  # 687

    result = set()

    with open("lexicon/opi_pos.txt", mode="r", encoding="utf-8") as fp:
        print("===== pos =====")
        temp = set()
        for line in fp.readlines():
            temp.add(line.strip())
        print("\n### 手动删除的")
        t = pos - temp
        for x in t:
            print(x)
        result |= t

        print("\n### 手动增加的")
        t = temp - pos
        for x in t:
            print(x)

    with open("lexicon/opi_neu.txt", mode="r", encoding="utf-8") as fp:
        print("===== neu =====")
        temp = set()
        for line in fp.readlines():
            temp.add(line.strip())
        print("\n### 手动删除的")
        t = neu - temp
        for x in t:
            print(x)
        result |= t

        print("\n### 手动增加的")
        t = temp - neu
        for x in t:
            print(x)

    with open("lexicon/opi_neg.txt", mode="r", encoding="utf-8") as fp:
        print("===== neg =====")
        temp = set()
        for line in fp.readlines():
            temp.add(line.strip())
        print("\n### 手动删除的")
        t = neg - temp
        for x in t:
            print(x)
        result |= t

        print("\n### 手动增加的")
        t = temp - neg
        for x in t:
            print(x)

    return result


def write(words):
    with open("lexicon/opi_error.txt", mode="w", encoding="utf-8") as fp:
        for word in words:
            fp.write(f"{word}\n")


if __name__ == '__main__':
    result = analysis()
    write(result)
