# -*- coding: utf-8 -*-
import datetime
import threading

from new_reviews.process.public import *
from new_reviews.process.cut_words import SPLIT, base
from new_reviews.process.readDB import *
from new_reviews.process.filter import *


def push_data(pcid, cid, msg_queue):
    for rows in get_cut_comments(pcid, cid):
        flag = False
        if 100 == msg_queue.qsize():
            print("队列已满")
            flag = True
            START = datetime.datetime.now()
        print("push了一次", len(rows))
        msg_queue.put(rows)
        if flag:
            END = datetime.datetime.now()
            print("push队列等待时间：", END - START)
    msg_queue.put(None)


def front_data(msg_queue, model):
    flag = False
    if 0 == msg_queue.qsize():
        print("队列为空")
        flag = True
        START = datetime.datetime.now()
    rows = msg_queue.get()
    if flag:
        END = datetime.datetime.now()
        print("push队列等待时间：", END - START)
    if rows is None:
        return None

    data = model.parse(rows)
    del rows
    return data


class OpinionExtraction(threading.Thread):
    def __init__(self, msg_queue, **kwargs):
        super(OpinionExtraction, self).__init__()
        self.pcid = kwargs["pcid"]
        self.cid = kwargs["cid"]
        self.is_add = kwargs["is_add"]  # True 为第二步抽取属性，False为第四步 终处理
        self.src_table = kwargs["src_table"]
        self.dst_table = kwargs["dst_table"]
        self.msg_queue = msg_queue
        try:
            self.limit = kwargs["limit"]
        except KeyError:
            self.limit = None
        try:
            self.threshold = kwargs["threshold"]
        except KeyError:
            self.threshold = WORD_NUM_THRESHOLD

        self.feature_frequency = dict()
        self.features = set()
        # self.opinions = dict()
        # self.O_Seed = dict()
        self.O_Map = dict()
        self.T_Seed = dict()
        self.ml_text = dict()
        self.ml_text_sample = dict()
        self.NewDBData = dict()
        self.NewDBData_Filtered = dict()

        self.frequency_t_o = dict()
        self.omit = dict()
        if STASFTRE:
            self.frequency_to = dict()
            self.frequency_t = dict()
            self.frequency_o = dict()
        """
        {"feature_frequency": feature_frequency,    {itemid: {feature: { opinion: frequency }}}
        "features": features,    set(target_word)
        "opinions": opinions,    {opinion_word, sentiment}
        "O_Seed": O_Seed,        {opinion_word, sentiment}
        "O_Map": O_Map,          {}
        "T_Seed": T_Seed,        {target_word: tag}
        "ml_text": ml_text,      {word: [相关评价]}
        "NewDBData": NewDBData}  {"itemid":[(comment_id,comment_date,opinions,target)]}
        """
        self.result = None

        self.win = 4  # max + 1
        lexicon = GetLexicon()
        lexicon.read_all(self.pcid)
        self.bounder = lexicon.get_bounder()
        self.opinions = lexicon.get_opinions()
        self.O_Seed = copy.copy(self.opinions)
        self.adverse = lexicon.get_adverse()
        self.new_adverse = dict()

    def find_pair(self, words, center):
        # 观点词前有否定词，如果库里没有，要加进去
        front, back = True, True
        inx = 0
        opi = ""
        for offset in range(1, self.win):
            if front:
                inx = center - offset
                if inx < 0 or words[inx] in self.bounder:
                    front = False
                else:
                    if words[inx] in self.opinions:
                        opi = words[inx]
                        break

            if back:
                inx = center + offset
                if inx >= len(words) or words[inx] in self.bounder:
                    back = False
                else:
                    if words[inx] in self.opinions:
                        opi = words[inx]
                        break

        index = inx
        if words[center] not in self.ml_text or len(self.ml_text[words[center]]) < 100:
            text = ""
            for inx in range(center - 3, center + 4):
                if inx < 0 or inx >= len(words):
                    continue
                text += words[inx]
            self.ml_text.setdefault(words[center], set()).add(text)

        if opi and back and index - 1 >= 0 and words[index - 1] in self.adverse:
            word = words[index - 1] + words[index]
            opi = word
            if word not in self.opinions:
                if 1 == self.opinions[words[index]]:
                    self.opinions[word] = -1
                    self.new_adverse[word] = -1
                elif -1 == self.opinions[words[index]]:
                    self.opinions[word] = 1
                    self.new_adverse[word] = 1
                elif 0 == self.opinions[words[index]]:
                    self.opinions[word] = 0
                    self.new_adverse[word] = 0
                elif 2 == self.opinions[words[index]]:
                    self.opinions[word] = 2
                    self.new_adverse[word] = 2
                else:
                    raise Exception("Unexpected Sentiment Orientation")

        return opi

    def make_result_is_add_stas(self, row, inx, opi):
        try:
            self.feature_frequency[row[0]][row[3][inx]][opi] += 1
        except KeyError:
            if row[0] not in self.feature_frequency:
                self.feature_frequency[row[0]] = dict()
                self.feature_frequency[row[0]][row[3][inx]] = dict()
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1
            elif row[3][inx] not in self.feature_frequency[row[0]]:
                self.feature_frequency[row[0]][row[3][inx]] = dict()
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1
            else:
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1

        try:
            self.frequency_t_o[row[3][inx]][opi] = \
                self.frequency_t_o[row[3][inx]].setdefault(opi, 0) + 1
        except KeyError:
            self.frequency_t_o[row[3][inx]] = dict()
            self.frequency_t_o[row[3][inx]][opi] = 1

        self.frequency_to[f"{row[3][inx]}-{opi}"] = self.frequency_to.setdefault(f"{row[3][inx]}-{opi}", 0) + 1
        self.frequency_t[row[3][inx]] = self.frequency_t.setdefault(row[3][inx], 0) + 1
        self.frequency_o[row[3][inx]] = self.frequency_o.setdefault(row[3][inx], 0) + 1

    def make_result_is_add(self, row, inx, opi):
        try:
            self.feature_frequency[row[0]][row[3][inx]][opi] += 1
        except KeyError:
            if row[0] not in self.feature_frequency:
                self.feature_frequency[row[0]] = dict()
                self.feature_frequency[row[0]][row[3][inx]] = dict()
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1
            elif row[3][inx] not in self.feature_frequency[row[0]]:
                self.feature_frequency[row[0]][row[3][inx]] = dict()
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1
            else:
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1

        try:
            self.frequency_t_o[row[3][inx]][opi] = \
                self.frequency_t_o[row[3][inx]].setdefault(opi, 0) + 1
        except KeyError:
            self.frequency_t_o[row[3][inx]] = dict()
            self.frequency_t_o[row[3][inx]][opi] = 1

    def make_result_not_add_stas(self, row, inx, opi):
        try:
            self.feature_frequency[row[0]][row[3][inx]][opi] += 1
        except KeyError:
            if row[0] not in self.feature_frequency:
                self.feature_frequency[row[0]] = dict()
                self.feature_frequency[row[0]][row[3][inx]] = dict()
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1
            elif row[3][inx] not in self.feature_frequency[row[0]]:
                self.feature_frequency[row[0]][row[3][inx]] = dict()
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1
            else:
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1

        self.NewDBData.setdefault(row[0], list()).append((row[1], row[2], opi, row[3][inx]))

        try:
            self.frequency_t_o[row[3][inx]][opi] = \
                self.frequency_t_o[row[3][inx]].setdefault(opi, 0) + 1
        except KeyError:
            self.frequency_t_o[row[3][inx]] = dict()
            self.frequency_t_o[row[3][inx]][opi] = 1

        self.frequency_to[f"{row[3][inx]}-{opi}"] = self.frequency_to.setdefault(f"{row[3][inx]}-{opi}", 0) + 1
        self.frequency_t[row[3][inx]] = self.frequency_t.setdefault(row[3][inx], 0) + 1
        self.frequency_o[row[3][inx]] = self.frequency_o.setdefault(row[3][inx], 0) + 1

    def make_result_not_add(self, row, inx, opi):
        try:
            self.feature_frequency[row[0]][row[3][inx]][opi] += 1
        except KeyError:
            if row[0] not in self.feature_frequency:
                self.feature_frequency[row[0]] = dict()
                self.feature_frequency[row[0]][row[3][inx]] = dict()
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1
            elif row[3][inx] not in self.feature_frequency[row[0]]:
                self.feature_frequency[row[0]][row[3][inx]] = dict()
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1
            else:
                self.feature_frequency[row[0]][row[3][inx]][opi] = 1

        self.NewDBData.setdefault(row[0], list()).append((row[1], row[2], opi, row[3][inx]))

        try:
            self.frequency_t_o[row[3][inx]][opi] = \
                self.frequency_t_o[row[3][inx]].setdefault(opi, 0) + 1
        except KeyError:
            self.frequency_t_o[row[3][inx]] = dict()
            self.frequency_t_o[row[3][inx]][opi] = 1

    def show(self):
        for itemid, value in self.feature_frequency.items():
            print(itemid, value)
        for k, v in self.NewDBData_Filtered.items():
            print(k, v)
        for k, v in self.frequency_t_o.items():
            print(k, v)
        for k, v in self.ml_text_sample.items():
            print(k, v)

        if STASFTRE:
            for k, v in self.frequency_to.items():
                print(k, v)
            for k, v in self.frequency_t.items():
                print(k, v)
            for k, v in self.frequency_o.items():
                print(k, v)

    def make_threshold(self):
        if self.limit is not None:
            print("LIMIT Has Set", self.limit)
            return
        temp = list()
        for tar, opis in self.frequency_t_o.items():
            for opi, freq in opis.items():
                temp.append([tar, opi, freq])
        temp.sort(key=lambda x: x[2], reverse=True)
        if len(temp) < self.threshold:
            self.limit = 10
        else:
            self.limit = temp[self.threshold][2]
        print("Set LIMIT", self.limit)

    def remove(self):
        for tar, opis in self.frequency_t_o.items():
            for opi, freq in opis.items():
                if freq < self.limit:
                    self.omit.setdefault(tar, set()).add(opi)

        for tar, opis in self.omit.items():
            for opi in opis:
                del self.frequency_t_o[tar][opi]
            if 0 == len(self.frequency_t_o[tar]):
                del self.frequency_t_o[tar]
                del self.ml_text[tar]

        feature_frequency_bak = copy.deepcopy(self.feature_frequency)
        for itemid, tars in feature_frequency_bak.items():
            for tar, opis in tars.items():
                if tar not in self.omit:
                    continue
                for opi in opis.keys():
                    if opi in self.omit[tar]:
                        del self.feature_frequency[itemid][tar][opi]
                if 0 == len(self.feature_frequency[itemid][tar]):
                    del self.feature_frequency[itemid][tar]
            if 0 == len(self.feature_frequency[itemid]):
                del self.feature_frequency[itemid]
        del feature_frequency_bak

        for itemid, records in self.NewDBData.items():
            for record in records:
                if record[3] not in self.omit:
                    self.NewDBData_Filtered.setdefault(itemid, list()).append(copy.copy(record))
                elif record[2] not in self.omit[record[3]]:
                    self.NewDBData_Filtered.setdefault(itemid, list()).append(copy.copy(record))
                else:
                    # print("删除记录", record)
                    pass
        del self.NewDBData

    def get_ml_text(self):
        size = 10
        for word, texts in self.ml_text.items():
            for rank, text in enumerate(texts, start=1):
                self.ml_text_sample.setdefault(word, list()).append(text)
                if size == rank:
                    break

    def add_new_adverse(self):
        pos = open(f"{NEW_REVIEW_PATH}/lexicon/opi_pos_adv.txt", mode="a", encoding="utf-8")
        neu = open(f"{NEW_REVIEW_PATH}/lexicon/opi_neu_adv.txt", mode="a", encoding="utf-8")
        neg = open(f"{NEW_REVIEW_PATH}/lexicon/opi_neg_adv.txt", mode="a", encoding="utf-8")
        vague = open(f"{NEW_REVIEW_PATH}/lexicon/vague_adv.txt", mode="a", encoding="utf-8")

        for word, sen in self.new_adverse.items():
            # print(f"write {word} {sen}")
            if 1 == sen:
                pos.write(f"{word}\r\n")
            elif 0 == sen:
                neu.write(f"{word}\r\n")
            elif -1 == sen:
                neg.write(f"{word}\r\n")
            elif 2 == sen:
                vague.write(f"{word}\r\n")
            else:
                raise Exception("Unexpected Sentiment Orientation")

    def run(self):
        model = Filter(self.pcid, self.cid, self.is_add)
        if not self.is_add:
            if STASFTRE:
                make_result = self.make_result_not_add_stas
            else:
                make_result = self.make_result_not_add
        else:
            if STASFTRE:
                make_result = self.make_result_is_add_stas
            else:
                make_result = self.make_result_is_add

        rank = 0
        while True:
            data = front_data(self.msg_queue, model)
            if data is None:
                break

            # 0 itemid 1 comment_id 2 datamonth 3 words 4 targets 5 indices
            for row in data:
                for inx in row[5]:
                    self.features.add(row[3][inx])
                    opi = self.find_pair(row[3], inx)
                    make_result(row, inx, opi)
            del data
            rank += 1
            print(f"第{rank}轮完成，each size={ANA_CHUNKSIZE}")

        model.save_noise()

        lexicon = GetLexicon()
        lexicon.read_all(self.pcid)
        self.opinions = lexicon.opinions
        # self.O_Seed = self.opinions
        # self.O_Map = {}
        self.T_Seed = get_target_seed(self.pcid, self.cid)

        self.make_threshold()
        self.remove()
        self.get_ml_text()
        self.add_new_adverse()
        # self.show()
        # 合并同义词

        # IsNoise = {word: True for word in self.frequency_t_o.keys()}
        """
        {"feature_frequency": feature_frequency,    {itemid: {feature: { opinion: frequency }}}
        "features": features,    set(target_word)
        "opinions": opinions,    {opinion_word, sentiment}
        "O_Seed": O_Seed,        {opinion_word, sentiment}
        "O_Map": O_Map,          {}
        "T_Seed": T_Seed,        {target_word: tag}
        "ml_text": ml_text,      {word: [相关评价]}
        "NewDBData": NewDBData}  {"itemid":[(comment_id,comment_date,opinions,target)]}
        """
        self.result = {
            "feature_frequency": self.feature_frequency,
            "features": self.features,
            "opinions": self.opinions,
            "O_Seed": self.O_Seed,
            "O_Map": self.O_Map,
            "T_Seed": self.T_Seed,
            "ml_text": self.ml_text_sample,
            "NewDBData": self.NewDBData_Filtered
        }

    def get_result(self):
        return self.result


if __name__ == '__main__':
    pass
    """
    之后：

    1. 通用词会漏
    opi_neu，新词整理

    通用
    先放开，后面写进 not_comment

    2. 功能，质量，护理，速度，时间，之类的词进行拓展
    一个字的词合并

    3. 颜色词为target

    4. TF-IDF                                                                         晚上多跑几个品类cut_words
    ***TF

    暂不考虑：
    app，APP大小写问题
    没有主语，迷你，小巧玲珑
    
    其他：
    adv是否不需要重新载入


    """
