# -*- coding: utf-8 -*-


from new_reviews.process.public import *


class Inverse(object):
    def __init__(self, pcid, cid):
        self.pcid = pcid
        self.cid = cid

    def get_frequency(self, pcid, cid, limit=10):
        sql = f"SELECT * FROM frequency.pcid{pcid}cid{cid} WHERE frequency > {limit};"
        df = pd.read_sql_query(sql, engine("lexicon"))
        words = set()
        word2freq = dict()
        for k, v in df.iterrows():
            if v["frequency"] > limit:
                words.add(v["word"])
                word2freq[v["word"]] = v["frequency"]
        return words, word2freq

    def TF(self):
        return 0

    def IDF(self):
        return 0

    def DIFF(self):
        """
            pcid0 其他 124086006 智能手表 95w
            pcid1 游戏话费 125104012 农药代练 19w
            pcid2 服装 50008898 卫衣 1965w 50008901 风衣 521w
            pcid3 手机数码 110808 路由器 127w
            pcid4 家用电器 50228001 音响 330w
            pcid5 美妆美饰 都做过了??? 121474010 面膜 7000w
            pcid6 母婴用品 50012440 理发器 45w 50013857 推车配件 42w
            pcid7 家居建材 121398012 窗帘轨道 36w 350615 接线板 300w
            pcid8 百货用品 121454005 剃须刀 100w
            pcid9 户外运动 50019775 电动平衡车 18w
            pcid10 文化娱乐 50017524 蓝牙耳机 0.4w
            pcid11 生活服务
            pcid12 空
            pcid13 汽配摩托 261712 车用氧吧/空气净化器 40w

            pcid100 特殊解决方式
        """
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
    words4, word2freq4 = obj.get_frequency("4", "50228001")
    words2, word2freq2 = obj.get_frequency("2", "50008898", limit=50)

    records = list()
    diff42 = words4 - words2
    for word in diff42:
        records.append([word, word2freq4[word]])
    records.sort(key=lambda x: x[1], reverse=True)

    for seq, record in enumerate(records, start=1):
        if record[1] > 500:
            print(seq, f": {record[0]} {record[1]}")

    """
    反向过滤发生在Filter之前，Filter __init__ 时候，过滤时把这些词放出来
    一些确定噪声词还是要过滤掉：符号，keyno
    """
