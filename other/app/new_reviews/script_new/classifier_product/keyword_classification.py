# -*- coding:utf-8 -*-
import psycopg2
import random
def db_99_server(db):
    return psycopg2.connect(database=db, user="zczx_write", password="zczxTech2012",
                            host='192.168.1.99', port='5432')
def db_get(server, sql):
    dbconn = server.cursor()
    result = True
    try:
        dbconn.execute(sql)
        result = dbconn.fetchall()
    except Exception as e:
        server.rollback()
        print(e)
        result = False
    dbconn.close()
    return result

class Classifier(object):
    def __init__(self,Word2Vec_model_path):
        self.tagclass =  ['使用场景', '适用人群', '价格', '服务', '活动', '质量', '功能', '款式']
        self.server99_lexicon = db_99_server("lexicon")
        self.TargetKeywords = self.load_targetkeywords()
        self.OpinionKeywords = self.load_opinionkeywords()
        self.rand1Cnt = 0
        self.rand2Cnt = 0
        self.getSimilarity = self.loadWord2Vec(path=Word2Vec_model_path)
            
    def load_targetkeywords(self):
        sql = "SELECT word,tag from classification_target_keywords"
        wordDic = {i:[] for i in self.tagclass}
        for word,tag in db_get(self.server99_lexicon, sql):
            wordDic[tag].append(word)
        return wordDic
    
    def load_opinionkeywords(self):
        sql = "SELECT word,tag from classification_opinion_keywords"
        wordDic = {i:[] for i in self.tagclass}
        for word,tag in db_get(self.server99_lexicon, sql):
            wordDic[tag].append(word)
        return wordDic
    
    def predbyOpinions(self,opinions,tags):
        """
            tags: 可选的分类
            opinions:需要分类的词
        """
        tagsCnt = dict.fromkeys(tags,0)
        for opinion in opinions:
            #按关键词分类
            for tag in tags:
                for key in self.OpinionKeywords[tag]:
                    if key in opinion:
                        tagsCnt[tag] += len(opinion)
        
        ans = sorted(tagsCnt.items(),key=lambda x:x[1],reverse=True)
        pred_tag = None 
        possible_tags = []
        #确认是否存在关键词匹配
        if ans[0][1] == 0:
            pred_tag = "rand"
            possible_tags = tags
        elif ans[0][1] == ans[1][1]:
            pred_tag = "rand"
            for i in range(0,len(ans)):
                if ans[i][1] == ans[0][1]:
                    possible_tags.append(ans[i][0])
        else:
            pred_tag = ans[0][0]
            
        return pred_tag,possible_tags
        
    def pred(self,word,opinions=[]):
        finalClass = dict.fromkeys(self.tagclass,0)
        
        #关键词分类，按照关键词长度匹配计算得分
        for tag in self.tagclass:
            for key in self.TargetKeywords[tag]:
                if key in word:
                    finalClass[tag] += len(key)
                    
        #根据得分排序确认最后分类
        ans = sorted(finalClass.items(),key=lambda x:x[1],reverse=True)
        
        pred_tag = None 
        #确认是否存在关键词匹配
        if ans[0][1] == 0:
            self.rand1Cnt += 1
            pred_tag,possible_tags =  self.predbyOpinions(opinions, self.tagclass) if opinions else ("rand",self.tagclass)
            pred_tag = self.predbyWord2Vec(word,possible_tags) if pred_tag == "rand" and self.getSimilarity else pred_tag
        #确认是否存在相同分数类别
        elif ans[0][1] == ans[1][1]:
            self.rand2Cnt += 1
            tags = []
            for i in range(0,len(ans)):
                if ans[i][1] == ans[0][1]:
                    tags.append(ans[i][0])
            pred_tag,possible_tags = self.predbyOpinions(opinions, tags) if opinions else ("rand",tags)
            pred_tag = self.predbyWord2Vec(word,possible_tags) if pred_tag == "rand" and self.getSimilarity else pred_tag
        else:
            pred_tag = ans[0][0]
        
        return pred_tag
    
    def loadWord2Vec(self,path):
        from gensim.models.keyedvectors import KeyedVectors
        import numpy as np
        word_vectors = KeyedVectors.load_word2vec_format(path,binary=False)
        def get_vector(word):
            vetcor = np.zeros([word_vectors.vector_size],np.float32)
            for w in word:
                if w in word_vectors.vocab:
                    vetcor = vetcor + word_vectors[w]
            vetcor = vetcor / len(word)
            return vetcor
        
        def get_similarity(w1,w2):
            w1_vector = get_vector(w1)
            w2_vector = get_vector(w2)
            
            sim = float(np.dot(w1_vector,w2_vector)) / (np.linalg.norm(w1_vector) + np.linalg.norm(w2_vector))
            sim = 0.5 + 0.5 * sim
            return sim
        return get_similarity
        
    def predbyWord2Vec(self,word,tags,alpha = 0.5):
        """
            alpha:分类最小阈值
            tags:可能的分类标签
            word:待分类的词语
        """
        MostSimilarity = dict.fromkeys(tags,0)
        for tag in tags:
            for w in self.TargetKeywords[tag]:
                grade = self.getSimilarity(w,word)
                if MostSimilarity[tag] < grade:
                    MostSimilarity[tag] = grade
        
        pred_tag = "rand"
        pred_grade = alpha
        for k,v in MostSimilarity.items():
            if pred_grade < v:
                pred_grade = v
                pred_tag = k
        return pred_tag
    

def predict(feature_frequency):
    featureOpinionDict = {}
    #预处理
    for itemid in feature_frequency:
        for feature in feature_frequency[itemid]:
            OpinionDic = featureOpinionDict.setdefault(feature,{})
            for opinion in feature_frequency[itemid][feature]:
                OpinionDic[opinion] = feature_frequency[itemid][feature][opinion] + OpinionDic.setdefault(opinion,0)
    
    Model = Classifier(Word2Vec_model_path="/home/nlp/word2vec/bert.vector")
    predict_result = {}
    for key in featureOpinionDict:
        pred_tag = Model.pred(key,featureOpinionDict[key])
        predict_result[key] = (pred_tag,1,'',0)
    return predict_result
        