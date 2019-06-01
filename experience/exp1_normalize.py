# -*- coding: utf-8 -*-

"""
2019/06/01
本文认为如果某个的词没有被少部分行业包含，相应减少其平均值计算时的行业数量，可以更好的反应其平均词频。
但如果某个的词没有被大部分行业包含，其平均词频应使用真实值。
"""

import matplotlib.pyplot as plt


def show(x, y):
    plt.plot(x, y)
    # plt.plot(y)
    plt.show()


def power12(base):
    size = 10000
    x, y = list(), list()
    for i in range(0, size+1):
        t = i / size
        x.append(t)
        y.append(t**base)
    show(x, y)


def power12cid7913(base):
    size = 7913
    use = 913
    x, y = list(), list()
    for i in range(0, size+1):
        t = i / size
        x.append(t)
        t = t**base * use + (size - use)
        y.append(t)
    show(x, y)


if __name__ == '__main__':
    base = 12
    power12(base)
    power12cid7913(base)
