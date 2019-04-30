# -*- coding: utf-8 -*-

from new_reviews.lexicon.lexicon import GetLexicon
from new_reviews.process.readDB import *


class Filter(object):
    def __init__(self, pcid, cid):
        lexicon = GetLexicon()
        lexicon.read_all(pcid)
        self.lex_words = lexicon.get_words()
        self.frequency = get_word_frequency(pcid, cid)

        self.noise = set()

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
                       if v not in self.lex_words and v not in self.noise]
            for inx in indices:
                flag = False
                for ch in words[inx]:
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
