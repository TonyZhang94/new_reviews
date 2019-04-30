# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import sqlalchemy as sa
import _pickle as pickle
import copy

# from DBparam import Outer99


class DB99(object):
    host = "192.168.1.99"
    port = 5432
    # host = "125.120.148.121"
    # port = 28943
    user = "zczx_write"
    password = "zczxTech2012"

    DB = dict()
    DB["standard_library"] = "standard_library"
    DB["fact_library"] = "fact_library"
    DB["zhuican_web"] = "zhuican_web"
    DB["raw_mj_category"] = "raw_mj_category"
    DB["report_dg"] = "report_dg"
    DB["raw_tb_comment_notag"] = "raw_tb_comment_notag"
    DB["tb_comment_hanlp"] = "tb_comment_hanlp"
    DB["lexicon"] = "lexicon"


DBDefault = DB99


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
            print("Try Create Connection With DB", db, "...")
            conn = sa.create_engine("postgresql://{USER}:{PASS}@{HOST}:{PORT}/{DB}".
                                    format(USER=info.user,
                                           PASS=info.password,
                                           HOST=info.host,
                                           PORT=info.port,
                                           DB=info.DB[db]))
            self.__class__.engines_pool[db] = conn
            return conn

    def __call__(self, db):
        return self.get_engine(db)


engine = Engine()
UTF8 = "utf_8_sig"
# NEW_REVIEW_LOCAL = True
NEW_REVIEW_LOCAL = False
FREQUENCY_LIMIT = 20
# STASFTRE = True
STASFTRE = False
CUT_CHUNKSIZE = 1e5
ANA_CHUNKSIZE = 1e5

# NEW_REVIEW_PATH = ".."
NEW_REVIEW_PATH = "new_reviews"

IF_DELAY = False
