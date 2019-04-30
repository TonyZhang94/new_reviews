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
    def __init__(self):
        self.tagclass = ['使用场景', '适用人群', '价格', '服务', '活动', '质量', '功能', '款式']
        self.server99_lexicon = db_99_server("lexicon")
        self.TargetKeywords = self.load_targetkeywords()
        self.OpinionKeywords = self.load_opinionkeywords()
        self.rand1Cnt = 0
        self.rand2Cnt = 0
            
    def load_targetkeywords(self):
        sql = "SELECT word,tag from classification_target_keywords"
        wordDic = {i: [] for i in self.tagclass}
        for word, tag in db_get(self.server99_lexicon, sql):
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
            # 按关键词分类
            for tag in tags:
                for key in self.OpinionKeywords[tag]:
                    if key in opinion:
                        tagsCnt[tag] += len(opinion) * opinions[opinion]
        
        ans = sorted(tagsCnt.items(),key=lambda x:x[1],reverse=True)
        pred_tag = None 
        # 确认是否存在关键词匹配
        if ans[0][1] == 0 or ans[0][1] == ans[1][1]:
            pred_tag = "rand"
        else:
            pred_tag = ans[0][0]
            
        return pred_tag
        
    def pred(self,word,opinions=[]):
        finalClass = dict.fromkeys(self.tagclass,0)
        
        # 关键词分类，按照关键词长度匹配计算得分
        for tag in self.tagclass:
            for key in self.TargetKeywords[tag]:
                if key in word:
                    finalClass[tag] += len(key)
                    
        # 根据得分排序确认最后分类
        ans = sorted(finalClass.items(), key=lambda x:x[1], reverse=True)
        
        pred_tag = None 
        # 确认是否存在关键词匹配
        if ans[0][1] == 0:
            self.rand1Cnt += 1
            pred_tag = self.predbyOpinions(opinions, self.tagclass) if opinions else "rand"
        # 确认是否存在相同分数类别
        elif ans[0][1] == ans[1][1]:
            self.rand2Cnt += 1
            tags = []
            for i in range(0, len(ans)):
                if ans[i][1] == ans[0][1]:
                    tags.append(ans[i][0])
            pred_tag = self.predbyOpinions(opinions, tags) if opinions else "rand"
        else:
            pred_tag = ans[0][0]
        
        return pred_tag
    

def predict(feature_frequency):
    featureOpinionDict = {}
    # 预处理
    for itemid in feature_frequency:
        for feature in feature_frequency[itemid]:
            OpinionDic = featureOpinionDict.setdefault(feature,{})
            for opinion in feature_frequency[itemid][feature]:
                OpinionDic[opinion] = feature_frequency[itemid][feature][opinion] + OpinionDic.setdefault(opinion,0)
    
    Model = Classifier()
    predict_result = {}
    for key in featureOpinionDict:
        pred_tag = Model.pred(key, featureOpinionDict[key])
        predict_result[key] = (pred_tag, 1, '', 0)
    return predict_result
