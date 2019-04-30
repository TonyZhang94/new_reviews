# -*- coding: utf-8 -*-

"""
2019/04/21
1-1000 汉字数字 字母表
增加：年份1978-2050
"""

words = list()

for i in range(0, 1001):
    words.append(str(i))

words.append("零")
words.append("〇")
nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
for i in nums:
    words.append(i)
for i in nums:
    if "一" == i:
        pre = ""
    else:
        pre = i
    words.append(pre+"十")
    for j in nums:
        words.append(pre+"十"+j)

for i in nums:
    words.append(i+"百")

words.append("一千")

Alpha = [chr(i) for i in range(ord("A"), ord("Z")+1)]
for ch in Alpha:
    words.append(ch)

alpha = [chr(i) for i in range(ord("a"), ord("z")+1)]
for ch in alpha:
    words.append(ch)

num2char = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
for i in range(1900, 2100):
    words.append(str(i))
    year, temp = "", i
    while 0 != temp:
        year = num2char[temp % 10] + year
        temp //= 10
    words.append(year)
    if "零" in year:
        words.append(year.replace("零", "〇"))


with open("lexicon/numsEn.txt", mode="w", encoding="utf-8") as fp:
    for word in words:
        fp.write(f"{word}\n")
