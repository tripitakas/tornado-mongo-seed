#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc: 加载app.yml、连接数据库、常用实用函数
@time: 2019/11/6
"""
from tornado.util import PY3
from os import path
from yaml import load as load_yml, SafeLoader
import pymongo

from hashids import Hashids
from datetime import datetime, timedelta
import inspect
import logging
import re

BASE_DIR = path.dirname(path.dirname(__file__))


def load_config():
    param = dict(encoding='utf-8') if PY3 else {}
    cfg_base = path.join(BASE_DIR, '_app.yml')
    cfg_file = path.join(BASE_DIR, 'app.yml')
    config = {}

    with open(cfg_base, **param) as f:
        config_base = load_yml(f, Loader=SafeLoader)
    if path.exists(cfg_file):
        with open(cfg_file, **param) as f:
            config = load_yml(f, Loader=SafeLoader)
    else:
        with open(cfg_file, 'w') as f:
            f.write('todo:')
    for k, v in config_base.items():
        if k not in config or k in ['site']:
            config[k] = v

    return config


def connect_db(cfg):
    if cfg.get('user'):
        uri = 'mongodb://{0}:{1}@{2}:{3}/admin'.format(
            cfg.get('user'), cfg.get('password'), cfg.get('host'), cfg.get('port', 27017)
        )
    else:
        uri = 'mongodb://{0}:{1}/'.format(cfg.get('host'), cfg.get('port', 27017))
    conn = pymongo.MongoClient(
        uri, connectTimeoutMS=2000, serverSelectionTimeoutMS=2000,
        maxPoolSize=10, waitQueueTimeoutMS=5000
    )
    return conn[cfg['name']], uri


def prop(obj, key, default=None):
    for s in key.split('.'):
        obj = obj.get(s) if isinstance(obj, dict) else None
    return default if obj is None else obj


def get_date_time(fmt=None, date_time=None, diff_seconds=None):
    time = date_time if date_time else datetime.now()
    if diff_seconds:
        time += timedelta(seconds=diff_seconds)

    return time.astimezone().strftime(fmt or '%Y-%m-%d %H:%M:%S')


def gen_id(value, salt='', rand=False, length=16):
    coder = Hashids(salt=salt and rand and salt + str(datetime.now().second) or salt, min_length=16)
    if isinstance(value, bytes):
        return coder.encode(*value)[:length]
    return coder.encode(*[ord(c) for c in list(value or [])])[:length]


def my_framer():
    """ 出错输出日志时原本显示的是底层代码文件，此类沿调用堆栈往上显示更具体的调用者 """
    f0 = f = old_framer()
    if f is not None:
        until = [s[1] for s in inspect.stack() if re.search(r'controller/(view|api)', s[1])]
        if until:
            while f.f_code.co_filename != until[0]:
                f0 = f
                f = f.f_back
            return f0
        f = f.f_back
        while re.search(r'web\.py|logging', f.f_code.co_filename):
            f0 = f
            f = f.f_back
    return f0


old_framer = logging.currentframe
logging.currentframe = my_framer
