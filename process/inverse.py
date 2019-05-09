# -*- coding: utf-8 -*-


from new_reviews.process.public import *
from new_reviews.lexicon.lexicon import GetLexicon


class Inverse(object):
    def __init__(self, pcid, cid, threshold_cmp=50, threshold_add=100, save=None):
        self.pcid = pcid
        self.cid = cid
        self.threshold_cmp = threshold_cmp
        self.threshold_add = threshold_add
        self.save = save

        self.chars = None
        self.keyno = None

    def get_frequency(self, pcid, cid, limit=50):
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
        mapping = {
            "0": ["2", "50008901"],
            "1": ["2", "50008901"],
            "2": ["4", "50228001"],
            "3": ["2", "50008901"],
            "4": ["2", "50008901"],
            "5": ["4", "50228001"],
            "6": ["4", "50228001"],
            # "7": ["5", "121474010"],
            "7": ["6", "50012440"],
            "8": ["2", "50008901"],
            "9": ["4", "50228001"],
            "10": ["4", "50228001"],
            "11": ["4", "50228001"],
            "12": ["4", "50228001"],
            "13": ["2", "50008901"],
            "100": ["0", "124086006"]
        }
        try:
            cmp_pcid, cmp_cid = mapping["pcid"]
        except KeyError:
            cmp_pcid, cmp_cid = "0", "124086006"

        words, words_freq = self.get_frequency(self.pcid, self.cid)
        words_cmp, _ = self.get_frequency(cmp_pcid, cmp_cid, self.threshold_cmp)
        return words-words_cmp, words_freq

    def search(self, method="DIFF"):
        if "DIFF" == method:
            self.DIFF()
        else:
            tf = self.TF()  # vector
            idf = self.IDF()  # vector
            return tf * idf

    def get_ml_text(self):
        sql = f"SELECT target, sentences FROM unsolved_targets WHERE pcid = '{self.pcid}' and cid = '{self.cid}';"
        df = pd.read_sql(sql, con=engine("lexicon"))
        ml_text = dict()
        for k, v in df.iterrows():
            ml_text[v["target"]] = v["sentences"]
        return ml_text

    def if_add(self, word, freq):
        if freq < self.threshold_add:
            return False
        if word in self.chars:
            return False
        for char in list(word):
            if char in self.keyno:
                return False
        return True

    def get_inverse_result(self):
        words, words_freq = self.DIFF()
        records = list()
        lexicon = GetLexicon()
        lexicon.read_all(self.pcid)
        self.chars = lexicon.get_chars()
        self.keyno = lexicon.get_keyno()
        # ml_text = self.get_ml_text()
        for word in words:
            if self.if_add(word, words_freq[word]):
                # (100) target 默认
                # (-1, 0, 1, 2, 9) opinion
                # -100 无用词
                # 0 局部 默认 1 全局
                # records.append([word, ml_text[word], words_freq[word], 100, 0])
                records.append([word, words_freq[word], 100, 0])
        records.sort(key=lambda x: x[1], reverse=True)

        if self.save is None:
            self.save = int(len(words) * 0.04)
            print("save set", self.save)
        if self.save < len(records):
            records = records[: self.save]
        # for seq, record in enumerate(records, start=1):
        #     print(seq, f": {record[0]} {record[1]}")

        return records


if __name__ == '__main__':
    """
    STEP1
    方案一：
    cut后
    
    方案二：
    filter后
    
    STEP2
    方案一：
    DIFF
    
    方案二：
    TF-IDF
    """
    pcid, cid = "2", "50008901"
    # pcid, cid = "4", "50228001"
    obj = Inverse(pcid, cid)
    obj.get_inverse_result()
    # words4, word2freq4 = obj.get_frequency("4", "50228001")
    # words2, word2freq2 = obj.get_frequency("2", "50008898", limit=50)
    #
    # records = list()
    # diff42 = words4 - words2
    # for word in diff42:
    #     records.append([word, word2freq4[word]])
    # records.sort(key=lambda x: x[1], reverse=True)
    #
    # for seq, record in enumerate(records, start=1):
    #     if record[1] > 500:
    #         print(seq, f": {record[0]} {record[1]}")

    """
    反向过滤发生在Filter之前，Filter __init__ 时候，过滤时把这些词放出来
    一些确定噪声词还是要过滤掉：符号，keyno
    """
