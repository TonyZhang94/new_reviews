from django.db import transaction

from celery.exceptions import Terminated

from main.utils import send_message

from analysis.celery import app
from analysis.script.config import NOW
from analysis.models import UserLog, User

from new_reviews.models import Task_state
from new_reviews.utils import *
from new_reviews.script.db_operation import get_predict_time


@app.task
def sentence_parse(**kwargs):
    user_id = kwargs.get('user_id')
    pcid = kwargs.get('pcid')
    cid = kwargs.get('cid')

    user = User.objects.get(id=user_id)
    name = user.name
    db = "raw_tb_comment_notag"
    s_table = "raw_comment_pcid{}.raw_tb_comment{}".format(pcid, cid)
    spend_minutes, table_size = get_predict_time(
        db, s_table, 800, increment=True, des_db='tb_comment_hanlp',
        des_table='pcid{}.raw_review_analysis_{}'.format(pcid, cid), column='comment_id',
    )
    # spend_minutes, table_size = "unknown", "unknown"
    data = "{}开始对PCID:{} CID:{}  品类进行 [第一步:分词] 共{}条待处理评价".format(
        name, pcid, cid, table_size)
    send_message(data)
    UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)
    item = Task_state.objects.get(pcid=pcid, cid=cid)
    item.step_1_status = 'doing'
    item.step_1_time = datetime.datetime.now() + datetime.timedelta(minutes=spend_minutes)
    item.save()

    status = False
    try:
        # hanlp_parse(pcid, cid)
        cut_words(pcid, cid)
        status = True
    finally:
        text = "{} 对PCID:{} CID:{} 品类 第一步:分词 ".format(name, pcid, cid)
        if status:
            item.step_1_status = 'done'
            item.step_2_status = 'go'
            item.step_1_time = NOW()
            data = "{}成功".format(text)
        else:
            data = "{}失败".format(text)
        item.status = 1
        item.save(update_fields=['step_1_status', 'step_2_status', 'step_1_time', 'status'])
        send_message(data)
        print("new_reviews 执行完了")


@app.task
def features_extraction(**kwargs):
    name = kwargs.get('name', None)
    pcid = kwargs.get('pcid', None)
    cid = kwargs.get('cid', None)

    item = Task_state.objects.get(pcid=pcid, cid=cid)

    status = False
    try:
        features_extraction_from_parse(**kwargs)
        status = True
    finally:
        text = "{}对PCID:{} CID:{}  品类 第二步:提取属性 ".format(name, pcid, cid)
        if status:
            item.step_2_status = 'done'
            item.step_3_status = 'go'
            item.step_2_time = NOW()
            data = "{}完成".format(text)
        else:
            data = "{}失败".format(text)
        item.status = 1
        item.save(update_fields=['step_2_status', 'step_3_status', 'step_2_time', 'status'])
        send_message(data)


@app.task
def reviews_extraction(**kwargs):
    name = kwargs.get('name', None)
    pcid = kwargs.get('pcid', None)
    cid = kwargs.get('cid', None)

    item = Task_state.objects.get(pcid=pcid, cid=cid)

    status = False
    try:
        reviews_extraction_from_parse(**kwargs)
        status = True
    finally:
        text = "{}对PCID:{} CID:{}  品类 第四步：终处理 ".format(name, pcid, cid)
        if status:
            item.step_4_status = 'done'
            item.step_4_time = NOW()
            item.lastfinishedtime = NOW()
            data = "{}完成".format(text)
        else:
            data = "{}失败".format(text)
        item.status = 1
        item.save(update_fields=['step_4_status', 'step_4_time', 'lastfinishedtime', 'status'])
        send_message(data)


@app.task
def cluster_target(**kwargs):
    name = kwargs.get('name', None)
    pcid = kwargs.get('pcid', None)
    cid = kwargs.get('cid', None)

    item = Task_state.objects.get(pcid=pcid, cid=cid)

    status = False
    try:
        reviews_targets_clusters(**kwargs)
        status = True
    finally:
        text = "{}对PCID:{} CID:{}  品类  文本近义词聚类 ".format(name, pcid, cid)
        if status:
            item.step_2_clutser_status = 1
            data = "{}完成".format(text)
        else:
            data = "{}失败".format(text)
        item.status = 1
        item.save(update_fields=['step_2_clutser_status', 'status'])
        send_message(data)


@app.task
def model_reviews_features_extraction_task(pcid, cid, name, text):
    status = False
    try:
        model_reviews_features_extraction_from_parse(pcid, cid)
        status = True
    finally:
        if status:
            data = "{} 成功".format(text)
        else:
            data = "{} 失败".format(text)
        send_message(data)
