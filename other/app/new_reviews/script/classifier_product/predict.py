import json
import sys
import os
import platform

from django.conf import settings

import tensorflow as tf
import numpy as np

from zhuican.enum import System
from zhuican.test import logger, log


#config
batch_size = 1
embedding_size = 256
vocabulary_size = 5000
# max_pool_size = 20

#CONV1
CONV1_HEIGHT = 2
CONV1_WIDTH = embedding_size
CONV1_DEEP = 50

CONV2_HEIGHT = 3
CONV2_WIDTH = embedding_size
CONV2_DEEP = 50

CONV3_HEIGHT = 4
CONV3_WIDTH = embedding_size
CONV3_DEEP = 50

NUM_CHANNELS = 1
IRRE_FC_SIZE = 6
RE_FC_SIZE = 5
FC_SIZE = 10

#选取top 概率大的
TOP = 2

def read_tag_from_file(path):
    tag_id = {}
    id_tag = {}
    with open(path,'r',encoding='utf-8') as f:
        for tag in f:
            tag = tag.strip('\n')
            tag_id[tag] = len(tag_id)
            id_tag[tag_id[tag]] = tag
    return tag_id,id_tag


absolute_path = os.path.join(settings.NLP_ROOT, 'classifier_model')

whole_tag_id,whole_id_tag = read_tag_from_file(os.path.join(absolute_path, 'tag_index.txt'))
irre_tag_id,irre_id_tag = read_tag_from_file(os.path.join(absolute_path, 'irre', 'tag_index_product_irrelated.txt'))
re_tag_id,re_id_tag = read_tag_from_file(os.path.join(absolute_path, 're', 'tag_index_product_related.txt'))

def product_related_inference(input_tensor,train=True,regularizer=None,dropout_keep_prob=0.5,reuse=False):
    
    with tf.variable_scope('layer1-conv1-product-related',reuse=reuse):
        conv1_weight = tf.get_variable('weight',[CONV1_HEIGHT,CONV1_WIDTH,NUM_CHANNELS,CONV1_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv1_biases = tf.get_variable('bias',[CONV1_DEEP],initializer=tf.constant_initializer(0.0))
        conv1 = tf.nn.conv2d(input_tensor, conv1_weight, strides=[1,1,1,1], padding='VALID')
        relu1 = tf.nn.relu(tf.nn.bias_add(conv1, conv1_biases))
        
    with tf.variable_scope('layer1-conv2-product-related',reuse=reuse):
        conv2_weight = tf.get_variable('weight',[CONV2_HEIGHT,CONV2_WIDTH,NUM_CHANNELS,CONV2_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv2_biases = tf.get_variable('bias',[CONV2_DEEP],initializer=tf.constant_initializer(0.0))
        conv2 = tf.nn.conv2d(input_tensor, conv2_weight, strides=[1,1,1,1], padding='VALID')
        relu2 = tf.nn.relu(tf.nn.bias_add(conv2, conv2_biases))
        
    with tf.variable_scope('layer1-conv3-product-related',reuse=reuse):
        conv3_weight = tf.get_variable('weight',[CONV3_HEIGHT,CONV3_WIDTH,NUM_CHANNELS,CONV3_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv3_biases = tf.get_variable('bias',[CONV3_DEEP],initializer=tf.constant_initializer(0.0))
        conv3 = tf.nn.conv2d(input_tensor, conv3_weight, strides=[1,1,1,1], padding='VALID')
        relu3 = tf.nn.relu(tf.nn.bias_add(conv3, conv3_biases))
        
    
    with tf.name_scope('layer2-pool-product-related'):
        max_pool1 = tf.squeeze(tf.reduce_max(relu1,reduction_indices=1,keep_dims=True),[1,2])
        max_pool2 = tf.squeeze(tf.reduce_max(relu2,reduction_indices=1,keep_dims=True),[1,2])
        max_pool3 = tf.squeeze(tf.reduce_max(relu3,reduction_indices=1,keep_dims=True),[1,2])
        reshaped = tf.concat([max_pool1,max_pool2,max_pool3],1)
        nodes = (CONV1_DEEP + CONV2_DEEP + CONV3_DEEP)
    
    with tf.variable_scope('layer3-fc1-product-related',reuse=reuse):
        fc1_weights = tf.get_variable("weight",[nodes,RE_FC_SIZE],initializer=tf.truncated_normal_initializer(stddev=0.1))
        if regularizer != None:
            tf.add_to_collection('losses',regularizer(fc1_weights))
        fc1_biases = tf.get_variable('bias',[RE_FC_SIZE],initializer=tf.constant_initializer(0.1))
        
        fc1 = tf.nn.relu(tf.matmul(reshaped,fc1_weights) + fc1_biases)
        if train:
            fc1 = tf.nn.dropout(fc1,dropout_keep_prob)
            
    return fc1

def product_irrelated_inference(input_tensor,train=True,regularizer=None,dropout_keep_prob=0.5,reuse=False):
    
    with tf.variable_scope('layer1-conv1-product-irrelated',reuse=reuse):
        conv1_weight = tf.get_variable('weight',[CONV1_HEIGHT,CONV1_WIDTH,NUM_CHANNELS,CONV1_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv1_biases = tf.get_variable('bias',[CONV1_DEEP],initializer=tf.constant_initializer(0.0))
        conv1 = tf.nn.conv2d(input_tensor, conv1_weight, strides=[1,1,1,1], padding='VALID')
        
        relu1 = tf.nn.relu(tf.nn.bias_add(conv1, conv1_biases))
        
    with tf.variable_scope('layer1-conv2-product-irrelated',reuse=reuse):
        conv2_weight = tf.get_variable('weight',[CONV2_HEIGHT,CONV2_WIDTH,NUM_CHANNELS,CONV2_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv2_biases = tf.get_variable('bias',[CONV2_DEEP],initializer=tf.constant_initializer(0.0))
        conv2 = tf.nn.conv2d(input_tensor, conv2_weight, strides=[1,1,1,1], padding='VALID')
        relu2 = tf.nn.relu(tf.nn.bias_add(conv2, conv2_biases))
        
    with tf.variable_scope('layer1-conv3-product-irrelated',reuse=reuse):
        conv3_weight = tf.get_variable('weight',[CONV3_HEIGHT,CONV3_WIDTH,NUM_CHANNELS,CONV3_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv3_biases = tf.get_variable('bias',[CONV3_DEEP],initializer=tf.constant_initializer(0.0))
        conv3 = tf.nn.conv2d(input_tensor, conv3_weight, strides=[1,1,1,1], padding='VALID')
        relu3 = tf.nn.relu(tf.nn.bias_add(conv3, conv3_biases))
        
    
    with tf.name_scope('layer2-pool-product-irrelated'):
        max_pool1 = tf.squeeze(tf.reduce_max(relu1,reduction_indices=1,keep_dims=True),[1,2])
        max_pool2 = tf.squeeze(tf.reduce_max(relu2,reduction_indices=1,keep_dims=True),[1,2])
        max_pool3 = tf.squeeze(tf.reduce_max(relu3,reduction_indices=1,keep_dims=True),[1,2])
        reshaped = tf.concat([max_pool1,max_pool2,max_pool3],1)
        nodes = (CONV1_DEEP + CONV2_DEEP + CONV3_DEEP)
    
    with tf.variable_scope('layer3-fc1-product-irrelated',reuse=reuse):
        fc1_weights = tf.get_variable("weight",[nodes,IRRE_FC_SIZE],initializer=tf.truncated_normal_initializer(stddev=0.1))
        if regularizer != None:
            tf.add_to_collection('losses',regularizer(fc1_weights))
        fc1_biases = tf.get_variable('bias',[IRRE_FC_SIZE],initializer=tf.constant_initializer(0.1))
        
        fc1 = tf.nn.relu(tf.matmul(reshaped,fc1_weights) + fc1_biases)
        if train:
            fc1 = tf.nn.dropout(fc1,dropout_keep_prob)
            
    return fc1

def strToIndexs(s,word_embeddings,dictionary):
    n = len(s)
    str2idx = np.zeros(n,dtype=np.int)
    sentence_embeddings = np.zeros([max(CONV3_HEIGHT,len(s)),embedding_size])
    for i in range(n):
        
        if s[i] not in dictionary:
            str2idx[i] = 0
        else:
            str2idx[i] = dictionary[s[i]]
        sentence_embeddings[range(0,n)] = word_embeddings[str2idx]
    return sentence_embeddings

def combine_two_result(re_y,irre_y):
    #如果irre_y 指向 other，则采用irre_y
    #如果irre_y没有指向other，选择概率最高的
    y_ = np.zeros(irre_y.shape[0],np.int32)
    irre_max_index = np.argmax(irre_y,1)
    re_max_index = np.argmax(re_y,1)
    for k,v in enumerate(irre_max_index):
        if v == 5:
            m = re_max_index[k]
            y_[k] = whole_tag_id[re_id_tag[m]]
        else:
            y_[k] = whole_tag_id[irre_id_tag[v]]
    return y_


def predict(raw_text_array):
    with tf.variable_scope('layer1-conv1-product-related'):
        conv1_weight = tf.get_variable('weight',[CONV1_HEIGHT,CONV1_WIDTH,NUM_CHANNELS,CONV1_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv1_biases = tf.get_variable('bias',[CONV1_DEEP],initializer=tf.constant_initializer(0.0))
        
    with tf.variable_scope('layer1-conv2-product-related'):
        conv2_weight = tf.get_variable('weight',[CONV2_HEIGHT,CONV2_WIDTH,NUM_CHANNELS,CONV2_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv2_biases = tf.get_variable('bias',[CONV2_DEEP],initializer=tf.constant_initializer(0.0))
        
    with tf.variable_scope('layer1-conv3-product-related'):
        conv3_weight = tf.get_variable('weight',[CONV3_HEIGHT,CONV3_WIDTH,NUM_CHANNELS,CONV3_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv3_biases = tf.get_variable('bias',[CONV3_DEEP],initializer=tf.constant_initializer(0.0))
    
    with tf.variable_scope('layer3-fc1-product-related'):
        nodes = (CONV1_DEEP + CONV2_DEEP + CONV3_DEEP)
        fc1_weights = tf.get_variable("weight",[nodes,RE_FC_SIZE],initializer=tf.truncated_normal_initializer(stddev=0.1))
        fc1_biases = tf.get_variable('bias',[RE_FC_SIZE],initializer=tf.constant_initializer(0.1))
    
    releated_variable = [conv1_weight,conv1_biases,conv2_weight,conv2_biases,conv3_weight,conv3_biases,fc1_weights,fc1_biases]
    
    with tf.variable_scope('layer1-conv1-product-irrelated'):
        conv1_weight = tf.get_variable('weight',[CONV1_HEIGHT,CONV1_WIDTH,NUM_CHANNELS,CONV1_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv1_biases = tf.get_variable('bias',[CONV1_DEEP],initializer=tf.constant_initializer(0.0))
        
        
    with tf.variable_scope('layer1-conv2-product-irrelated'):
        conv2_weight = tf.get_variable('weight',[CONV2_HEIGHT,CONV2_WIDTH,NUM_CHANNELS,CONV2_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv2_biases = tf.get_variable('bias',[CONV2_DEEP],initializer=tf.constant_initializer(0.0))
        
    with tf.variable_scope('layer1-conv3-product-irrelated'):
        conv3_weight = tf.get_variable('weight',[CONV3_HEIGHT,CONV3_WIDTH,NUM_CHANNELS,CONV3_DEEP],initializer=tf.truncated_normal_initializer(stddev=0.1))
        conv3_biases = tf.get_variable('bias',[CONV3_DEEP],initializer=tf.constant_initializer(0.0))
        
    with tf.variable_scope('layer3-fc1-product-irrelated'):
        fc1_weights = tf.get_variable("weight",[nodes,IRRE_FC_SIZE],initializer=tf.truncated_normal_initializer(stddev=0.1))
        fc1_biases = tf.get_variable('bias',[IRRE_FC_SIZE],initializer=tf.constant_initializer(0.1))
        
    irreleated_variable = [conv1_weight,conv1_biases,conv2_weight,conv2_biases,conv3_weight,conv3_biases,fc1_weights,fc1_biases]
    
    x = tf.placeholder(tf.float32, [batch_size,None,embedding_size,1], name = "x-input")
    re_y = product_related_inference(x,train=False,reuse=True)
    irre_y = product_irrelated_inference(x,train=False,reuse=True)
    
    target_count = {}
    predict_result = {}
    with tf.Session() as sess:
        saver_1 = tf.train.Saver(releated_variable)
        saver_2 = tf.train.Saver(irreleated_variable)
        saver_1.restore(sess, absolute_path + "/re/cnn_shorttext_classifer.ckpt")
        saver_2.restore(sess, absolute_path + "/irre/cnn_shorttext_classifer.ckpt")
        
        word_embeddings = np.fromfile(absolute_path + "/word/word_embeding.bin",dtype=np.float32)
        word_embeddings.shape = vocabulary_size,embedding_size
        dictionary = read_dict(absolute_path + "/word/dictionary.json")
        
        for target,raw_text_list in raw_text_array.items():
            for raw_text in raw_text_list:
                batch_data = [strToIndexs(raw_text, word_embeddings, dictionary)]
                batch_data = np.asarray(batch_data)
                batch_data = batch_data[:,:,:,np.newaxis]
                re_y_fetched,irre_y_fetched = sess.run([re_y,irre_y],feed_dict={x:batch_data})
                p_y_fetched = combine_two_result(re_y_fetched,irre_y_fetched)
                if target not in target_count:
                    target_count[target] = [0] * len(whole_id_tag)
                target_count[target][p_y_fetched[0]] += 1
        
        for target,count in target_count.items():
            sorted_list = sorted(count,reverse = True)
            top1_index = count.index(sorted_list[0])
            top1_tag = whole_id_tag[top1_index]
            top2_index = count.index(sorted_list[1])
            if sorted_list[1] == 0 or top2_index == top1_index:
                top2_tag = ""
            else:
                top2_tag = whole_id_tag[top2_index]
            predict_result[target] = (top1_tag,top2_tag)
        return predict_result
    

def read_dict(filename):
    with open(filename,'r',encoding='utf-8') as f:
        dic = json.loads(f.read())
        return dic

def read_tag(filename):
    tag_array = []
    with open(filename,'r',encoding='utf-8') as f:
        for line in f:
            tag_array.append(line.strip('\n'))
        return tag_array

def read_precidt_data_from_file(path):
    raw_text_data = {}
    with open(path,'r',encoding='utf-8') as f:
        for line in f:
            cols = line.strip('\n').split(';')
            comment = cols[0]
            target = cols[1]
            if target not in raw_text_data:
                raw_text_data[target] = []
            raw_text_data[target].append(comment)
    return raw_text_data

def test():
    file_path = "classifier_data.txt"
    raw_data = read_precidt_data_from_file(file_path)
    predict(raw_data)
    

if __name__ == "__main__":
    if len(sys.argv) == 2:
        file_path = sys.argv[1]
        raw_data = read_precidt_data_from_file(file_path)
        predict(raw_data)
    else:
        test()
        print('please input the file path.')
    print('ok.')