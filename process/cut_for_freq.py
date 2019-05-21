# -*- coding: utf-8 -*-

import multiprocessing
import os

import jieba
import time
import datetime

# from new_reviews.process.public import *
from public import *


SPLIT = '#='
base = "../comments/pcid{}cid{}/"


def cut(sentence):
    if not sentence:
        return []
    r = jieba.cut(sentence)
    words = SPLIT.join(r)
    r = pd.DataFrame([[sentence, words]], columns=['comment_all', 'word'])
    return r


def update_freq(freq, sentences):
    for sentence in sentences:
        words = sentence.split(SPLIT)
        for word in words:
            freq[word] = freq.setdefault(word, 0) + 1


def get_comments(pcid, cid):
    table_src = 'raw_comment_pcid{}.raw_tb_comment{}'.format(pcid, cid)
    sql = "select itemid, comment_id, comment_all, comment_date from {} " \
          "order by itemid;".format(table_src)

    for df in pd.read_sql_query(
            sql, engine("raw_tb_comment_notag"), chunksize=CUT_CHUNKSIZE):
        yield df


def get_init_info(pcid, cid):
    sql = f"SELECT count(*) FROM raw_comment_pcid{pcid}.raw_tb_comment{cid};"
    res = pd.read_sql(sql, con=engine("raw_tb_comment_notag"))
    num_comments = res["count"].values[0]
    print(f"Comments Num: {num_comments}")
    print(f"Rounds:", (num_comments+CUT_CHUNKSIZE-1)//CUT_CHUNKSIZE)

    num_words = -1
    try:
        sql = f"SELECT count(*) FROM frequency.pcid{pcid}cid{cid};"
        res = pd.read_sql(sql, con=engine("lexicon"))
        num_words = res["count"].values[0]
        print(f"freq已存在，数量：{num_words}")
    except Exception as e:
        # print("表不存在")
        pass
    return num_comments, num_words


def cut_words(pcid, cid):
    num_comments, num_words = get_init_info(pcid, cid)
    if -1 != num_words:
        return num_comments, num_words
    if 0 == num_comments:
        return 0, 0

    columns = ['itemid', 'comment_id', 'comment_all', 'word', 'datamonth']
    rank = 0
    frequency = dict()
    for df in get_comments(pcid, cid):
        df['comment_all'].fillna('', inplace=True)
        df = df[df['comment_all'] != '']
        df = df.reindex(columns=['itemid', 'comment_id', 'comment_all', 'comment_date'])
        df['comment_date'] = df['comment_date'].fillna("0").astype("str")
        df['datamonth'] = df['comment_date'].str.slice(0, 6)

        max_count = 10
        tmp = df.groupby(['comment_all']).agg(dict(comment_id='count')).reset_index()
        tmp = tmp[tmp['comment_id'] > max_count]

        df['is_useful'] = '是'
        df.loc[df['comment_all'].isin(tmp['comment_all']), 'is_useful'] = ''
        del tmp
        print('有效评价数量：{}'.format(len(df[df['is_useful'] != ''])))

        sentences = df.loc[df['is_useful'] != '', 'comment_all'].drop_duplicates().tolist()
        print('有效评价唯一数量：{}'.format(len(sentences)))

        result = map(cut, sentences)
        result = pd.concat(result, ignore_index=True)

        result = pd.merge(df, result, how='left', on=['comment_all'])
        del df
        result = result.reindex(columns=columns)

        update_freq(frequency, result["word"].astype(str).tolist())

        rank += 1
        print(f"第{rank}轮完成，each size={CUT_CHUNKSIZE}")
        del result
        del sentences

    all_frequency = 0
    for _, freq in frequency.items():
        all_frequency += freq
    frequency["#总词频#"] = all_frequency

    values = list()
    for k, v in frequency.items():
        values.append([k, v, v/all_frequency])
    values.sort(key=lambda x: x[1], reverse=True)
    df = pd.DataFrame(values, columns=["word", "frequency", "share"])
    df.to_sql(f"pcid{pcid}cid{cid}", con=engine("lexicon"), schema="frequency", index=False, if_exists='append')
    print("frequency已存入数据库")

    num_words = len(df)
    del df
    return num_comments, num_words


def print_time(msg, START, pcid, cid, num_comments, num_words, rank, total):
    END = datetime.datetime.now()
    print(f"\n===== {msg} =====")
    print(f"pcid {pcid} cid {cid} rank {rank}/{total}")
    print(f"Comments Num: {num_comments}")
    print(f"Words Num: {num_words}")
    print("Start Time", START)
    print("End Time", END)
    cost = END - START
    print("Cost", cost)
    return cost


def execute(tasks):
    try:
        os.remove("freq_stas.txt")
    except FileNotFoundError:
        pass
    for rank, task in enumerate(tasks, start=1):
        pcid, cid = task
        START = datetime.datetime.now()
        print("\n===== Begin =====")
        print(f"pcid {pcid} cid {cid} rank {rank}/{len(tasks)}")
        print(f"Time: {START}")
        num_comments, num_words = cut_words(pcid, cid)
        cost = print_time("Cut Words for Freq", START, pcid, cid, num_comments, num_words, rank, len(tasks))
        with open("freq_stas.txt", mode="a", encoding="utf-8") as fp:
            if NEW_REVIEW_LOCAL:
                fp.write(f"pcid {pcid} cid {cid} numComments {num_comments} numWords {num_words} costTime {cost}\n")
            else:
                fp.write(f"pcid {pcid} cid {cid} numComments {num_comments} numWords {num_words} costTime {cost}\r\n")


def get_tasks():
    pcids = [str(pcid) for pcid in range(0, 14)] + ["100"]

    sql = "SELECT table_name FROM information_schema.tables WHERE table_schema='raw_comment_pcid{pcid}';"
    result = dict()
    print("\n读取信息 ...")
    for pcid in pcids:
        tables = pd.read_sql(sql.format(pcid=pcid), con=engine("raw_tb_comment_notag"))
        result[pcid] = list()
        for table in tables["table_name"].values:
            parts = table.split("_")
            if "raw" != parts[0] or "tb" != parts[1] or "comment" != parts[2][: 7]:
                print("error table", table)
            elif 3 != len(parts):
                print("衍生表", table)
            else:
                cid = parts[2][7:]
                # print(f"pcid{pcid} 添加cid {cid}， table {table}")
                result.setdefault(pcid, list()).append(cid)

    tasks = list()
    print("\n创建任务 ...")
    for pcid, cids in result.items():
        if len(cids) != len(set(cids)):
            print(f"pcid{pcid} 存在重复表")
        else:
            print(f"pcid{pcid} 有 {len(cids)} 个cid")
            for cid in cids:
                tasks.append([pcid, cid])

    return tasks


if __name__ == '__main__':
    tasks = get_tasks()
    execute(tasks)
