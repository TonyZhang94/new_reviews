# -*- coding: utf-8 -*-

"""
2019/04/21
sentiment_global
"""

import datetime

from new_reviews.process.public import *


def read():
    schema, table = "public", "sentiment_global"
    sql = f"SELECT * FROM {schema}.{table}"

    df = pd.read_sql_query(sql, engine("lexicon"))
    df.to_csv("data/sentiment_global.csv", encoding=UTF8)


def analysis():
    # 查看有没有重复的
    df = pd.read_csv("data/sentiment_global.csv", encoding=UTF8, index_col=0)
    words = df["opinion"]
    print(len(words))
    words = set(words)
    print(len(words))


def write():
    df = pd.read_csv("data/sentiment_global.csv", encoding=UTF8, index_col=0)
    df["grade"] = df["grade"].astype("Int32")
    pos, neu, neg = set(), set(), set()
    for k, v in df.iterrows():
        if 1 == v["grade"]:
            pos.add(v["opinion"])
            pos.add(v["merge"])
        elif 0 == v["grade"]:
            neu.add(v["opinion"])
            neu.add(v["merge"])
        else:
            neg.add(v["opinion"])
            neg.add(v["merge"])

    # print(len(df))  # 111
    # print(len(set(pos)))  # 97
    # print(len(set(neu)))  # 2
    # print(len(set(neg)))  # 36

    with open("lexicon/gopi_pos.txt", mode="w", encoding="utf-8") as fp:
        for word in pos:
            fp.write(f"{word}\n")

    with open("lexicon/gopi_neu.txt", mode="w", encoding="utf-8") as fp:
        for word in neu:
            fp.write(f"{word}\n")

    with open("lexicon/gopi_neg.txt", mode="w", encoding="utf-8") as fp:
        for word in neg:
            fp.write(f"{word}\n")


if __name__ == '__main__':
    # read()
    # analysis()
    write()
    # 配对，增加价格低
