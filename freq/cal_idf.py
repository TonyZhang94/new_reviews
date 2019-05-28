# -*- coding: utf-8 -*-

"""
2019/05/25

根据use.txt计算idf
"""

import _pickle as pickle
import os
import time
import math

from new_reviews.process.public import *


base = 10
def log(x):
    return math.log(x, base)


def read_tasks(restart=True):
    print("Restart:", restart)
    if restart is True:
        time.sleep(5)

    used = list()
    if not restart:
        with open("used.txt", mode="r", encoding="utf-8") as fp:
            for line in fp.readlines():
                used.append(line.strip())
    else:
        with open("used.txt", mode="w", encoding="utf-8") as fp:
            pass
        try:
            os.remove("freq_data/info.pkl")
            print("freq_data/info.pkl 已删除")
        except FileNotFoundError:
            print("freq_data/info.pkl 不存在")

        try:
            os.remove("freq_data/temp.txt")
            print("freq_data/temp.txt 已删除")
        except FileNotFoundError:
            print("freq_data/temp.txt 不存在")


    tasks = list()
    tasks_info = dict()
    with open("use.txt", mode="r", encoding="utf-8") as fp:
        for line in fp.readlines():
            info = line.strip()
            if info in used:
                continue
            pcid, _, cid, _, _, _, _ = info.split(",")
            tasks.append([pcid, cid])
            tasks_info[f"pcid{pcid}cid{cid}"] = info

    print("Used Num:", len(used))
    print("New Tasks:")
    for task in tasks:
        print(f"pcid {task[0]} cid {task[1]}")

    return tasks, tasks_info, len(used)


def read_freq(pcid, cid):
    try:
        df = pd.read_csv(f"freq_data/pcid{pcid}cid{cid}.csv", encoding=UTF8)
        print(f"pcid {pcid} cid {cid} read local data. ", len(df))
    except FileNotFoundError:
        sql = f"SELECT * FROM frequency.pcid{pcid}cid{cid} order by frequency DESC;"
        df = pd.read_sql(sql, engine("lexicon"))
        print(f"pcid {pcid} cid {cid} read db data. ", len(df))
        df.to_csv(f"freq_data/pcid{pcid}cid{cid}.csv", encoding=UTF8)
    return df, len(df)


def make_info(tasks, tasks_info, rank):
    try:
        with open("freq_data/info.pkl", mode="rb") as fp:
            info = pickle.load(fp)
        print("Load info dict")
    except Exception:
        print("First Task. Init info dict")
        info = dict()

    for num, task in enumerate(tasks, start=rank+1):
        pcid, cid = task
        freq, size = read_freq(pcid, cid)
        for k, v in freq.iterrows():
            word, rank, rank_share, rerank, frequency, frequency_share = v["word"], k, 1-(k/size), size-k, v["frequency"], v["share"]
            if "#总词频#" == word or word != word:
                continue
            if word in info:
                info[word].append([rank, rank_share, rerank, frequency, frequency_share])
            else:
                info[word] = list()
                for _ in range(num-1):
                    info[word].append([])
                info[word].append([rank, rank_share, rerank, frequency, frequency_share])
        for word, record in info.items():
            if num-1 == len(record):
                info[word].append([])
            if num != len(record):
                print(f"warning ... {word}")

        with open("used.txt", mode="a", encoding="utf-8") as fp:
            fp.write(tasks_info[f"pcid{pcid}cid{cid}"]+"\n")

    with open("freq_data/info.pkl", mode="wb") as fp:
        pickle.dump(info, fp)

    # with open("freq_data/temp.txt", mode="w", encoding="utf-8") as fp:
    #     for word, record in info.items():
    #         record = map(str, record)
    #         line = f"{word} {' '.join(record)}\n"
    #         fp.write(line)


def cal_idf():
    print("Loading info dict ...")
    with open("freq_data/info.pkl", mode="rb") as fp:
        info = pickle.load(fp)
    print("Complete")

    idf_info = dict()
    num_info = dict()
    for word, records in info.items():
        cnt, acc = 0, 0
        feedback = 0
        total_freq = 0
        total_cnt = 0
        for record in records:
            if 0 == len(record) or record[3] < 10:
                cnt += feedback
                feedback = max(feedback, 0.1)
                feedback *= 2
                feedback = min(feedback, 1.0)
                continue
            cnt += 1
            total_freq += record[3]
            total_cnt += 1
            acc += record[4]
        num_info[word] = [total_freq, total_cnt]
        if acc != 0:
            idf_info[word] = acc / cnt
        # else:
        #     print("filtered:", word, acc / cnt)

    with open("freq_data/info_idf.pkl", mode="wb") as fp:
        pickle.dump(idf_info, fp)

    with open("freq_data/temp_idf.txt", mode="w", encoding="utf-8") as fp:
        records = list()
        for word, idf in idf_info.items():
            records.append([word, idf])

        records.sort(key=lambda x: x[1], reverse=True)
        # records.sort(key=lambda x: x[1])
        for record in records:
            word, idf = record
            line = f"{word} {idf} {' '.join(map(str, num_info[word]))}\n"
            fp.write(line)


if __name__ == '__main__':
    # tasks, tasks_info, rank = read_tasks(restart=False)
    # tasks, tasks_info, rank = read_tasks(restart=True)
    # make_info(tasks, tasks_info, rank)
    cal_idf()
