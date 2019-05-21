# -*- coding: utf-8 -*-

"""
2019/05/18
整理通用opinion词
"""

import datetime

from new_reviews.process.public import *


def get_tasks():
    pcids = [str(pcid) for pcid in range(14)] + ["100"]
    print(pcids)
    result = dict()
    sql = "SELECT table_name FROM information_schema.tables WHERE table_schema='pcid{pcid}';"
    for pcid in pcids:
        tables = pd.read_sql(sql.format(pcid=pcid), con=engine("tb_comment_nlp"))
        result[pcid] = set()
        for table in tables["table_name"].values:
            parts = table.split("_")
            if len(parts) < 3:
                print(f"table {table} is illegal")
                continue
            if "review" != parts[0] or "analysis" != parts[1]:
                print(f"table {table} is illegal")
                continue
            try:
                int(parts[2])
                result[pcid].add(parts[2])
            except Exception as e:
                print(e)
                print(f"table {table} is illegal")
                continue
    return result


def get_words(tasks):
    total = 0
    for pcid, tables in tasks.items():
        print(pcid, tables, len(tables))
        total += len(tables)

    base = "SELECT DISTINCT opinion FROM pcid{pcid}.review_analysis_{cid};"
    result = dict()
    rank = 0
    for pcid, cids in tasks.items():
        for cid in cids:
            sql = base.format(pcid=pcid, cid=cid)
            df = pd.read_sql(sql, con=engine("tb_comment_nlp"))
            print(f"pcid{pcid} cid{cid} size={len(df)}")
            for word in df["opinion"].values:
                result[word] = result.setdefault(word, 0) + 1
            rank += 1
            print(f"complete pcid{pcid} cid{cid} {rank}/{total}")

    result = sorted(result.items(), key=lambda x: x[1], reverse=True)
    with open("lexicon/comment_opinion_withFreq.txt", mode="w", encoding="utf-8") as fp:
        for line in result:
            fp.write(f"{line[0]} {line[1]}\n")

    with open("lexicon/comment_opinion.txt", mode="w", encoding="utf-8") as fp:
        for line in result:
            fp.write(f"{line[0]}\n")


def make_comment_opinion_by_freq(threshold=0):
    opinions = list()

    special = set()
    special.add("小巧")
    special.add("小巧玲珑")
    special.add("迷你")
    special.add("自动")
    special.add("无线")
    special.add("多功能")
    special.add("轻巧")
    special.add("家用")
    special.add("迷你型")
    with open("lexicon/comment_opinion_withFreq.txt", mode="r", encoding="utf-8") as fp:
        for line in fp.readlines():
            try:
                word, freq = line.strip().split()
            except ValueError:
                print(line)
                continue
            if int(freq) > threshold:
                if word in special:
                    continue
                opinions.append(word)

    with open("lexicon/comment_opinion.txt", mode="w", encoding="utf-8") as fp:
        content = "\n".join(opinions) + "\n"
        fp.write(content)


if __name__ == '__main__':
    # tasks = get_tasks()
    # get_words(tasks)
    make_comment_opinion_by_freq()
