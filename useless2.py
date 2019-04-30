# -*- coding: utf-8 -*-

"""
2019/04/20
读取几个行业无用词
"""
import datetime
import time

from new_reviews.process.public import *


def read(pcid, cid):
    START = time.time()

    schema, table = f"raw_comment_pcid{pcid}", f"raw_tb_comment{cid}_cut_target"

    """
    target != '' 5,431,198
    target is null 33,306,380
    """
    sql = f"SELECT count(*) FROM {schema}.{table} WHERE target is null;"
    df = pd.read_sql_query(sql, engine("raw_tb_comment_notag"))
    print("有多少行数据")
    print(df)
    POINT1 = time.time()
    print("读取行数用时", POINT1 - START)

    sql = f"SELECT word FROM {schema}.{table} WHERE target is null;"
    df = pd.read_sql_query(sql, engine("raw_tb_comment_notag"))
    print("有多少行数据", len(df))

    POINT2 = time.time()
    print("读取具体数据用时", POINT2 - POINT1)

    df.to_csv(f"data/cut_{pcid}_{cid}.csv", encoding=UTF8)


def rank(pcid, cid):
    START = time.time()
    records = dict()
    df = pd.read_csv(f"data/cut_{pcid}_{cid}.csv", encoding=UTF8)
    for k, v in df.iterrows():
        records[v["word"]] = records.setdefault(v["word"], 0) + 1

    print("有多少种词", len(records))

    POINT1 = time.time()
    print("统计用时", POINT1 - START)

    records = sorted(records.items(), key=lambda x: x[1], reverse=True)

    POINT2 = time.time()
    print("排序用时", POINT2 - POINT1)

    values = []
    for x in records:
        temp = [x[0], x[1]]
        values.append(temp)
    df = pd.DataFrame(values, columns=["word", "frequency"])

    POINT3 = time.time()
    print("数据重组用时", POINT3 - POINT2)

    df.to_csv(f"data/freq_{pcid}_{cid}.csv", encoding=UTF8)


def write(pcid, cid):
    try:
        with open("lexicon/words.txt", encoding="utf-8", mode="r") as fp:
            seq = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            with open(f"lexicon/words_{seq}.txt", encoding="utf-8", mode="w") as bak:
                lines = fp.readlines()
                for line in lines:
                    bak.write(line)
    except Exception as e:
        pass

    df = pd.read_csv(f"data/freq_{pcid}_{cid}.csv", encoding=UTF8, index_col=0)
    start = 0
    end = 3000
    with open("lexicon/words.txt", encoding="utf-8", mode="a+") as fp:
        for k, v in df.iterrows():
            if k >= start:
                fp.write(f"{v['word']}\n")
            if k >= end:
                break


if __name__ == '__main__':
    tasks = list()
    tasks.append(["4", "50012097"])
    for task in tasks:
        pcid, cid = task
        # read(pcid, cid)
        # rank(pcid, cid)
        write(pcid, cid)
