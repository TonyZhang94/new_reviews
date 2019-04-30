# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import sqlalchemy as sa
import _pickle as pickle
import copy

from DBparam import Outer99


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
NEW_REVIEW_LOCAL = True
# NEW_REVIEW_LOCAL = False
FREQUENCY_LIMIT = 20
WORD_NUM_THRESHOLD = 2000
# STASFTRE = True
STASFTRE = False
CUT_CHUNKSIZE = 1e5
ANA_CHUNKSIZE = 1e5

NEW_REVIEW_PATH = ".."
# NEW_REVIEW_PATH = "new_reviews"

IF_DELAY = False
