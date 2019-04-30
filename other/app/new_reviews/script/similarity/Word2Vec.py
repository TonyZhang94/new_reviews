from gensim.models import word2vec
import logging
import jieba
import re
import csv
from ..db_operation import *

class cidCorpus(object):
    """
                    读取comments文件数据并处理，采用迭代器的设计，节约内存
                    记得注意comments文件格式
    """
    def __init__(self,pcid,cid):
        self.cid = cid
        self.pcid = pcid
        self.server99_comments = db_99_server("raw_tb_comment_notag")
        self.src_table = "raw_comment_pcid{}.raw_tb_comment{}".format(self.pcid,self.cid)
        self.stopwords = self.stopwordslist("./data/stopwords.txt")
        
    def load_reviews_data(self):
        sql = "SELECT comment_all from %s " % (self.src_table)
        result = db_get(self.server99_comments, sql)
        return result
        
    def clean_sent(self,text):
        string = re.sub("[A-Z]+|[a-z]+|[0-9]+|[\s+\.\!\/_,$%^*(+\"\']+|[<>《》+——！，。？、~@#￥%……&*（）]+", "",text)  
        return string
    
    def stopwordslist(self,filepath):
        try:
            stopwords = [line.strip() for line in open(filepath, 'r', encoding='utf-8').readlines()]  
        except Exception as e:
            stopwords = []
            print(e)
        return stopwords
    
    def __iter__(self):
        
        for row in self.load_reviews_data(): 
            seg_list = jieba.cut(self.clean_sent(row[0]),cut_all=False)
            yield [w for w in seg_list if w not in self.stopwords]


def trainWord2Vec(pcid,cid,save_vector_path):
    """
            通过gensim训练数据，并保存
    """
    wordSize = 64
    windows_width = 5
#     save_vector_path = save_path + "./{}_word.vector".format(cid)
    corpus = cidCorpus(pcid,cid)
    # 构建模型,min_count为过滤低频词,windows为词向量窗口大小，size为训练之后的词向量维度
    model = word2vec.Word2Vec(corpus, min_count=5,window=5,size=wordSize)
    # 保存模型
    model.wv.save_word2vec_format(save_vector_path,binary=False)
    return model.wv

if __name__ == '__main__':
    
    trainWord2Vec(pcid,cid)