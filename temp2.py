# -*- coding: utf-8 -*-

"""
2019/05/16
迁移cut_new表
"""

import datetime
import time

from new_reviews.process.public import *


def migrate(tasks):
    engine114 = sa.create_engine("postgresql://{USER}:{PASS}@{HOST}:{PORT}/{DB}".
                                 format(USER="zczx_write",
                                        PASS="zczxTech2012",
                                        HOST="192.168.1.114",
                                        PORT=5432,
                                        DB="tb_comment_words")
                                 )

    schema_base, table_base = "raw_comment_pcid{pcid}", "raw_tb_comment{cid}_cut_new"
    sql_base = "SELECT * FROM {schema}.{table}"
    # del_base = "DELETE raw_comment_pcid{pcid}.raw_tb_comment{cid}_cut_new"
    for task in tasks:
        pcid, cid = task
        schema, table = schema_base.format(pcid=pcid), table_base.format(cid=cid)
        sql = sql_base.format(schema=schema, table=table)
        rank = 1
        for df in pd.read_sql_query(sql, con=engine("raw_tb_comment_notag"), chunksize=10000):
            df.to_sql(name=table, con=engine114, schema=schema, index=False, if_exists="append")
            print(f"已完成{rank}轮")
            rank += 1


if __name__ == '__main__':
    tasks = list()
    tasks.append(["4", "50228001"])
    migrate(tasks)
