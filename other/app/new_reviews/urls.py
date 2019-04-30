# @Time    : 17-9-21 下午4:37
# @Author  : Dragon
# @Site    : 
# @File    : urls.py
# @Software: PyCharm


from django.conf.urls import url
from new_reviews import views

urlpatterns = [
    url(r'search/$', views.reviews),  # 文本处理主页
    url(r'create_new_state$', views.create_new_state),  # create new state about cid
    url(r'sentence_parse_step$', views.sentence_parse_step),  # run sentence parse
    url(r'reviews_extraction_step$', views.reviews_extraction_step),  # run sentence parse
    url(r'features_extraction_step$', views.features_extraction_step),  # run sentence parse
    url(r'jump_features_check$', views.jump_features_check),  # jump feature check step
    url(r'reset_status$', views.reset_configuration),  # reset some pcid cid status
    url(r'tags/$', views.tagscheck),  # 属性标注
    url(r'update_targets$', views.update_targets),  # 属性标注更新
    url(r'opinions/$', views.opinionscheck),  # 观点标注
    url(r'update_opinions$', views.update_opinions),  # 观点标注更新
    # url(r'word_clusters/$', views.wordcluster),  # 聚类检查页面
    url(r'^word_clusters/$', views.wordcluster_v2),  # 聚类检查页面
    url(r'^cluster/words/(?P<pcid>[0-9]{1,3})/(?P<cid>[0-9]+)/$', views.get_words_cluster_result),  # 获取聚类结果
    url(r'^cluster/words/(?P<pcid>[0-9]{1,3})/(?P<cid>[0-9]+)/delete/$', views.delete_words_cluster_result),  # 删除聚类结果
    url(r'^update_clusters/$', views.update_clusters),  # 聚类结果更新
    url(r'^update_clusters/v2/$', views.update_clusters_v2),  # 聚类结果更新
    url(r'cluster_targets$', views.cluster_targets),  # 进行聚类

    # 词库主页
    url(
        r'^lexicon/(?P<lexicon_type>(synonym_global)|(synonym)|(target_global)|(target))/$',
        views.get_lexicon_list,
    ),
    # 编辑词库
    url(
        r'^lexicon/(?P<lexicon_type>(synonym_global)|(synonym)|(target_global)|(target))/'
        r'(?P<op>(save)|(delete)|(reverse))/$',
        views.edit_lexicon,
    ),
    # 批量修改词库
    url(
        r'^lexicon/(?P<lexicon_type>(synonym_global)|(synonym)|(target_global)|(target))/save/all/$',
        views.save_lexicon,
    ),

    url(r'^sentiment/$', views.show_cid_sentiment),  # 品类情感词合并页面
    url(r'^sentiment/save/$', views.save_cid_sentiment),  # 保存品类情感词
    url(r'^sentiment/save/one/$', views.save_cid_sentiment_one),  # 保存品类下单个情感词
    url(r'^sentiment/global/$', views.get_sentiment_global_list),  # 全局情感词库主页
    url(r'^sentiment/global/(?P<op>(save)|(delete)|(reverse))/$', views.edit_sentiment_global),  # 编辑全局情感词库

    # 批量修改词库
    url(
        r'^sentiment/global/save/all/$',
        views.save_sentiment_global,
    ),

    url(r'^model/targets/$', views.get_model_reviews_targets),  # 获取单品罗盘评价数据
    url(r'^model/targets/download/$', views.download_model_reviews_targets),  # 下载单品罗盘评价数据
    url(r'^model/targets/upload/$', views.upload_model_reviews_target),  # 上传单品罗盘评价数据

    url(r'model/features_extraction/$', views.model_reviews_features_extraction),  # 单品罗盘提取属性
]
