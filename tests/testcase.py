#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@time: 2018/12/22
"""
from tornado.escape import to_basestring, native_str
from tornado.testing import AsyncHTTPTestCase
from tornado.httpclient import HTTPRequest
from tornado.options import options
from functools import partial
from tornado.util import PY3
from bson import json_util
import uuid
import re
import mimetypes
import controller as c
from controller.app import Application

if PY3:
    import http.cookies as Cookie
else:
    import Cookie

cookie = Cookie.SimpleCookie()


# https://github.com/ooclab/ga.service/blob/master/src/codebase/utils/fetch_with_form.py
def body_producer(boundary, files, params, write):
    boundary_bytes = boundary.encode()
    crlf = b'\r\n'

    for arg_name in files:
        filename = files[arg_name]
        filename_bytes = filename.encode()
        write(b'--%s%s' % (boundary_bytes, crlf))
        write(b'Content-Disposition: form-data; name="%s"; filename="%s"%s' %
              (arg_name.encode(), filename_bytes, crlf))

        m_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        write(b'Content-Type: %s%s' % (m_type.encode(), crlf))
        write(crlf)
        with open(filename, 'rb') as f:
            while True:
                # 16k at a time.
                chunk = f.read(16 * 1024)
                if not chunk:
                    break
                write(chunk)

        write(crlf)

    assert isinstance(params, dict)
    for arg_name in params:
        value = str(params[arg_name])
        write(b'--%s%s' % (boundary_bytes, crlf))
        write(b'Content-Disposition: form-data; name="%s"{}{}%s{}'.replace(b'{}', crlf) %
              (arg_name.encode(), value.encode()))

    write(b'--%s--%s' % (boundary_bytes, crlf))


class APITestCase(AsyncHTTPTestCase):

    def get_app(self, testing=True, debug=False, extra_handlers=None):
        options.testing = testing
        options.debug = debug
        options.port = self.get_http_port()
        return Application(c.handlers + c.views + (extra_handlers or []), db_name_ext='_test',
                           ui_modules=c.modules, default_handler_class=c.InvalidPageHandler)

    def tearDown(self):
        super(APITestCase, self).tearDown()
        self._app.stop()

    @staticmethod
    def parse_response(response):
        body = response.body and to_basestring(response.body) or '{}'
        if body and body.startswith('{'):
            body = json_util.loads(body)
            if 'data' in body and isinstance(body['data'], dict):  # 将data的内容赋给body，以便测试使用
                body.update(body['data'])
            elif 'error' in body and isinstance(body['error'], dict):
                body.update(body['error'])
        if response.code != 200 and 'code' not in body:
            body = dict(code=response.code, message=response.reason)
        return body

    def get_code(self, response):
        response = self.parse_response(response)
        return isinstance(response, dict) and response.get('code')

    def assert_code(self, code, response, msg=None):
        """
        判断response中是否存在code
        :param code: 有三种类型：code; (code, message); [(code, message), (code, message)...]
        :param response: 请求的响应体
        """
        code = code[0] if isinstance(code, tuple) else code
        r_code = self.get_code(response) if self.get_code(response) else response.code
        if isinstance(code, list):
            self.assertIn(r_code, [c[0] if isinstance(c, tuple) else c for c in code], msg=msg)
        else:
            self.assertEqual(code, r_code, msg=msg)

    def fetch(self, url, **kwargs):
        files = kwargs.pop('files', None)  # files包含字段名和文件名，例如 files={'img': img_path}
        if isinstance(kwargs.get('body'), dict):
            if not files:
                kwargs['body'] = json_util.dumps(kwargs['body'])
            elif 'data' in kwargs['body']:  # 可以同时指定files和body={'data': {...}}，在API内取 self.get_request_data()
                kwargs['body']['data'] = json_util.dumps(kwargs['body']['data'])
        if 'body' in kwargs or files:
            kwargs['method'] = kwargs.get('method', 'POST')

        headers = kwargs.get('headers', {})
        headers['Cookie'] = ''.join(['%s=%s;' % (x, morsel.value) for (x, morsel) in cookie.items()])

        host = kwargs.pop('host', None)
        url = url if re.match('^http', url) else (host + url if host else self.get_url(url))
        if files:
            boundary = uuid.uuid4().hex
            headers.update({'Content-Type': 'multipart/form-data; boundary=%s' % boundary})
            producer = partial(body_producer, boundary, files, kwargs.pop('body', {}))
            request = HTTPRequest(url, headers=headers, body_producer=producer, **kwargs)
        else:
            request = HTTPRequest(url, headers=headers, **kwargs)

        self.http_client.fetch(request, self.stop)

        response = self.wait(timeout=60)
        headers = response.headers
        try:
            sc = headers._dict.get('Set-Cookie') if hasattr(headers, '_dict') else headers.get('Set-Cookie')
            if sc:
                text = native_str(sc)
                text = re.sub(r'Path=/(,)?', '', text)
                cookie.update(Cookie.SimpleCookie(text))
                while True:
                    cookie.update(Cookie.SimpleCookie(text))
                    if ',' not in text:
                        break
                    text = text[text.find(',') + 1:]
        except KeyError:
            pass

        return response
