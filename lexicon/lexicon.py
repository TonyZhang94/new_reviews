# -*- coding: utf-8 -*-

from new_reviews.process.readDB import *


# 地理名词，国家，城市，省份，等
# html转义符
class GetLexicon(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            print("Creating Lexicon Singleton ...")
            cls.instance = super().__new__(cls)
        return cls.instance

    def __init__(self):
        self.words_files = [
            "adverse",
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
        self.opinion_file = [
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

        self.store = None
        self.words = None
        self.opinions = None
        self.tar_opi = None
        self.chars = None
        self.bounder = None

        self.path = f"{NEW_REVIEW_PATH}/lexicon/"

    def read(self, file):
        self.store[file] = set()
        with open(f"{self.path}{file}.txt", mode="r", encoding="utf-8") as fp:
            for line in fp.readlines():
                self.store[file].add(line.strip())
        self.words |= self.store[file]

    def read_opinion(self, file):
        if "pos" in file:
            sen = 1
        elif "neu" in file:
            sen = 0
        elif "neg" in file:
            sen = -1
        else:
            raise Exception("非法情感文件")
        with open(f"{self.path}{file}.txt", mode="r", encoding="utf-8") as fp:
            for line in fp.readlines():
                word = line.strip()
                if word in self.store["vague"]:
                    continue
                if word not in self.opinions:
                    self.opinions[word] = sen
                elif self.opinions[word] != sen:
                    print("情感冲突", file, word)

    def opinion_override(self, cur_pcid):
        # 建立 tar_opi
        for word in self.store["vague"]:
            self.opinions[word] = 2

        for word in self.store["vague_adv"]:
            self.opinions[word] = 2

        for word in self.store["vague_manu"]:
            self.opinions[word] = 2

        tasks = [["gopi_pos", 1], ["gopi_neu", 0], ["gopi_neg", -1]]
        for task in tasks:
            file, sen = task
            with open(f"{self.path}{file}.txt", mode="r", encoding="utf-8") as fp:
                for line in fp.readlines():
                    word = line.strip()
                    if word not in self.opinions:
                        self.opinions[word] = sen
                    elif self.opinions[word] != sen:
                        # print("global覆盖重写", file, word, sen)
                        self.opinions[word] = sen
                    elif self.opinions[word] == sen:
                        pass
                        # print("与global一致", file, word, sen)
                    else:
                        raise Exception("未知情况")

        pcids = [str(pcid) for pcid in range(0, 14)
                 if str(pcid) != cur_pcid] + ["100"]

        pcid_special = set()
        for pcid in pcids:
            try:
                df = get_sentiment_pcid(pcid)
            except Exception as e:
                # print(f"sentiment.pcid{pcid}不存在")
                continue
            for k, v in df.iterrows():
                opi1, opi2, sen = v["opinion"], v["merge"], v["grade"]
                for opi in [opi for opi in [opi1, opi2] if opi == opi]:
                    if opi not in pcid_special:
                        pcid_special.add(opi)
                        if opi not in self.opinions:
                            # print(f"pcid{pcid}新添{opi} {sen}")
                            self.opinions[opi] = sen
                        elif self.opinions[opi] != sen:
                            # print(f"pcid{pcid}覆盖重写 {opi} {sen}")
                            self.opinions[opi] = sen
                        else:
                            # print(f"pcid{pcid}与原先一致 {opi} {sen}")
                            pass
                    else:
                        if self.opinions[opi] != sen:
                            # print(f"pcid{pcid}覆盖重写其他pcid {opi} {sen}")
                            self.opinions[opi] = sen
                        else:
                            # print(f"pcid{pcid}与其他pcid一致 {opi} {sen}")
                            pass

        cid_special = set()
        try:
            df = get_sentiment_pcid(cur_pcid)
        except Exception as e:
            # print(f"sentiment.pcid{cur_pcid}不存在")
            return
        for k, v in df.iterrows():
            opi1, opi2, sen = v["opinion"], v["merge"], v["grade"]
            for opi in [opi for opi in [opi1, opi2] if opi == opi]:
                if opi not in cid_special:
                    cid_special.add(opi)
                    if opi not in self.opinions:
                        # print(f"pcid{cur_pcid}新添{opi} {sen}")
                        self.opinions[opi] = sen
                    elif self.opinions[opi] != sen:
                        # print(f"pcid{cur_pcid}覆盖重写 {opi} {sen}")
                        self.opinions[opi] = sen
                    else:
                        # print(f"pcid{pcid}与原先一致 {opi} {sen}")
                        pass
                else:
                    if self.opinions[opi] != sen:
                        # print(f"pcid{cur_pcid}覆盖重写其他cid {opi} {sen}")
                        self.opinions[opi] = sen
                    else:
                        # print(f"pcid{pcid}与其他pcid一致 {opi} {sen}")
                        pass
        self.opinions[""] = 9

    def opinion_override_1(self, cur_pcid):
        # 建立 tar_opi
        for word in self.store["vague"]:
            self.opinions[word] = 2

        for word in self.store["vague_adv"]:
            self.opinions[word] = 2

        for word in self.store["vague_manu"]:
            self.opinions[word] = 2

        tasks = [["gopi_pos", 1], ["gopi_neu", 0], ["gopi_neg", -1]]
        for task in tasks:
            file, sen = task
            with open(f"{self.path}{file}.txt", mode="r", encoding="utf-8") as fp:
                for line in fp.readlines():
                    word = line.strip()
                    if word not in self.opinions:
                        self.opinions[word] = sen
                    elif self.opinions[word] != sen:
                        # print("global覆盖重写", file, word, sen)
                        self.opinions[word] = sen
                    elif self.opinions[word] == sen:
                        pass
                        # print("与global一致", file, word, sen)
                    else:
                        raise Exception("未知情况")

        pcids = [str(pcid) for pcid in range(0, 14)
                 if str(pcid) != cur_pcid] + ["100"]

        pcid_special = dict()
        for pcid in pcids:
            try:
                df = get_sentiment_pcid(pcid)
            except Exception as e:
                # print(f"sentiment.pcid{pcid}不存在")
                continue
            for k, v in df.iterrows():
                opi1, opi2, sen = v["opinion"], v["merge"], v["grade"]
                for opi in [opi for opi in [opi1, opi2] if opi == opi]:
                    pcid_special[opi] = pcid_special.setdefault(opi, 0) + sen

        cid_special = dict()
        try:
            df = get_sentiment_pcid(cur_pcid)
        except Exception as e:
            df = pd.DataFrame()
        for k, v in df.iterrows():
            opi1, opi2, sen = v["opinion"], v["merge"], v["grade"]
            for opi in [opi for opi in [opi1, opi2] if opi == opi]:
                cid_special[opi] = cid_special.setdefault(opi, 0) + sen

        for opi, score in pcid_special.items():
            if score > 0:
                sen = 1
            elif score < 0:
                sen = -1
            else:
                sen = 0
            if opi not in self.opinions:
                self.opinions[opi] = sen
            else:
                if self.opinions[opi] == sen:
                    # print(f"pcid 与原先一致 {opi} {sen}")
                    pass
                else:
                    # print(f"pcid 覆盖重写 {opi} {sen}， 原先 {self.opinions[opi]}")
                    self.opinions[opi] = sen

        for opi, score in cid_special.items():
            if score > 0:
                sen = 1
            elif score < 0:
                sen = -1
            else:
                sen = 0
            if opi not in self.opinions:
                self.opinions[opi] = sen
            else:
                if self.opinions[opi] == sen:
                    # print(f"cid 与原先一致 {opi} {sen}")
                    pass
                else:
                    # print(f"cid 覆盖重写 {opi} {sen}， 原先 {self.opinions[opi]}")
                    self.opinions[opi] = sen
        self.opinions[""] = 9

    def read_comment_target(self):
        self.store["comment_target"] = set()
        with open(f"{self.path}comment_target.txt", mode="r", encoding="utf-8") as fp:
            for line in fp.readlines():
                word = line.strip()
                self.store["comment_target"].add(word)

    def read_target_opi(self):
        self.store["target_opi"] = set()
        with open(f"{self.path}target_opi.txt", mode="r", encoding="utf-8") as fp:
            for line in fp.readlines():
                word = line.strip()
                self.store["target_opi"].add(word)

    def read_merge_word(self):
        self.store["merge_front"] = set()
        with open(f"{self.path}merge_front.txt", mode="r", encoding="utf-8") as fp:
            for line in fp.readlines():
                word = line.strip()
                self.store["merge_front"].add(word)

        self.store["merge_back"] = set()
        with open(f"{self.path}merge_back.txt", mode="r", encoding="utf-8") as fp:
            for line in fp.readlines():
                word = line.strip()
                self.store["merge_back"].add(word)

    def read_all(self, pcid):
        if self.store is not None:
            print("Lexicon数据已有")
            return

        print("读取Lexicon数据")
        self.store = dict()
        self.words = set()
        self.opinions = dict()
        self.tar_opi = dict()
        self.chars = set()
        self.bounder = set()

        for file in self.words_files:
            self.read(file)
            if file in self.opinion_file:
                self.read_opinion(file)

        self.opinion_override_1(pcid)

        self.chars |= self.store["emji1"]
        self.chars |= self.store["keyno"]
        self.chars |= self.store["numsEn"]
        self.chars |= self.store["special_chars"]
        self.chars |= self.store["symbols"]

        self.bounder |= self.store["symbols"]

        self.read_comment_target()
        self.read_target_opi()
        self.read_merge_word()

    def show(self):
        for file in self.store:
            print(f"{file}有词{len(self.store[file])}个")
        print(f"intersection去重后一共{len(self.words)}个词")
        print(f"opinions一共{len(self.opinions)}个词")

    def clear_all(self):
        del self.store
        del self.words
        del self.opinions
        del self.tar_opi
        del self.chars
        del self.bounder

    def get_words(self):
        return self.words

    def get_opinions(self):
        return self.opinions

    def get_chars(self):
        return self.chars

    def get_bounder(self):
        return self.bounder

    def get_adverse(self):
        return self.store["adverse"]

    def get_keyno(self):
        return self.store["keyno"]

    def get_comment_target(self):
        return self.store["comment_target"]

    def get_target_opi(self):
        return self.store["target_opi"]

    def get_merge_front(self):
        return self.store["merge_front"]

    def get_merge_back(self):
        return self.store["merge_back"]

    def find_word(self, word):
        print("找词", word)
        for file in self.store:
            if word in self.store[file]:
                print(file)

    def find_words(self, words):
        # 找find.txt文件中的
        result = dict()
        for file in self.store:
            for word in words:
                if word in self.store[file]:
                    result.setdefault(file, list()).append(word)
        for word in words:
            find = False
            for k, v in result.items():
                if word in v:
                    find = True
                    break
            if not find:
                result.setdefault("notFind", list()).append(word)
        return result

    def find_key_char(self):
        chars = list()
        chars.append("色")
        chars.append("赤")
        chars.append("红")
        chars.append("朱")
        chars.append("粉")
        chars.append("橙")
        chars.append("橘")
        chars.append("黄")
        chars.append("绿")
        chars.append("青")
        chars.append("蓝")
        chars.append("靛")
        chars.append("紫")
        chars.append("黑")
        chars.append("白")
        chars.append("灰")
        chars.append("金")
        chars.append("银")
        chars.append("深")
        chars.append("墨")
        chars.append("浅")
        chars.append("淡")

        print("颜色词有", len(chars), "个")
        if len(set(chars)) != len(chars):
            print("chars中有重复的")
            return

        files = copy.copy(self.words_files)
        # files.append("comment_target")
        files.append("target_opi")
        print("find key char 有多少文件待查看", len(set(files)))
        # 没有 lexicon.py，__init__.py，find，target_freq，opinion_freq

        count = {char: 0 for char in chars}
        for file in files:
            print(f"\n{file}文件中:")
            num = 0
            with open(f"{self.path}{file}.txt", mode="r", encoding="utf-8") as fp:
                for line in fp.readlines():
                    word = line.strip()
                    show = True
                    for char in chars:
                        if char in word:
                            if show:
                                num += 1
                                print(word)
                            show = False
                            count[char] += 1
            print(f"{file}文件中有{num}个颜色词")

        print("\n统计：")
        total = 0
        for color, num in count.items():
            print(color, num)
            total += num
        print("总计", total)

    def append_words(self, words):
        with open(f"{self.path}words.txt", mode="a", encoding="utf-8") as fp:
            for word in words:
                fp.write(f"{word}\n")

    def append_opi(self, opinions):
        pos, neu, neg = list(), list(), list()
        for opi in opinions:
            word, sen = opi
            if 1 == sen:
                pos.append(word)
            elif 0 == sen:
                neu.append(word)
            elif -1 ==sen:
                neg.append(word)
            else:
                raise Exception("error sentiment")
        with open(f"{self.path}opi_pos.txt", mode="a", encoding="utf-8") as fp:
            for word in pos:
                fp.write(f"{word}\n")
        with open(f"{self.path}opi_neu.txt", mode="a", encoding="utf-8") as fp:
            for word in neu:
                fp.write(f"{word}\n")
        with open(f"{self.path}opi_neg.txt", mode="a", encoding="utf-8") as fp:
            for word in neg:
                fp.write(f"{word}\n")

    def append_words_manu(self, words, sen=""):
        if 0 == len(words):
            return
        name = {
            -1: "opi_neg_manu.txt",
            0: "opi_neu_manu.txt",
            1: "opi_pos_manu.txt",
            2: "vague_manu.txt",
            "": "words_manu.txt"
        }

        with open(f"{self.path}{name[sen]}", mode="a", encoding="utf-8") as fp:
            content = "\r\n".join(words) + "\r\n"
            fp.write(content)

        not_target = set()

        for word in words:
            if word in self.store["comment_target"]:
                not_target.add(word)

        if 0 != len(not_target):
            print("修改 common target")
            print(not_target)

            with open(f"{self.path}comment_not_target.txt", mode="a", encoding="utf-8") as fp:
                for word in not_target:
                    fp.write(f"{word}\r\n")

            targets = list()
            with open(f"{self.path}comment_target.txt", mode="r", encoding="utf-8") as fp:
                for line in fp.readlines():
                    word = line.strip()
                    if word not in not_target:
                        targets.append(word)

            with open(f"{self.path}comment_target.txt", mode="w", encoding="utf-8") as fp:
                for word in targets:
                    fp.write(f"{word}\r\n")

            del self.store["comment_target"]
            self.read_comment_target()


if __name__ == '__main__':
    obj = GetLexicon()
    obj.read_all("4")
    # obj.show()
    obj.find_word("棒棒")
    exit()
    # obj.find_word("很漂亮")  # nomeanings，comment_target
    # obj.find_key_char()
    words = list()
    with open("find.txt", mode="r", encoding="utf-8") as fp:
        for line in fp.readlines():
            words.append(line.strip())
    result = obj.find_words(words)
    for k, v in result.items():
        print(k, len(v), v)
    # print(obj.opinions["过细"])
    # obj.append_words(["天内", "作出评价"])
    # obj.append_opi([["辣鸡", -1]])
    # obj.read_all("4")
