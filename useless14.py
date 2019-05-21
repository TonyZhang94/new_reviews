# -*- coding: utf-8 -*-

"""
2019/05/18
整理通用target词
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

    base = "SELECT DISTINCT target FROM pcid{pcid}.review_analysis_{cid};"
    result = dict()
    rank = 0
    for pcid, cids in tasks.items():
        for cid in cids:
            sql = base.format(pcid=pcid, cid=cid)
            df = pd.read_sql(sql, con=engine("tb_comment_nlp"))
            print(f"pcid{pcid} cid{cid} size={len(df)}")
            for word in df["target"].values:
                result[word] = result.setdefault(word, 0) + 1
            rank += 1
            print(f"complete pcid{pcid} cid{cid} {rank}/{total}")

    result = sorted(result.items(), key=lambda x: x[1], reverse=True)
    with open("lexicon/comment_target_withFreq.txt", mode="w", encoding="utf-8") as fp:
        for line in result:
            fp.write(f"{line[0]} {line[1]}\n")

    with open("lexicon/comment_target.txt", mode="w", encoding="utf-8") as fp:
        for line in result:
            fp.write(f"{line[0]}\n")


def find_conflict():
    from new_reviews.lexicon.lexicon import GetLexicon
    lexicon = GetLexicon()
    lexicon.read_all(pcid="4")
    useless = lexicon.get_words()
    with open("comment_target.txt", mode="r", encoding="utf-8") as fp:
        rank = 0
        seq = 0
        for line in fp.readlines():
            rank += 1
            word = line.strip()
            if word in useless:
            # if word not in useless:
                seq += 1
                print(rank, seq, word)


def make_comment_target_by_freq(threshold=1):
    from new_reviews.lexicon.lexicon import GetLexicon
    lexicon = GetLexicon()
    lexicon.read_all(pcid="4")
    useless = lexicon.get_words()
    targets = list()

    special = set()
    special.add("好")
    special.add("不错")
    special.add("不错呀")
    special.add("双十一")
    special.add("买一送一")
    with open("comment_target_withFreq.txt", mode="r", encoding="utf-8") as fp:
        for line in fp.readlines():
            word, freq = line.strip().split()
            if int(freq) > threshold or word not in useless:
                if word in special:
                    continue
                targets.append(word)

    with open("comment_target.txt", mode="w", encoding="utf-8") as fp:
        content = "\n".join(targets) + "\n"
        fp.write(content)


if __name__ == '__main__':
    # tasks = get_tasks()
    # get_words(tasks)

    # 下面两个函数需要放到lexicon文件夹内运行
    # find_conflict()
    make_comment_target_by_freq()
