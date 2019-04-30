# -*- coding: utf-8 -*-

"""
2019/04/21
noisefilterkeywords
"""

import datetime
import time

from new_reviews.process.public import *


def read():
    schema, table = "public", "noisefilterkeywords"
    sql = f"SELECT * FROM {schema}.{table}"

    df = pd.read_sql_query(sql, engine("lexicon"))
    df.to_csv("data/noisefilterkeywords.csv", encoding=UTF8)


def statistic():
    df = pd.read_csv("data/noisefilterkeywords.csv", encoding=UTF8)
    records = dict()
    for k, v in df.iterrows():
        records[v["word"]] = records.setdefault(v["word"], 0) + 1

    print("有多少种词", len(records))

    records = sorted(records.items(), key=lambda x: x[1], reverse=True)
    values = []
    for x in records:
        temp = [x[0], x[1]]
        values.append(temp)
    df = pd.DataFrame(values, columns=["word", "frequency"])
    df.to_csv(f"data/freq_noisekey.csv", encoding=UTF8)


def write():
    df = pd.read_csv("data/freq_noisekey.csv", encoding=UTF8, index_col=0)
    start = 0
    end = 3000
    with open("lexicon/keyno.txt", encoding="utf-8", mode="a+") as fp:
        for k, v in df.iterrows():
            if k >= start:
                fp.write(f"{v['word']}\n")
            if k >= end:
                break


if __name__ == '__main__':
    # read()
    # statistic()
    write()
