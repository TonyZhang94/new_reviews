# -*- coding: utf-8 -*-

"""
2019/04/21
frequency表增加share字段
"""

import datetime
import time

from new_reviews.process.public import *


def execute(tasks):
    base = "SELECT * FROM frequency.{table} order by frequency DESC;"
    for table in tasks:
        print("start to process table", table)
        data = list()
        sql = base.format(table=table)
        df = pd.read_sql(sql, con=engine("lexicon"))
        print("has", len(df), "words")
        print("get ready to analysis...")
        total = df.at[0, "frequency"]
        for k, v in df.iterrows():
            data.append([v["word"], v["frequency"], v["frequency"]/total])

        del df
        df = pd.DataFrame(data, columns=["word", "frequency", "share"])

        print("get ready to replace...")
        df.to_sql(table, con=engine("lexicon"), schema="frequency", index=False, if_exists='replace')


if __name__ == '__main__':
    tasks = list()
    # tasks.append("pcid0cid124086006")
    tasks.append("pcid1cid125104012")
    tasks.append("pcid2cid50008898")
    tasks.append("pcid2cid50008901")
    tasks.append("pcid3cid110808")
    tasks.append("pcid4cid50012097")
    tasks.append("pcid4cid50228001")
    tasks.append("pcid6cid50012440")
    tasks.append("pcid6cid50013857")
    tasks.append("pcid7cid121398012")
    tasks.append("pcid7cid350615")
    tasks.append("pcid8cid121454005")
    tasks.append("pcid9cid50019775")
    tasks.append("pcid10cid50017524")
    tasks.append("pcid13cid261712")
    tasks.append("pcid100cid2018101516")

    execute(tasks)
