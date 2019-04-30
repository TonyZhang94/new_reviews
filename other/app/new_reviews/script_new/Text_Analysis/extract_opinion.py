# -*-coding:utf-8-*-

import threading
import psycopg2
import psycopg2.extras
import json
import traceback
import random
from zhuican.test import log, logger

from analysis.script.utils import *

from .opinions_target_extract.o_t_propagation_extraction import Opinion_Target_Propagation
from reviews.script_new.db_operation import db_99_server, db_99_get, get_table_size_v2
from reviews.script_new.identify_words.filter_noise import FilterNoisy
from collections import Counter
import gc


def update_ml_text(ml_text, update_text, ml_text_max_size):
    for word in update_text:
        if word not in ml_text:
            ml_text[word] = update_text[word]
        else:
            ml_text[word].extend(update_text[word])
            if len(ml_text[word]) >= 2 * ml_text_max_size:
                ml_text[word] = random.sample(ml_text[word], ml_text_max_size)


def load_similar_dictionary(pcid, cid):
    # server99_lexicon = db_99_server("lexicon")
    # server99_comments = db_99_server("tb_comment_hanlp")
    #
    # # 全局近义词
    # sql = "SELECT src_word,des_word from synonym_global "
    # dictionary = {row[0]: row[1] for row in db_execute(server99_lexicon, sql)}
    #
    # # 品类近义词
    # sql = "SELECT src_word,des_word from synonym where cid = '{}'".format(cid)
    # dictionary2 = {row[0]: row[1] for row in db_execute(server99_lexicon, sql)}
    #
    # dictionary.update(dictionary2)

    dictionary = dict()

    return dictionary


def db_execute(server, sql):
        dbconn = server.cursor()
        result = []
        try:
            dbconn.execute(sql)
            result = dbconn.fetchall()
            server.commit()
        except Exception as e:
            log.logger.exception(e)
            server.rollback()
        dbconn.close()
        return result


def fetch_itemcomment(src_table, q):
    # 从句法库中获得句法
    sql = "SELECT itemid,parsejson,comment_id,comment_date from {} order by itemid".format(src_table)
    server = db_99_server("tb_comment_hanlp")
    res = []
    dbconn = server.cursor('fetchmanyCursor', cursor_factory=psycopg2.extras.DictCursor)
    dbconn.itersize = 100000
    ItemId = ""
    start = NOW()
    i = 0
    try:
        dbconn.execute(sql)
        for row in dbconn:
            i += 1
            if i % 100000 == 0:
                end = NOW()
                log.logger.info('fetch data: {}s'.format((end - start).total_seconds()))
                start = NOW()

            if ItemId == "":
                ItemId = row[0]
            if row[0] == ItemId:
                res.append(row)
            else:
                q.put(res)
                res = []
                ItemId = row[0]
                res.append(row)
    except Exception as e:
        log.logger.exception(e)
    finally:
        dbconn.close()
    if res:
        q.put(res)
    q.put(None)
    log.logger.info("quit producer [fetch_itemcomment]")


# Producer thread
class OpinionExtraction(threading.Thread):
    def __init__(self, args, q):
        super(OpinionExtraction, self).__init__()
        self.pcid = args["pcid"]
        self.cid = args["cid"]
        self.is_add = args["is_add"]  # True 为第二步抽取属性，False为第四步 终处理
        self.src_table = args["src_table"]
        self.dst_table = args["dst_table"]
        self.q = q  # 任务队列
        self.load_config()  # 初始化数据库连接

    def run(self):
        log.logger.info('从数据库提取种子词库...')
        # 载入反义词
        Adversatives = self.load_Adversatives_dictionary()
        # 载入情感词库-包括全局和品类
        O_Seed, O_Map = self.load_opinion_dictionary()
        # 载入情感词库-包括全局和品类
        T_Seed = self.load_feature_dictionary()
        # 载入近义词词库-包括全局和品类
        Replace_Seed = load_similar_dictionary(self.pcid, self.cid)
        # 通过 FilterNoisy 类过滤，其中包括关键字过滤以及词匹配过滤
        noisyFilter = FilterNoisy(self.pcid, self.cid, model_filter=False)
        # NoSense_Seed = self.load_nosense_dictionary()

        log.logger.info('从数据库提取评价数据并生成树状结构...')

        # 返回所有挖掘到的目标词和观点词
        features = set()
        opinions = {}
        feature_frequency = {}
        # 关于挖掘到的词具体信息，itemid为Key, (comment_id,comment_date,opinions,target) 为Value
        NewDBData = {}
        # 分类所需数据
        ml_text = {}
        ml_text_max_size = 10

        # 统计处理评价总数
        num = 0
        num_current = 0
        start = NOW()

        while True:
            rows = self.q.get()
            if not rows:
                break

            num += len(rows)
            num_current += len(rows)

            itemid = rows[0][0]
            itemid_review_data = []
            for row in rows:
                itemid_review_data.append((row[1], row[2], row[3]))
            del rows

            process = Opinion_Target_Propagation(O_Seed=O_Seed.copy(), T_Seed=T_Seed.copy(),
                                                 Reviews_Data=itemid_review_data, Replace_Seed=Replace_Seed,
                                                 NoSense_Seed={}, Adversatives=Adversatives)
            # 结构化评价文本
            process.init_parse_reviews()
            # 提取
            process.propagation()
            # 提取之后去除无义词
            # process.remove_nosense_words_before_count()
            # 提取词组
            process.identify_target_phrases(limited_num=0, is_add=True)
            # 计算词频
            process.compute_word_frequency()
            # 移除 targets 低频词语
            process.remove_little_frequency_targets(length_limit=2, frequency_limit_num=0)

            # 再次移除无意义词，防止词组混进来
            # process.remove_nosense_words()
            # 通过模型过滤
            process.remove_nosense_words_by_model(noisyFilter)

            # 可选过程，新型数据，包含comment_id和comment_date
            process.generate_word_frequency_by_sentence()
            # 属性同义词替换
            process.combine_similar_words()

            NewDBData[itemid] = [
                row + [i] for i, rows in process.NewDBData.items() for row in rows if not noisyFilter.isNoisyWord(i)]

            feature_frequency[itemid] = process.feature_frequency.copy()

            # 更新
            features = features | set(feature_frequency[itemid].keys())
            opinions.update(process.Opinions)

            tmp = process.get_trainData_from_corpus(ml_text_max_size)
            update_ml_text(ml_text, tmp, ml_text_max_size)

            if num_current >= 100000:
                end = NOW()
                log.logger.info('handle data {} cost {}s'.format(num, (end - start).total_seconds()))
                start = NOW()
                num_current = 0

        end = NOW()
        log.logger.info('handle {} itemid cost {}s'.format(num, (end - start).total_seconds()))

        # 移除 opinions 低频词语
        opinions = self.remove_little_frequency_opinions(feature_frequency, opinions, 5)

        log.logger.info("quit comsumer [OpinionExtraction]")
        log.logger.info("unsolved data in queue:{}".format(self.q.qsize()))

        self.result = {"feature_frequency": feature_frequency,
                       "features": features,
                       "opinions": opinions,
                       "O_Seed": O_Seed,
                       "O_Map": O_Map,
                       "T_Seed": T_Seed,
                       "ml_text": ml_text,
                       "NewDBData": NewDBData}

    def get_result(self):
        return self.result

    def remove_little_frequency_opinions(self, feature_frequency, opinions, limit_num=2):
        all_opinions = Counter()
        for itemid in feature_frequency:
            for feature in feature_frequency[itemid]:
                opinion_list = feature_frequency[itemid][feature]
                all_opinions.update(Counter(opinion_list))

        selected_opinions = list(filter(lambda x: x[1] > limit_num, all_opinions.most_common()))
        new_opinions = {}
        for item in selected_opinions:
            new_opinions[item[0]] = opinions[item[0]]
        return new_opinions

    def load_reviews_data(self):
        log.logger.info('start get itemids')
        sql = "SELECT itemid from {} group by itemid order by itemid".format(self.src_table)
        itemids = db_execute(self.server99_comments, sql)
        log.logger.info('get itemids success')
        start = 0
        length = 10000
        itemid_review_data = {}
        while start < len(itemids):
            start_itemid = itemids[start][0]
            end_itemid = itemids[start + length - 1][0]
            sql = "SELECT itemid,parsejson,comment_id,comment_date from {}" \
                  " where itemid >= '{}' and itemid <= '{}'".format(self.src_table, start_itemid, end_itemid)
            result = db_execute(self.server99_comments, sql)
            for row in result:
                itemid_review_data.setdefault(row[0], [])
                itemid_review_data[row[0]].append((row[1], row[2], row[3]))
            start += length
            log.logger.info('get data itemid from {} to {} success'.format(start_itemid, end_itemid))
        log.logger.info('get all data success')
        return itemid_review_data

    def load_config(self):
        self.server99_lexicon = db_99_server("lexicon")
        self.server99_comments = db_99_server("tb_comment_hanlp")

    def load_opinion_dictionary(self):
        # 全局情感词库
        sql = "SELECT word,grade from opinions"
        O_Seed = {row[0]: row[1] for row in db_execute(self.server99_lexicon, sql)}
        # O_Seed = dict()
        O_Map = {"*": {}}

        # # 全局情感词库合并
        # sql = "SELECT opinion,grade,merge from sentiment_global;"
        # for src, grade, dec in db_execute(self.server99_lexicon, sql):
        #     O_Seed[src] = grade
        #     O_Seed[dec] = grade
        #     O_Map["*"][src] = (dec, grade)
        #
        # # 品类情感词库替换
        # sql = "SELECT target,opinion,grade,merge from sentiment.pcid{} where cid='{}';".format(self.pcid, self.cid)
        # for target, src, grade, dec in db_execute(self.server99_lexicon, sql):
        #     tmp = O_Map.setdefault(target, {})
        #     tmp[src] = (dec, grade)

        return O_Seed, O_Map

    def load_feature_dictionary(self):
        # # 全局属性词
        # sql = "SELECT target,tag from targets_global where tag != 'delete';"
        # T_Seed = {row[0]: row[1] for row in db_execute(self.server99_lexicon, sql)}
        #
        # # 品类属性词
        # sql = "SELECT target,tag from targets where cid = '{}';".format(self.cid)
        # T_Seed2 = {row[0]: row[1] for row in db_execute(self.server99_lexicon, sql)}
        #
        # T_Seed.update(T_Seed2)

        T_Seed = dict()

        return T_Seed

    def load_nosense_dictionary(self):
        T_Seed = {}
        sql = "SELECT word from nomeaning where cid = '%s'"
        result = db_execute(self.server99_lexicon, sql % (self.cid))
        for row in result:
            T_Seed[row[0]] = 0
        return T_Seed

    def load_Adversatives_dictionary(self):
        Adversative = {}
        sql = "SELECT word from adversative"
        result = db_execute(self.server99_lexicon, sql)
        for row in result:
            Adversative[row[0]] = 0
        return Adversative
