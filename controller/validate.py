#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc: 数据校验类
@time: 2019/4/29
"""

import re
from bson.objectid import ObjectId
from tornado.web import Finish
import controller.errors as e


def validate(data, rules, handler=None):
    """
    数据校验主控函数
    :param data:  待校验的数据，一般是指从页面POST的dict类型的数据
    :param rules: 校验规则列表，每个rule是一个(func, para1, para2, ...)元组，其中，func是校验工具函数。关于para1、para2等参数：
                  1. 如果是字符串格式，则表示data的属性，将data[para1]数据作为参数传递给func函数
                  2. 如果不是字符串格式，则直接作为参数传递给func函数
    :param handler: Web请求响应对象，指定则发送错误消息并抛出异常结束
    :return: 如果校验有误，则返回校验错误，格式为{key: (error_code, message)}，其中，key为data的属性。无误，则无返回值。
    """
    errs = {}
    for rule in rules:
        func = rule[0]
        kw = {para: data.get(para) for para in rule[1:] if isinstance(para, str)}
        args = [para for para in rule[1:] if not isinstance(para, str)]
        ret = func(*args, **kw)
        if ret:
            errs.update(ret)
    if errs and handler:
        handler.send_error_response(errs)
        raise Finish()
    return errs or None


def i18n_trans(key):
    maps = {
        'title': '名称',
        'name': '姓名',
    }
    return maps[key] if key in maps else key


def not_empty(**kw):
    """不允许为空以及空串"""
    code, message = e.not_allowed_empty
    errs = {k: (code, message % i18n_trans(k)) for k, v in kw.items() if not v}
    return errs or None


def not_both_empty(**kw):
    """不允许同时为空以及空串"""
    assert len(kw) == 2
    k1, k2 = kw.keys()
    v1, v2 = kw.values()
    code, message = e.not_allowed_both_empty
    err = code, message % (i18n_trans(k1), i18n_trans(k2))
    if not v1 and not v2:
        return {k1: err, k2: err}


def not_equal(**kw):
    assert len(kw) == 2
    k1, k2 = kw.keys()
    v1, v2 = kw.values()
    code, message = e.both_times_equal
    err = code, message % (i18n_trans(k1), i18n_trans(k2))
    if v1 == v2:
        return {k1: err, k2: err}


def equal(**kw):
    assert len(kw) == 2
    k1, k2 = kw.keys()
    v1, v2 = kw.values()
    code, message = e.not_equal
    err = code, message % (i18n_trans(k1), i18n_trans(k2))
    if v1 != v2:
        return {k1: err, k2: err}


def is_name(**kw):
    """ 检查是否为姓名。"""
    assert len(kw) == 1
    k, v = list(kw.items())[0]
    regex = r'^[\u4E00-\u9FA5]{2,5}$|^[A-Za-z][A-Za-z -]{2,19}$'
    # 值为空或空串时跳过而不检查
    if v and not re.match(regex, v):
        return {k: e.invalid_name}


def is_phone(**kw):
    """ 检查是否为手机。"""
    assert len(kw) == 1
    k, v = list(kw.items())[0]
    regex = r'^1[34578]\d{9}$'
    # 值为空或空串时跳过而不检查
    if v and not re.match(regex, str(v)):
        return {k: e.invalid_phone}


def is_email(**kw):
    """ 检查是否为邮箱。"""
    assert len(kw) == 1
    k, v = list(kw.items())[0]
    regex = r'^[a-z0-9][a-z0-9_.-]+@[a-z0-9_-]+(\.[a-z]+){1,2}$'
    # 值为空或空串时跳过而不检查
    if v and not re.match(regex, v):
        return {k: e.invalid_email}


def is_phone_or_email(**kw):
    """ 检查是否为手机或邮箱。"""
    assert len(kw) == 1
    k, v = list(kw.items())[0]
    email_regex = r'^[a-z0-9][a-z0-9_.-]+@[a-z0-9_-]+(\.[a-z]+){1,2}$'
    phone_regex = r'^1[34578]\d{9}$'
    # 值为空或空串时跳过而不检查
    if v and not re.match(email_regex, v) and not re.match(phone_regex, v):
        return {k: e.invalid_phone_or_email}


def is_password(**kw):
    """ 检查是否为密码。"""
    assert len(kw) == 1
    k, v = list(kw.items())[0]
    regex = r'^(?![0-9]+$)(?![a-zA-Z]+$)[A-Za-z0-9,.;:!@#$%^&*-_]{6,18}$'
    # 值为空或空串时跳过而不检查
    if v and not re.match(regex, str(v)):
        return {k: e.invalid_password}


def is_digit(**kw):
    """ 检查是否为数字。"""
    code, message = e.invalid_digit
    errs = {k: (code, '%s:%s' % (k, message)) for k, v in kw.items() if v and not re.match(r'^\d+$', str(v))}
    return errs or None


def between(min_v, max_v, **kw):
    assert len(kw) == 1
    k, v = list(kw.items())[0]
    if isinstance(v, str) and re.match(r'^\d+$', v):
        v = int(v)
    code, message = e.invalid_range
    err = code, message % (i18n_trans(k), min_v, max_v)
    if isinstance(v, int) and (v < min_v or v > max_v):
        return {k: err}


def in_list(lst, **kw):
    """检查是否在lst列表中"""
    k, v = list(kw.items())[0]
    if v:
        code, message = e.should_in_list
        err = code, message % (i18n_trans(k), lst)
        assert type(v) in [str, list]
        v = [v] if isinstance(v, str) else v
        not_in = [i for i in v if i not in lst]
        if not_in:
            return {k: err}


def has_fields(fields, **kw):
    """检查是否有fields中的字段"""
    k, v = list(kw.items())[0]
    if v:
        need_fields = [r for r in fields if r not in v.keys()]
        if need_fields:
            err = e.tptk_field_error[0], '缺字段：%s' % ','.join(need_fields)
            return {k: err}


def not_existed(collection=None, exclude_id=None, **kw):
    """
    校验数据库中是否不存在kw中对应的记录，存在则报错
    :param collection: mongdb的collection
    :param exclude_id: 校验时，排除某个id对应的记录
    """
    errs = {}
    code, message = e.record_existed
    if collection:
        for k, v in kw.items():
            condition = {k: v}
            if exclude_id:
                condition['_id'] = {'$ne': exclude_id}
            if v and collection.find_one(condition):
                errs[k] = code, message % i18n_trans(k)
    return errs or None


def exist(collection=None, **kw):
    """
    校验数据库中是否存在kw中对应的记录，不存在则报错
    :param collection: mongdb的collection
    """
    errs = {}
    code, message = e.record_existed
    if collection:
        for k, v in kw.items():
            condition = {k: ObjectId(v) if k == '_id' else v}
            if v and not collection.find_one(condition):
                errs[k] = code, message % i18n_trans(k)
    return errs or None


def is_unique(collection=None, **kw):
    """校验数据库中是否唯一"""
    errs = {}
    code, message = e.record_existed
    if collection:
        for k, v in kw.items():
            if v is not None and collection.count_documents({k: v}) > 1:
                errs[k] = code, message % i18n_trans(k)
    return errs or None
