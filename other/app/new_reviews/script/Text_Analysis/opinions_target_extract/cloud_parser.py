#-*-coding:utf-8-*-
import urllib
import json
import time
import random
MY_AUTH_KEY = 'K95738J5cv7Oqz3X5TRUYYCyLm3e6q6aTKVwGXAW'
#document: http://www.ltp-cloud.com/document/#api_rest_format_json

class Node(object):
    """Node"""
    def __init__(self, data='root', id = 0, pos='root', parent=-2,parent_relation='',position = 0):
        """Node"""
        self.id = id
        self.data = data
        self.parent = parent
        self.pos = pos
        self.parent_relation = parent_relation
        self.children = []
        self.position = position#正面或负面
        self.type = 0 # 0:other 1:aspect 2:opinions
        self.nexthash = False
        self.nextNode = None
        
class Tree(object):
    def __init__(self,sentence_json):
        self.node_dict = dict()
        self.root_node = Node()
        self.node_array = dict()
        self.generate_tree_by_json(sentence_json)
        
    def generate_tree_by_json(self,sentence_json):
        for i in sentence_json:
            try:
                utf8_data = i["cont"]
                n_node = Node(data=utf8_data,id=i["id"],pos=i["pos"],parent=i["parent"],parent_relation=i["relate"])
                self.node_array[i["id"]] = n_node
            except Exception as e:
                print(e)
        
        for index in self.node_array:
            node = self.node_array[index]
            if node.parent in self.node_array:
                node.parent = self.node_array[node.parent]
#                 node.parent.children.append(node)
                self.set_hash_for_dictionary(node)
            elif node.parent == '0':
                node.parent = self.root_node
#                 self.root_node.children.append(node) 
                self.set_hash_for_dictionary(node)
                
    def set_hash_for_dictionary(self,node):
        if node.id not in self.node_array:
            self.node_array[node.id] = node
        try:
            if node not in node.parent.children:
                node.parent.children.append(node)
        except Exception as e:
            print(e)
        
        if node.data not in self.node_dict:
            self.node_dict[node.data] = node
        else:
            next_node = self.node_dict[node.data]
            while True:
                loop = next_node.nexthash
                if loop:
                    next_node = next_node.nextNode
                else:
                    break
            next_node.nexthash = True
            next_node.nextNode = node
    
    def delete_hash_in_dictionary(self,node):
        if node.data in self.node_dict:
            #delete from parent 
            if node.parent and node in node.parent.children:
                node.parent.children.remove(node)
            
            cur_node = self.node_dict[node.data]
            last_node = None
            is_first = True
            while cur_node:
                if cur_node == node:
                    if cur_node.id in self.node_array:
                        del self.node_array[cur_node.id]
                        
                    if is_first:
                        if cur_node.nextNode:
                            del self.node_dict[node.data]
                            self.node_dict[node.data] = cur_node.nextNode
                        else:
                            del self.node_dict[node.data]
                    else:
                        last_node.nexthash = cur_node.nexthash
                        last_node.nextNode = cur_node.nextNode
                    break
                else:
                    last_node = cur_node
                    cur_node = cur_node.nextNode
                is_first = False  
#             del node
            return True
        else:
            return False
    
    def get_raw_text(self,sep=' '):
        raw_text = ""
        sorted_node = list(self.node_array.keys())
        sorted_node.sort()
        for i in sorted_node:
            raw_text += sep + self.node_array[i].data
        return raw_text
    
    def get_pos_text(self,sep=' '):
        pos_text = ""
        sorted_node = list(self.node_array.keys())
        sorted_node.sort()
        for i in sorted_node:
            pos_text += sep+self.node_array[i].pos
        return pos_text
    
    def get_tag_text(self,t_tag_b=" [",t_tag_e="] ",o_tag_b=" |",o_tag_e="| "):
        raw_text = ""
        sorted_node = list(self.node_array.keys())
        sorted_node.sort()
        for i in sorted_node:
            node = self.node_array[i]
            if node.type == 1:
                raw_text += " "+t_tag_b+node.data+t_tag_e
            elif node.type == 2:
                raw_text += " "+o_tag_b+node.data+o_tag_e
            else:
                raw_text += " "+node.data
        return raw_text

    def get_short_text_by_target(self, target):
        raw_text = target
        sorted_node = self.node_array.keys()
        sorted_node = sorted(list(sorted_node))
        node_id = sorted_node.index(self.node_dict[target].id)
        #add text before target word
        i = node_id - 1
        while i >= 0:
            if self.node_array[sorted_node[i]].pos not in ['w','wp'] and self.node_array[sorted_node[i]].data != 'root':
                raw_text = self.node_array[sorted_node[i]].data + raw_text
            else:
                break
            i -= 1
        
        i = node_id + 1
        while i < len(sorted_node):
            if self.node_array[sorted_node[i]].pos not in ['w','wp'] and self.node_array[sorted_node[i]].data != 'root':
                raw_text = raw_text + self.node_array[sorted_node[i]].data
            else:
                break
            i += 1
        return raw_text
        
def send_reviews_text_to_cload_parser(text):
    url_get_base = "http://api.ltp-cloud.com/analysis/"
    args = { 
        'api_key' : MY_AUTH_KEY,
        'text' : text,
        'pattern' : 'dp',
        'format' : 'json'
    }
    loop = True
    waiting_time = 1
    while(loop):
#         print 'waiting',str(waiting_time),'s'
        time.sleep(waiting_time)
        try:
            result = urllib.urlopen(url_get_base, urllib.urlencode(args)) # POST method
            content = json.loads(result.read())
            loop = False
        except Exception as e:
#             print Exception,":",e
            waiting_time = 1 #+ int(10 * random.random())
            
    return content

def decode_from_json_to_tree(text_parse_json):
    tree_array = []
    for segment in text_parse_json:
        for sentence_json in segment:
            tree = Tree(sentence_json)
            tree_array.append(tree)
    return  tree_array

def parse(text):
    text_parse_json = send_reviews_text_to_cload_parser(text)
    tree_array = decode_from_json_to_tree(text_parse_json)
    return tree_array