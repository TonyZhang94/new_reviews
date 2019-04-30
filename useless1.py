# -*- coding: utf-8 -*-

"""
2019/04/20
读取nomeaning的词
"""
import datetime

from new_reviews.process.public import *


def read():
    schema, table = "public", "nomeaning"
    sql = f"SELECT * FROM {schema}.{table}"

    df = pd.read_sql_query(sql, engine("lexicon"))
    df.to_csv("data/nomeanings.csv", encoding=UTF8)


def statistic():
    df = pd.read_csv("data/nomeanings.csv", encoding=UTF8)
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
    df.to_csv(f"data/freq_nomeaning.csv", encoding=UTF8)


def write():
    try:
        with open("lexicon/nomeanings.txt", encoding="utf-8", mode="r") as fp:
            seq = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            with open(f"lexicon/words_{seq}.txt", encoding="utf-8", mode="w") as bak:
                lines = fp.readlines()
                for line in lines:
                    bak.write(line)
    except Exception as e:
        pass

    df = pd.read_csv("data/freq_nomeaning.csv", encoding=UTF8, index_col=0)
    start = 0
    end = 3000
    with open("lexicon/nomeanings.txt", encoding="utf-8", mode="a+") as fp:
        for k, v in df.iterrows():
            if k >= start:
                fp.write(f"{v['word']}\n")
            if k >= end:
                break


def analysis1():
    df = pd.read_csv("data/freq_nomeaning.csv", encoding=UTF8)
    nomeanings = df["word"].values[: 3000]
    nomeanings = set(nomeanings)
    words = set()
    with open("lexicon/words.txt", encoding="utf-8", mode="r") as fp:
        lines = fp.readlines()
        for line in lines:
            words.add(line.strip())

    intersection = words & nomeanings
    print(len(intersection))
    for x in intersection:
        print(x)


if __name__ == '__main__':
    # read()
    # statistic()
    # analysis1()
    write()
