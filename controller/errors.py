#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc 定义后端API的错误码和数据库常用函数
@time: 2018/10/23
"""

need_login = 403, '尚未登录'
db_error = 10000, '服务访问出错'
mongo_error = 20000, '文档库访问出错'

multiple_errors = 1000, '多个数据校验错误'
not_allowed_empty = 1001, '%s不允许为空'
not_allowed_both_empty = 1002, '%s和%s不允许同时为空'
invalid_name = 1003, '姓名应为2~5个汉字，或3~20个英文字母（可含空格和-）'
invalid_phone = 1004, '手机号码格式有误'
invalid_email = 1005, '邮箱格式有误'
invalid_password = 1006, '密码应为6至18位由数字、字母和英文符号组成的字符串，不可以为纯数字或纯字母'
invalid_range = 1007, '%s数据范围应为[%s, %s]'
need_phone_or_email = 1008, '没有指定手机或邮箱'
invalid_phone_or_email = 1009, '手机或邮箱格式有误'
need_password = 1010, '没有指定密码'
both_times_equal = 1011, '%s和%s一致'
not_equal = 1012, '%s和%s不一致'
record_existed = 1013, '%s已存在'
record_not_existed = 1014, '%s不存在'
should_in_list = 1016, '%s应在列表%s中'
invalid_digit = 1018, '数字格式有误'

no_object = 2000, '对象不存在'
no_user = 2001, '用户不存在'
unauthorized = 2002, '没有权限'
url_not_config = 2003, '路径没有配置'
