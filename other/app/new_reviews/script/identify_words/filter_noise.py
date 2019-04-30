# -*-coding:utf-8-*-
import sys
sys.path.append(r"D:\workspace\django\zhuican_web")
from reviews.script.db_operation import db_99_server, db_get

class Ngram(object):
    def __init__(self,**kargs):
        self.N = kargs['N']
        self.Mcls = kargs['Mcls']
        
    def nwords(self,sent):
        for i in range(len(sent)-(self.N-1)):
            yield sent[i:i+self.N]
                
    def fit(self):
        self.ngram_cnt = {}
        self.cls_cnt = {}
        self.all_cnt = 0
        
        for cls in self.Mcls:
            cnt = 0
            cnt_dict = {}
            for line in self.Mcls[cls]:
                if len(line) <= self.N:
                    continue
                words = self.nwords(line)
                for w in words:
                    cnt += self.Mcls[cls][line]
                    cnt_dict.setdefault(w,0)
                    cnt_dict[w] += self.Mcls[cls][line]
            self.ngram_cnt[cls] = cnt_dict
            self.cls_cnt[cls] = cnt
            
        self.all_cnt = 0
        for cls in self.Mcls:
            self.all_cnt += self.cls_cnt[cls]
    
    def prob(self,sent):
        if len(sent) < self.N:
            return dict.fromkeys(self.Mcls,0)
        words = self.nwords(sent)
        probs_cls = dict.fromkeys(self.Mcls,1.0)
        for w in words:
            for cls in self.Mcls:
                probs_cls[cls] *= (self.ngram_cnt[cls].get(w,0) *1.0 +1)/ (self.cls_cnt[cls] + len(self.ngram_cnt[cls]) )
        
        for cls in self.Mcls:
            probs_cls[cls] *= self.cls_cnt[cls] * 1.0 / self.all_cnt
        
        return probs_cls
    
    def get_pred(self,result):
        man = 0
        max_cls = ""
        for cls in result.keys():
            if result[cls] > man:
                man = result[cls]
                max_cls = cls
        return max_cls
                    

class FilterNoisy(object):
    def __init__(self,pcid,cid,model_filter = False):
        self.pcid = pcid
        self.cid = cid
        self.server99_lexicon = db_99_server("lexicon")
        self.NoiseFilterKeywords = self.load_nosiefilterkeyword()
        self.NoiseWords = self.load_noisy_words()
        self.model_filter = model_filter
        if self.model_filter:
            self.train_model()
    
    def train_model(self):
        noisy_words = self.load_Negwords()
        normal_words = self.load_Poswords()
        Mcls = {'n':normal_words,'y':noisy_words}
        self.Unimodel = Ngram(Mcls=Mcls,N=1)
        self.Unimodel.fit()
        self.Bimodel = Ngram(Mcls=Mcls,N=2)
        self.Bimodel.fit()
        
    def load_Negwords(self):
        sql = "SELECT word,count(*) as num from nomeaning group by word;".format(self.pcid)
        wordDic = {i:int(j) for i,j in db_get(self.server99_lexicon, sql)}
        sql = "SELECT word from opinions;"
        for i, in db_get(self.server99_lexicon, sql):
            wordDic[i] = wordDic.setdefault(i,0) + 1
        return wordDic
    
    def load_Poswords(self):
        sql = "SELECT target,count(*) as num from targets group by target;".format(self.pcid)
        wordDic = {i:j for i,j in db_get(self.server99_lexicon, sql)}
        return wordDic
    
    def load_nosiefilterkeyword(self):
        sql = "SELECT word from noisefilterkeywords ;".format(self.pcid)
        wordSet = [i for i, in db_get(self.server99_lexicon, sql)]
        return wordSet
    
    def load_noisy_words(self):
        #cid无意词库
        sql = "SELECT word from nomeaning where cid = '{}';".format(self.cid)
        wordSet_1 = {i:1 for i, in db_get(self.server99_lexicon, sql)}
        
        #全局无意词库
        sql = "SELECT target from targets_global where tag = 'delete';".format(self.cid)
        wordSet_1.update({i:1 for i, in db_get(self.server99_lexicon, sql)})
        
        return wordSet_1
    
    def isNoisyWord(self,word):
        #噪音词库过滤
        if word in self.NoiseWords:
            return True
        
        #噪音关键词过滤
        for keyword in self.NoiseFilterKeywords:
            if keyword in word:
                return True
        
        if self.model_filter:
            #贝叶斯分类模型过滤
            Uniresult = self.Unimodel.get_pred(self.Unimodel.prob(word))
            Biresult = self.Bimodel.get_pred(self.Bimodel.prob(word))
            return Uniresult == 'y' and Biresult == 'y'
        
        return False
    
if __name__ == "__main__":
    NoiseFilters = FilterNoisy(4,50013008)
    TestCases = ['阿志很','阿志','志气','空调','空空','支精华','柠檬皮']
    print(list(filter(NoiseFilters.isNoisyWord,TestCases)))
    