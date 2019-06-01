# -*- coding: utf-8 -*-

"""
2019/05/31
测试一个词占总词频
占核心词词频
有多少条有效评价有这个词
"""

from new_reviews.process.public import *
from new_reviews.process.readDB import get_cut_comments
from new_reviews.process.temp3 import *


def word_info(pcid, cid):
    df = pd.read_csv(f"../freq/freq_data/pcid{pcid}cid{cid}.csv")
    words = dict()
    for k, v in df.iterrows():
        word, frequency, share = v["word"], v["frequency"], v["share"]
        words[word] = [frequency, share]
    return words


def get_cut_comments(pcid, cid):
    # table = 'raw_comment_pcid{}.raw_tb_comment{}_cut_new'.format(pcid, cid)
    # sql = f"SELECT * FROM {table} WHERE word != '' and word is not null;"
    # for df in pd.read_sql_query(sql, engine("raw_tb_comment_notag"), chunksize=ANA_CHUNKSIZE):
    #     yield df.values

    df = pd.read_csv(f"cut_new_pcid{pcid}cid{cid}.cvs", encoding=UTF8, index_col=0)
    return df.values, len(df)


def exp_1_1(words, targets):
    for target in targets:
        print(target, words[target])


def exp_1_2(pcid, cid, words, targets):
    rules = dict()
    rule1 = get_rule1_set(pcid=pcid, cid=cid)
    rules.update(rule1)
    core_words = get_word_check_data(pcid=pcid, cid=cid, rules=rules)

    core_word_num = 0
    core_word_freq = 0
    core_word = list()

    inverse_num = 0
    normal_num = 0
    filter_num = 0

    inverse_freq = 0
    normal_freq = 0
    filter_freq = 0

    inverse_word = list()
    normal_word = list()
    filter_word = list()

    target_freq = {tar: 0 for tar in targets}
    targets_bak = set(targets)

    for record in core_words:
        word, freq, rule = record[0], record[1], record[4]
        # try:
        #     word, freq, rule = record[0], words[record[0]][0], record[4]
        # except KeyError:
        #     word, freq, rule = record[0], 0, record[4]
        if word in targets_bak:
            target_freq[word] = freq
            print("target word", word, freq)
            print(record)

        if 1 == rule:
            core_word_num += 1
            core_word_freq += freq
            core_word.append(word)

            inverse_num += 1
            inverse_freq += freq
            inverse_word.append(word)
        elif 0 == rule and freq >= 1000:
            core_word_num += 1
            core_word_freq += freq
            core_word.append(word)

            normal_num += 1
            normal_freq += freq
            normal_word.append(word)
        else:
            filter_num += 1
            filter_freq += freq
            filter_word.append(word)

    print(f"core word num {core_word_num} freq {core_word_freq}")
    print(f"inverse word num {inverse_num} freq {inverse_freq}")
    print(f"normal word num {normal_num} freq {normal_freq}")
    print(f"filter word num {filter_num} freq {filter_freq}")
    for target in targets:
        print(target, target_freq[target], target_freq[target]/core_word_freq)


def exp_1_3(pcid, cid, targets):
    table = 'raw_comment_pcid{}.raw_tb_comment{}'.format(pcid, cid)
    sql = f"SELECT count(*) FROM {table};"
    df = pd.read_sql(sql, engine("raw_tb_comment_notag"))
    cnt_all = df["count"].values[0]
    print("all comment num:", cnt_all)

    table = 'raw_comment_pcid{}.raw_tb_comment{}_cut_new'.format(pcid, cid)
    sql = f"SELECT count(*) FROM {table};"
    df = pd.read_sql(sql, engine("raw_tb_comment_notag"))
    cnt_valid = df["count"].values[0]
    print("valid comment num:", cnt_valid)

    SPLIT = '#='
    freq = {tar: 0 for tar in targets}
    data, size = get_cut_comments(pcid, cid)
    target_comments = {tar: 0 for tar in targets}
    print("comments num:", size)
    for seq, row in enumerate(data, start=1):
        comment_words = set(str(row[3]).split(SPLIT))
        for target in targets:
            if target in comment_words:
                target_comments[target] += 1

        if 0 == seq % 1e4:
            print(f"process {seq}/{size} ...")

    for target in targets:
        print(target, target_comments[target], target_comments[target] / size)


if __name__ == '__main__':
    pcid, cid = "4", "50228001"
    targets = ["声音", "音质"]
    words = word_info(pcid, cid)

    print("\n词频，词频率（占总词频）")
    exp_1_1(words, targets)

    print("\n词频，词频率（占核心词，此处粗糙统计）")
    exp_1_2(pcid, cid, words, targets)

    print("\n评价信息")
    exp_1_3(pcid, cid, targets)
