# -*- coding: utf-8 -*-

from new_reviews.lexicon.lexicon import GetLexicon
from new_reviews.process.inverse import Inverse
from new_reviews.process.readDB import *


class Filter(object):
    def __init__(self, pcid, cid, isStep2=False):
        lexicon = GetLexicon()
        lexicon.read_all(pcid)
        self.lex_words = lexicon.get_words()
        self.keyno = lexicon.get_keyno()
        self.frequency = get_word_frequency(pcid, cid)
        self.noise = set()

        self.targets_cid = self.get_target(pcid, cid)
        self.useless_cid = self.get_useless(pcid, cid)
        if isStep2:
            print("is step2 new words set is considered")
            self.new_words = self.get_new_words(pcid, cid)
        else:
            print("is step4 new words set is empty")
            self.new_words = set()

    @staticmethod
    def get_target(pcid, cid):
        sql = f"SELECT DISTINCT target FROM public.targets WHERE pcid='{pcid}' and cid='{cid}';"
        df = pd.read_sql(sql, con=engine("lexicon"))
        print(f"targets {len(df)}")
        return set(df["target"].values)

    @staticmethod
    def get_useless(pcid, cid):
        sql = f"SELECT DISTINCT word FROM public.nomeaning WHERE pcid='{pcid}' and cid='{cid}';"
        df = pd.read_sql(sql, con=engine("lexicon"))
        print(f"no meanings {len(df)}")
        return set(df["word"].values)

    @staticmethod
    def get_new_words(pcid, cid):
        obj = Inverse(pcid, cid)
        records = obj.get_inverse_result()
        new_words = [record[0] for record in records]
        print(f"new words {len(new_words)}")
        return set(new_words)

    def if_reserve(self, word):
        if word in self.targets_cid:
            return True
        if word in self.useless_cid:
            return False
        if word in self.new_words:
            return True
        if word in self.lex_words:
            return False
        if word in self.noise:
            return False
        return True

    def parse(self, rows):
        data = list()
        for row in rows:
            if not row[3]:
                data.append([])
                continue
            record = [row[0], row[1], row[4]]
            words = row[3].split(SPLIT)
            record.append(words)
            record.append(list())
            record.append(list())
            indices = [k for k, v in enumerate(words)
                       if self.if_reserve(v)]
            for inx in indices:
                flag = False
                if words[inx] not in self.targets_cid:
                    for ch in words[inx]:
                        if ch in self.keyno:
                            flag = True
                            break
                        if ch < u'\u4e00' or u'\u9fff' < ch:
                            flag = True
                            break
                if flag is True:
                    self.noise.add(words[inx])
                else:
                    record[4].append(words[inx])
                    record[5].append(inx)
            data.append(record)
        return data

    def save_noise(self, out=False):
        if out:
            for x in self.noise:
                print(x)
        else:
            pass
