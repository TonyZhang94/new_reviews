import traceback
from multiprocessing import cpu_count

from django.conf import settings

import psycopg2

from analysis.script.utils import *


def db_99_server(db):
    port = 5432
    if db == 'report_dg':
        port = 5433
    return psycopg2.connect(database=db, user="zczx_write", password="zczxTech2012",
                            host='192.168.1.99', port=port)


def db_execute(server, sql, raise_exception=False):
    dbconn = server.cursor()
    result = True
    try:
        dbconn.execute(sql)
        server.commit()
    except Exception as e:
        if raise_exception:
            raise e
        else:
            traceback.print_exc()
            server.rollback()
            result = False
    dbconn.close()
    return result


def db_get(server, sql):
    dbconn = server.cursor()
    rows = []
    try:
        dbconn.execute(sql)
        rows = dbconn.fetchall()
    except Exception as e:
        traceback.print_exc()
    finally:
        dbconn.close()
    return rows


def db_99_psql(db, sql):
    conn = db_99_server(db)
    status = False
    try:
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        status = True
    except Exception as e:
        traceback.print_exc()
    finally:
        conn.close()
        return status


def db_99_get(db, sql, raise_exception=False):
    conn = db_99_server(db)
    rows = []
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
    except Exception as e:
        if raise_exception:
            raise e
        else:
            traceback.print_exc()
    finally:
        conn.close()
    return rows


def get_table_size(db, table_name, increment=False, des_db_name=None, des_table=None, column=None):
    if des_db_name and check_table_exists(get_99_engine(des_db_name), des_table) and increment:
        sql = (
            "SELECT COUNT({column}) FROM {}"
            " WHERE {column} NOT IN (SELECT comment_id"
            " FROM dblink('"
            "hostaddr={} port={} dbname={} user={} password={}',"
            "'select distinct({column}) from {}' )"
            " AS T({column} CHARACTER VARYING ( 20 )))"
        ).format(table_name, settings.DB_99, settings.DB_99_PORT, des_db_name, settings.DB_99_USERNAME,
                 settings.DB_99_PASSWORD, des_table, column=column)
    else:
        sql = 'select count(*) from {}'.format(table_name)
    rows = db_99_get(db, sql, raise_exception=True)
    if rows:
        size = rows[0][0]
    else:
        size = -1
    return size


def get_table_size_v2(db, table_name):
    if '.' in table_name:
        schema, table_name = table_name.split('.')
    else:
        schema = 'public'
    sql = "SELECT reltuples FROM pg_class r join pg_namespace n on relnamespace = n.oid" \
          " WHERE relkind = 'r' AND relname = '{}' and n.nspname = '{}';".format(table_name, schema)
    rows = db_99_get(db, sql)
    if rows:
        size = rows[0][0]
    else:
        size = -1
    return size


@logger
def get_predict_time(db, table_name, per_minutes_per_kernel_speed, is_using_multiprocess=True, increment=False,
                     des_db=None, des_table=None, column=None):
    if is_using_multiprocess:
        per_minute = cpu_count() * per_minutes_per_kernel_speed
    else:
        per_minute = per_minutes_per_kernel_speed

    if increment:
        table_size = get_table_size(db, table_name, increment, des_db, des_table, column)
    else:
        table_size = get_table_size_v2(db, table_name)
        # 元数据可能出现不准，这种情况下直接查询表记录数
        if table_size <= 0:
            table_size = get_table_size(db, table_name)

    if table_size <= -1:
        spent_time = 0
    else:
        spent_time = table_size / per_minute

    return spent_time, table_size


def update_targets_table(server, pcid, cid, data):
    insert_targets_sql = "INSERT INTO targets(pcid, cid, target, tag) VALUES ('%s','%s','%s','%s')"
    del_targets_sql = "delete from targets where target = '{}'"
    remove_targets_sql = "Delete from unsolved_targets where id = '%s' "
    insert_nomeaning_sql = "INSERT INTO nomeaning(pcid, cid, word) VALUES ('%s','%s','%s')"
    del_nomeaning_sql = "delete from nomeaning where word = '{}'"

    # if effective insert into and remove itself in unsolved_targets
    if data["iseffective"]:
        db_execute(server, del_targets_sql.format(data['target']))
        db_execute(server, insert_targets_sql % (pcid, cid, data["target"], data["tag"]), raise_exception=True)
        db_execute(server, remove_targets_sql % (data["id"]), raise_exception=True)
    else:
        # if not effective insert into nomeaning and remove itself in unsolved_targets
        if data['tag'] == 'delete':
            db_execute(server, del_nomeaning_sql.format(data["target"]))
            db_execute(server, insert_nomeaning_sql % (pcid, cid, data["target"]), raise_exception=True)
            db_execute(server, remove_targets_sql % (data["id"]), raise_exception=True)


def update_opinions_table(server, item):
    sql = "INSERT INTO opinions(word,grade) VALUES ('%s','%s')"

    if item["tag"] != "delete":
        db_execute(server, sql % (item["op"], item["tag"]))


def update_synonym_table(pcid, cid, context, unsolved):
    unsolved = unsolved or []
    engine = get_99_engine('lexicon')
    default_frequency = 110

    table = 'nomeaning'
    sql = "select word from {} where pcid = '{}' and cid = '{}'".format(table, pcid, cid)
    df = read_data(sql, engine, table)
    nomeaning = df['word'].tolist()

    if unsolved:
        sql = (
            "delete from synonym where pcid = '{}' and cid = '{}' and des_word in ({})"
        ).format(pcid, cid, ','.join(["'{}'".format(i['word']) for i in unsolved]))
        db_psql(engine, sql)

    del_sql = "delete from synonym where pcid = '{}' and cid = '{}' and src_word = %s".format(pcid, cid)
    insert_sql = (
        "INSERT INTO synonym(pcid, cid, src_word, des_word) VALUES ('{}','{}',%s,%s)"
    ).format(pcid, cid)
    del_sql_unsolved = (
        "delete from unsolved_synonym WHERE pcid = '{}' and cid = '{}' and src_word = %s"
    ).format(pcid, cid)
    insert_sql_unsolved = (
        "INSERT INTO unsolved_synonym(pcid, cid, src_word, des_word, frequency, sentences)"
        " VALUES ('{}','{}',%s,%s,%s,%s)"
    ).format(pcid, cid)

    del_sql_global = "delete from synonym_global where src_word = %s"
    insert_sql_global = "INSERT INTO synonym_global(src_word, des_word) VALUES (%s,%s)"

    del_sql_target_unsolved = (
        "DELETE FROM unsolved_targets where pcid = '{}' and cid = '{}' and target = %s"
    ).format(pcid, cid)
    del_sql_target = (
        "DELETE FROM targets where pcid = '{}' and cid = '{}' and target = %s"
    ).format(pcid, cid)
    insert_sql_target_unsolved = (
        "INSERT INTO unsolved_targets(pcid,cid,target,sentences,frequency) VALUES ('{}','{}',%s,%s,%s)"
    ).format(pcid, cid)

    params_del_sql = [[i['word']] for i in unsolved if i not in nomeaning]
    params_insert_sql = []
    params_del_sql_unsolved = []
    params_insert_sql_unsolved = []
    for i in unsolved:
        params_del_sql_unsolved.append([i['word']])
        if i['word'] not in nomeaning:
            params_insert_sql_unsolved.append([i['word'], i['word'], i['frequency'], i['sentences']])

    params_del_sql_global = []
    params_insert_sql_global = []

    params_del_sql_target_unsolved = []
    params_del_sql_target = []

    table = 'targets'
    sql = "select target, tag from {} where pcid = '{}' and cid = '{}'".format(table, pcid, cid)
    df_target_solved = read_data(sql, engine, table)
    targets_solved = df_target_solved['target'].tolist()

    table = 'unsolved_targets'
    sql = "select target, sentences from {} where pcid = '{}' and cid = '{}'".format(table, pcid, cid)
    df = read_data(sql, engine, table)
    df['sentences'].fillna('', inplace=True)
    targets = dict()
    for i, v in df.iterrows():
        targets[v['target']] = v['sentences']
    exists = set(df['target'].tolist())
    r = []
    for i in unsolved:
        if i['word'] not in exists and i['word'] not in nomeaning and i['word'] not in targets_solved:
            r.append([i['word'], i['sentences'], i['frequency'] or default_frequency])
    params_insert_sql_target_unsolved = r

    for des_word in context:
        item = context[des_word]
        src_words = item['srcs']
        is_global = item['global']
        for src_word in src_words:
            params_del_sql.append([src_word])
            if src_word not in nomeaning:
                params_insert_sql.append([src_word, des_word])
            params_del_sql_unsolved.append([src_word])
            params_del_sql_target_unsolved.append([src_word])
            params_del_sql_target.append([src_word])

            if is_global:
                params_del_sql_global.append([src_word])
                params_insert_sql_global.append([src_word, des_word])

        params_del_sql.append([des_word])
        params_del_sql_unsolved.append([des_word])
        params_del_sql_target_unsolved.append([des_word])
        if des_word not in nomeaning and des_word not in targets_solved:
            text = "合并的近义词:" + ",".join(src_words)
            t = targets.get(des_word)
            if t:
                if '合并的近义词:' in t:
                    index = t.find('合并的近义词:')
                    t = t[:index]
                    t = t.rstrip(';')
                text = '{};{}'.format(t, text) if t else text
            params_insert_sql_target_unsolved.append([des_word, text, default_frequency])

    table = 'synonym'
    sql = "select src_word, des_word from {} where pcid = '{}' and cid = '{}'".format(table, pcid, cid)
    df = read_data(sql, engine, table)
    insert_synonym = [i[0] for i in params_insert_sql]
    del_synonym = [i[0] for i in params_del_sql if i[0] not in insert_synonym]
    insert_targets = [i[0] for i in params_insert_sql_target_unsolved]

    df = df[df['src_word'].isin(del_synonym)]
    for i in set(df['des_word'].tolist()):
        if i in insert_targets or i in nomeaning:
            continue

        params_del_sql_target_unsolved.append([i])
        params_insert_sql_target_unsolved.append([i, '', default_frequency])

    # 删除已处理的近义词中重复的
    if params_del_sql:
        db_psql(engine, del_sql, params=params_del_sql)
    # 插入新的近义词合并结果
    if params_insert_sql:
        db_psql(engine, insert_sql, params=params_insert_sql)
    # 清理未处理的近义词
    if params_del_sql_unsolved:
        db_psql(engine, del_sql_unsolved, params=params_del_sql_unsolved)
    # 插入未处理的近义词
    if params_insert_sql_unsolved:
        db_psql(engine, insert_sql_unsolved, params=params_insert_sql_unsolved)
    # 清理未处理的target中合并的
    if params_del_sql_target_unsolved:
        db_psql(engine, del_sql_target_unsolved, params=params_del_sql_target_unsolved)
    # 插入合并后的target
    if params_insert_sql_target_unsolved:
        db_psql(engine, insert_sql_target_unsolved, params=params_insert_sql_target_unsolved)
    # 清理已处理的target中合并的
    if params_del_sql_target:
        db_psql(engine, del_sql_target, params=params_del_sql_target)
    # 删除全局近义词词库中重复的
    if params_del_sql_global:
        db_psql(engine, del_sql_global, params=params_del_sql_global)
    # 插入新加的全局近义词
    if params_insert_sql_global:
        db_psql(engine, insert_sql_global, params=params_insert_sql_global)


def get_unsolved_targets_size(cid):
    sql = "select count(*) from unsolved_targets where cid = '{}' ".format(cid)
    rows = db_99_get("lexicon", sql)
    if rows:
        size = rows[0][0]
    else:
        size = -1
    return size


if __name__ == '__main__':
    t = get_table_size_v2('raw_tb_comment_notag', "raw_comment_pcid100.raw_tb_comment2018101911")
    print(t)
