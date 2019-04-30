# -*-coding:utf-8-*-
import traceback

from . import cloud_parser
import json
import re
import collections


class Opinion_Target_Propagation(object):
    def __init__(self, O_Seed, T_Seed, Reviews_Data, Replace_Seed, NoSense_Seed, Adversatives):
        self.Opinions = O_Seed
        self.T_Seed = T_Seed
        self.Features = dict()
        self.Origin_Reviews_Data = Reviews_Data
        self.Prase_Reviews_Data = []
        self.Prase_Review_ID_MAP = []
        # self.MR = ["ATT", "SBV"]
        self.MR = ["ATT", "SBV", 'VOB']
        self.NN = ["j", "n", "nh", "ni", "nl", "ns", "nz"]
        self.JJ = ["a", "b", "d"]
        self.CONJ = ["COO"]
        self.features_opinion = {}
        self.feature_frequency = {}
        self.Replace_Seed = Replace_Seed
        self.NoSense_Seed = NoSense_Seed
        self.Adversatives = Adversatives

    def resert_seed(self, O_Seed, T_Seed):
        self.Opinions = O_Seed
        self.T_Seed = T_Seed
        self.Features = dict()
        self.features_opinion = {}
        self.feature_frequency = {}

    def init_parse_reviews(self):
        while (len(self.Origin_Reviews_Data) > 0):
            review = self.Origin_Reviews_Data.pop()
            if not review:
                continue
            try:
                review_json = json.loads(review[0].replace('\\', '\\\\'), strict=False)
                tree = cloud_parser.Tree(review_json)
                self.Prase_Reviews_Data.append(tree)
                self.Prase_Review_ID_MAP.append([review[1], review[2]])
            except Exception as e:
                traceback.print_exc()

        del self.Origin_Reviews_Data

    def extract_features_by_opinions(self, sentence_tree):
        # R11 R12
        # R12 不存在拥有两个父类的节点
        features = dict()
        for word in sentence_tree.node_dict:
            if word in self.Opinions:
                next_node = sentence_tree.node_dict[word]
                while True:
                    for child_node in next_node.children:
                        # R11
                        if child_node.parent_relation in self.MR \
                                and child_node.pos in self.NN \
                                and child_node.data not in self.Features:
                            # for sentiment propagation
                            child_node.position = self.Opinions[word]
                            # add features
                            features[child_node.data] = 0
                            # for connect features and opinions
                            if child_node.data in self.features_opinion:
                                self.features_opinion[child_node.data].append(word)
                            else:
                                self.features_opinion[child_node.data] = [word]

                    if next_node.nexthash:
                        next_node = next_node.nextNode
                    else:
                        break
        return features

    def extract_opinions_by_features(self, sentence_tree, extracted_featrues):
        for word in sentence_tree.node_dict:
            if word in self.Opinions:
                tmp_node = sentence_tree.node_dict[word]
                while tmp_node.nexthash:
                    tmp_node.position = self.Opinions[word]
                    tmp_node = tmp_node.nextNode
        # R21 R22
        opinions = dict()
        for word in sentence_tree.node_dict:
            if word in extracted_featrues:
                next_node = sentence_tree.node_dict[word]
                while True:
                    # R21
                    if next_node.parent_relation in self.MR \
                            and next_node.parent.pos in self.JJ \
                            and next_node.parent.data not in self.Opinions:
                        if next_node.position == 0:
                            # compute the polarity of review

                            polarity = 0
                            for tmp in sentence_tree.node_dict:
                                if tmp in self.Opinions:
                                    polarity += self.Opinions[tmp]
                            if polarity >= 0:
                                opinions[next_node.parent.data] = 1
                            else:
                                opinions[next_node.parent.data] = -1
                        else:
                            next_node.parent.position = next_node.position
                            opinions[next_node.parent.data] = next_node.position

                        if word in self.features_opinion:
                            self.features_opinion[word].append(next_node.parent.data)
                        else:
                            self.features_opinion[word] = [next_node.parent.data]
                    if next_node.nexthash:
                        next_node = next_node.nextNode
                    else:
                        break
        return opinions

    def extract_features_by_features(self, sentence_tree, extracted_featrues):
        # R31 R32
        features = dict()
        for word in sentence_tree.node_dict:
            if word in extracted_featrues:
                next_node = sentence_tree.node_dict[word]
                while True:

                    for child_node in next_node.children:
                        # R11
                        if child_node.parent_relation in self.CONJ \
                                and child_node.pos in self.NN \
                                and child_node.data not in self.Features:
                            features[child_node.data] = 0
                            child_node.position = next_node.position

                    if next_node.parent_relation in self.CONJ \
                            and next_node.parent.pos in self.NN \
                            and next_node.parent.data not in self.Features:
                        features[next_node.parent.data] = 0
                        next_node.parent.position = next_node.position
                        if next_node.parent.data not in self.features_opinion:
                            self.features_opinion[next_node.parent.data] = []

                    if next_node.nexthash:
                        next_node = next_node.nextNode
                    else:
                        break

        return features

    def extract_opinions_by_opinions(self, sentence_tree):
        # R41 R42
        opinions = dict()
        for word in sentence_tree.node_dict:
            if word in self.Opinions:
                next_node = sentence_tree.node_dict[word]
                is_adverse = 1
                for child_node in next_node.children:
                    if child_node.data in self.Adversatives:
                        is_adverse = is_adverse * -1
                        break

                while True:

                    for child_node in next_node.children:
                        # R41
                        if child_node.parent_relation in self.CONJ \
                                and child_node.pos in self.JJ \
                                and child_node.data not in self.Opinions:
                            # 或许要考虑转折词
                            is_again_adverse = is_adverse
                            for child in child_node.children:
                                if child.data in self.Adversatives:
                                    is_again_adverse = is_again_adverse * -1
                                    break
                            opinions[child_node.data] = is_again_adverse * self.Opinions[word]

                    if next_node.parent_relation in self.CONJ \
                            and next_node.parent.pos in self.JJ \
                            and next_node.parent.data not in self.Opinions:
                        is_again_adverse = is_adverse
                        for child in next_node.parent.children:
                            if child.data in self.Adversatives:
                                is_again_adverse = is_again_adverse * -1
                                break

                        opinions[next_node.parent.data] = self.Opinions[word]
                    # 暂无
                    if next_node.nexthash:
                        next_node = next_node.nextNode
                    else:
                        break

        return opinions

    def propagation(self):
        loop = True
        first_time = True
        New_Featrues = dict()
        New_Opinions = dict()
        __New_Features = dict()
        __New_Opinions = dict()
        while (loop):
            for sentence_tree in self.Prase_Reviews_Data:
                extracted_features = self.extract_features_by_opinions(sentence_tree)
                extracted_opinions = self.extract_opinions_by_opinions(sentence_tree)
                New_Featrues.update(extracted_features)
                New_Opinions.update(extracted_opinions)

            if first_time:
                self.Features.update(self.T_Seed)
                New_Featrues.update(self.T_Seed)
                first_time = False

            self.Features.update(New_Featrues)
            self.Opinions.update(New_Opinions)

            for sentence_tree in self.Prase_Reviews_Data:
                extracted_features = self.extract_features_by_features(sentence_tree, New_Featrues)
                extracted_opinions = self.extract_opinions_by_features(sentence_tree, New_Featrues)
                __New_Features.update(extracted_features)
                __New_Opinions.update(extracted_opinions)

            New_Featrues.update(__New_Features)
            New_Opinions.update(__New_Opinions)

            self.Features.update(__New_Features)
            self.Opinions.update(__New_Opinions)

            if len(New_Featrues) == 0 and len(New_Opinions) == 0:
                loop = False

            New_Featrues.clear()
            New_Opinions.clear()
            __New_Features.clear()
            __New_Opinions.clear()

    # 识别出前n个词组
    def select_target_phrases(self, n=1, limited_num=1):
        Target_Pharse = {}
        Target_Pharse_Counter = {}
        Target_Pharse_Map = {}  # 近义词合并
        Select_Pharse = {}
        for w in self.Features:
            for sentence_tree in self.Prase_Reviews_Data:
                if w in sentence_tree.node_dict:
                    target_phrase = [w]
                    jinyi_pharse = self.Replace_Seed.get(w, w)
                    extracted_pharse = w
                    last_node = sentence_tree.node_dict[w]
                    id = int(sentence_tree.node_dict[w].id)
                    for i in range(1, n + 1):
                        if id - i >= 1:
                            new_node = sentence_tree.node_array[str(id - i)]
                            if (new_node.parent == last_node or last_node in new_node.children) \
                                    and new_node.pos not in ['w'] \
                                    and new_node.parent_relation in self.MR \
                                    and new_node.data not in self.Opinions:
                                target_phrase.insert(0, new_node.data)
                                jinyi_pharse = self.Replace_Seed.get(new_node.data, new_node.data) + jinyi_pharse
                                extracted_pharse = new_node.data + extracted_pharse
                                last_node = new_node
                            else:
                                break
                    if len(target_phrase) > 1:
                        Target_Pharse_Map.setdefault(extracted_pharse, jinyi_pharse)
                        Target_Pharse.setdefault(extracted_pharse, target_phrase)
                        Target_Pharse_Counter[jinyi_pharse] = 1 + Target_Pharse_Counter.setdefault(jinyi_pharse, 0)

        for extracted_pharse, jinyi_pharse in Target_Pharse_Map.items():
            if Target_Pharse_Counter[jinyi_pharse] > limited_num:
                Select_Pharse.setdefault(jinyi_pharse, []).append(Target_Pharse[extracted_pharse])

        #         for pharse, count in Target_Pharse_Counter.items():
        #             if count > limited_num:
        #                 Select_Pharse[pharse] = Target_Pharse[pharse]
        return Select_Pharse

    def identify_target_phrases(self, n=1, limited_num=1, is_add=False):
        """
        parms:
        n 表示考虑前 n个词汇
        limited_num: 表示最少出现次数
        is_add:表示是否修改新词汇在原句法结构中.True表示添加,False不修改.
        """
        Select_Pharse = self.select_target_phrases(n=n, limited_num=limited_num)
        for pharse, wordslist in Select_Pharse.items():
            if not is_add and pharse not in self.T_Seed:
                continue
            for words in wordslist:
                self.Features[pharse] = 0
                self.features_opinion[pharse] = list(
                    set(self.features_opinion.setdefault(pharse, []) + self.features_opinion.setdefault(words[-1], [])))
                for sentence_tree in self.Prase_Reviews_Data:
                    i = 0
                    w = words[0]
                    if w in sentence_tree.node_dict:
                        # record the track node
                        track_node = [sentence_tree.node_dict[w]]
                        cur_node = sentence_tree.node_dict[w]
                        # fit phrase
                        is_fit = True
                        for j in range(1, n + 1):
                            cur_node = cur_node.parent
                            track_node.append(cur_node)
                            if cur_node.data != words[i + j]:
                                is_fit = False
                                break
                        if is_fit:
                            sentence_tree.delete_hash_in_dictionary(cur_node)
                            cur_node.data = pharse
                            cur_node.pos = 'n'
                            cur_node.type = 1
                            sentence_tree.set_hash_for_dictionary(cur_node)
                            for node in track_node[:-1]:
                                for child in node.children:
                                    child.parent = cur_node
                                    cur_node.children.append(child)
                                sentence_tree.delete_hash_in_dictionary(node)

    def compute_word_frequency(self):
        for w in self.features_opinion:
            self.feature_frequency[w] = {}
            self.features_opinion[w] = set(self.features_opinion[w])
            for o in self.features_opinion[w]:
                self.feature_frequency[w][o] = 0

        for review in self.Prase_Reviews_Data:
            for word in review.node_dict:
                if word in self.feature_frequency:
                    # add tag for is the feature-opinion relationship being extracted
                    is_extracted = False
                    next_node = review.node_dict[word]
                    while True:
                        for child_node in next_node.children:
                            if child_node.data in self.feature_frequency[word]:
                                is_extracted = True
                                self.feature_frequency[word][child_node.data] += 1
                                child_node.type = 2

                        if next_node.parent.data in self.feature_frequency[word]:
                            is_extracted = True
                            self.feature_frequency[word][next_node.parent.data] += 1
                            next_node.parent.type = 2

                        if next_node.nexthash:
                            next_node = next_node.nextNode
                        else:
                            break
                    if is_extracted:
                        review.node_dict[word].type = 1
        del self.features_opinion
        self.features_opinion = None

    def generate_word_frequency_by_sentence(self):
        """
        func:为了统计句子级别中被提取中的词语，为了生成数据库数据，应该在调用compute_word_frequency函数之后被调用
        """
        self.NewDBData = collections.defaultdict(list)  # 插入格式(comment_id,comment_date,opinions)

        for i, review in enumerate(self.Prase_Reviews_Data):
            for word in review.node_dict:
                if word in self.feature_frequency:
                    # add tag for is the feature-opinion relationship being extracted
                    next_node = review.node_dict[word]
                    while True:
                        for child_node in next_node.children:
                            if child_node.data in self.feature_frequency[word]:
                                self.NewDBData[word].append(self.Prase_Review_ID_MAP[i] + [child_node.data])

                        if next_node.parent.data in self.feature_frequency[word]:
                            self.NewDBData[word].append(self.Prase_Review_ID_MAP[i] + [next_node.parent.data])

                        if next_node.nexthash:
                            next_node = next_node.nextNode
                        else:
                            break

    def combine_similar_words(self):
        delete_words = []
        for w in list(self.feature_frequency.keys()):
            if w in self.Replace_Seed:
                # 获得替换词
                des_word = self.Replace_Seed[w]
                if w == des_word:
                    continue

                if hasattr(self, 'NewDBData'):
                    self.NewDBData.setdefault(des_word, [])
                    self.NewDBData[des_word] = self.NewDBData[des_word] + self.NewDBData[w]
                    del self.NewDBData[w]

                self.feature_frequency.setdefault(des_word, {})
                tag = self.Features.setdefault(des_word, False)
                if not tag:
                    self.Features[des_word] = self.Features[w]

                # 合并观点词
                for opinion in self.feature_frequency[w]:
                    src_int = self.feature_frequency[des_word].setdefault(opinion, 0)
                    self.feature_frequency[des_word][opinion] = src_int + self.feature_frequency[w][opinion]
                delete_words.append(w)

        for w in delete_words:
            del self.feature_frequency[w]
            del self.Features[w]

    def remove_nosense_words_before_count(self):
        delete_words = []
        for w in self.features_opinion:
            if w in self.NoSense_Seed:
                delete_words.append(w)

        for w in delete_words:
            del self.features_opinion[w]
            del self.Features[w]

    def remove_nosense_words(self):
        delete_words = []
        for w in self.feature_frequency:
            if w in self.NoSense_Seed:
                delete_words.append(w)

        for w in delete_words:
            del self.feature_frequency[w]
            del self.Features[w]

    def combine_similar_words_by_outseed(self, outseed):
        delete_words = []
        for w in self.feature_frequency.keys():
            if w in outseed:
                # 获得替换词
                des_word = outseed[w]
                if w == des_word:
                    continue
                self.feature_frequency.setdefault(des_word, {})
                tag = self.Features.setdefault(des_word, "")
                if not tag:
                    self.Features[des_word] = self.Features[w]
                # 合并观点词
                for opinion in self.feature_frequency[w]:
                    src_int = self.feature_frequency[des_word].setdefault(opinion, 0)
                    self.feature_frequency[des_word][opinion] = src_int + self.feature_frequency[w][opinion]
                delete_words.append(w)

        for w in delete_words:
            del self.feature_frequency[w]
            del self.Features[w]

        if len(delete_words) > 0:
            return True
        else:
            return False

    def remove_nosense_words_by_model(self, filter):
        delete_words = []
        for w in self.feature_frequency:
            if filter.isNoisyWord(w):
                delete_words.append(w)

        for w in delete_words:
            del self.feature_frequency[w]
            del self.Features[w]

    def remove_little_frequency_targets(self, length_limit=4, frequency_limit_num=2):
        delete_words = []
        for w in self.feature_frequency.keys():
            count = 0
            if len(w) < length_limit:
                delete_words.append(w)
                continue
            for o in self.feature_frequency[w]:
                count += self.feature_frequency[w][o]
            if count < frequency_limit_num:
                delete_words.append(w)

        for w in delete_words:
            del self.Features[w]
            del self.feature_frequency[w]

    def get_trainData_from_corpus(self, max_size=100):
        """
        Funcs: 从评价数据中获得训练数据
        """
        text = {}
        new_features = []
        for x in self.Features:
            if self.Features[x] == 0 and len(self.feature_frequency.get(x, [])) > 0:
                new_features.append(x)

        if len(new_features) > 0:
            for sentence_tree in self.Prase_Reviews_Data:
                for w in new_features:
                    if w in sentence_tree.node_dict:
                        short_text = sentence_tree.get_short_text_by_target(w)
                        if w in text and len(text[w]) < max_size:
                            text[w].append(short_text)
                        else:
                            text[w] = [short_text]
        return text

        # 根据target 和  opinion 一起匹配文本

    #         if len(new_features) > 0:
    #             for i, review in enumerate(self.Prase_Reviews_Data):
    #                     for word in review.node_dict:
    #                         if word in new_features:
    #                             # add tag for is the feature-opinion relationship being extracted
    #                             next_node = review.node_dict[word]
    #                             while True:
    #                                 for child_node in next_node.children:
    #                                     if child_node.data in self.feature_frequency[word]:
    #                                         keyString = "{}_{}".format(word, child_node.data)
    #                                         keyStringSample = text.setdefault(keyString,[])
    #                                         if len(keyStringSample) >= max_size:
    #                                             continue
    #                                         sample = self.get_train_from_sentence(review, next_node, child_node)
    #                                         if sample:
    #                                             keyStringSample.append(sample)
    #
    #                                 if next_node.parent.data in self.feature_frequency[word]:
    #                                     keyString = "{}_{}".format(word, next_node.parent.data)
    #                                     keyStringSample = text.setdefault(keyString,[])
    #                                     if len(keyStringSample) < max_size:
    #                                         sample = self.get_train_from_sentence(review, next_node, next_node.parent)
    #                                         if sample:
    #                                             text[keyString].append(sample)
    #
    #                                 if next_node.nexthash:
    #                                     next_node = next_node.nextNode
    #                                 else:
    #                                     break
    #         return text

    def get_train_from_sentence(self, review, target_node, opinion_node):

        def cleanText(line):
            line = re.sub("┐.{0,5}┌|<.{0,5}>|&[a-z]+;", '', line)
            line = re.sub(
                r"[~0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz\\/]*\(.{0,5}\)[~0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz\\/]*",
                '', line)
            line = re.sub("[A-Z]+|[a-z]+", "EN", line)  # english
            line = re.sub("\d+(\.\d+)?", "NUM", line)  # number
            line = re.sub(r"[\"'\\/<>《》\+—~_^$@#￥%&*（）\(\)-\|]+", "T", line)  # ordinary punctuation
            line = re.sub("[\s+\，～、……,;；：:]+", "MI", line)  # middle of sentence
            line = re.sub("[!！。\.？?]+", "SE", line)  # small end of comment
            line = "".join(filter(lambda ch: (u'\u4e00' <= ch <= u'\u9fa5') or ('A' <= ch <= 'Z'), line))
            return line

        # 错别字修正
        def isValidCh(words):
            for ch in words:
                if not ((u'\u4e00' <= ch <= u'\u9fa5') or ('A' <= ch <= 'Z')):
                    return False
            return True

        train_text_data = []
        train_pos_data = []

        target_id = int(target_node.id)
        opinion_id = int(opinion_node.id)
        final_t_id = None
        final_o_id = None

        raw_text = review.get_raw_text()
        clean_text = cleanText(raw_text.replace(' ', ''))

        raw_pos = review.get_pos_text().split(' ')
        raw_text = raw_text.split(' ')
        new_text = []
        for i, (word, pos) in enumerate(zip(raw_text, raw_pos)):
            if len(word) > 0 and u'\u4e00' <= word[0] <= u'\u9fa5':
                new_text.append([word, pos])
        raw_text = new_text

        raw_text_itr = 0
        wordSeg = ""

        start = 0
        while start < len(clean_text):
            if ('A' <= clean_text[start] <= 'Z'):
                wordSeg = clean_text[start]
                end = start + 1
                while wordSeg not in ["MI", "NUM", "EN", "T", "SE", "BE", "END"]:
                    end += 1
                    wordSeg = clean_text[start:end]
                train_text_data.append(wordSeg)
                train_pos_data.append('x')
                start = end
            else:
                while start < len(clean_text):
                    tmp_itr = raw_text_itr
                    while len(raw_text) > tmp_itr and clean_text[start:start + len(raw_text[tmp_itr][0])] != \
                            raw_text[tmp_itr][0]:
                        tmp_itr += 1
                    if tmp_itr == len(raw_text):
                        tmp_itr = raw_text_itr
                        start += 1
                    else:
                        break

                if start >= len(clean_text) or tmp_itr == len(raw_text):
                    break

                raw_text_itr = tmp_itr
                if raw_text[raw_text_itr][0] == target_node.data:
                    if (not final_t_id) or (
                            final_t_id and abs(len(train_text_data) - target_id) < abs(final_t_id - target_id)):
                        final_t_id = len(train_text_data)
                if raw_text[raw_text_itr][0] == opinion_node.data:
                    if (not final_o_id) or (
                            final_o_id and abs(len(train_text_data) - target_id) < abs(final_o_id - opinion_id)):
                        final_o_id = len(train_text_data)

                start = start + len(raw_text[raw_text_itr][0])
                train_text_data.append(raw_text[raw_text_itr][0])
                train_pos_data.append(raw_text[raw_text_itr][1])
                raw_text_itr += 1

        #         for i,ch in enumerate(clean_text):
        #             wordSeg += ch
        #             if raw_text_itr < len(raw_text)  and wordSeg == raw_text[raw_text_itr][0]:
        #                 if raw_text[raw_text_itr][0] == target_node.data:
        #                     if (not final_t_id) or (final_t_id and abs(len(train_text_data) - target_id) < abs(final_t_id - target_id)):
        #                         final_t_id = len(train_text_data)
        #
        #                 if raw_text[raw_text_itr][0] == opinion_node.data:
        #                     if (not final_o_id) or (final_o_id and abs(len(train_text_data) - target_id) < abs(final_o_id - opinion_id)):
        #                         final_o_id = len(train_text_data)
        #
        #                 train_text_data.append(raw_text[raw_text_itr][0])
        #                 train_pos_data.append(raw_text[raw_text_itr][1])
        #                 wordSeg = ''
        #                 raw_text_itr += 1
        #             elif wordSeg in ["MI","NUM","EN","T","SE","BE","END"]:
        #                 train_text_data.append(wordSeg)
        #                 train_pos_data.append('x')
        #                 wordSeg = ''
        train_text_data.insert(0, "BE")
        train_text_data.append("END")
        train_pos_data.insert(0, "x")
        train_pos_data.append("x")
        try:
            final_t_id += 1
            final_o_id += 1
        except Exception as e:
            return False

        return (final_t_id, final_o_id, train_text_data, train_pos_data)
