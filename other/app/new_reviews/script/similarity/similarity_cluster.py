import os

from gensim.models.keyedvectors import KeyedVectors
import numpy as np

from zhuican.test import logger, log

from reviews.script.db_operation import *
from reviews.script.Text_Analysis.extract_opinion import load_similar_dictionary


SAMPLE_SEN = 6


def generate_sample_sents(sents, word):
    ans = []
    for sent in sents:
        try:
            t_id = sent.index(word)
            end_id = min(t_id + 1, len(sent))
            for i in range(end_id, len(sent)):
                if 'A' <= sent[i][0] <= 'Z':
                    end_id = i
                    break
            start_id = max(0, t_id - 1)
            for i in range(start_id, 0, -1):
                if 'A' <= sent[i][0] <= 'Z':
                    start_id = i + 1
                    break
            ans.append("".join(sent[start_id:end_id]))
        except Exception as e:
            pass
    return list(set(ans))


class Simlarity(object):
    def __init__(self, text=None):
        text = text or dict()
        self.server99_lexicon = db_99_server("lexicon")
        self.server99_nlp = db_99_server("tb_comment_nlp")
        self.text = text

    @logger
    def load_Word2Vec(self, pcid, cid, vector_path):
        """
        func:载入词向量，若不存在则在线训练
        """
        #         vector_path = path + "/{}_word.vector".format(cid)
        if os.path.exists(vector_path):
            log.logger.info("========> 载入词向量")
            self.word_vectors = KeyedVectors.load_word2vec_format(vector_path, binary=False)
        else:
            log.logger.info("========> 词向量文件不存在 :", vector_path)

    @logger
    def load_target(self, pcid, cid):
        """
        func:载入需要聚类的词语
        """
        clusters = []
        sql = "SELECT target,frequency from unsolved_targets where cid = '{}' ".format(cid)
        nlp_sql = "SELECT target,count(*) from pcid{}.review_analysis_{} group by target".format(pcid, cid)
        result = db_get(self.server99_lexicon, sql)
        self.target_freq = {row[0]: row[1] for row in result}
        result = db_get(self.server99_nlp, nlp_sql)
        self.target_freq.update({row[0]: row[1] for row in result})
        self.wordmap = {k: i for i, k in enumerate(self.target_freq.keys())}
        self.idmap = {i: k for i, k in enumerate(self.target_freq.keys())}
        self._init_clusters = [[k] for k in self.target_freq.keys()]
        print(f"有{len(self._init_clusters)}待聚类")
        log.logger.info("========> 载入打标词汇")

    @logger
    def run(self, pcid, cid, path, alpha=0.85):
        """
        params:
        path:词向量文件的路径
        alpha:相似度的最小阈值
        """
        log.logger.info("alpha:{}".format(alpha))
        self.load_target(pcid, cid)
        self.load_Word2Vec(pcid, cid, path)
        self._init_similarity()

        flag = True
        while flag:
            index, simi = self.get_next(self._init_clusters, alpha)
            if index:
                log.logger.info("combine({}):{} and {}".format(simi, index[0], index[1]))
                self.combine(self._init_clusters, index[0], index[1])
            else:
                flag = False

        # 结束
        self.get_clustersname(pcid, cid)

        self.wirte_to_table(pcid, cid)

    def combine(self, clusters, i, j):
        """
        func:合并指定的两个聚类
        """
        del_1 = clusters[i]
        del_2 = clusters[j]
        new_cluster = clusters[i] + clusters[j]
        clusters.remove(del_1)
        clusters.remove(del_2)
        clusters.append(new_cluster)

    def get_next(self, clusters, alpha):
        """
        func:获得下一个合并的聚类
        """
        max_simi = alpha
        index = None
        n = len(clusters)
        for i in range(n):
            for j in range(i + 1, n):
                simi = self.compute_similarity(clusters[i], clusters[j])
                if simi > max_simi:
                    index = [i, j]
                    max_simi = simi
        return index, max_simi

    def _init_similarity(self):
        """
        func:相似矩阵生成完成
        """
        n = len(self.wordmap)
        self.simi_np = np.zeros([n, n])
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    self.simi_np[i, j] = 1
                else:
                    try:
                        self.simi_np[i, j] = self.simi_np[j, i] = self.word_vectors.similarity(self.idmap[i],
                                                                                               self.idmap[j])
                    except:
                        self.simi_np[i, j] = self.simi_np[j, i] = -1

    def compute_similarity(self, cluster_1, cluster_2):
        """
        func:计算两个聚类的相似度
        """
        score = 0
        for i in cluster_1:
            for j in cluster_2:
                score += self.simi_np[self.wordmap[i], self.wordmap[j]]

        score = score / (len(cluster_1) * len(cluster_2))
        return score

    def get_clustersname(self, pcid, cid):
        """
        func:取频率最大的为类名
        """
        lexicon = load_similar_dictionary(pcid, cid)
        targets = set(lexicon.values())

        self.clustersName = []
        for i, cluster in enumerate(self._init_clusters):
            t = set(cluster) & targets
            if not t:
                t = cluster
            if len(t) > 1:
                freqs = [self.target_freq[word] for word in t]
                name = cluster[freqs.index(max(freqs))]
            else:
                name = list(t)[0]
            self.clustersName.append(name)

    def wirte_to_table(self, pcid, cid):
        clean_sql = "DELETE from unsolved_synonym where cid = '{}'".format(cid)
        sql = (
            "INSERT INTO unsolved_synonym (pcid,cid,src_word,des_word,frequency,sentences)"
            " VALUES('{}','{}','{}','{}','{}','{}')"
        )
        db_execute(self.server99_lexicon, clean_sql)

#         data_synonym_global = self.get_lexicon_synonym_global()
        sample_sen = SAMPLE_SEN

        for i, cluster in enumerate(self._init_clusters):
            name = self.clustersName[i]
            for word in cluster:
                correct_name = name
                # 利用全局近义词词库纠正单次聚类结果
#                 correct_name = data_synonym_global.get(word,name)

                sentence = ''
                if word in self.text:
                    undouble_list = generate_sample_sents(self.text[word], word)
                    sentence = ";".join(undouble_list[0:sample_sen])

                if not db_execute(
                        self.server99_lexicon,
                        sql.format(pcid, cid, word, correct_name, self.target_freq.get(word) or 0, sentence),
                ):
                    log.logger.info("插入聚类结果失败...")

    def write_file(self):
        r = open(self.desti_path, 'w', encoding='utf-8')
        for cluster in self._init_clusters:
            r.write(",".join(cluster) + "\n")

    def get_lexicon_synonym_global(self):
        """
        获取全局近义词词库内容
        :return:
        """
        rows = db_get(self.server99_lexicon, "select src_word, des_word from synonym_global")
        result = {}
        for src_word, des_word in rows:
            result[src_word] = des_word
        return result


if __name__ == '__main__':
    s = Simlarity()
    s.run(pcid="4", cid="121703", path="./{}_word.vector".format("121703"), alpha=0.85)
