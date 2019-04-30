# -*- coding: utf-8 -*-

"""
2019/04/28
地理名词&一些其他无用词
"""

# http://www.resgain.net/country.html


def knowledge_useless():
    useless_words = ["新品", "清仓", "降价", "促销", "秒杀", "只限", "购物", "国庆", "五一", "双十一", "双十二",
                     "抢鲜", "抵扣", "特价", "活动", "开业", "全场", "特惠", "包邮", "新款", "打折", "新年",
                     "新春", "迎新", "减价", "新店", "狂欢", "限时", "限购", "全国", "半价", "专属", "活动",
                     "换季", "店庆", "团购", "专享", "淘宝", "天猫", "京东", "爆款", "满减", "一口价", "回馈",
                     "年末", "周年", "同款", "折扣", "其他", "其它", "其他品牌", "淘金币", "双10一", "买", "减",
                     "批发", "快递", "代购", "点券", "疯抢", "薄利多销", "惊喜价", "亏本", "发货", "超值", "现货",
                     "涨价", "冲销量", "已售", "推荐", "出租", "尝鲜价", "冰点价", "甩卖", "酬宾", "清货", "包年",
                     "包月", "即将", "拍前", "节日大促", "晒图", "同款", "旗舰店", "专业", "品牌", "专柜", "专用"
                     ]
    return useless_words


def knowledge_country():
    country_base = ["中", "日", "韩", "英", "法", "德", "美", "泰"]
    country = list()
    country.extend([x+"国" for x in country_base])
    country.extend([x+"式" for x in country_base])
    country.extend([x+"系" for x in country_base])

    other_country = ["欧式", "意式", "港式", "台湾"]
    country.extend(other_country)

    country_key = set()
    country_map = dict()
    for base in country_base:
        key = base + "式"
        country_key.add(key)
        country_map[key] = set()
        country_map[key].add(key)
        country_map[key].add(base + "系")
        country_map[key].add(base + "国")

    for other in other_country:
        key = other
        country_key.add(key)
        country_map[key] = set()
        country_map[key].add(key)

    country.append("意大利")
    country_map["意式"].add("意大利")
    country.append("欧美")
    country_map["欧式"].add("欧美")
    country.append("香港")
    country_map["港式"].add("香港")
    country.append("日本")
    country_map["日式"].add("日本")

    return set(country), country_key, country_map


def common_char():
    chars = ["色", "款", "式", "防", "无"]
    return set(chars)


if __name__ == '__main__':
    words = knowledge_useless()
    with open("lexicon/sales.txt", mode="w", encoding="utf-8") as fp:
        content = "\n".join(words) + "\n"
        fp.write(content)

    words, _, _ = knowledge_country()
    words = sorted(list(words))

    cities = ["北京", "天津", "上海", "重庆", "香港", "澳门",
              "苏州", "温州", "深圳", "东莞", "潮汕", "三亚", "吐鲁番"
                                                  "呼和浩特", "拉萨", "乌鲁木齐", "银川", "南宁",
              "哈尔冰", "长春", "沈阳",
              "石家庄", "太原", "济南", "西安", "武汉", "长沙", "南昌", "合肥", "郑州",
              "南京", "浙江",
              "成都", "昆明", "贵阳",
              "兰州", "西宁",
              "福州", "广州", "海口", "台北"]
    provinces = ["内蒙古", "西藏", "新疆", "宁夏", "广西",
                 "黑龙江", "吉林", "辽宁",
                 "河北", "山西", "山东", "陕西", "湖北", "湖南", "江西", "安徽", "河南",
                 "江苏", "浙江",
                 "四川", "云南", "贵州",
                 "甘肃", "青海",
                 "福建", "广东", "海南", "台湾"]

    for city in cities:
        words.append(city)
        words.append(city + "市")
    for province in provinces:
        words.append(province)
        words.append(province + "省")

    words.append("亚洲")
    words.append("东北亚")
    words.append("东亚")
    words.append("东南亚")
    words.append("南亚")
    words.append("西亚")
    words.append("中东")
    words.append("阿拉伯")
    words.append("东欧")
    words.append("南欧")
    words.append("西欧")
    words.append("北欧")
    words.append("非洲")
    words.append("东非")
    words.append("南非")
    words.append("西非")
    words.append("北非")
    words.append("美洲")
    words.append("北美")
    words.append("南美")
    words.append("澳洲")
    words.append("大洋洲")
    words.append("南极")
    words.append("南极洲")
    words.append("南极圈")
    words.append("北极")
    words.append("北极圈")

    words.append("地中海")
    words.append("爱情海")
    words.append("红海")
    words.append("黑海")
    words.append("南海")
    words.append("东海")
    words.append("黄海")
    words.append("渤海")
    words.append("北海道")
    words.append("索马里")
    words.append("撒哈拉沙漠")
    words.append("西伯利亚")
    words.append("高加索")
    words.append("高加索山脉")
    words.append("阿尔卑斯山")
    words.append("喜马拉雅山")
    words.append("昆仑山")
    words.append("天山")
    words.append("青藏高原")
    words.append("黄土高原")
    words.append("云贵高原")
    words.append("吐鲁番盆地")
    words.append("准格尔盆地")
    words.append("塔里木盆地")
    words.append("贝加尔湖")
    words.append("南方")
    words.append("北冰洋")
    words.append("太平洋")
    words.append("大西洋")
    words.append("印度洋")
    words.append("热带")

    words.append("俄罗斯")
    words.append("马来西亚")
    words.append("新加坡")
    words.append("印度尼西亚")
    words.append("印尼")
    words.append("菲律宾")
    words.append("文莱")
    words.append("越南")
    words.append("缅甸")
    words.append("印度")
    words.append("斯里兰卡")
    words.append("马尔代夫")
    words.append("巴基斯坦")
    words.append("以色列")
    words.append("土耳其")
    words.append("沙特阿拉伯")
    words.append("沙特")
    words.append("巴勒斯坦")
    words.append("卡塔尔")
    words.append("瑞士")
    words.append("瑞典")
    words.append("丹麦")
    words.append("冰岛")
    words.append("比利时")
    words.append("卢森堡")
    words.append("荷兰")
    words.append("奥地利")
    words.append("希腊")
    words.append("克罗地亚")
    words.append("马其顿")
    words.append("塞尔维亚")
    words.append("芬兰")
    words.append("爱尔兰")
    words.append("英格兰")
    words.append("挪威")
    words.append("葡萄牙")
    words.append("西班牙")
    words.append("波兰")
    words.append("乌克兰")
    words.append("匈牙利")
    words.append("立陶宛")
    words.append("爱沙尼亚")
    words.append("保加利亚")
    words.append("安道尔")
    words.append("白俄罗斯")
    words.append("南非")
    words.append("坦桑尼亚")
    words.append("埃塞俄比亚")
    words.append("喀麦隆")
    words.append("肯尼亚")
    words.append("尼日利亚")
    words.append("摩洛哥")
    words.append("几内亚")
    words.append("津巴布韦")
    words.append("赤道几内亚")
    words.append("埃及")
    words.append("加拿大")
    words.append("墨西哥")
    words.append("古巴")
    words.append("巴西")
    words.append("哥伦比亚")
    words.append("乌拉圭")
    words.append("阿根廷")
    words.append("智利")
    words.append("秘鲁")
    words.append("澳大利亚")
    words.append("新西兰")

    words.append("伦敦")
    words.append("巴黎")
    words.append("哥本哈根")
    words.append("雅典")
    words.append("罗马")
    words.append("柏林")
    words.append("纽约")
    words.append("华盛顿")
    words.append("西雅图")
    words.append("洛杉矶")
    words.append("芝加哥")
    words.append("莫斯科")
    words.append("东京")
    words.append("大阪")
    words.append("平壤")
    words.append("汉城")
    words.append("吉隆坡")
    words.append("雅加达")
    words.append("墨西哥城")
    words.append("巴西利亚")

    # 爬一个国家首都网站？

    with open("lexicon/geography.txt", mode="w", encoding="utf-8") as fp:
        content = "\n".join(words) + "\n"
        fp.write(content)
