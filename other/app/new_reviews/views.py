import traceback
import json
import math
from itertools import chain

from django.http import HttpResponse, Http404, HttpResponseBadRequest, FileResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET

import chardet

from main.utils import process_request, gen_response, send_message

from analysis.utils.views import get_page_list
from analysis.models import User, UserLog
from analysis.task_def.ax import cal_model_reviews_comment_task
from analysis.utils.ax import *

from new_reviews.config import PAGE_LENGTH
from new_reviews.script.db_operation import *
# 和“文本分类使用相同的处理状态”
# from reviews.models import Task_state
# 和“文本分类使用不同的处理状态”
from new_reviews.models import Task_state
from new_reviews.tasks import sentence_parse, features_extraction, reviews_extraction, cluster_target
from new_reviews.process.public import IF_DELAY


# Create your views here.
@process_request
def reviews(request):
    # 返回月更新
    if request.GET:
        pcid = request.GET.get('pcid', None)
        cid = request.GET.get('cid', None)
        context = {
            "status": "1",
            "search_condition": {
                "pcid": pcid,
                "cid": cid
            },
            "result": []
        }
        if pcid and cid:
            cid = cid.strip()
            pcid = pcid.strip()
            res = Task_state.objects.filter(cid=cid, pcid=pcid)
        elif cid:
            cid = cid.strip()
            res = Task_state.objects.filter(cid=cid)
        elif pcid:
            pcid = pcid.strip()
            res = Task_state.objects.filter(pcid=pcid)
        if res.exists():
            for item in res:
                info = {
                    'pcid': item.pcid,
                    'cid': item.cid,
                    'lastfinishedtime': item.lastfinishedtime or '未完成',
                    'step_1_status': item.step_1_status,
                    'step_1_time': item.step_1_time or '未完成',
                    'step_2_status': item.step_2_status,
                    'step_2_time': item.step_2_time or '未完成',
                    'step_2_cluster_status': item.step_2_clutser_status,
                    'step_2_cluster_alpha': item.step_2_cluster_alpha,
                    'step_2_feature_limit': item.step_2_feature_limit,
                    'step_3_status': item.step_3_status,
                    'step_3_time': item.step_3_time or '未完成',
                    'step_4_status': item.step_4_status,
                    'step_4_time': item.step_4_time or '未完成'
                }
                context['result'].append(info)
    else:
        context = {"status": "0"}
    return render(request, 'new_reviews/search.html', context)


@require_GET
@process_request
def tagscheck(request):
    data = request.GET
    pcid = data.get('pcid')
    cid = data.get('cid')
    pgNumber = int(data.get('pgnumber', 500))
    pgIndex = int(data.get('pgindex', 1))
    sort = data.get('sort', 'freq')
    desc = data.get('desc') == 'true'

    product_irrelated_tag = ("使用场景", "适用人群", "价格", "服务", "物流")
    context = {
        "status": "1",
        "pg_nav": {"curindex": 0, "indexlist": []},
        "result": {"pcid": pcid, "cid": cid, "ir": [], "irre": []}
    }
    all_number = get_unsolved_targets_size(cid)
    all_index = math.ceil(all_number / pgNumber)
    offset = (pgIndex - 1) * pgNumber
    curindex = pgIndex
    context["pg_nav"]["curindex"] = curindex
    context["pg_nav"]["indexlist"] = list(range(1, all_index + 1))

    table = 'unsolved_targets'
    sql = (
        "select target, top1class, top2class, sentences, id, frequency"
        " from {} where cid = '{}'"
    ).format(table, cid)
    if sort == 'freq':
        sql = "{} order by frequency".format(sql)
    else:
        sql = "{} order by convert_to(target, 'GBK')".format(sql)
    if desc:
        sql = "{} desc".format(sql)
    sql = "{} limit {} offset {}".format(sql, str(pgNumber), str(offset))
    df = read_data(sql, get_99_engine('lexicon'), table)
    df['sentences'].fillna('', inplace=True)

    Ir_No_id = 1
    Irre_No_id = 1
    for i, v in df.iterrows():
        info = {
            "target": v['target'], "top1class": v['top1class'], "top2class": v['top2class'],
            "sentences": v['sentences'].split(';'), "id": v['id'], 'frequency': v['frequency'],
        }
        if info["top1class"] in product_irrelated_tag:
            info["No"] = Irre_No_id
            Irre_No_id += 1
            context["result"]["irre"].append(info)
        else:
            info["No"] = Ir_No_id
            Ir_No_id += 1
            context["result"]["ir"].append(info)
    context['sort'] = sort
    desc = desc and 'true' or 'false'
    context['desc'] = desc
    return render(request, 'reviews/tagscheck_version2.html', context)


@process_request
def opinionscheck(request):
    context = {"status": "1", "result": []}
    rows = db_99_get("lexicon", "select opinion,sentiment,id from unsolved_opinions")
    No_id = 1
    hash_opinion = {}
    for row in rows:
        if row[0] not in hash_opinion:
            context["result"].append({"No": No_id, "opinion": row[0], "sentiment": str(row[1]), "id": row[2]})
            No_id += 1
            hash_opinion[row[0]] = 0
    return render(request, 'reviews/opinionscheck.html', context)


@csrf_exempt
def update_targets(request):
    status = {'status': '0', 'msg': 'error'}
    req = json.loads(request.body)
    pcid = req.get('pcid', None)
    cid = req.get('cid', None)
    user_id = req.get('user_id', None)
    context = req.get('context', None)
    global_targets = req.get('global_targets') or {}

    if pcid and cid:
        server = db_99_server("lexicon")
        for item in context:
            update_targets_table(server, pcid, cid, item)

        insert_targets_global = "insert into targets_global(target, tag) values ('%s', '%s')"
        update_targets_global = "update targets_global set tag = '{}' where target = '{}'"

        for target, tag in global_targets.items():
            if not db_execute(server, insert_targets_global % (target, tag)):
                db_execute(server, update_targets_global.format(tag, target))

        status['status'] = '1'
        status['msg'] = 'success'
        all_number = get_unsolved_targets_size(cid)
        if all_number == 0:
            user = User.objects.get(id=user_id)
            data = "{} 对PCID:{} CID:{}  品类 [第三步：业务人员属性标注] 全部完成".format(user.name, pcid, cid)
            send_message(data)
            UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)

            item = Task_state.objects.get(pcid=pcid, cid=cid)
            item.step_3_status = 'done'
            item.step_4_status = 'go'
            item.step_3_time = NOW()
            item.save()
        else:
            status['status'] = '2'
            user = User.objects.get(id=user_id)
            data = "{} 对PCID:{} CID:{}  品类进行 [第三步：业务人员属性标注] 完成 {} 条".format(user.name, pcid, cid, len(context))
            send_message(data)
            UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)
    return gen_response(status, True)


@csrf_exempt
def update_opinions(request):
    status = {'status': '0', 'msg': 'error'}
    req = json.loads(request.body)
    user_id = req.get('user_id', None)
    context = req.get('context', None)
    if user_id:
        server = db_99_server("lexicon")
        for item in context:
            update_opinions_table(server, item)
        db_execute(server, "TRUNCATE TABLE unsolved_opinions")
        status['status'] = '1'
        status['msg'] = 'success'

        user = User.objects.get(id=user_id)
        data = "{} 进行 [业务人员 观点标注] 完成".format(user.name)
        send_message(data)
    return gen_response(status, True)


@csrf_exempt
def create_new_state(request):
    status = {'status': '0', 'msg': 'error'}
    pcid = request.POST.get('pcid', None)
    cid = request.POST.get('cid', None)
    if pcid and cid:
        test1 = Task_state.objects.create(
            pcid=pcid, cid=cid, step_1_status='go', step_2_status='no', step_3_status='no', step_4_status='no', )
        # test1.save()
        status['status'] = '1'
        status['msg'] = 'success'
    return gen_response(status, True)


@csrf_exempt
def sentence_parse_step(request):
    status = {'status': '0', 'msg': 'error'}
    pcid = request.POST.get('pcid', None)
    cid = request.POST.get('cid', None)
    is_jump = request.POST.get('isjump', False)
    user_id = request.POST.get('user_id', None)
    if pcid and cid and user_id:
        user = User.objects.get(id=user_id)
        if is_jump == '1':
            print("STEP1 Jump")
            data = "{}跳过 PCID:{} CID:{}  品类 [第一步:分词]".format(user.name, pcid, cid)
            send_message(data)
            UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)
            item = Task_state.objects.get(pcid=pcid, cid=cid)
            item.step_1_status = 'done'
            item.step_2_status = 'go'
            item.step_1_time = NOW()
            item.save()
        else:
            if IF_DELAY:
                print("STEP1 Delay")
                sentence_parse.delay(pcid=pcid, cid=cid, user_id=user.id, name=user.name)
            else:
                print("STEP1 Execute")
                sentence_parse(pcid=pcid, cid=cid, user_id=user.id, name=user.name)
        status['status'] = '1'
        status['msg'] = 'success'
    return gen_response(status, True)


@csrf_exempt
def features_extraction_step(request):
    status = {'status': '0', 'msg': 'error'}
    try:
        pcid = request.POST.get('pcid', None)
        cid = request.POST.get('cid', None)
        is_jump = request.POST.get('isjump', False)
        is_cluster = request.POST.get('iscluster', False)
        cluster_alpha = float(request.POST.get('cluster_alpha', 0.85))
        feature_limit = int(request.POST.get('feature_limit', 10))
        if is_cluster == '0':
            is_cluster = False
        else:
            is_cluster = True
        user_id = request.POST.get('user_id', None)
        if pcid and cid and user_id:
            user = User.objects.get(id=user_id)
            if is_jump == '1':
                print("STEP2 Jump")
                data = "{}跳过 PCID:{} CID:{}  品类 [第二步:提取属性]".format(user.name, pcid, cid)
                send_message(data)
                UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)

                item = Task_state.objects.get(pcid=pcid, cid=cid)
                item.step_2_status = 'done'
                item.step_3_status = 'go'
                item.step_2_time = NOW()
                item.save()
            else:
                db = "tb_comment_hanlp"
                s_table = "pcid" + pcid + ".raw_review_analysis_" + cid
                # spend_minutes, table_size = get_predict_time(
                #     db, s_table, 200000, is_using_multiprocess=False
                # )
                spend_minutes, table_size = 0, 0

                item = Task_state.objects.get(pcid=pcid, cid=cid)
                item.step_2_status = 'doing'
                item.step_2_time = NOW() + datetime.timedelta(minutes=spend_minutes)
                if is_cluster:
                    item.step_2_clutser_status = 1
                else:
                    item.step_2_clutser_status = 0
                item.step_2_cluster_alpha = cluster_alpha
                item.step_2_feature_limit = feature_limit
                item.save()

                if IF_DELAY:
                    print("STEP2 Delay")
                    features_extraction.delay(pcid=pcid, cid=cid, name=user.name, is_cluster=is_cluster,
                                              cluster_alpha=cluster_alpha, feature_limit=feature_limit)
                else:
                    print("STEP2 Execute")
                    features_extraction(pcid=pcid, cid=cid, name=user.name, is_cluster=is_cluster,
                                        cluster_alpha=cluster_alpha, feature_limit=feature_limit)
                data = "{}开始对PCID:{} CID:{}  品类进行 [第二步:提取属性] 共{}条待处理评价".format(user.name, pcid, cid, table_size)
                send_message(data)
                UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)
            status['status'] = '1'
            status['msg'] = 'success'

    except Exception as e:
        traceback.print_exc()
    return gen_response(status, True)


@csrf_exempt
def reviews_extraction_step(request):
    status = {'status': '0', 'msg': 'error'}
    try:
        pcid = request.POST.get('pcid', None)
        cid = request.POST.get('cid', None)
        is_jump = request.POST.get('isjump', False)
        user_id = request.POST.get('user_id', None)
        if pcid and cid and user_id:
            user = User.objects.get(id=user_id)
            if is_jump == '1':
                print("STEP4 Jump")
                data = "{}跳过 PCID:{} CID:{}  品类 [第四步：终处理]".format(user.name, pcid, cid)
                send_message(data)
                UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)

                item = Task_state.objects.get(pcid=pcid, cid=cid)
                item.step_4_status = 'done'
                item.step_4_time = NOW()
                item.save()
            else:
                db = "tb_comment_hanlp"
                s_table = "pcid" + pcid + ".raw_review_analysis_" + cid
                # spend_minutes, table_size = get_predict_time(db, s_table, 40000, False)
                spend_minutes, table_size = 0, 0

                if IF_DELAY:
                    print("STEP4 Delay")
                    reviews_extraction.delay(pcid=pcid, cid=cid, name=user.name)
                else:
                    print("STEP4 Execute")
                    reviews_extraction(pcid=pcid, cid=cid, name=user.name)
                data = "{}开始对PCID:{} CID:{}  品类进行 [第四步：终处理] 共{}条待处理评价".format(user.name, pcid, cid, table_size)
                send_message(data)
                UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)

                item = Task_state.objects.get(pcid=pcid, cid=cid)
                item.step_4_status = 'doing'
                item.step_4_time = NOW() + datetime.timedelta(minutes=spend_minutes)
                item.save()
            status['status'] = '1'
            status['msg'] = 'success'

    except Exception as e:
        print(e)
    return gen_response(status, True)


@csrf_exempt
def jump_features_check(request):
    status = {'status': '0', 'msg': 'error'}
    try:
        pcid = request.POST.get('pcid', None)
        cid = request.POST.get('cid', None)
        user_id = request.POST.get('user_id', None)
        if pcid and cid and user_id:
            print("STEP3 Jump")
            user = User.objects.get(id=user_id)

            data = "{}跳过 PCID:{} CID:{}  品类 [第三步：业务人员标注]".format(user.name, pcid, cid)
            send_message(data)
            UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)

            item = Task_state.objects.get(pcid=pcid, cid=cid)
            item.step_3_status = 'done'
            item.step_4_status = 'go'
            item.step_3_time = NOW()
            item.save()

            status['status'] = '1'
            status['msg'] = 'success'

    except Exception as e:
        print(e)
    return gen_response(status, True)


@csrf_exempt
def reset_configuration(request):
    status = {'status': '0', 'msg': 'error'}
    try:
        pcid = request.POST.get('pcid', None)
        cid = request.POST.get('cid', None)
        user_id = request.POST.get('user_id', None)
        if pcid and cid and user_id:
            user = User.objects.get(id=user_id)

            data = "{}对 PCID:{} CID:{}  品类 [重置文本分析状态]".format(user.name, pcid, cid)
            print("new_reviews 重置状态")
            send_message(data)
            UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)

            item = Task_state.objects.get(pcid=pcid, cid=cid)
            item.step_1_time = None
            item.step_2_time = None
            item.step_3_time = None
            item.step_4_time = None
            item.step_1_status = 'go'
            item.step_2_status = 'no'
            item.step_3_status = 'no'
            item.step_4_status = 'no'
            item.status = 1
            item.save()

            status['status'] = '1'
            status['msg'] = 'success'

    except Exception as e:
        print(e)
    return gen_response(status, True)


@require_GET
def wordcluster(request):
    pcid = request.GET.get('pcid', None)
    cid = request.GET.get('cid', None)
    edit = request.GET.get('edit')
    if edit:
        db = 'synonym'
    else:
        db = 'unsolved_synonym'
    rows = db_99_get("lexicon", "select src_word, des_word from {} where cid = '{}'".format(db, cid))
    clusters = {}
    context = {
        "status": "1",
        "result": {
            "pcid": pcid,
            "cid": cid,
            "clusters": [],
            "single_cluster": ""
        },
        'edit': edit,
    }

    # 合并数据
    for row in rows:
        if row[1] not in clusters:
            clusters[row[1]] = []
        clusters[row[1]].append(row[0])

    # 获得单个词组
    single_word_clusters = []
    for k in list(clusters.keys()):
        if len(set(clusters[k])) <= 1:
            single_word_clusters.extend(clusters[k])
            del clusters[k]
    item = Task_state.objects.filter(cid=cid)[0]
    context["result"]["cluster_alpha"] = item.step_2_cluster_alpha
    context["result"]["clusters"] = [{"des": k, "src": " / ".join(sorted(set(v)))} for k, v in clusters.items()]
    context["result"]["single_cluster"] = "\n".join(sorted(set(single_word_clusters)))
    return render(request, 'reviews/wordcluster.html', context)


@require_GET
def wordcluster_v2(request):
    print("这里在聚类")
    pcid = request.GET.get('pcid', None)
    cid = request.GET.get('cid', None)

    item = Task_state.objects.filter(pcid=pcid, cid=cid).first()

    return render(request, 'reviews/wordcluster_v2.html', locals())


@require_GET
def get_words_cluster_result(request, pcid, cid):
    solved = dict()
    solved_words = dict()
    unsolved = dict()
    unsolved_words = dict()
    frequency = dict()
    sentences = dict()

    engine = get_99_engine('lexicon')

    srcs = set()

    table = 'synonym'
    sql = "select src_word, des_word from {} where pcid = '{}' and cid = '{}'".format(table, pcid, cid)
    df = read_data(sql, engine, table)
    if not df.empty:
        for i, v in df.iterrows():
            des_word = v['des_word']
            src_word = v['src_word']
            if src_word in srcs:
                continue
            srcs.add(src_word)
            if des_word not in solved:
                solved[des_word] = set()
            if src_word != des_word:
                solved[des_word].add(src_word)
            if src_word not in solved_words:
                solved_words[src_word] = set()
            solved_words[src_word].add(des_word)

    table = 'unsolved_synonym'
    sql = (
        "select src_word, des_word, frequency, sentences"
        " from {} where pcid = '{}' and cid = '{}'"
    ).format(table, pcid, cid)
    df = read_data(sql, engine, table)
    if not df.empty:
        for i, v in df.iterrows():
            des_word = v['des_word']
            src_word = v['src_word']
            frequency[src_word] = v['frequency']
            sentences[src_word] = v['sentences']
            if src_word in srcs:
                continue
            srcs.add(src_word)
            if des_word not in unsolved:
                unsolved[des_word] = set()
            if src_word != des_word:
                unsolved[des_word].add(src_word)
            if src_word not in unsolved_words:
                unsolved_words[src_word] = set()
            unsolved_words[src_word].add(des_word)

    singles = set()

    keys = list(solved.keys()) + list(unsolved.keys())
    for i in keys:
        if i in solved_words or i in unsolved_words:
            continue

        un_words = set()
        words = set()
        un_words.update(list(solved.get(i) or []))
        un_words.update(list(unsolved.get(i) or []))
        need = False
        error = False
        while un_words:
            t = un_words.pop()
            if t in words:
                error = True
                break
            words.add(t)
            r = set()
            r.update(list(solved.get(t) or []))
            r.update(list(unsolved.get(t) or []))
            if r:
                need = True
            un_words.update(list(r))
        if error:
            for j in words:
                singles.add(j)
                t = set(j)
                t.update(unsolved_words.pop(j) or [])
                t.update(solved_words.pop(j) or [])
                for k in t:
                    t = solved.pop(k, [])
                    singles.update(t)
                    t = unsolved.pop(k, [])
                    singles.update(t)
        else:
            if words and need:
                r = set(words)
                t = set(words)
                for j in words:
                    t.update(unsolved_words.pop(j, []))
                    t.update(solved_words.pop(j, []))
                for j in t:
                    r.update(unsolved.pop(j, []))
                    r.update(solved.pop(j, []))
                if i in r:
                    r.remove(i)
                unsolved[i] = r

    result = []
    for des_word in solved:
        tmp = dict(des=des_word)
        edit_srcs = solved[des_word]
        srcs = set()
        if des_word in unsolved:
            srcs = unsolved.pop(des_word)
        srcs = srcs - edit_srcs
        if not edit_srcs and not srcs:
            continue

        tmp['edit_srcs'] = list(edit_srcs)
        tmp['srcs'] = list(srcs)
        result.append(tmp)

    for des_word in unsolved:
        tmp = dict(des=des_word)
        edit_srcs = set()
        srcs = unsolved[des_word]
        srcs = srcs - edit_srcs
        if len(srcs) == 0:
            singles.add(des_word)
            continue
        if not edit_srcs and not srcs:
            continue
        tmp['edit_srcs'] = list(edit_srcs)
        tmp['srcs'] = list(srcs)
        result.append(tmp)

    singles = list(singles)

    result.sort(key=lambda x: (len(x['edit_srcs']) == 0 and len(x['srcs']) > 0, len(x['srcs']) > 0), reverse=True)

    status = dict(status=200)
    status['data'] = result
    status['singles'] = singles
    status['frequency'] = frequency
    status['sentences'] = sentences

    return gen_response(status)


@csrf_exempt
def update_clusters(request):
    status = {'status': '0', 'msg': 'error'}
    try:
        req = json.loads(request.body)
        pcid = req.get('pcid', None)
        cid = req.get('cid', None)
        user_id = req.get('user_id', None)
        context = req.get('context', {})
        server = db_99_server("lexicon")
        update_synonym_table(server, pcid, cid, context, req.get('edit'))
        user = User.objects.get(id=user_id)
        data = "{} 对PCID:{} CID:{}  品类 [第二步：聚类结果检查及合并] 共{}个词全部完成".format(user.name, pcid, cid, len(context))
        send_message(data)
        UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)
        item = Task_state.objects.filter(pcid=pcid, cid=cid)[0]
        item.step_2_clutser_status = 0
        item.save()

        status['status'] = '1'
        status['msg'] = 'success'

    except Exception as e:
        traceback.print_exc()
    return gen_response(status, True)


@csrf_exempt
@require_POST
def update_clusters_v2(request):
    data = request.POST
    pcid = data.get('pcid')
    cid = data.get('cid')
    user_id = data.get('user_id')
    context = data.get('data')
    context = context and json.loads(context) or dict()
    unsolved = data.get('unsolved')
    unsolved = unsolved and json.loads(unsolved) or []
    update_synonym_table(pcid, cid, context, unsolved)
    user = User.objects.get(id=user_id)
    data = "{} 对PCID:{} CID:{}  品类 [第二步：聚类结果检查及合并] 共{}个词全部完成".format(user.name, pcid, cid, len(context))
    send_message(data)
    UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)
    item = Task_state.objects.filter(pcid=pcid, cid=cid)[0]
    item.step_2_clutser_status = 0
    item.save()

    status = dict()
    status['status'] = 200
    status['msg'] = 'success'
    return gen_response(status, True)


@csrf_exempt
def cluster_targets(request):
    status = {'status': '0', 'msg': 'error'}
    try:
        pcid = request.POST.get('pcid', None)
        cid = request.POST.get('cid', None)
        user_id = request.POST.get('user_id', None)
        cluster_alpha = float(request.POST.get('cluster_alpha', None))
        if pcid and cid and user_id:
            user = User.objects.get(id=user_id)

            cluster_target.delay(pcid=pcid, cid=cid, name=user.name, cluster_alpha=cluster_alpha)

            data = "{}对 PCID:{} CID:{}  品类 [进行文本近义词聚类]".format(user.name, pcid, cid)
            send_message(data)
            UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=data)
            item = Task_state.objects.get(pcid=pcid, cid=cid)
            item.step_2_cluster_alpha = cluster_alpha
            item.save()

            status['status'] = '1'
            status['msg'] = 'success'

    except Exception as e:
        print(e)
    return gen_response(status, True)


LEXICON_TYPE_ATTRS = dict(
    synonym_global=dict(
        table_name='synonym_global',
        left_column='src_word',
        right_column='des_word',
        url_root='/reviews/lexicon/synonym_global',
        left_name='相近词',
        right_name='替换词',
        type='global',
    ),
    synonym=dict(
        table_name='synonym',
        left_column='src_word',
        right_column='des_word',
        url_root='/reviews/lexicon/synonym',
        left_name='相近词',
        right_name='替换词',
        type='cid',
    ),
    target_global=dict(
        table_name='targets_global',
        left_column='target',
        right_column='tag',
        url_root='/reviews/lexicon/target_global',
        left_name='属性',
        right_name='标注值',
        type='global',
    ),
    target=dict(
        table_name='targets',
        left_column='target',
        right_column='tag',
        url_root='/reviews/lexicon/target',
        left_name='属性',
        right_name='标注值',
        type='cid',
    )
)


@require_GET
def get_lexicon_list(request, lexicon_type):
    data = request.GET
    left = data.get('left', '').strip()
    right = data.get('right', '').strip()
    page = int(data.get('page') or 1)
    length = PAGE_LENGTH
    attrs = LEXICON_TYPE_ATTRS[lexicon_type]
    template_name = 'reviews/lexicon.html'

    url_root = attrs['url_root']
    left_name = attrs['left_name']
    right_name = attrs['right_name']
    left_column = attrs['left_column']
    right_column = attrs['right_column']
    table_name = attrs['table_name']
    is_global = attrs['type'] == 'global'

    db_name = "lexicon"
    engine = get_99_engine(db_name)
    sql_prefix = "select {}, {} from {} where 1 = 1".format(
        left_column, right_column, table_name)
    pcid = cid = ''
    if not is_global:
        pcid = data.get('pcid')
        cid = data.get('cid')
        if not pcid or not cid:
            return render(request, template_name, locals())
        sql_prefix += " and pcid = '{}' and cid = '{}'".format(pcid, cid)

    only_one = False
    only_one_value = None
    if left and right:
        con = "and {} ~ '{}' and {} ~ '{}'".format(left_column, left, right_column, right)
    elif left:
        con = "and {} ~ '{}'".format(left_column, left)
        only_one = left_column
        only_one_value = left
    elif right:
        con = "and {} ~ '{}'".format(right_column, right)
        only_one = right_column
        only_one_value = right
    else:
        con = 'and 1 = 1'

    sql = "select count(*) num from {} where 1 = 1 {}".format(table_name, con)
    if pcid and cid:
        sql = "{} and pcid = '{}' and cid = '{}'".format(sql, pcid, cid)
    df = read_data(sql, engine, table_name)
    num = df['num'].tolist()[0]
    pages = num // length if num % length == 0 else num // length + 1
    pages = list(range(1, pages + 1))
    pages = get_page_list(page, pages)

    sql = "{} {} order by {}, {} limit {}".format(sql_prefix, con, right_column, left_column, length)
    if page:
        sql = "{} offset {}".format(sql, (page - 1) * length)
    df = read_data(sql, engine, table_name)

    # 筛选可能重复的值
    if not df.empty and only_one:
        only_one_column = right_column if only_one == left_column else left_column
        items = df[only_one].drop_duplicates().tolist()
        items = ["'{}'".format(i) for i in items]
        items = ','.join(items)
        df = df.append(read_data(
            "{} and {} in ({}) and {} != {}".format(sql_prefix, only_one_column, items, left_column, right_column),
            engine,
            table_name,
        ), ignore_index=True, sort=False)

    df.drop_duplicates(inplace=True)
    clusters = []
    for i, v in df.iterrows():
        clusters.append(dict(left=v[left_column], right=v[right_column]))

    return render(request, template_name, locals())


@csrf_exempt
@require_POST
def edit_lexicon(request, lexicon_type, op):
    attrs = LEXICON_TYPE_ATTRS[lexicon_type]

    left_column = attrs['left_column']
    right_column = attrs['right_column']
    left_name = attrs['left_name']
    right_name = attrs['right_name']
    table_name = attrs['table_name']
    is_global = attrs['type'] == 'global'

    data = request.POST
    left = (data.get('left') or '').strip()
    right = (data.get('right') or '').strip()
    old_left = (data.get('old_left') or '').strip()
    old_right = (data.get('old_right') or '').strip()
    if not left or not right:
        return gen_response(dict(status='0', msg='{}或{}不能为空'.format(left_name, right_name)), True)
    if left == right:
        return gen_response(dict(status='0', msg='{}不能等于{}'.format(left_name, right_name)), True)

    db_name = 'lexicon'
    sql_prefix = "select {}, {} from {} where".format(left_column, right_column, table_name)
    if not is_global:
        pcid = data.get('pcid')
        cid = data.get('cid')
        if not pcid or not cid:
            return gen_response(dict(status='0', msg='pcid或cid不能为空'), True)
        sql_prefix += " pcid = '{}' and cid = '{}' and".format(pcid, cid)
    if op in ['save', 'reverse']:
        if op == 'save':
            sql = (
                "{} ({} = '{}' or {} = '{}') and not ({} = {})"
            ).format(sql_prefix, left_column, right, right_column, left, left_column, right_column)
        else:
            sql = (
                "{prefix} ({left_column} in ('{left}', '{right}') or {right_column} = '{left}')"
                " and not ({left_column} = '{old_left}' and {right_column} = '{old_right}')"
                " and not ({left_column} = {right_column})"
            ).format(
                prefix=sql_prefix, left_column=left_column, left=left, right=right, right_column=right_column,
                old_left=old_left, old_right=old_right,
            )
        data = db_99_get(db_name, sql)
        if data:
            result = dict(left=[], right=[])
            for i in data:
                if i[0] == right:
                    result['right'].append(i)
                else:
                    result['left'].append(i)
            result = result['left'] + result['right']
            return gen_response(dict(status='0', msg='存在值重复', error='conflict', data=result), True)

        sql_prefix = "update {} set {} = '{}' where".format(table_name, right_column, right)
        if not is_global:
            sql_prefix += " pcid = '{}' and cid = '{}' and".format(pcid, cid)
        if op == 'save':
            db_execute(
                db_99_server(db_name),
                "{} {} = '{}'".format(sql_prefix, left_column, left),
            )
        else:
            db_execute(
                db_99_server(db_name),
                "{} {} = '{}' and {} = '{}'".format(sql_prefix, left_column, old_left, right_column, old_right),
            )
    elif op == 'delete':
        sql_prefix = "delete from {} where".format(table_name)
        if not is_global:
            sql_prefix += " pcid = '{}' and cid = '{}' and".format(pcid, cid)
        db_execute(
            db_99_server(db_name),
            "{} {} = '{}' and {} = '{}'".format(sql_prefix, left_column, left, right_column, right),
        )
    else:
        return gen_response(dict(status='0'), True)

    return gen_response(dict(status='1'), True)


@csrf_exempt
@require_POST
def save_lexicon(request, lexicon_type):
    attrs = LEXICON_TYPE_ATTRS[lexicon_type]

    left_column = attrs['left_column']
    right_column = attrs['right_column']
    left_name = attrs['left_name']
    right_name = attrs['right_name']
    table_name = attrs['table_name']
    is_global = attrs['type'] == 'global'
    db_name = 'lexicon'
    engine = get_99_engine(db_name)

    data = request.POST
    words = data.get('data')
    if not words:
        return gen_response(dict(status='0', msg='data不能为空'))
    words = json.loads(words)

    sql_prefix = "select {}, {} from {} where".format(left_column, right_column, table_name)
    pcid = cid = ''
    if not is_global:
        pcid = data.get('pcid')
        cid = data.get('cid')
        if not pcid or not cid:
            return gen_response(dict(status='0', msg='pcid或cid不能为空'))
        sql_prefix += " pcid = '{}' and cid = '{}' and".format(pcid, cid)
    sql_update = "update {} set {} = %s where {} = %s".format(table_name, right_column, left_column)
    if not is_global:
        sql_update += " and pcid = '{}' and cid = '{}'".format(pcid, cid)

    params = []
    for left, right in words:
        if not left or not right:
            continue

        sql = (
            "{} ({} = '{}' or {} = '{}') and not ({} = {})"
        ).format(sql_prefix, left_column, right, right_column, left, left_column, right_column)
        df = read_data(sql, engine, table_name)
        if not df.empty:
            result = dict(left=[], right=[])
            for i, v in df.iterrows():
                if v[left_column] == right:
                    result['right'].append(i)
                else:
                    result['left'].append(i)
            result = result['left'] + result['right']
            return gen_response(dict(
                status='0', msg='存在值重复', error='conflict', data=result, item=[left, right]), True)

        params.append([right, left])

    if params:
        db_psql(engine, sql_update, params=params)

    return gen_response(dict(status=200), True)


@require_GET
def show_cid_sentiment(request):
    data = request.GET
    pcid = data.get('pcid')
    cid = data.get('cid')
    if not pcid or not cid:
        raise Http404

    db_name = 'lexicon'
    engine = get_99_engine(db_name)

    # 获取全局情感词库
    table = 'sentiment_global'
    df = read_data("select target, opinion, grade, merge from {}".format(table), engine, table)
    tmp = {}
    global_lexicon_merge = {}
    for i, v in df.iterrows():
        target, opinion, grade, merge = v['target'], v['opinion'], v['grade'], v['merge']
        value = dict(grade=grade, merge=merge)
        if target not in tmp:
            tmp[target] = dict()
        tmp[target][opinion] = value
        if target not in global_lexicon_merge:
            global_lexicon_merge[target] = dict()
        global_lexicon_merge[target][merge] = dict(grade=grade, opinion=opinion)
    global_lexicon = tmp

    # 获取品类情感词库
    table = get_pcid_sentiment_table_name(pcid)
    if check_table_exists(engine, table):
        df = read_data(
            "select target, opinion, grade, merge from {} where cid = '{}'".format(table, cid),
            engine, table,
        )
    else:
        df = pd.DataFrame()
    tmp = {}
    last_edit_merge = {}
    for i, v in df.iterrows():
        target, opinion, grade, merge = v['target'], v['opinion'], v['grade'], v['merge']
        value = dict(grade=grade, merge=merge)
        if target in tmp:
            tmp[target][opinion] = value
        else:
            tmp[target] = {opinion: value}
        if target in last_edit_merge:
            last_edit_merge[target][merge] = dict(grade=grade, opinion=opinion)
        else:
            last_edit_merge[target] = {merge: dict(grade=grade, opinion=opinion)}
    last_edit = tmp

    table = 'sentiment_recommend'
    df = read_data("select target, opinion, grade, merge, type from {}".format(table), engine, table)
    # eg.{opinion: {target:{}}}
    tmp = {}
    for i, v in df.iterrows():
        target, opinion, grade, merge, record_type = v['target'], v['opinion'], v['grade'], v['merge'], v['type']
        value = dict(grade=grade, merge=merge, type=record_type)
        if opinion in tmp:
            if target in tmp[opinion]:
                if record_type > tmp[opinion][target]['type']:
                    tmp[opinion][target] = value
            else:
                tmp[opinion][target] = value
        else:
            tmp[opinion] = {target: value}
    recommend = tmp

    db_name = 'tb_comment_nlp'
    engine = get_99_engine(db_name)
    table = 'pcid{}.review_analysis_{}'.format(pcid, cid)
    df = read_data(
        (
            "select target, opinion, grade, comment_date"
            " from {}"
        ).format(table),
        engine, table,
    )
    df['datamonth'] = df['comment_date'].str.slice(0, 6)
    df = df.groupby(['target', 'opinion', 'grade', 'datamonth']).agg(dict(comment_date='count')).reset_index()
    df.rename(columns=dict(comment_date='num_datamonth'), inplace=True)

    tmp = df.groupby(['target', 'opinion']).agg(dict(num_datamonth='sum')).reset_index()
    tmp.rename(columns=dict(num_datamonth='num'), inplace=True)
    df = pd.merge(df, tmp, how='left', on=['target', 'opinion'])
    del tmp

    datamonth_list = df['datamonth'].drop_duplicates().sort_values(ascending=False)

    log.logger.info('iter df start')
    result = {}
    for i, v in df.iterrows():
        # 寻找情感词可能的设置，匹配顺序为
        # - 已经编辑过的品类情感词库
        # - 全局情感词库符合opinion的值
        # - 同时符合target和opinion的推荐值
        # - 只符合opinion的推荐值
        target, opinion, grade = v['target'], v['opinion'], v['grade']
        num, num_datamonth, datamonth = v['num'], v['num_datamonth'], v['datamonth']

        if target in result and opinion in result[target]:
            result[target][opinion]['num_datamonth'] += ';{}:{}'.format(datamonth, num_datamonth)
            continue

        merge = ''
        is_global = False
        rule = ''
        rule_record = None
        global_lexicon_target = global_lexicon.get(target) or dict()
        global_lexicon_merge_target = global_lexicon_merge.get(target) or dict()

        if target in last_edit and opinion in last_edit[target]:
            rule = 'cid'
            merge = last_edit[target][opinion]['merge']
            grade = last_edit[target][opinion]['grade']
            rule_record = dict(target=target, opinion=opinion, merge=merge, grade=grade)
        elif target in last_edit_merge and opinion in last_edit_merge[target]:
            rule = 'cid'
            merge = opinion
            grade = last_edit_merge[target][opinion]['grade']
            rule_record = dict(
                target=target, opinion=last_edit_merge[target][opinion]['opinion'], merge=opinion, grade=grade
            )
        elif opinion in global_lexicon_target:
            rule = 'global'
            merge = global_lexicon_target[opinion]['merge']
            grade = global_lexicon_target[opinion]['grade']
            is_global = True
            rule_record = dict(target=target, opinion=opinion, merge=merge, grade=grade)
        elif opinion in global_lexicon_merge_target:
            rule = 'global'
            merge = opinion
            grade = global_lexicon_merge_target[opinion]['grade']
            is_global = True
            rule_record = dict(
                target=target, opinion=global_lexicon_merge_target[opinion]['opinion'], merge=merge, grade=grade
            )
        elif opinion in recommend:
            rule = 'recommend'
            if target in recommend[opinion]:
                merge = recommend[opinion][target]['merge']
            else:
                for i in recommend[opinion]:
                    merge = recommend[opinion][i]['merge']
                    break
            rule_record = dict(
                target=target, opinion=opinion, merge=merge, grade=grade
            )

        if not is_global and (
                opinion in global_lexicon and merge == global_lexicon[opinion]['merge']
                and grade == global_lexicon[opinion]['grade']
                or opinion in global_lexicon_merge and global_lexicon_merge[opinion]['grade'] == grade):
            is_global = True

        value = {
            'grade': grade,
            'merge': merge,
            'global': is_global,
            'num': num,
            'num_datamonth': '{}:{}'.format(datamonth, num_datamonth),
            'rule': rule,
            'rule_record': '{};{};{};{}'.format(
                rule_record['target'], rule_record['opinion'], rule_record['grade'], rule_record['merge']
            ) if rule_record else '',
        }

        if target in result:
            result[target][opinion] = value
        else:
            result[target] = {opinion: value}
    log.logger.info('iter df end')

    return render(request, 'reviews/sentiment_merge.html', locals())


def get_pcid_sentiment_table_name(pcid):
    return 'sentiment.pcid{}'.format(pcid)


def create_table_pcid_sentiment(pcid):
    db_name = 'lexicon'
    table_name = get_pcid_sentiment_table_name(pcid)
    return db_99_psql(db_name,
                      """
       CREATE TABLE if not exists {table_name}
       (
         target character varying,
         opinion character varying,
         grade integer,
         merge character varying,
         cid character varying(20),
         CONSTRAINT pk_pcid{pcid}_target_opinion UNIQUE (cid, target, opinion)
       )
       WITH (
         OIDS=FALSE
       );
                       """.format(pcid=pcid, table_name=table_name))


@csrf_exempt
@require_POST
def save_cid_sentiment(request):
    data = request.POST
    pcid = data.get('pcid')
    cid = data.get('cid')
    target = data.get('target')
    sentiment_data = data.get('data')
    if not pcid or not cid or not sentiment_data or not target:
        raise Http404
    sentiment_data = json.loads(sentiment_data)

    if not create_table_pcid_sentiment(pcid):
        return gen_response(dict(status='0', msg='建表失败'), allow=True)

    db_name = 'lexicon'
    engine = get_99_engine(db_name)
    table_name = get_pcid_sentiment_table_name(pcid)

    edit_opinions = []
    sql_data = []
    for i in sentiment_data:
        sql_data.append([cid, i['target'], i['opinion'], int(i['grade']), i['merge']])
        edit_opinions.append(i['opinion'])

    db_psql(
        engine,
        "delete from {} where cid = '{}' and target = '{}' and opinion in ({})".format(
            table_name, cid, target, ','.join(["'{}'".format(i) for i in edit_opinions])),
    )

    db_psql(
        engine,
        "insert into {}(cid, target, opinion, grade, merge) values(%s, %s, %s, %s, %s)".format(table_name),
        params=sql_data,
    )

    global_data = [dict(
        target=i['target'], opinion=i['opinion'], grade=int(i['grade']), merge=i['merge'],
    ) for i in sentiment_data if i.get('set_global') and i['merge'] and i['opinion'] != i['merge']]

    select_sql = "select * from sentiment_global where target = '{}' and opinion = '{}';"
    update_sql = "update sentiment_global set grade = '{}', merge = '' where target = '{}' and opinion = '{}';"
    insert_sql = "insert into sentiment_global(target, opinion, grade, merge) values('{}', '{}', '{}', '{}');"
    for i in global_data:
        if db_99_get(db_name, select_sql.format(i['target'], i['opinion'])):
            db_99_psql(db_name, update_sql.format(i['grade'], i['merge'], i['target'], i['opinion']))
        else:
            db_99_psql(db_name, insert_sql.format(i['target'], i['opinion'], i['grade'], i['merge']))

    return gen_response(dict(status='1'), allow=True)


@csrf_exempt
@require_POST
def save_cid_sentiment_one(request):
    data = request.POST
    pcid = data.get('pcid')
    cid = data.get('cid')
    target = data.get('target')
    opinion = data.get('opinion')
    grade = data.get('grade')
    merge = data.get('merge')
    is_global = data.get('set_global')

    if not create_table_pcid_sentiment(pcid):
        return gen_response(dict(status='0', msg='建表失败'), allow=True)

    db_name = 'lexicon'
    table_name = get_pcid_sentiment_table_name(pcid)

    if merge:
        rows = db_99_get(db_name, "select target, opinion, grade, merge from {}"
                                  " where target = '{}' and merge = '{}' and grade != {}".format(
            table_name, target, merge, grade))
        for row in rows:
            return gen_response(dict(
                status='0',
                msg='主语【{}】下的情感词【{}】的替换词【{}】的正负向为【{}】'.format(row[0], row[1], row[3], {
                    1: '正面', -1: '负面', 0: '中立'}.get(row[2]))), allow=True)

        db_99_psql(db_name, "delete from {} where cid = '{}' and target = '{}' and opinion = '{}';".format(
            table_name, cid, target, opinion))

        status = db_99_psql(
            db_name,
            "insert into {}(cid, target, opinion, grade, merge) values('{}', '{}', '{}', {}, '{}');".format(
                table_name, cid, target, opinion, grade, merge),
        )
        if not status:
            return gen_response(dict(status='0', msg='保存失败'), allow=True)
    else:
        db_99_psql(db_name, "delete from {} where cid = '{}' and target = '{}' and opinion = '{}';".format(
            table_name, cid, target, opinion))

    if is_global and merge:
        select_sql = "select * from sentiment_global where opinion = '{}';"
        update_sql = "update sentiment_global set grade = '{}', merge = '' where target = '{}' and opinion = '{}'"
        insert_sql = "insert into sentiment_global(target, opinion, grade, merge) values('{}', '{}', '{}', '{}')"
        if db_99_get(db_name, select_sql.format(opinion)):
            db_99_psql(db_name, update_sql.format(grade, merge, target, opinion))
        else:
            db_99_psql(db_name, insert_sql.format(target, opinion, grade, merge))

    return gen_response(dict(status='1'), allow=True)


@require_GET
def get_sentiment_global_list(request):
    data = request.GET
    opinion = data.get('opinion', '').strip()
    merge = data.get('merge', '').strip()
    page = int(data.get('page') or 1)
    length = PAGE_LENGTH
    template_name = 'reviews/sentiment_global.html'

    db_name = "lexicon"
    engine = get_99_engine(db_name)
    table_name = 'sentiment_global'
    sql_prefix = "select opinion, grade, merge from {} where".format(table_name)

    only_one = False
    only_one_value = None
    if opinion and merge:
        con = "opinion ~ '{}' and merge ~ '{}'".format(opinion, merge)
    elif opinion:
        con = "opinion ~ '{}'".format(opinion)
        only_one = 'opinion'
        only_one_value = opinion
    elif merge:
        con = "merge ~ '{}'".format(merge)
        only_one = 'merge'
        only_one_value = merge
    else:
        con = "1 = 1"

    sql = "select count(*) num from {} where {}".format(table_name, con)
    df = read_data(sql, engine, table_name)
    num = df['num'].tolist()[0]
    pages = num // length if num % length == 0 else num // length + 1
    pages = list(range(1, pages + 1))
    pages = get_page_list(page, pages)

    sql = "{} {} order by merge, opinion limit {}".format(sql_prefix, con, length)
    if page:
        sql = "{} offset {}".format(sql, (page - 1) * length)
    df = read_data(sql, engine, table_name)

    result = []
    # 合并数据
    for i, v in df.iterrows():
        result.append(dict(opinion=v['opinion'], grade=v['grade'], merge=v['merge']))

    if result and only_one:
        df = read_data(
            "{} {} = '{}'".format(sql_prefix, 'merge' if only_one == 'opinion' else 'opinion', only_one_value),
            engine, table_name,
        )
        for i, v in df.iterrows():
            result.append(dict(opinion=v['opinion'], grade=v['grade'], merge=v['merge']))

    return render(request, template_name, locals())


@csrf_exempt
@require_POST
def edit_sentiment_global(request, op):
    data = request.POST
    opinion = (data.get('opinion') or '').strip()
    merge = (data.get('merge') or '').strip()
    grade = (data.get('grade') or '').strip()
    old_opinion = (data.get('old_opinion') or '').strip()
    old_merge = (data.get('old_merge') or '').strip()
    if not opinion or not merge:
        return gen_response(dict(status='0', msg='情感词或替换词不能为空'), True)
    if opinion == merge:
        return gen_response(dict(status='0', msg='情感词不能等于替换词'), True)

    db_name = 'lexicon'
    sql_prefix = "select opinion, merge, grade from sentiment_global where"
    if op in ['save', 'reverse']:
        if op == 'save':
            sql = "{} (opinion = '{}' or merge = '{}')".format(
                sql_prefix, merge, opinion)
        else:
            sql = "{prefix} (opinion in ('{opinion}', '{merge}') or merge = '{opinion}')".format(
                prefix=sql_prefix, opinion=opinion, merge=merge)
            sql = '{} and not (opinion = "{}" and merge = "{}")'.format(sql, old_opinion, old_merge)
        data = db_99_get(db_name, sql)
        if data:
            result = dict(opinion=[], merge=[])
            for i in data:
                v = dict(opinion=i[0], merge=i[1], grade=i[2])
                if v['opinion'] == merge:
                    result['merge'].append(v)
                elif v['merge'] == opinion:
                    result['opinion'].append(v)
            result = result['opinion'] + result['merge']
            return gen_response(dict(status='0', msg='存在值重复', error='conflict', data=result), True)

        sql_prefix = "update sentiment_global set opinion = '{}', merge = '{}', grade = {} where".format(opinion, merge,
                                                                                                         grade)
        if op == 'save':
            db_execute(
                db_99_server(db_name),
                "{} opinion = '{}'".format(sql_prefix, old_opinion),
            )
        else:
            db_execute(
                db_99_server(db_name),
                "{} opinion = '{}' and merge = '{}'".format(sql_prefix, old_opinion, old_merge),
            )
    elif op == 'delete':
        sql_prefix = "delete from sentiment_global where"
        db_execute(
            db_99_server(db_name),
            "{} opinion = '{}' and merge = '{}'".format(sql_prefix, old_opinion, old_merge),
        )
    else:
        return gen_response(dict(status='0'), True)

    return gen_response(dict(status='1'), True)


@csrf_exempt
@require_POST
def save_sentiment_global(request):
    db_name = 'lexicon'
    engine = get_99_engine(db_name)
    table = 'sentiment_global'

    data = request.POST
    words = data.get('data')
    if not words:
        return gen_response(dict(status='0', msg='data不能为空'), True)
    words = json.loads(words)

    sql = "select opinion, grade, merge from {}".format(table)
    df = read_data(sql, engine, table)

    sql_update = (
        "update {} set opinion = %s, grade = %s, merge = %s"
        " where opinion = %s and merge = %s"
    ).format(table)

    params = []
    for item in words:
        opinion = item['opinion']
        grade = item['grade']
        merge = item['merge']
        old_opinion = item['old_opinion']
        old_grade = item['old_grade']
        old_merge = item['old_merge']
        reverse = item.get('reverse')

        if reverse:
            index = (df['opinion'].isin([opinion, merge])) | (df['merge'] == opinion)
            index = (index) & ~((df['opinion'] == old_opinion) & (df['merge'] == old_merge))
        else:
            index = (df['opinion'] == merge) | (df['merge'] == opinion)
        tmp = df[index]
        if not tmp.empty:
            result = dict(opinion=[], merge=[])
            for i, v in tmp.iterrows():
                v = dict(opinion=i['opinion'], merge=i['merge'], grade=i['grade'])
                if v['opinion'] == merge:
                    result['merge'].append(v)
                elif v['merge'] == opinion:
                    result['opinion'].append(v)
            result = result['opinion'] + result['merge']
            return gen_response(dict(
                status='0', msg='存在值重复', error='conflict', data=result, item=[opinion, merge]))

        params.append([opinion, grade, merge, old_opinion, old_merge])

    if params:
        db_psql(engine, sql_update, params=params)

    return gen_response(dict(status=200), True)


@require_POST
@csrf_exempt
def delete_words_cluster_result(request, pcid, cid):
    data = request.POST
    words = data.get('data')
    words = words and json.loads(words) or []
    if not pcid or not cid or not words:
        return HttpResponseBadRequest
    words_tmp = words
    engine = get_99_engine('lexicon')
    words = ["'{}'".format(i) for i in words]
    sql = (
        "delete from unsolved_synonym where pcid = '{}' and cid = '{}' and src_word in ({})"
    ).format(pcid, cid, ','.join(words))
    db_psql(engine, sql)
    sql = (
        "delete from unsolved_targets where pcid = '{}' and cid = '{}' and target in ({})"
    ).format(pcid, cid, ','.join(words))
    db_psql(engine, sql)

    sql = "delete from nomeaning where pcid = '{}' and cid = '{}' and word in ({})".format(pcid, cid, ','.join(words))
    db_psql(engine, sql)
    sql = "insert into nomeaning(pcid, cid, word) values (%s, %s, %s)"
    db_psql(engine, sql, params=[[pcid, cid, i] for i in words_tmp])

    return gen_response(dict(status=200, msg='success'))


@require_GET
def get_model_reviews_targets(request):
    data = request.GET
    pcid = str(data.get('pcid') or '')
    cid = data.get('cid')
    page = data.get('page') or 0
    length = 1000

    if not pcid or not cid:
        return HttpResponseBadRequest()

    result = dict(status=200, msg='success')

    engine = get_99_engine('tb_comment_nlp')
    engine_comment = get_99_engine('raw_tb_comment_notag')
    table = f'pcid{pcid}.review_analysis_{cid}'
    table_comment = f'raw_comment_pcid{pcid}.raw_tb_comment{cid}'

    df = read_data(
        f"select target, opinion, grade, frequency, comment_id from {table}",
        engine, table,
    )
    df_comment = read_data(
        f"select itemid, comment_id, comment_date, comment_all from {table_comment}",
        engine_comment, table_comment,
    )

    df = pd.merge(df, df_comment, how='left', on=['comment_id'])
    del df_comment

    df = pd.merge(
        df,
        df.groupby(['target']).agg(dict(frequency='sum')).reset_index().rename(
            columns=dict(frequency='target_frequency')),
        how='left', on=['target'],
    )
    df['url'] = get_itemid_url_tb(df['itemid'])

    df.sort_values(['target_frequency', 'target', 'comment_date'], inplace=True, ascending=False)

    targets_info = []
    opinions_info = dict()
    comments_info = dict()

    last_target = ''
    for i, v in df.iterrows():
        target = v['target']

        if target != last_target:
            last_target = target
            targets_info.append(dict(target=target, target_frequency=v['target_frequency']))

        comments_info.setdefault(target, [])
        comments_info[target].append(dict(
            comment_id=v['comment_id'], comment_all=v['comment_all'], comment_date=v['comment_date'],
            itemid=v['itemid'], url=v['url'],
        ))

        opinions_info.setdefault(target, [])
        opinions_info[target].append(dict(
            opinion=v['opinion'], grade=v['grade'], frequency=v['frequency'],
            comment_id=v['comment_id'], comment_all=v['comment_all'], comment_date=v['comment_date'],
            itemid=v['itemid'], url=v['url'],
        ))

    result['targets'] = targets_info
    result['opinions'] = opinions_info
    result['comments'] = comments_info

    return gen_response(result)


@require_GET
def download_model_reviews_targets(request):
    data = request.GET
    pcid = str(data.get('pcid') or '')
    cid = data.get('cid')
    only_target = data.get('only_target')

    if not pcid or not cid:
        return HttpResponseBadRequest()

    engine = get_99_engine('tb_comment_nlp')
    engine_comment = get_99_engine('raw_tb_comment_notag')
    table = f'pcid{pcid}.review_analysis_{cid}_model_reviews'
    if not check_table_exists(engine, table):
        table = f'pcid{pcid}.review_analysis_{cid}'
    table_comment = f'raw_comment_pcid{pcid}.raw_tb_comment{cid}'

    if only_target:
        columns = ['target', 'tag', 'new_target', 'new_tag', 'frequency', 'comment_all']

        df = read_data(
            f"select target, tag, frequency, comment_id from {table}",
            engine, table,
        )
        df = df.groupby(['tag', 'target', 'comment_id']).agg(dict(frequency='sum')).reset_index()

        df_comment = read_data(
            f"select itemid, comment_id, comment_date, comment_all from {table_comment}",
            engine_comment, table_comment,
        )
        max_count = 100
        tmp = df_comment.groupby(['comment_all']).agg(dict(comment_id='count')).reset_index()
        tmp = tmp[tmp['comment_id'] <= max_count]
        df_comment = pd.merge(df_comment, tmp[['comment_all']], how='inner', on=['comment_all'])
        df = pd.merge(df, df_comment, how='inner', on=['comment_id'])
        del df_comment

        df = pd.merge(
            df,
            df.groupby(['target']).agg(dict(frequency='sum')).reset_index().rename(
                columns=dict(frequency='target_frequency')),
            how='left', on=['target'],
        )

        def func(df):
            comment_all = df['comment_all'].drop_duplicates().tolist()
            frequency = df['frequency'].sum()

            df['t'] = 1
            df.drop_duplicates('t', inplace=True)
            df.drop(columns=['t'], inplace=True)

            df['comment_all'] = '；'.join(comment_all[:100])
            df['frequency'] = frequency

            return df

        df.sort_values(['target', 'frequency', 'comment_all'], ascending=False, inplace=True)
        df = df.groupby(['target']).apply(func).reset_index(drop=True)

        df.sort_values(
            ['target_frequency', 'target', 'frequency', 'comment_date'],
            inplace=True, ascending=False,
        )
    else:
        columns = ['target', 'tag', 'new_target', 'new_tag', 'opinion', 'grade', 'frequency', 'comment_all']

        df = read_data(
            f"select target, tag, opinion, grade, frequency, comment_id from {table}",
            engine, table,
        )
        df = df.groupby(['tag', 'target', 'opinion', 'grade', 'comment_id']).agg(dict(frequency='sum')).reset_index()
        df_comment = read_data(
            f"select itemid, comment_id, comment_date, comment_all from {table_comment}",
            engine_comment, table_comment,
        )
        max_count = 100
        tmp = df_comment[['comment_id', 'comment_all']].drop_duplicates().groupby(['comment_all']).agg(
            dict(comment_id='count')).reset_index()
        tmp = tmp[tmp['comment_id'] <= max_count]
        df_comment = pd.merge(df_comment, tmp[['comment_all']], how='inner', on=['comment_all'])
        df = pd.merge(df, df_comment, how='inner', on=['comment_id'])
        del df_comment

        df = pd.merge(
            df,
            df.groupby(['target']).agg(dict(frequency='sum')).reset_index().rename(
                columns=dict(frequency='target_frequency')),
            how='left', on=['target'],
        )

        def func(df):
            comment_all = df['comment_all'].drop_duplicates().tolist()
            frequency = df['frequency'].sum()

            df['t'] = 1
            df.drop_duplicates('t', inplace=True)
            df.drop(columns=['t'], inplace=True)

            df['comment_all'] = '；'.join(comment_all[:100])
            df['frequency'] = frequency

            return df

        df.sort_values(['target', 'opinion', 'frequency', 'comment_all'], ascending=False, inplace=True)
        df = df.groupby(['target', 'opinion']).apply(func).reset_index(drop=True)

        df.sort_values(
            ['target_frequency', 'target', 'frequency', 'opinion', 'comment_date'],
            inplace=True, ascending=False,
        )

    df['url'] = get_itemid_url_tb(df['itemid'])

    # file_name = f'单品罗盘打标pcid{pcid}cid{cid}.xlsx'
    file_name = f'单品罗盘打标pcid{pcid}cid{cid}{"target合并" if only_target else ""}.csv'
    path = os.path.join(settings.BASE_DIR, 'tmp', file_name)
    # with pd.ExcelWriter(path) as writer:
    #     df.reindex(columns=[
    #         'target', 'tag', 'new_target', 'new_tag', 'target_frequency', 'comment_all',
    #     ]).rename(columns=dict(
    #         target_frequency='frequency'
    #     )).drop_duplicates().to_excel(writer, sheet_name='target合并')
    #     df.reindex(columns=[
    #         'target', 'tag', 'opinion', 'grade', 'frequency', 'comment_all',
    #     ]).to_excel(writer, sheet_name='正负向')

    df_to_csv(df.reindex(columns=columns), path, header=True, na_rep='', sep=',', encoding='gb18030')

    response = FileResponse(open(path, 'rb'))
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = f'attachment;filename="{urllib.parse.quote(file_name)}"'
    return response


@csrf_exempt
@require_POST
def upload_model_reviews_target(request):
    data = request.POST
    file = request.FILES.get('targets')

    pcid = str(data.get('pcid') or '')
    cid = data.get('cid')
    datamonth = data.get('datamonth')
    all_datamonth = data.get('all_datamonth')
    user_id = data.get('user_id')
    user = User.objects.get(id=user_id)
    force_nlp = data.get('force_nlp')

    if not pcid or not cid:
        return HttpResponseBadRequest()

    df = pd.DataFrame()
    for encoding in [
        'UTF-8-SIG',
        'gb18030',
        'utf-8', 'gbk',
    ]:
        try:
            df = pd.read_csv(file, sep=',', encoding=encoding)
        except Exception as e:
            log.logger.exception(e)
            file.seek(0)
            continue

    if df.empty:
        return HttpResponseBadRequest('读取文件失败')

    merge_model_reviews_comment(df, pcid, cid, force_original=False)

    result = dict(status=200, msg='success')

    return gen_response(result)


@csrf_exempt
@require_POST
def model_reviews_features_extraction(request):
    status = {'status': '0', 'msg': 'error'}
    pcid = request.POST.get('pcid')
    cid = request.POST.get('cid')
    user_id = request.POST.get('user_id', None)
    if pcid and cid and user_id:
        user = User.objects.get(id=user_id)
        db = "tb_comment_hanlp"
        s_table = "pcid" + pcid + ".raw_review_analysis_" + cid
        spend_minutes, table_size = get_predict_time(
            db, s_table, 200000, is_using_multiprocess=False,
        )

        data = "对PCID:{} CID:{}  品类 单品罗盘提取属性 共{}条待处理评价".format(
            pcid, cid, table_size)
        from reviews.tasks import model_reviews_features_extraction_task
        model_reviews_features_extraction_task.delay(pcid, cid, user.name, f'{user.name}{data}')
        msg = f'{user.name}开始{data}'
        send_message(msg)
        UserLog.objects.create(user_id=user_id, pcid=pcid, cid=cid, data=msg)
        status['status'] = 200
        status['msg'] = 'success'
    return gen_response(status)
