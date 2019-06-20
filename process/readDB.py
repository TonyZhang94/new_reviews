# -*- coding: utf-8 -*-

# from analysis.script.utils import *

from new_reviews.process.public import *
from new_reviews.process.cut_words import SPLIT, base


def get_cut_comments(pcid, cid, local=NEW_REVIEW_LOCAL):
    if local:
        print("本地读取cut结果")
        rank = 0
        dir_path = base.format(pcid, cid)
        while True:
            try:
                df = pd.read_csv(
                    f"{dir_path}comments_2_{rank}.csv", encoding=UTF8, index_col=0)
                df['datamonth'] = df['datamonth'].astype("int32").astype("str")
                rank += 1
                yield df.values
            except Exception as e:
                print(e)
                raise StopIteration
    else:
        print("数据库读取cut结果")
        table = 'raw_comment_pcid{}.raw_tb_comment{}_cut_new'.format(pcid, cid)
        sql = f"SELECT * FROM {table} WHERE word != '' and word is not null;"
        for df in pd.read_sql_query(sql, engine("tb_comment_words"), chunksize=ANA_CHUNKSIZE):
            yield df.values


def get_word_frequency(pcid, cid, local=NEW_REVIEW_LOCAL):
    dir_path = base.format(pcid, cid)
    if local:
        print("本地读取frequency")
        with open(f"{dir_path}frequency.pkl", mode="rb") as fp:
            frequency = pickle.load(fp)
        return frequency
    else:
        sql = f"SELECT word, frequency FROM frequency.pcid{pcid}cid{cid};"
        df = pd.read_sql(sql, engine("lexicon"))
        frequency = dict()
        for k, v in df.iterrows():
            frequency[v["word"]] = v["frequency"]
        return frequency


def get_target_seed(pcid, cid, isStep2=False):
    # 全局属性词
    # sql = "SELECT target,tag FROM targets_global WHERE tag != 'delete';"
    # df = pd.read_sql_query(sql, engine("lexicon"))
    #
    T_Seed = dict()
    # for k, v in df.iterrows():
        # if v["target"] in T_Seed:
        #     print("# global # 已有", v["target"])
        #     if T_Seed[v["target"]] != v["tag"]:
        #         print("冲突", T_Seed[v["target"]], v["tag"])
        # T_Seed[v["target"]] = v["tag"]

    # 品类属性词
    sql = "SELECT target,tag FROM targets WHERE pcid = '{}' and cid = '{}';".format(pcid, cid)
    df = pd.read_sql_query(sql, engine("lexicon"))
    if isStep2 and df.empty:
        sql = "SELECT target,top1class as tag FROM unsolved_targets WHERE pcid = '{}' and cid = '{}';".format(pcid, cid)
        df = pd.read_sql_query(sql, engine("lexicon"))
    for k, v in df.iterrows():
        # if v["target"] in T_Seed:
        #     print("# target # 已有", v["target"])
        #     if T_Seed[v["target"]] != v["tag"]:
        #         print("冲突", T_Seed[v["target"]], v["tag"])
        T_Seed[v["target"]] = v["tag"]

    return T_Seed


def get_sentiment_pcid(pcid, local=NEW_REVIEW_LOCAL):
    sql = f"SELECT * FROM sentiment.pcid{pcid};"
    try:
        if local:
            # print("本地读取sentiment.pcid")
            df = pd.read_csv(f"../data/sentiment.pcid{pcid}.csv", encoding=UTF8, index_col=0)
        else:
            # print("数据库读取sentiment.pcid")
            df = pd.read_sql_query(sql, engine("lexicon"))
    except Exception as e:
        raise e
    return df


if __name__ == '__main__':
    pcid, cid = "4", "50012097"
    # freq = get_word_frequency(pcid, cid)
    # for k, v in freq.items():
    #     print(k, v)

    for k, v in get_target_seed(pcid, cid).items():
        print(k, v)
