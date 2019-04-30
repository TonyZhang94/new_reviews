# -*- coding: utf-8 -*-

"""
2019/04/22
html字符转义
"""

from urllib import request
from bs4 import BeautifulSoup

# https://www.cnblogs.com/subsir/articles/3374027.html
# https://www.cnblogs.com/yasmi/articles/4884396.html

# /b>
# <b

symbols = list()
def fadd(x):
    symbols.append(x)


url = "https://www.cnblogs.com/subsir/articles/3374027.html"
response = request.urlopen(url=url)
page = response.read()
content = page.decode("utf-8")

soup = BeautifulSoup(content, "lxml")
tables = soup.body.find("div", {"id": "cnblogs_post_body"}).findAll("table")


def get_table0():
    """
    &nbsp|&quot|&amp|&lt|&gt等html字符转义
    :return:
    """
    table = tables[0]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[1].text)
        fadd(tds[2].text)
        fadd(tds[3].text)
        fadd(tds[4].text)


def get_table1():
    """
    iSO 8859-1 characters
    :return:
    """
    table = tables[1]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table2():
    """
    Latin Extended-B
    :return:
    """
    table = tables[2]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table3():
    """
    Arrows
    :return:
    """
    table = tables[3]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table4():
    """
    Mathematical Operators
    :return:
    """
    table = tables[4]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table5():
    """
    General Punctuation
    :return:
    """
    table = tables[5]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table6():
    """
    Miscellaneous Technical
    :return:
    """
    table = tables[6]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table7():
    """
    Geometric Shapes
    :return:
    """
    table = tables[7]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table8():
    """
    Miscellaneous Symbols
    :return:
    """
    table = tables[8]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table9():
    """
    Letterlike Symbols
    :return:
    """
    table = tables[9]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table10():
    """
    Greek
    :return:
    """
    table = tables[10]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table11():
    """
    C0 Controls and Basic Latin
    :return:
    """
    table = tables[11]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table12():
    """
    Latin Extended-A
    :return:
    """
    table = tables[12]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table13():
    """
    Spacing Modifier Letters
    :return:
    """
    table = tables[13]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


def get_table14():
    """
    Spacing Modifier Letters
    :return:
    """
    table = tables[14]
    trs = table.findAll("tr")
    for y, tr in enumerate(trs, start=0):
        if 0 == y:
            continue

        tds = tr.findAll("td")
        fadd(tds[0].text)
        fadd(tds[1].text)


if __name__ == '__main__':
    get_table0()
    get_table1()
    get_table2()
    get_table3()
    get_table4()
    get_table5()
    get_table6()
    get_table7()
    get_table8()
    get_table9()
    get_table10()
    get_table11()
    get_table12()
    get_table13()
    get_table14()
    # print(len(symbols))
    # print(symbols)

    with open("lexicon/htmls.txt", mode="w", encoding="utf-8") as fp:
        for char in symbols:
            fp.write(f"{char}\n")
