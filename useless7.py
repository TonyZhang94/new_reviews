# -*- coding: utf-8 -*-

"""
2019/04/21
opinions
"""

import datetime

from new_reviews.process.public import *


def read():
    schema, table = "public", "opinions"
    sql = f"SELECT * FROM {schema}.{table}"

    df = pd.read_sql_query(sql, engine("lexicon"))
    df.to_csv("data/opinions.csv", encoding=UTF8)


def analysis():
    # 查看有没有重复的
    df = pd.read_csv("data/opinions.csv", encoding=UTF8, index_col=0)
    words = df["word"]
    print(len(words))
    words = set(words)
    print(len(words))


def write():
    df = pd.read_csv("data/opinions.csv", encoding=UTF8, index_col=0)
    df["grade"] = df["grade"].astype("Int32")
    pos, neu, neg = list(), list(), list()
    for k, v in df.iterrows():
        if 1 == v["grade"]:
            pos.append(v["word"])
        elif 0 == v["grade"]:
            neu.append(v["word"])
        else:
            neg.append(v["word"])

    # print(len(df))  # 3124
    # print(len(pos))  # 1559
    # print(len(neu))  # 878
    # print(len(neg))  # 687

    with open("lexicon/opi_pos.txt", mode="w", encoding="utf-8") as fp:
        for word in pos:
            fp.write(f"{word}\n")

    with open("lexicon/opi_neu.txt", mode="w", encoding="utf-8") as fp:
        for word in neu:
            fp.write(f"{word}\n")

    with open("lexicon/opi_neg.txt", mode="w", encoding="utf-8") as fp:
        for word in neg:
            fp.write(f"{word}\n")


if __name__ == '__main__':
    # read()
    # analysis()
    write()
