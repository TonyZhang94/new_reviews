from zhuican.settings.dev import *


BROKER_URL = 'amqp://zhuican:zczx2012@192.168.1.6/zhuican_reviews_test'
CELERY_RESULT_BACKEND = 'redis://192.168.1.111:6379/0'
DEBUG = True