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
        try:
            df = pd.read_csv(f"pcid{pcid}cid{cid}.csv")
            print("Read Local Data")
        except FileNotFoundError:
            print("Read Data From DB")
            sql = f"SELECT * FROM frequency.pcid{pcid}cid{cid} WHERE frequency > {limit};"
            df = pd.read_sql_query(sql, engine("lexicon"))
            df.to_csv(f"pcid{pcid}cid{cid}.csv")
        words = set()
        word2freq = dict()
        for k, v in df.iterrows():
            if v["frequency"] > limit:
                words.add(v["word"])
                # word2freq[v["word"]] = v["frequency"]
                word2freq[v["word"]] = [v["frequency"], v["share"]]
        return words, word2freq

    def TF(self):
        _, words_tf = self.get_frequency(self.pcid, self.cid, 100)
        return words_tf

    def IDF(self):
        with open("../freq/freq_data/info_idf.pkl", mode="rb") as fp:
            words_idf = pickle.load(fp)
        return words_idf

    def cal_score(self):
        words_tf = self.TF()
        words_idf = self.IDF()
        records = list()
        records_not_find = list()
        for word, record in words_tf.items():
            freq, tf = record
            if word not in words_idf:
                # print(f"{word} not in idf")
                records_not_find.append([word, tf, freq])
                continue
            records.append([word, tf/words_idf[word], freq])

        records.sort(key=lambda x: x[1], reverse=True)
        records_not_find.sort(key=lambda x: x[1], reverse=True)

        return records, records_not_find

    def search(self, method="DIFF"):
        pass

    def if_add(self, word, freq):
        pass

    def get_inverse_result(self, top1=1000, top2=500, not_find_threshold={"freq": 1.5e-7, "cnt": 50}):
        records, records_not_find = self.cal_score()
        print("\nTop", top1)
        for seq, record in enumerate(records, start=1):
            print(seq, record[0], record[1], record[2])
            if seq >= top1:
                break

        print("\nNot Find:")
        for seq, record in enumerate(records_not_find, start=1):
            if not_find_threshold["freq"] > record[1] or not_find_threshold["cnt"] > record[2]:
                break
            print(seq, record[0], record[1], record[2])
            if seq >= top2:
                break


if __name__ == '__main__':
    """
    实际：
    统计词频
    每个行业取10个/20个？1000w级别的cid
    
    一个cid和几个cid做差，然后比较
    
    最高的去掉不算推荐：的了着，通用target在comment_target里有，漏掉也无所谓
    全都很低的不算
    
    ========================================= 算了
    统计idf词频，计入本地，list保存，排名，排名百分比，词频百分比
    =========================================
    
    理论：
    选取多少个行业：7000+
    
    词内部权重TF 高 log 词频/总数，外部没有的词怎么办
    词外部权重IDF 低 log 词频/总数 加和（为什么要取log，评价太多了，难保不相关词会出现，不同行业评价数量差异过大，用词频率表示）
    
    有一个高频停用词库，保证样本的高正确性
    
    加通用target
    
    挑一句话有多个target的，比例，多少字中有一个target（指标）
    loss怎么定
    """
    # pcid, cid = "2", "50008901"
    pcid, cid = "4", "50228001"
    obj = Inverse(pcid, cid)
    obj.get_inverse_result()
