# -*- coding: utf-8 -*-

"""
2019/05/18
整理颜色词
"""

import datetime

from new_reviews.process.public import *


# 见lexicon

def replace_synonym(words):
    synonym = {"秦始皇": "汉武帝"}
    for inx in range(len(words)):
        if words[inx] in synonym:
            words[inx] = synonym[words[inx]]


if __name__ == '__main__':
    words = ["我", "秦始皇", "打钱"]
    print(words)
    replace_synonym(words)
    print(words)
