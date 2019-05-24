# -*- coding: utf-8 -*-

import _pickle as pickle

from new_reviews.process.public import *


def load_cidname():
    try:
        with open("cidname.pkl", mode="rb") as fp:
            ciddict = pickle.load(fp)
        print("读取本地cidname.pkl")
    except FileNotFoundError:
        print("从数据库读取数据，请稍等 ...")
        ciddict = dict()
        sql = "SELECT * FROM basics.mj_cid_tree;"
        df = pd.read_sql(sql, engine("chu"))
        for k, v in df.iterrows():
            pcid, pcidname = v["pcid"], v["pcidname"]

            cid, cidname = v["c1id"], v["c1idname"]
            if cid is not None and 0 != len(cid):
                info = [pcid, pcidname, cid, cidname, "c1id"]
                if cid in ciddict:
                    if cidname != ciddict[cid][3]:
                        print(f"{cid} has included in ciddict")
                        print("ciddict info:", ciddict[cid])
                        print("present info:", info)
                else:
                    ciddict[cid] = info

            cid, cidname = v["c2id"], v["c2idname"]
            if cid is not None and 0 != len(cid):
                info = [pcid, pcidname, cid, cidname, "c2id"]
                if cid in ciddict:
                    if cidname != ciddict[cid][3]:
                        print(f"{cid} has included in ciddict")
                        print("ciddict info:", ciddict[cid])
                        print("present info:", info)
                else:
                    ciddict[cid] = info

            cid, cidname = v["c3id"], v["c3idname"]
            if cid is not None and 0 != len(cid):
                info = [pcid, pcidname, cid, cidname, "c3id"]
                if cid in ciddict:
                    if cidname != ciddict[cid][3]:
                        print(f"{cid} has included in ciddict")
                        print("ciddict info:", ciddict[cid])
                        print("present info:", info)
                else:
                    ciddict[cid] = info

            cid, cidname = v["c4id"], v["c4idname"]
            if cid is not None and 0 != len(cid):
                info = [pcid, pcidname, cid, cidname, "c4id"]
                if cid in ciddict:
                    if cidname != ciddict[cid][3]:
                        print(f"{cid} has included in ciddict")
                        print("ciddict info:", ciddict[cid])
                        print("present info:", info)
                else:
                    ciddict[cid] = info

        print("结果存入本地cidname.pkl")
        with open("cidname.pkl", mode="wb") as fp:
            pickle.dump(ciddict, fp)

    return ciddict


def make_result(warning_threshold1=1e5, warning_threshold2=5e3):
    pcids = list()
    # pcids.append("0")
    pcids.append("1")
    pcids.append("2")
    pcids.append("3")
    pcids.append("4")
    # pcids.append("5")
    # pcids.append("6")
    # pcids.append("7")
    # pcids.append("8")
    # pcids.append("9")
    # pcids.append("10")
    # pcids.append("11")
    # pcids.append("12")
    # pcids.append("13")
    # pcids.append("100")

    columns = ["pcid", "pcidname", "cid", "cidname", "cidtype", "comment_num", "word_num"]
    cidname = load_cidname()
    for the_pcid in pcids:
        records = list()
        with open("freq_stas.txt", mode="r", encoding="utf-8") as fp:
            for line in fp.readlines():
                _, pcid, _, cid, _, comment_num, _, word_num, _, _ = line.strip().split()
                comment_num, word_num = int(comment_num), int(word_num)
                if pcid != the_pcid:
                    continue
                try:
                    record = [pcid, cidname[cid][1], cid, cidname[cid][3], cidname[cid][4], comment_num, word_num]
                    records.append(copy.copy(record))
                except KeyError:
                    if comment_num >= warning_threshold1 or word_num >= warning_threshold2:
                        print("Not Find:", [pcid, cid, comment_num, word_num])

        df = pd.DataFrame(records, columns=columns)
        df = df.sort_values(["comment_num", "word_num"], ascending=False).reset_index(drop=True)
        df.to_csv(f"info_pcid{the_pcid}.csv", encoding=UTF8)


if __name__ == '__main__':
    make_result()
