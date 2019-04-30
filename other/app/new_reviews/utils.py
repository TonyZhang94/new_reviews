import datetime
import subprocess
import os

from django.conf import settings
import multiprocessing
from analysis.script.utils import *

from zhuican.log import Logger
from zhuican.enum import System
from zhuican.test import log

from new_reviews.script.Text_Analysis.main import task
from new_reviews.script.similarity.similarity_cluster import Simlarity


NOW_STR = lambda: str(datetime.datetime.now())


HANLP_PATH = os.path.join(settings.NLP_ROOT, 'hanlp', 'SentenceDependencyParser.jar')


def hanlp_parse(pcid, cid):
    abusolute_path = HANLP_PATH
    cmd = 'java -jar {} -p {} -c {}'.format(abusolute_path, pcid, cid)
    p = subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, close_fds=True)
    encoding = 'gbk' if settings.SYSTEM_TYPE == System.WINDOWS else 'utf-8'
    while p.poll() == None:
        line = p.stdout.readline().decode(encoding).strip('\n').strip('\r').strip()
        if line:
            log.logger.info(line)
    lines = p.stdout.readlines()
    for line in lines:
        line = line.decode(encoding).strip('\n').strip('\r').strip()
        if line:
            log.logger.info(line)
    if p.poll():
        raise Exception('{} error'.format(cmd))
    return NOW_STR()


def cut_words(pcid, cid):
    from new_reviews.process.cut_words import cut_words as cut_func
    cut_func(pcid, cid)
    return NOW_STR()


def features_extraction_from_parse(**kwargs):
    # step2
    pcid = kwargs.get('pcid', None)
    cid = kwargs.get('cid', None)

    params = {
        "pcid": pcid,
        "cid": cid,
        "is_add": True,
        "dst_table": "pcid" + pcid + ".review_analysis_" + cid,
        "src_table": "pcid" + pcid + ".raw_review_analysis_" + cid,
        "is_add_both": True,
        "is_cluster": kwargs.get('is_cluster', None),
        "settings": {
            "cluster_alpha": kwargs.get('cluster_alpha', 0.85),
            "feature_limit": kwargs.get('feature_limit', 10)
        }
    }
    task(**params)

    return NOW_STR()


def reviews_extraction_from_parse(**kwargs):
    # step4
    pcid = kwargs.get('pcid', None)
    cid = kwargs.get('cid', None)
    dst_table = "pcid" + pcid + ".review_analysis_" + cid
    src_table = "pcid" + pcid + ".raw_review_analysis_" + cid

    task(pcid=pcid, cid=cid, is_add=False, dst_table=dst_table, src_table=src_table, is_add_both=False,
         is_cluster=False)

    return NOW_STR()


def reviews_targets_clusters(**kwargs):
    pcid = kwargs.get('pcid', None)
    cid = kwargs.get('cid', None)

    cluster_alpha = kwargs.get("cluster_alpha", 0.85)
    Word2Vec_model_path = "/home/nlp/word2vec/base.vector"
    s = Simlarity()
    s.run(pcid=pcid, cid=cid, path=Word2Vec_model_path, alpha=cluster_alpha)

    return NOW_STR()


def model_reviews_features_extraction_from_parse(pcid, cid):
    params = {
        "pcid": pcid,
        "cid": cid,
        "is_add": True,
        "dst_table": f'pcid{pcid}.review_analysis_{cid}_model_reviews',
        "src_table": f'pcid{pcid}.raw_review_analysis_{cid}',
        "is_add_both": True,
        "is_cluster": False,
        "settings": {
            "cluster_alpha": 0.85,
            "feature_limit": 10,
        }
    }
    from reviews.script_new.Text_Analysis.main import task as task_new
    task_new(**params)

    return NOW_STR()
