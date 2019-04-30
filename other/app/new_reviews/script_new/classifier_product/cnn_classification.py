import json
import sys
import os
import platform

import tensorflow as tf
import numpy as np

from zhuican.test import logger, log

# batch_size = 50
#词向量参数
windows_width = 5
word_embedding_dim = 64
word_vocab_size = None

#单句最大长度
num_classes = 8
max_sent_size = 15
word_pos_num = 2* ( max_sent_size + 5 ) 
word_pos_size = 6
word_pos_tag_num = 40
word_pos_tag_size = 6

#词向量部分
WORD_ALL_WIDTH = word_embedding_dim + word_pos_size*2 + word_pos_tag_size
WORD_CONV1_HEIGHT = 2
WORD_CONV1_WIDTH = WORD_ALL_WIDTH
WORD_CONV1_DEEP = 50
WORD_CONV2_HEIGHT = 3
WORD_CONV2_WIDTH = WORD_ALL_WIDTH
WORD_CONV2_DEEP = 50
WORD_CONV3_HEIGHT = 4
WORD_CONV3_WIDTH = WORD_ALL_WIDTH
WORD_CONV3_DEEP = 50
NUM_CHANNELS = 1
FC_SIZE = num_classes


if platform.system() == 'Windows':
    absolute_path = r'D:\nlp\classifier_model'
    wordMap_path = r"D:\nlp\50013008.word_64W5_wordmap"
else:
    absolute_path = '/home/nlp/classifier_model'
    wordMap_path = "/home/nlp/50013008.word_64W5_wordmap"


def inference(input_word,input_pos1_word,input_pos2_word,input_pos2,word_vocab_size,word_embedding_dim,
              train=True,regularizer=None,dropout_keep_prob=0.5,reuse=False):
    
    with tf.variable_scope('embedding-layer',reuse=reuse):
        word_embedding = tf.get_variable("word_embedding",shape=[word_vocab_size+1, word_embedding_dim],initializer=tf.constant_initializer(value=0, dtype=tf.float32),trainable=False)
        word_targetpos_embedding = tf.get_variable('word_target_pos_embedding',[word_pos_num,word_pos_size],dtype=tf.float32,initializer=tf.truncated_normal_initializer(stddev=0.1))
        word_opinionpos_embedding = tf.get_variable('word_opinion_pos_embedding',[word_pos_num,word_pos_size],dtype=tf.float32,initializer=tf.truncated_normal_initializer(stddev=0.1))
        word_pos2_embedding = tf.get_variable('word_pos2_embedding',[word_pos_tag_num,word_pos_tag_size],dtype=tf.float32,initializer=tf.truncated_normal_initializer(stddev=0.1))
        
        # embedding layer，返回inputs 为 batch * max_sent_size * ( embedding_size + word_pos_size + word_pos_tag_size)
        
        word_tensor = tf.concat([tf.nn.embedding_lookup(word_embedding,input_word),
                                 tf.nn.embedding_lookup(word_targetpos_embedding,input_pos1_word),
                                 tf.nn.embedding_lookup(word_opinionpos_embedding,input_pos2_word),
                                tf.nn.embedding_lookup(word_pos2_embedding,input_pos2)],
                                2)
        word_tensor = tf.expand_dims(word_tensor, -1)
        
    with tf.variable_scope('layer-word',reuse=reuse):
        conv1_weight = tf.get_variable('conv1-weight',[WORD_CONV1_HEIGHT,WORD_CONV1_WIDTH,NUM_CHANNELS,WORD_CONV1_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv1_biases = tf.get_variable('conv1-bias',[WORD_CONV1_DEEP],initializer=tf.constant_initializer(0.0))
        conv1 = tf.nn.conv2d(word_tensor, conv1_weight, strides=[1,1,1,1], padding='VALID')
        relu1 = tf.nn.relu(tf.nn.bias_add(conv1, conv1_biases))
        
        conv2_weight = tf.get_variable('conv2-weight',[WORD_CONV2_HEIGHT,WORD_CONV2_WIDTH,NUM_CHANNELS,WORD_CONV2_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv2_biases = tf.get_variable('conv2-bias',[WORD_CONV2_DEEP],initializer=tf.constant_initializer(0.0))
        conv2 = tf.nn.conv2d(word_tensor, conv2_weight, strides=[1,1,1,1], padding='VALID')
        relu2 = tf.nn.relu(tf.nn.bias_add(conv2, conv2_biases))
        
        conv3_weight = tf.get_variable('conv3-weight',[WORD_CONV3_HEIGHT,WORD_CONV3_WIDTH,NUM_CHANNELS,WORD_CONV3_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv3_biases = tf.get_variable('conv3-bias',[WORD_CONV3_DEEP],initializer=tf.constant_initializer(0.0))
        conv3 = tf.nn.conv2d(word_tensor, conv3_weight, strides=[1,1,1,1], padding='VALID')
        relu3 = tf.nn.relu(tf.nn.bias_add(conv3, conv3_biases))
        
        max_pool1 = tf.squeeze(tf.reduce_max(relu1,reduction_indices=1,keep_dims=True),[1,2])
        max_pool2 = tf.squeeze(tf.reduce_max(relu2,reduction_indices=1,keep_dims=True),[1,2])
        max_pool3 = tf.squeeze(tf.reduce_max(relu3,reduction_indices=1,keep_dims=True),[1,2])
        word_reshaped = tf.concat([max_pool1,max_pool2,max_pool3],1)
        
    all_reshaped = word_reshaped
    nodes =  WORD_CONV1_DEEP + WORD_CONV2_DEEP + WORD_CONV3_DEEP
    
    with tf.variable_scope('layer-mlp',reuse=reuse):
        fc1_weights = tf.get_variable("weight",[nodes,FC_SIZE],initializer=tf.truncated_normal_initializer(stddev=0.1))
        if regularizer != None:
            tf.add_to_collection('losses',regularizer(fc1_weights))
        fc1_biases = tf.get_variable('bias',[FC_SIZE],initializer=tf.constant_initializer(0.1))
        if train:
            all_reshaped = tf.nn.dropout(all_reshaped,dropout_keep_prob)
            
        fc1 = tf.nn.sigmoid(tf.matmul(all_reshaped,fc1_weights) + fc1_biases)            
            
    return fc1

class Data(object):
    def __init__(self,textDic):
        global wordMap_path,word_vocab_size
        #生成词ID对应
        with open(wordMap_path,'r',encoding='utf-8') as f:
            self.word_map = json.loads(f.read())
            word_vocab_size = len(self.word_map)
        
        self.id_tag =  ['使用场景', '适用人群', '功能', '质量', '款式', '价格', '服务', '活动']
        
        
        #生成词性ID对应
        self.pos_id = {"Ag":0,"a":1,"ad":2,"an":3,"b":4,"c":5,"dg":6,"d":7,"e":8,"f":9,"g":10,
                           "h":11,"i":12,"j":13,"k":14,"l":15,"m":16,"Ng":17,"n":18,"nr":19,"ns":20,
                           "nt":21,"nz":22,"o":23,"p":24,"q":25,"r":26,"s":27,"tg":28,"t":29,"u":30,
                           "vg":31,"v":32,"vd":33,"vn":34,"w":35,"x":36,"y":37,"z":38,"un":39}
        self.max_sent_size = 15
        self.textDic = textDic
        
    def wordsToIndex(self,s,max_sent_size):
        sent_index = np.zeros([max_sent_size])
        for i in range(min(len(s),max_sent_size)):
            sent_index[i] = self.word_map.get(s[i],0)
        return sent_index
    
    def strToPos2(self,s_pos,max_sent_size):
        sent_pos = np.zeros([max_sent_size])
        for i,w in enumerate(s_pos):
            sent_pos[i] = self.pos_id.get(w,0)
        return sent_pos
    
    def wordsToPos1(self,t_id,max_sent_size):
        sent_pos = np.zeros([max_sent_size])
        t_id = min(max_sent_size,max(0,t_id))
        for i in range(max_sent_size):
            sent_pos[i] = i - t_id + max_sent_size
        return sent_pos
    
    def reCleanSent(self,text_sentence,max_sent_size):
        t_id,o_id,text,pos = text_sentence

        if t_id > max_sent_size /2 :
            end = min(t_id + max_sent_size//2,len(text))
            start = max(0,end - max_sent_size)
        else:
            start = 0
            end = min(len(text),max_sent_size)
        text_sentence = ( t_id - start, o_id - start,text[start:end],pos[start:end])
        return text_sentence
    
    def get_trainData(self):
        for key in self.textDic:
            sentList = self.textDic[key]
            if len(sentList) == 0:
                continue
            batch_wordstext = []
            batch_wordspos1 = []
            batch_wordspos2 = []
            batch_wordPOS = []
            
            for sent in sentList:
                t_id,o_id,text,pos = self.reCleanSent(sent, self.max_sent_size)
                train_words = self.wordsToIndex(text,max_sent_size)
                train_wordspos1 = self.wordsToPos1(t_id,max_sent_size)
                train_wordspos2 = self.wordsToPos1(o_id,max_sent_size)
                train_POS = self.strToPos2(text,max_sent_size)
                
                batch_wordstext.append(train_words)
                batch_wordspos1.append(train_wordspos1)
                batch_wordspos2.append(train_wordspos2)
                batch_wordPOS.append(train_POS)
                
            batch_wordstext = np.asarray(batch_wordstext)
            batch_wordspos1 = np.asarray(batch_wordspos1)
            batch_wordspos2 = np.asarray(batch_wordspos2)
            batch_wordPOS = np.asarray(batch_wordPOS)
            
            yield batch_wordstext,batch_wordspos1,batch_wordspos2,batch_wordPOS,key
    
def predict(text_array):
    #训练数据
    data = Data(text_array)
    #输入向量，词向量
    input_word = tf.placeholder(dtype=tf.int32,shape=[None,max_sent_size],name='input_word')
    #输入向量，位置向量
    input_word_pos1 = tf.placeholder(dtype=tf.int32,shape=[None,max_sent_size],name='input_pos1_word')
    #输入向量，位置向量
    input_word_pos2 = tf.placeholder(dtype=tf.int32,shape=[None,max_sent_size],name='input_pos2_word')
    #输入向量，词性标注向量
    input_pos2 = tf.placeholder(dtype=tf.int32,shape=[None,max_sent_size],name='input_pos2')
    
    word_embedding_placeholder = tf.placeholder(dtype=tf.float32,shape=[word_vocab_size+1, word_embedding_dim],name="embedding_placeholder")
    
    with tf.name_scope('evaluation'):
        y_test = inference(input_word,input_word_pos1,input_word_pos2,input_pos2,word_vocab_size,word_embedding_dim,
                  False, None,dropout_keep_prob = 0.5,reuse=False)
    
    saver = tf.train.Saver()
    target_count = {}
    with tf.Session() as sess:
        saver.restore(sess, absolute_path + "/cnn_shorttext_classifer.ckpt")  
        for batch_wordstext,batch_wordspos1,batch_wordspos2,batch_wordPOS,key in data.get_trainData():
            feed_data = {input_word:batch_wordstext,
                         input_word_pos1:batch_wordspos1,
                         input_word_pos2:batch_wordspos2,
                         input_pos2:batch_wordPOS}
            target,_ = key.split('_')
            y_test_fetched, = sess.run([y_test],feed_dict=feed_data)
            max_index = np.argmax(y_test_fetched,1)
            
            if target not in target_count:
                target_count[target] = [0] * num_classes
            
            for v in max_index:
                target_count[target][v] += 1
        
    #处理结果
    predict_result = {}
    for target,count in target_count.items():
            all_cnt = sum(count)
            sorted_list = sorted(count,reverse = True)
            top1_index = count.index(sorted_list[0])
            top1_tag = data.id_tag[top1_index]
            top2_index = count.index(sorted_list[1])
            if sorted_list[1] == 0 or top2_index == top1_index:
                top2_tag = ""
            else:
                top2_tag = data.id_tag[top2_index]
            predict_result[target] = (top1_tag,sorted_list[0]/all_cnt,top2_tag,sorted_list[1]/all_cnt)
    return predict_result
    

    