#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc: Handler基类
@time: 2018/6/23
"""

import re
import logging
import traceback
from bson import json_util
from bson.errors import BSONError
from bson.objectid import ObjectId
from datetime import datetime
from pymongo.errors import PyMongoError
from tornado.escape import to_basestring
from tornado.options import options
from tornado.web import RequestHandler, MissingArgumentError
from tornado_cors import CorsMixin
from controller import errors as e
from controller.com.access import prepare_access, can_access
from utils.helper import get_date_time
from utils.http_helper import call_api_async

MongoError = (PyMongoError, BSONError)
DbError = MongoError


class BaseHandler(CorsMixin, RequestHandler):
    """ 后端API响应类的基类 """
    CORS_HEADERS = 'Content-Type,Host,X-Forwarded-For,X-Requested-With,User-Agent,Cache-Control,Cookies,Set-Cookie'
    CORS_CREDENTIALS = True

    def __init__(self, application, request, **kwargs):
        super(BaseHandler, self).__init__(application, request, **kwargs)
        self.db = self.application.db
        self.config = self.application.config
        self.more = {}  # 给子类记录使用

    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*' if options.debug else self.application.site['domain'])
        self.set_header('Cache-Control', 'no-cache')
        self.set_header('Access-Control-Allow-Headers', self.CORS_HEADERS)
        self.set_header('Access-Control-Allow-Methods', self._get_methods())
        self.set_header('Access-Control-Allow-Credentials', 'true')

    def prepare(self):
        """ 调用 get/post 前的准备 """

        try:
            uid = self.get_query_argument('sso_id')
            name = self.get_query_argument('sso_name')
            roles = self.get_query_argument('roles')

            self.current_user = user = {'_id': ObjectId(uid), 'name': name, 'roles': roles}
            self.set_secure_cookie('user', json_util.dumps(user), expires_days=2)
            self.add_op_log('login_ok', message=user['name'])
            return self.redirect(self.request.path)
        except (MissingArgumentError, BSONError):
            pass

        return prepare_access(self, self.request.path, self.request.method)

    def get_current_user(self):
        if 'Access-Control-Allow-Origin' not in self._headers:
            self.write({'code': 403, 'error': 'Forbidden'})
            return self.finish()

        user = self.get_secure_cookie('user')
        try:
            return user and json_util.loads(user) or None
        except TypeError as err:
            print(user, str(err))

    def render(self, template_name, **kwargs):
        kwargs['currentRoles'] = self.current_user and self.current_user.get('roles') or ''
        kwargs['currentUserId'] = self.current_user and self.current_user.get('_id') or ''
        kwargs['debug'] = self.application.settings['debug']
        kwargs['site'] = dict(self.application.site)
        kwargs['current_path'] = self.request.path
        kwargs['full_url'] = self.request.full_url()
        # can_access/dumps/to_date_str传递给页面模板
        kwargs['can_access'] = lambda req_path, method='GET': can_access(self, req_path, method)
        kwargs['dumps'] = json_util.dumps
        kwargs['to_date_str'] = lambda t, fmt='%Y-%m-%d %H:%M': get_date_time(fmt=fmt, date_time=t) if t else ''
        if self._finished:  # check_auth 等处报错返回后就不再渲染
            return

        # 单元测试时，获取传递给页面的数据
        if self.get_query_argument('_raw', 0) == '1':
            kwargs = {k: v for k, v in kwargs.items() if not hasattr(v, '__call__') and k != 'error'}
            if template_name.startswith('_404') or template_name.startswith('_error'):
                return self.send_error_response((self.get_status(), self._reason), **kwargs)
            return self.send_data_response(**kwargs)

        logging.info(template_name + ' by ' + re.sub(r"^.+controller\.|'>", '', str(self.__class__)))
        try:
            super(BaseHandler, self).render(template_name, **kwargs)
        except Exception as err:
            traceback.print_exc()
            message = '网页生成出错(%s): %s' % (template_name, str(err) or err.__class__.__name__)
            kwargs.update(dict(code=500, message=message))
            super(BaseHandler, self).render('_error.html', **kwargs)

    def get_request_data(self):
        """
        获取请求数据。
        客户端请求需在请求体中包含 data 属性，例如 $.ajax({url: url, data: {data: some_obj}...
        """
        if 'data' not in self.request.body_arguments:
            body = b'{"data":' in self.request.body and json_util.loads(to_basestring(self.request.body)).get('data')
        else:
            body = json_util.loads(to_basestring(self.get_body_argument('data')))
        return body or {}

    def send_data_response(self, data=None, **kwargs):
        """
        发送正常响应内容，并结束处理
        :param data: 返回给请求的内容，字典或列表
        :param kwargs: 更多上下文参数
        :return: None
        """
        assert data is None or isinstance(data, (list, dict))
        self.set_header('Content-Type', 'application/json; charset=UTF-8')

        response = dict(status='success', data=data, code=200)
        response.update(kwargs)
        self.write(json_util.dumps(response))
        self.finish()

    def send_error_response(self, error=None, **kwargs):
        """
        反馈错误消息，并结束处理
        :param error: 单一错误描述的元组(见errors.py)，或多个错误的字典对象
        :param kwargs: 错误的具体上下文参数，例如 message、render、page_name
        :return: None
        """
        code, message = list(error.values())[0] if isinstance(error, dict) else error
        # 如果kwargs中含有message，则覆盖error中对应的message
        message = kwargs['message'] if kwargs.get('message') else message

        response = dict(status='failed', code=code, message=message, error=error)
        kwargs.pop('exc_info', 0)
        response.update(kwargs)

        render = '/api' not in self.request.path and not self.get_query_argument('_raw', 0)
        if response.pop('render', render):  # 如果是页面渲染请求，则返回错误页面
            return self.render('_error.html', **response)

        user_name = self.current_user and self.current_user['name']
        class_name = re.sub(r"^.+controller\.|'>", '', str(self.__class__)).split('.')[-1]
        logging.error('%d %s in %s [%s %s]' % (code, message, class_name, user_name, self.get_ip()))

        if not self._finished:
            response.pop('exc_info', None)
            self.set_header('Content-Type', 'application/json; charset=UTF-8')
            self.write(json_util.dumps(response))
            self.finish()

    def send_error(self, status_code=500, **kwargs):
        """拦截系统错误，不允许API调用"""
        self.write_error(status_code, **kwargs)

    def write_error(self, status_code, **kwargs):
        """拦截系统错误，不允许API调用"""
        assert isinstance(status_code, int)
        message = kwargs.get('message') or kwargs.get('reason') or self._reason
        exc = kwargs.get('exc_info')
        exc = exc and len(exc) == 3 and exc[1]
        message = message if message != 'OK' else '无权访问' if status_code == 403 else '后台服务出错 (%s, %s)' % (
            str(self).split('.')[-1].split(' ')[0],
            '%s(%s)' % (exc.__class__.__name__, re.sub(r"^'|'$", '', str(exc)))
        )
        if re.search(r'\[Errno \d+\]', message):
            code = int(re.sub(r'^.+Errno |\].+$', '', message))
            message = re.sub(r'^.+\]', '', message)
            message = '无法访问文档库' if code in [61] else '%s: %s' % (e.mongo_error[1], message)
            return self.send_error_response((e.mongo_error[0] + code, message))
        return self.send_error_response((status_code, message), **kwargs)

    def send_db_error(self, error, render=False):
        code = type(error.args) == tuple and len(error.args) > 1 and error.args[0] or 0
        if not isinstance(code, int):
            code = 0
        reason = re.sub(r'[<{;:].+$', '', error.args[1]) if code else re.sub(r'\(0.+$', '', str(error))
        if not code and '[Errno' in reason and isinstance(error, MongoError):
            code = int(re.sub(r'^.+Errno |\].+$', '', reason))
            reason = re.sub(r'^.+\]', '', reason)
            reason = '无法访问文档库' if code in [61] or 'Timeout' in error.__class__.__name__ else '%s(%s)%s' % (
                e.mongo_error[1], error.__class__.__name__, ': ' + (reason or '')
            )
            return self.send_error_response((e.mongo_error[0] + code, reason), render=render)

        if code:
            logging.error(error.args[1])
        if 'InvalidId' == error.__class__.__name__:
            code, reason = 1, e.no_object[1]
        if code not in [2003, 1]:
            traceback.print_exc()

        default_error = e.mongo_error if isinstance(error, MongoError) else e.db_error
        reason = '无法连接数据库' if code in [2003] else '%s(%s)%s' % (
            default_error[1], error.__class__.__name__, ': ' + (reason or '')
        )

        return self.send_error_response((default_error[0] + code, reason), render=render)

    def get_ip(self):
        ip = self.request.headers.get('x-forwarded-for') or self.request.remote_ip
        return ip and re.sub(r'^::\d$', '', ip[:15]) or '127.0.0.1'

    def add_op_log(self, op_type, target_id=None, message=None, username=None):
        username = username or self.current_user and self.current_user.get('name')
        user_id = self.current_user and self.current_user.get('_id')
        logging.info('%s,username=%s,target_id=%s,message=%s' % (op_type, username, target_id, message))
        try:
            self.db.log.insert_one(dict(
                op_type=op_type, username=username, user_id=user_id, target_id=target_id and str(target_id) or None,
                message=message, ip=self.get_ip(), create_time=datetime.now(),
            ))
        except MongoError:
            pass

    def call_back_api(self, url, handle_response, handle_error=None, **kwargs):
        self._auto_finish = False
        if not re.match(r'http(s)?://', url):
            url = '%s://localhost:%d%s' % (self.request.protocol, options['port'], url)
        call_api_async(url, self.request.headers, handle_response,
                       lambda s: handle_error(s) if handle_error else self.render('_error.html', code=500, message=s),
                       **kwargs)
