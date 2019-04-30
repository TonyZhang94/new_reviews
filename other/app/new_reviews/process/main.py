# -*- coding: utf-8 -*-

import queue
import threading

from new_reviews.process.analysis import push_data
from new_reviews.process.analysis import OpinionExtraction


if __name__ == '__main__':
    pcid, cid = "4", "50012097"
    kwargs = {"pcid": pcid, "cid": cid, "is_add": False,
              "src_table": "src", "dst_table": "dst"}

    msg_queue = queue.Queue(100)
    producer = threading.Thread(
        target=push_data, name='getSqlFromDB', args=(pcid, cid, msg_queue))
    comsumer = OpinionExtraction(msg_queue, **kwargs)
    producer.start()
    comsumer.start()
    producer.join()
    comsumer.join()

    result = comsumer.get_result()
