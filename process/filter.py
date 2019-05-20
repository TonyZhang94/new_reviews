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
        self.comment_target = lexicon.get_comment_target()
        self.target_opi = lexicon.get_target_opi()
        self.merge_front = lexicon.get_merge_front()
        print("merge front:")
        for word in self.merge_front:
            print(word)
        self.merge_back = lexicon.get_merge_back()
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

    def merge_words(self, indices, words):
        words_back = copy.copy(words)
        new_indices, new_words = list(), list()
        seq = 0  # indices
        seq_offset = 0
        rank = 0  # words
        while True:
            if rank == len(words):
                break
            try:
                inx = indices[seq]
            except IndexError:
                inx = len(words)

            if rank < inx:
                new_words.append(words[rank])
                rank += 1
                continue
            if seq + 1 < len(indices) and indices[seq+1] == inx+1 and words[inx+1] in self.merge_front:
                print("front合并", words[inx], words[inx+1])
                new_indices.append(inx + seq_offset)
                new_words.append(words[inx] + words[inx+1])
                seq += 2
                seq_offset -= 1
                rank += 2
            else:
                new_indices.append(inx + seq_offset)
                new_words.append(words[inx])
                seq += 1
                rank += 1

        # 合并后向
        # for seq in range(len(indices)):
        #     if words[inx] in self.merge_back and seq < len(indices)-1 and indices[seq+1] == inx+1:
        #         print("合并", words[inx], words[inx+1])

        # 一个字合并

        if len(words_back) != len(new_words):
            print(words_back)
            print(new_words)
            print(new_indices)

        return new_indices, new_words

    def if_reserve(self, word):
        if word in self.targets_cid:
            return True
        if word in self.new_words:
            return True
        if word in self.comment_target:
            return True
        if word in self.target_opi:
            return True
        if word in self.useless_cid:
            return False
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
            indices, words = self.merge_words(indices, words)
            for inx in indices:
                flag = False
                if words[inx] not in self.targets_cid and words[inx] not in self.new_words \
                        and words[inx] not in self.comment_target and words[inx] not in self.target_opi:
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
            if out:
                path = f"{NEW_REVIEW_PATH}/lexicon/"
                with open(f"{path}noise.txt", mode="w", encoding="utf-8") as fp:
                    for x in self.noise:
                        fp.write(f"{x}\r\n")
        else:
            pass


if __name__ == '__main__':
    obj = Filter(pcid="4", cid="50228001")
    res = obj.if_reserve("质量")
    print(res)
