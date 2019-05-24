# -*- coding: utf-8 -*-

import os


def delete_and_create_linxu_file():
    linux_file = [
        "opi_neg_adv",
        "opi_neu_adv",
        "opi_pos_adv",
        "vague_adv",
        "opi_neg_manu",
        "opi_neu_manu",
        "opi_pos_manu",
        "vague_manu",
        "words_manu",
        "comment_not_target"
    ]

    for file in linux_file:
        try:
            os.remove(f"{file}.txt")
        except FileNotFoundError:
            pass
        with open(f"{file}.txt", mode="a+", encoding="utf-8") as fp:
            pass


def change_n2rn():
    files = ["adverse",
             "adverse_db",  # not real adverse
             "comment_not_target",
             "comment_opinion",
             "degree",
             "emji",
             "emji1",
             "geography",
             "how_deg",
             "how_neg_com",
             "how_neg_sen",
             "how_opinion",
             "how_pos_com",
             "how_pos_sen",
             "htmls",
             "keyno",
             "nomeanings",
             "numsEn",
             "opi_error",
             "sales",
             "special_chars",
             "stops",
             "symbols",
             "vague",
             "vague_adv",
             "vague_manu",
             "words",
             "words_manu",

             "gopi_neg",
             "opi_neg",
             "opi_neg_adv",
             "opi_neg_manu",
             "opi_neg_pre",
             "gopi_neu",
             "opi_neu",
             "opi_neu_adv",
             "opi_neu_manu",
             "gopi_pos",
             "opi_pos",
             "opi_pos_adv",
             "opi_pos_manu",
             "opi_pos_pre"
             ]

    files.append("comment_opinion_withFreq")
    files.append("comment_target")
    files.append("comment_target_withFreq")
    files.append("merge_back")
    files.append("merge_front")
    files.append("target_opi")
    files.append("find")
    # 缺 运行日志，lexicon.py，__init.py__
    # print(len(files))
    # print(len(set(files)))
    # exit()

    for file in files:
        records = list()
        with open(f"{file}.txt", mode="r", encoding="utf-8") as fp:
            for line in fp.readlines():
                records.append(line.strip())

        with open(f"{file}.txt", mode="w", encoding="utf-8") as fp:
            for record in records:
                fp.write(f"{record}\r\n")


if __name__ == '__main__':
    delete_and_create_linxu_file()
    change_n2rn()
