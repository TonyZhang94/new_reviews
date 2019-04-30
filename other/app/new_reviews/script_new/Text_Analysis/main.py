# -*-coding:utf-8-*-

import sys

sys.path.append(r"D:\workspace\django\zhuican_web")

from zhuican.test import log
import queue
import threading

from analysis.script.utils import *

from reviews.script_new.db_operation import db_99_server, db_99_get
from reviews.script_new.Text_Analysis.extract_opinion import OpinionExtraction, fetch_itemcomment
from reviews.script_new.classifier_product.keyword_classification import predict
from reviews.script_new.similarity.similarity_cluster import Simlarity, generate_sample_sents, SAMPLE_SEN
from reviews.script_new.identify_words.filter_noise import FilterNoisy


def ExtractTargetsAndOpinions(kwargs):
    q = queue.Queue(100)
    producer = threading.Thread(target=fetch_itemcomment, name='getSqlFromDB', args=(kwargs["src_table"], q))
    comsumer = OpinionExtraction(kwargs, q)
    producer.start()
    comsumer.start()
    producer.join()
    comsumer.join()
    return comsumer.get_result()


def task(**kwargs):
    pcid = kwargs["pcid"]
    cid = kwargs["cid"]
    is_add = kwargs["is_add"]  # 标注是否为人工标注阶段
    src_table = kwargs["src_table"]
    dst_table = kwargs["dst_table"]
    is_add_both = kwargs["is_add_both"]  # 是否将情感词unsolved_opinions
    is_cluster = kwargs["is_cluster"]  # 是否对targets进行语义聚类

    # 从句法库中抽取Targets,Opinions,以及其他的信息
    result = ExtractTargetsAndOpinions(kwargs)

    is_add = False
    if is_add:
        # 新增关键词
        settings = kwargs.get('settings', {"feature_limit": 10, "cluster_alpha": 0.6})
        # 保存机器学习打标数据到本地
        ml_text = result["ml_text"]
        # CNN网络预测标签
        # predict_result = predict(ml_text)
        # 基于关键词分类
        predict_result = predict(result["feature_frequency"])
        # 基于贝叶斯分类器噪音分类
        noisyFilter = FilterNoisy(pcid, cid, model_filter=True)
        IsNoise = {key: noisyFilter.isNoisyWord(key) for key in ml_text.keys()}

        # 过滤噪声词并且重新组织机器学习语料
        #         noisyFilter = FilterNoisy(pcid, cid, model_filter=True)
        #         new_ml_text = {}
        #         IsNoise = {}
        #         for x in ml_text.keys():
        #             key, opinion = x.split('_')
        #             if key not in IsNoise:
        #                 new_ml_text[key] = list(map(lambda t: t[2], ml_text[x]))
        #                 IsNoise[key] = noisyFilter.isNoisyWord(key)
        #             else:
        #                 new_ml_text[key].extend(list(map(lambda t: t[2], ml_text[x])))
        #         del ml_text
        #         ml_text = new_ml_text

        # get global frequency of targets and opinions
        target_frequency, opinion_frequency = compute_frequency(result["feature_frequency"])

        write_back_original_targets(
            pcid, cid, result["features"], ml_text, IsNoise, predict_result, target_frequency,
            settings["feature_limit"],
        )

        # 将新增词汇写入数据库
        new_opinions = get_new_words(result["opinions"], result["O_Seed"])
        new_features = result["features"] - set(result["T_Seed"].keys())

        write_back_new_targets(pcid, cid, new_features, ml_text, IsNoise, predict_result, target_frequency,
                               settings["feature_limit"])

        if is_add_both:
            write_back_new_opinions(new_opinions, opinion_frequency, 5)

        if is_cluster:
            # 新生成的目标词聚类
            Word2Vec_model_path = "/home/nlp/word2vec/bert.vector"
            s = Simlarity(ml_text)
            s.run(pcid=pcid, cid=cid, path=Word2Vec_model_path, alpha=settings["cluster_alpha"])
    else:
        # 观点词词语映射
        O_Map = result["O_Map"]
        # 已有的词语标注
        T_Seed = result["T_Seed"]
        # 全局观点词正负
        O_Seed = result["O_Seed"]
        # 直接写入结果表
        data = generate_data(pcid, cid, result["NewDBData"], T_Seed, O_Seed, O_Map)
        write_back_review_analysis(data, dst_table)


def generate_data(pcid, cid, NewDBData, T_Seed, O_Seed, O_Map):
    """
    params:
    NewDBData: dict({"itemid":[(comment_id,comment_date,opinions,target)]})
    """
    table_list = []
    for itemid in NewDBData:
        for row in NewDBData[itemid]:
            id = row[0]
            date = row[1]
            o = row[2]
            w = row[3]
            if o in O_Seed:
                opinion_pos = O_Seed[o]
                # 情感词库在提取属性的时候不应用
                # map_item = O_Map.get(w, O_Map["*"]).get(o, None)
                # if map_item:
                #     if map_item[0]:
                #         o = map_item[0]
                #     if map_item[1]:
                #         opinion_pos = map_item[1]
                table_list.append((pcid, cid, itemid, w, '', o, 1, opinion_pos, date, id))
    return table_list


def compute_frequency(feature_frequency):
    feature_result = {}
    opinion_result = {}
    for itemid in feature_frequency:
        for feature in feature_frequency[itemid]:
            if feature not in feature_result:
                feature_result[feature] = 0
            for opinion in feature_frequency[itemid][feature]:
                if opinion not in opinion_result:
                    opinion_result[opinion] = 0
                num = feature_frequency[itemid][feature][opinion]
                opinion_result[opinion] += num
                feature_result[feature] += num
    return feature_result, opinion_result


def get_new_words(_new, _old):
    new_words = set(map(lambda x, y: (x, y), _new.keys(), _new.values()))
    orgin_words = set(map(lambda x, y: (x, y), _old.keys(), _old.values()))
    return new_words - orgin_words


def save_target(ml_text, path=None):
    filename = path or "classifier_data.txt"
    if filename:
        tmp_file = open(filename, mode='w')
        for w, text in ml_text.items():
            for sen in text:
                tmp_file.write(sen.encode('utf-8') + ";" + w.encode('utf-8') + "\n")
        tmp_file.close()


def get_lexicon_targets_global():
    """
    获取全局属性标签内容
    :return:
    """
    rows = db_99_get("lexicon", "select target, tag from targets_global")
    result = {}
    for target, tag in rows:
        result[target] = tag
    return result


def write_back_new_targets(pcid, cid, new_features, ml_text, IsNoise, predict_result, target_frequency, limit_num=2):
    server = db_99_server("lexicon")
    dst_table = "unsolved_targets"
    sql = "INSERT INTO " + dst_table + " (pcid,cid,target,top1class,top1prob,top2class,top2prob,sentences,frequency) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    sample_sen = SAMPLE_SEN  # 每个目标次保留句子数
    # clean old data in table
    clean_history_in_table(server, dst_table, cid)
    global_targets = get_lexicon_targets_global()

    # go on add
    data = []
    for feature in new_features:
        word = feature
        if word not in ml_text:
            continue
        #         undouble_list = generate_sample_sents(ml_text[word], word)
        undouble_list = list(set(ml_text[word]))
        sentence = ";".join(undouble_list[0:sample_sen])
        word_frequency = target_frequency.get(word, -1)
        if word_frequency > limit_num:
            if not IsNoise[word] and word in predict_result:
                pre_info = predict_result[word]

                top1class = global_targets.get(word)
                if not top1class:
                    top1class = pre_info[0]

                data.append((pcid, cid, word, top1class, predict_result[word][1], predict_result[word][2],
                             predict_result[word][3], sentence, word_frequency))
            else:
                data.append((pcid, cid, word, 'delete', 0, '', 0, sentence, word_frequency))

    dbconn = server.cursor()
    try:
        dbconn.executemany(sql, data)
        server.commit()
    except Exception as e:
        log.logger.exception(e)
        server.rollback()
    dbconn.close()


def write_back_original_targets(pcid, cid, features, ml_text, IsNoise, predict_result, target_frequency, limit_num=2):
    dst_table = "original_targets"
    sql = (
            "INSERT INTO {}(pcid,cid,target,top1class,top1prob,top2class,top2prob,sentences,frequency)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    ).format(dst_table)
    sample_sen = SAMPLE_SEN  # 每个目标次保留句子数

    engine = get_99_engine('lexicon')

    sql = (
        "select pcid, cid, target, top1class, top1prob, top2class, top2prob, sentences, frequency from {}"
        " where pcid = {} and cid = {}"
    ).format(dst_table, pcid, cid)
    df = read_data(sql, engine, dst_table)

    global_targets = get_lexicon_targets_global()

    # go on add
    data = []
    for feature in features:
        word = feature
        if word not in ml_text:
            continue
        #         undouble_list = generate_sample_sents(ml_text[word], word)
        undouble_list = list(set(ml_text[word]))
        sentence = ";".join(undouble_list[0:sample_sen])
        word_frequency = target_frequency.get(word, -1)
        if word_frequency > limit_num:
            if not IsNoise[word] and word in predict_result:
                pre_info = predict_result[word]
                top1class = global_targets.get(word)
                if not top1class:
                    top1class = pre_info[0]

                data.append((pcid, cid, word, top1class, predict_result[word][1], predict_result[word][2],
                             predict_result[word][3], sentence, word_frequency))
            else:
                data.append((pcid, cid, word, 'delete', 0, '', 0, sentence, word_frequency))

    new_df = pd.DataFrame(data, columns=[
        'pcid', 'cid', 'target', 'top1class', 'top1prob', 'top2class', 'top2prob', 'sentences', 'frequency',
    ])
    df = df[~df['target'].isin(new_df['target'])]
    df = pd.concat([df, new_df], ignore_index=True, sort=False)

    sql = "delete from {} where pcid = {} and cid = {}".format(dst_table, pcid, cid)
    db_psql(engine, sql)
    postgres_save_df(df, engine, dst_table)


def write_back_new_opinions(opinions, opinion_frequency, limit_num=2):
    server = db_99_server("lexicon")
    dst_table = "unsolved_opinions"
    sql = "INSERT INTO " + dst_table + " (opinion,sentiment) VALUES (%s,%s)"
    data = []
    for item in opinions:
        if opinion_frequency[item[0]] > limit_num:
            data.append(item)

    dbconn = server.cursor()
    try:
        dbconn.executemany(sql, data)
        server.commit()
    except Exception as e:
        log.logger.exception(e)
        server.rollback()
    dbconn.close()


def table_is_exist(server, dst_table):
    dbconn = server.cursor()
    schmema, tablename = dst_table.split('.')
    sql = "select schemaname,tablename from pg_tables where tablename = '" + tablename + "' and tablename not like 'sql_%' and schemaname = '" + schmema + "'"
    result = True
    try:
        dbconn.execute(sql)
        row = dbconn.fetchall()
        if len(row) == 0:
            result = False
        server.commit()
    except Exception as e:
        log.logger.exception(e)
        server.rollback()
    dbconn.close()
    return result


def create_dst_table(engine, dst_table):
    schmema, tablename = dst_table.split('.')
    sql = "CREATE TABLE " + dst_table + " ( id serial NOT NULL, pcid character(5),cid character varying(20), \
  itemid character varying(20),frequency integer,grade integer,target character varying,opinion character varying,\
  tag character varying,comment_date character varying,comment_id character varying,\
  title character varying,brand character varying,model character varying,price numeric,\
  CONSTRAINT " + tablename + "_pk_id PRIMARY KEY (id) )"
    db_psql(engine, sql)


def turncate_table(server, dst_table):
    sql = "TRUNCATE TABLE " + dst_table
    dbconn = server.cursor()
    try:
        dbconn.execute(sql)
        server.commit()
    except Exception as e:
        log.logger.exception(e)
        server.rollback()
    dbconn.close()


def clean_history_in_table(server, dst_table, cid):
    sql = "DELETE FROM " + dst_table + " WHERE cid = '{}' ".format(cid)
    dbconn = server.cursor()
    try:
        dbconn.execute(sql)
        server.commit()
    except Exception as e:
        log.logger.exception(e)
        server.rollback()
    dbconn.close()


def write_back_review_analysis(data, dst_table):
    engine = get_99_engine("tb_comment_nlp")

    df = pd.DataFrame(data, columns=[
        'pcid', 'cid', 'itemid', 'target', 'tag', 'opinion', 'frequency', 'grade', 'comment_date', 'comment_id'
    ])

    del_sql = "drop table if exists {}".format(dst_table)
    db_psql(engine, del_sql)
    create_table(df, dst_table, engine, get_columns_types(df))

    dst_table_bak = f'{dst_table}_bak'
    del_sql = "drop table if exists {}".format(dst_table_bak)
    db_psql(engine, del_sql)
    create_table(df, dst_table_bak, engine)

    postgres_save_df(df, engine, dst_table)
    postgres_save_df(df, engine, dst_table_bak)


def print_help():
    print(" -p 必填，输入pcid")
    print(" -c 必填，输入cid")
    print(" -add 与noadd二选一，将新词写入数据库，新词需要业务人员处理确认后，再次运行该程序，并选择noadd选项")
    print(" -noadd 与add二选一，忽略产生的新词，直接将分析结果写入数据库")
    print(" -dst_table 可不填，写入分析数据的表名,默认为例如  [pcid4.review_analysis_50003695]")
    print(" -src_table 可不填，读取分析数据的表名，默认为例如 [pcid4.raw_review_analysis_50003695]")
    print(" -add_both 可不填，将新增观点词也加入数据库")


def start():
    if len(sys.argv) < 2:
        print_help()
    pcid = None
    cid = None
    is_add_new_targets = True
    is_add_both = False
    dst_table = None
    src_table = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "-p":
            i = i + 1
            pcid = sys.argv[i]
        elif sys.argv[i] == '-c':
            i = i + 1
            cid = sys.argv[i]
        elif sys.argv[i] == '-add':
            is_add_new_targets = True
        elif sys.argv[i] == '-noadd':
            is_add_new_targets = False
        elif sys.argv[i] == "-dst_table":
            i = i + 1
            dst_table = sys.argv[i]
        elif sys.argv[i] == "-src_table":
            i = i + 1
            src_table = sys.argv[i]
        elif sys.argv[i] == "-add_both":
            is_add_both = True
        i += 1

    is_ready = False
    if pcid and cid:
        is_ready = True
        if dst_table == None:
            dst_table = "pcid" + pcid + ".review_analysis_" + cid
        if src_table == None:
            src_table = "pcid" + pcid + ".raw_review_analysis_" + cid

    else:
        print("请输入pcid和cid")
        print_help()

    if is_ready:
        task(pcid=pcid, cid=cid, is_add=is_add_new_targets, dst_table=dst_table, src_table=src_table,
             is_add_both=is_add_both)


if __name__ == "__main__":
    pcid = '4'
    cid = '50008366'
    dst_table = "pcid" + pcid + ".review_analysis_" + cid
    src_table = "pcid" + pcid + ".raw_review_analysis_" + cid
    task(pcid=pcid, cid=cid, is_add=True, dst_table=dst_table, src_table=src_table, is_add_both=False,
         is_cluster=False)
