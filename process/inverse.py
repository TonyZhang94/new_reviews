# -*- coding: utf-8 -*-


from new_reviews.process.public import *


class Inverse(object):
    def __init__(self, pcid, cid):
        self.pcid = pcid
        self.cid = cid

    def get_frequency(self, pcid, cid):
        sql = f"SELECT * FROM frequency.pcid{pcid}cid{cid};"
        df = pd.read_sql_query(sql, engine("lexicon"))
        print(df)
        pass

    def TF(self):
        return 0

    def IDF(self):
        return 0

    def DIFF(self):
        if "4" == self.pcid:
            cmp_pcid = "2"
            cmp_cid = ""
        else:
            cmp_pcid = "4"
            cmp_cid = "50012097"

        self.get_frequency(self.pcid, self.cid)
        # self.get_frequency(cmp_pcid, cmp_cid)

    def search(self, method="DIFF"):
        if "DIFF" == method:
            self.DIFF()
        else:
            tf = self.TF()  # vector
            idf = self.IDF()  # vector
            return tf * idf


if __name__ == '__main__':
    """
    STEP1
    方案一：
    cut后
    
    方案二：
    filter后
    
    STEP2
    方案一：
    差集
    
    方案二：
    TF-IDF
    """
    pcid, cid = "4", "50012097"
    obj = Inverse(pcid, cid)
    obj.DIFF()
