# -*- coding: utf-8 -*-

import multiprocessing
import os

import jieba

from new_reviews.process.public import *


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


def get_comments(pcid, cid, dir_path):
    rank = 0
    if NEW_REVIEW_LOCAL:
        print("本地读取评价")
        while True:
            try:
                df = pd.read_csv(
                    f"{dir_path}comments_1_{rank}.csv", encoding=UTF8, index_col=0)
                rank += 1
                yield df
            except Exception as e:
                print(e)
                raise StopIteration
    else:
        print("数据库读取评价")
        # os.makedirs(dir_path)

        table_src = 'raw_comment_pcid{}.raw_tb_comment{}'.format(pcid, cid)
        sql = "select itemid, comment_id, comment_all, comment_date from {} " \
              "order by itemid Limit 10000".format(table_src)

        # table_src = 'raw_comment_pcid{}.raw_tb_comment{}'.format(pcid, cid)
        # sql = "select itemid, comment_id, comment_all, comment_date from {} " \
        #       "order by itemid;".format(table_src)

        for df in pd.read_sql_query(
                sql, engine("raw_tb_comment_notag"), chunksize=CUT_CHUNKSIZE):
            # df.to_csv(f"{dir_path}comments_1_{rank}.csv", encoding=UTF8)
            rank += 1
            yield df


def save_result(result, dir_path, table, rank):
    if NEW_REVIEW_LOCAL:
        print("测试环境，result结果保存至本地")
        result.to_csv(f"{dir_path}comments_2_{rank}.csv", encoding="utf-8")
        rank += 1
    else:
        print("运行环境，result结果保存至数据库")
        result.to_sql(table.split(".")[1], con=engine("raw_tb_comment_notag"),
                      schema=table.split(".")[0], if_exists='append', index=False, dtype=None)


def init_table(columns, table):
    if not NEW_REVIEW_LOCAL:
        print(f"初始化数据表{table}")
        df = pd.DataFrame(columns=columns)
        df.to_sql(table.split(".")[1], con=engine("raw_tb_comment_notag"),
                  schema=table.split(".")[0], if_exists='append', index=False, dtype=None)
        sql = "TRUNCATE table {};".format(table)
        try:
            pd.read_sql(sql, engine("raw_tb_comment_notag"))
        except Exception as e:
            # This result object does not return rows. It has been closed automatically.
            # 错误忽略
            pass


def cut_words(pcid, cid):
    dir_path = base.format(pcid, cid)
    columns = ['itemid', 'comment_id', 'comment_all', 'word', 'datamonth']
    table = 'raw_comment_pcid{}.raw_tb_comment{}_cut_new'.format(pcid, cid)
    init_table(columns, table)

    rank = 0
    frequency = dict()
    for df in get_comments(pcid, cid, dir_path):
        df['comment_all'].fillna('', inplace=True)
        df = df[df['comment_all'] != '']
        df = df.reindex(columns=['itemid', 'comment_id', 'comment_all', 'comment_date'])
        df['comment_date'] = df['comment_date'].fillna("0").astype("str")
        df['datamonth'] = df['comment_date'].str.slice(0, 6)

        max_count = 10
        tmp = df.groupby(['comment_all']).agg(dict(comment_id='count')).reset_index()
        tmp = tmp[tmp['comment_id'] > max_count]

        # def func(df):
        #     print(df["comment_all"].values[0])
        #     print("此条无用评价有", len(df), "条")
        # tmp.groupby(["comment_all"]).apply(func)

        df['is_useful'] = '是'
        df.loc[df['comment_all'].isin(tmp['comment_all']), 'is_useful'] = ''
        del tmp
        print('有效评价数量：{}'.format(len(df[df['is_useful'] != ''])))

        sentences = df.loc[df['is_useful'] != '', 'comment_all'].drop_duplicates().tolist()
        print('有效评价唯一数量：{}'.format(len(sentences)))

        # pool = multiprocessing.Pool(multiprocessing.cpu_count())
        # result = pool.map(cut, sentences)
        result = map(cut, sentences)
        result = pd.concat(result, ignore_index=True)

        result = pd.merge(df, result, how='left', on=['comment_all'])
        del df
        result = result.reindex(columns=columns)
        # result = optimize_df_memory_usage(result)

        update_freq(frequency, result["word"].astype(str).tolist())
        """TF"""
        save_result(result, dir_path, table, rank)
        rank += 1
        print(f"第{rank}轮完成，each size={CUT_CHUNKSIZE}")
        del result
        del sentences

    all_frequency = 0
    for _, freq in frequency.items():
        all_frequency += freq
    frequency["#总词频#"] = all_frequency

    if NEW_REVIEW_LOCAL:
        with open(f"{dir_path}frequency.pkl", mode="wb") as fp:
            pickle.dump(frequency, fp)
    else:
        sql = f"DROP table frequency.pcid{pcid}cid{cid};"
        try:
            pd.read_sql(sql, engine("lexicon"))
            print("清空frequency数据")
        except Exception as e:
            # This result object does not return rows. It has been closed automatically.
            # 错误忽略
            pass

        values = list()
        for k, v in frequency.items():
            values.append([k, v])
        values.sort(key=lambda x: x[1], reverse=True)
        df = pd.DataFrame(values, columns=["word", "frequency"])
        df.to_sql(f"pcid{pcid}cid{cid}", con=engine("lexicon"), schema="frequency", index=False, if_exists='append')
        print("frequency已存入数据库")


import time
import datetime


def print_time(msg, START):
    END = datetime.datetime.now()
    print(f"===== {msg} =====")
    print("start time", START)
    print("end time", END)
    print("cost", END - START)
    return END


if __name__ == '__main__':
    pcid, cid = "4", "50012097"
    # pcid, cid = "4", "50228001"
    START = datetime.datetime.now()
    print("begin", START)
    cut_words(pcid, cid)
    print_time("cut words", START)
