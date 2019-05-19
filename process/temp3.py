# -*- coding: utf-8 -*-

"""
2019/05/18
查看为什么会漏target，反向的等等
"""

import datetime

from new_reviews.process.public import *
from new_reviews.process.inverse import Inverse


def get_rule1_set(pcid, cid):
    obj = Inverse(pcid, cid)
    data = obj.get_inverse_result()
    res = dict()
    for item in data:
        res[item[0]] = 1
    return res


def get_word_check_data(pcid, cid, rules):
    sql = f"SELECT target, sentences, frequency, top1class " \
        f"FROM unsolved_targets WHERE pcid = '{pcid}' and cid = '{cid}' order by frequency desc;"
    df = pd.read_sql(sql, engine("lexicon"))
    data = list()
    for k, v in df.iterrows():
        # 0: target word
        # 1: 频次
        # 2: 相关句子
        # 3: 100 target -100 useless
        # 4: rule type

        # 其他
        # (-1, 0, 1, 2, 9) opinion
        # 0 局部 默认 1 全局

        if "delete" != v["top1class"]:
            ifuse = 100
        else:
            ifuse = -100

        try:
            rule_type = rules[v["target"]]
        except KeyError:
            rule_type = 0

        data.append([v["target"], v["frequency"], v["sentences"], ifuse, rule_type])
    return data


if __name__ == '__main__':
    pcid, cid = "4", "50228001"
    rules = dict()
    rule1 = get_rule1_set(pcid=pcid, cid=cid)
    rules.update(rule1)
    words = get_word_check_data(pcid=pcid, cid=cid, rules=rules)

    print("\ntype1")
    rank = 0
    for word in words:
        if 1 == word[4]:
            rank += 1
            print(rank, word[0], word[1])

    print("\ntype0")
    rank = 0
    for word in words:
        if 0 == word[4]:
            rank += 1
            print(rank, word[0], word[1])

