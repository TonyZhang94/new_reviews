# -*- coding: utf-8 -*-

"""
2019/05/31
cut_new 数据太多，98上读完拷贝下来
"""

import numpy as np
import pandas as pd
import sqlalchemy as sa

dynamic_ip = "office.e-corp.cn"


class Outer99(object):
    host = dynamic_ip
    port = 28943
    user = "zczx_write"
    password = "zczxTech2012"

    DB = dict()
    DB["standard_library"] = "standard_library"
    DB["fact_library"] = "fact_library"
    DB["zhuican_web"] = "zhuican_web"
    DB["raw_mj_category"] = "raw_mj_category"
    DB["report_dg"] = "report_dg"
    DB["raw_tb_comment_notag"] = "raw_tb_comment_notag"
    DB["tb_comment_nlp"] = "tb_comment_nlp"
    DB["lexicon"] = "lexicon"
    DB["tb_comment_words"] = "tb_comment_words"
    DB["chu"] = "chu"


DBDefault = Outer99


class Engine(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            print("Creating Engine Singleton ...")
            cls.engines_pool = dict()
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self, *args, **kwargs):
        pass

    def get_engine(self, db, info=DBDefault):
        try:
            conn = self.__class__.engines_pool[db]
            # print("Find Existed Connection With", db, "...")
            return conn
        except KeyError:
            if "tb_comment_words" != db:
                print("Try Create Connection With DB on 99", db, "...")
                conn = sa.create_engine("postgresql://{USER}:{PASS}@{HOST}:{PORT}/{DB}".
                                        format(USER=info.user,
                                               PASS=info.password,
                                               HOST=info.host,
                                               PORT=info.port,
                                               DB=info.DB[db]))
            else:
                print("Try Create Connection With DB on 114", db, "...")
                conn = sa.create_engine("postgresql://{USER}:{PASS}@{HOST}:{PORT}/{DB}".
                                        format(USER=info.user,
                                               PASS=info.password,
                                               # HOST="192.168.1.114",  # for use
                                               HOST=info.host,  # for test
                                               PORT=info.port,
                                               DB=info.DB[db]))
            self.__class__.engines_pool[db] = conn
            return conn

    def __call__(self, db):
        return self.get_engine(db)


UTF8 = "utf_8_sig"


def get_all_cut_comments(pcid, cid):
    engine = Engine()
    table = 'raw_comment_pcid{}.raw_tb_comment{}_cut_new'.format(pcid, cid)
    sql = f"SELECT * FROM {table} WHERE word != '' and word is not null LIMIT 1000;"
    # sql = f"SELECT * FROM {table} WHERE word != '' and word is not null;"
    df = pd.read_sql(sql, engine("raw_tb_comment_notag"))
    df.to_csv(f"cut_new_pcid{pcid}cid{cid}.cvs", encoding=UTF8)


if __name__ == '__main__':
    pcid, cid = "4", "50228001"
    get_all_cut_comments(pcid, cid)
