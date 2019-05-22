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
        self.merge_back = lexicon.get_merge_back()
        self.frequency = get_word_frequency(pcid, cid)
        self.noise = set()

        self.targets_cid = self.get_target(pcid, cid)
        self.synonym = self.get_synonym(pcid, cid)
        self.useless_cid = self.get_useless(pcid, cid)
        self.isStep2 = isStep2
        if isStep2:
            print("is step2 new words set is considered")
            self.new_words = self.get_new_words(pcid, cid)
        else:
            # print("is step4 new words set is empty")
            # self.new_words = set()
            print("is step4 new words set use to filter")
            self.new_words = self.get_new_words(pcid, cid)

    @staticmethod
    def get_target(pcid, cid):
        sql = f"SELECT DISTINCT target FROM public.targets WHERE pcid='{pcid}' and cid='{cid}';"
        df = pd.read_sql(sql, con=engine("lexicon"))
        print(f"targets {len(df)}")
        return set(df["target"].values)

    @staticmethod
    def get_synonym(pcid, cid):
        synonym = dict()
        sql = f"SELECT src_word, des_word FROM public.synonym_global;"
        df = pd.read_sql(sql, con=engine("lexicon"))
        len_global = len(df)
        for k, v in df.iterrows():
            synonym[v["src_word"]] = v["des_word"]
        del df

        sql = f"SELECT src_word, des_word FROM public.synonym WHERE pcid='{pcid}' and cid='{cid}';"
        df = pd.read_sql(sql, con=engine("lexicon"))
        len_cid = len(df)
        for k, v in df.iterrows():
            synonym[v["src_word"]] = v["des_word"]
        del df

        print("synonym global num:", len_global)
        print("synonym cid num:", len_cid)
        print("merge num:", len(synonym))

        return synonym

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
        # 合并前向
        # words_back = copy.copy(words)
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
            if seq + 1 < len(indices) and indices[seq + 1] == inx + 1 and words[inx+1] in self.merge_front:
                # print("front合并", words[inx], words[inx+1])
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
        indices, words = copy.copy(new_indices), copy.copy(new_words)
        indices_bak = copy.copy(indices)
        words_bak = copy.copy(words)
        del new_indices
        del new_words
        new_indices, new_words = list(), list()
        new_indices_append, new_words_append = list(), list()
        seq = 0  # indices
        # seq_offset = 0
        rank = 0  # words
        tail = len(words) - 1  # 末位下标

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

            # 逻辑2
            # 单字合并后面的词
            # 非单字合并后面的单字

            # 逻辑1
            if 1 == len(words[inx]):
                # print("删除单字", words[inx])
                if 0 < seq and indices[seq - 1] == inx - 1 and 1 != len(words[inx-1]):
                    # print("单字front合并", words[inx - 1], words[inx])
                    start = max(0, inx - 4)
                    end = min(len(words), inx + 4)
                    new_words_append.append("#")
                    tail += 1
                    for i in range(start, end):
                        if i == inx - 1:
                            new_indices_append.append(tail + 1)
                            new_words_append.append(words[inx - 1] + words[inx])
                        elif i == inx:
                            continue
                        else:
                            new_words_append.append(words[i])
                        tail += 1

                if seq + 1 < len(indices) and indices[seq + 1] == inx + 1:
                    # print("单字back合并", words[inx], words[inx + 1])
                    start = max(0, inx - 3)
                    end = min(len(words), inx + 5)
                    new_words_append.append("#")
                    tail += 1
                    for i in range(start, end):
                        if i == inx:
                            new_indices_append.append(tail + 1)
                            new_words_append.append(words[inx] + words[inx + 1])
                        elif i == inx + 1:
                            continue
                        else:
                            new_words_append.append(words[i])
                        tail += 1

                new_words.append(words[inx])
                seq += 1
                # seq_offset -= 1
                rank += 1

            else:
                # new_indices.append(inx + seq_offset)
                new_indices.append(inx)
                new_words.append(words[inx])
                seq += 1
                rank += 1

        new_indices.extend(new_indices_append)
        new_words.extend(new_words_append)

        self.single_rank = 0
        for inx in new_indices:
            if 1 == len(new_words[inx]):
                print("\n")
                print(words_bak)
                print(indices_bak)
                print(new_words)
                print(new_indices)
                print(inx, new_words[inx])
                self.single_rank += 1
                if self.single_rank > 5:
                    exit()

        # if len(words_bak) != len(new_words):
        #     print(words_back)
        #     print(new_words)
        #     print(new_indices)
        #     print("merge:")
        #     for inx in new_indices_append:
        #         print(inx, new_words[inx])

        return new_indices, new_words

    def if_reserve_step2(self, word):
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

    def if_reserve_step4(self, word):
        if word in self.useless_cid:
            return False
        if word in self.targets_cid:
            return True
        if word in self.new_words:
            return True
        if word in self.comment_target:
            return True
        if word in self.target_opi:
            return True
        if word in self.lex_words:
            return False
        if word in self.noise:
            return False
        return True

    def replace_synonym(self, words):
        for inx in range(len(words)):
            if words[inx] in self.synonym:
                words[inx] = self.synonym[words[inx]]

    def parse(self, rows):
        if self.isStep2:
            if_reserve = self.if_reserve_step2
        else:
            if_reserve = self.if_reserve_step4
        data = list()
        for row in rows:
            if not row[3]:
                data.append([])
                continue
            record = [row[0], row[1], row[4]]
            words = row[3].split(SPLIT)

            self.replace_synonym(words)
            indices = [k for k, v in enumerate(words)
                       if if_reserve(v)]

            # indices, words = self.merge_words(indices, words)
            # self.replace_synonym(words)

            # record.append(words)
            # record.append(list())
            # record.append(list())

            temp_indices = list()
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
                    # record[4].append(words[inx])
                    # record[5].append(inx)
                    temp_indices.append(inx)

            indices, words = self.merge_words(temp_indices, words)
            self.replace_synonym(words)

            record.append(words)
            record.append(list())  # targets 无用
            record.append(indices)
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
