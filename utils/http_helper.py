#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import uuid
import traceback
import mimetypes
from tornado import gen
from bson import json_util
import http.cookies as Cookie
from functools import partial
from tornado.escape import to_basestring, native_str
from tornado.httpclient import HTTPError, HTTPRequest
from tornado.httpclient import AsyncHTTPClient, HTTPClient

global_cookie = Cookie.SimpleCookie()


@gen.coroutine
def call_api_async(url, headers, handle_response, handle_error=None, **kwargs):
    """
    异步调用本站或外部的API，可传文件和字典数据
    :param url: API地址，绝对地址或站内相对地址
    :param headers: self.request.headers
    :param handle_response: 调用成功后的结果回调函数，必须指定，函数的字典参数里有data或error成员
    :param handle_error: 调用失败的回调函数，函数参数为错误描述文本，不指定则抛出ValueError异常
    :param kwargs: 更多参数，可指定files、body、binary_response、params、error_code、connect_timeout、request_timeout 等参数
    :return: None
    """

    def _error(e):
        raise ValueError(error_code, e)

    def callback(r):
        _handle_response(r, handle_response, handle_error, binary_res, params_for_handler)

    if handle_error is None:
        handle_error = _error
    error_code = kwargs.pop('error_code', 500)
    request, binary_res, params_for_handler = _create_request(url, headers, **kwargs)
    client = AsyncHTTPClient()
    try:
        yield client.fetch(request, callback=callback)
    except (OSError, HTTPError) as err_con:
        handle_error('服务无响应: ' + str(err_con))


def call_api_sync(url, handle_response=None, handle_error=None, **kwargs):
    """
    同步调用外部API，可传文件和字典数据，在外部脚本或单元测试中使用
    :param url: API地址，绝对地址
    :param handle_response: 调用成功后的结果回调函数，函数的字典参数里有data或error成员，如果不指定则直接返回结果
    :param handle_error: 调用失败的回调函数，函数参数为错误描述文本，不指定则直接返回错误描述文本
    :param kwargs: 更多参数，可指定files、body、binary_response、params、connect_timeout、request_timeout 等参数
    :return: API调用结果(有data或error成员)、异常对象或错误描述文本
    """

    headers = kwargs.get('headers', {})
    cookie = kwargs.pop('cookie', global_cookie)
    headers['Cookie'] = ''.join(['%s=%s;' % (x, morsel.value) for (x, morsel) in cookie.items()])
    request, binary_res, params_for_handler = _create_request(url, headers, **kwargs)
    client = HTTPClient()
    try:
        response = client.fetch(request)
        ret = _handle_response(response, handle_response or (lambda r: r), handle_error or (lambda r: r),
                               binary_res, params_for_handler)
    except (OSError, HTTPError) as err_con:
        ret = handle_error(err_con) if handle_error else err_con

    client.close()
    return ret


def _create_request(url, headers, **kwargs):
    kwargs['connect_timeout'] = kwargs.get('connect_timeout', 5)
    kwargs['request_timeout'] = kwargs.get('request_timeout', 10)
    kwargs['method'] = kwargs.get('method', 'POST' if 'body' in kwargs or 'files' in kwargs else 'GET')

    # 设置cookie
    cookie = headers._dict.get('Cookie') if hasattr(headers, '_dict') else headers.get('Cookie')
    xsrf = re.search(r'(.+; *)?_xsrf *= *([^;" ]+)', cookie or '')
    if xsrf:
        headers['X-Xsrftoken'] = xsrf.group(2)

    # body参数，格式为body={'data': {...}}
    if isinstance(kwargs.get('body'), dict):
        kwargs['body'] = json_util.dumps(kwargs['body'])

    # files参数，格式为files={'img': img_path, 'csv': csv_path}，每个成员对应一个文件名
    files = kwargs.pop('files', None)
    if files:
        boundary = uuid.uuid4().hex
        headers.update({'Content-Type': 'multipart/form-data; boundary=%s' % boundary})
        producer = partial(body_producer, boundary, files, kwargs.pop('body', {}))
        request = HTTPRequest(url, headers=headers, body_producer=producer, validate_cert=False, **kwargs)
    else:
        request = HTTPRequest(url, headers=headers, validate_cert=False, **kwargs)

    return request, kwargs.pop('binary_response', False), kwargs.pop('params', {})


def _handle_response(r, handle_response, handle_error, binary_res, params_for_handler):
    if r.error:
        return handle_error(r.error)
    else:
        try:
            sc = r.headers._dict.get('Set-Cookie') if hasattr(r.headers, '_dict') else r.headers.get('Set-Cookie')
            if sc:
                text = native_str(sc)
                text = re.sub(r'Path=/(,)?', '', text)
                global_cookie.update(Cookie.SimpleCookie(text))
                while True:
                    global_cookie.update(Cookie.SimpleCookie(text))
                    if ',' not in text:
                        break
                    text = text[text.find(',') + 1:]

            if binary_res and r.body:
                return handle_response(r.body, **params_for_handler)
            else:
                try:
                    body = str(r.body, encoding='utf-8').strip()
                except UnicodeDecodeError:
                    body = str(r.body, encoding='gb18030').strip()
                except TypeError:
                    body = to_basestring(r.body).strip()
                return _handle_body(body, params_for_handler, handle_response, handle_error)

        except ValueError as err:
            return handle_error(str(err))
        except Exception as err:
            # err = '错误(%s): %s' % (err.__class__.__name__, str(err))
            traceback.print_exc()
            return handle_error(err)


def _handle_body(body, params_for_handler, handle_response, handle_error):
    if re.match(r'(\s|\n)*(<!DOCTYPE|<html)', body, re.I):
        return handle_response(body, **params_for_handler)
    else:
        body = json_util.loads(body)
        if isinstance(body, dict) and body.get('error'):
            return handle_error(body)
        else:
            return handle_response(body, **params_for_handler)


def body_producer(boundary, files, params, write):
    boundary_bytes = boundary.encode()
    cr_lf = b'\r\n'

    for arg_name in files:
        filename = files[arg_name]
        filename_bytes = filename.encode()
        write(b'--%s%s' % (boundary_bytes, cr_lf))
        write(b'Content-Disposition: form-data; name="%s"; filename="%s"%s' %
              (arg_name.encode(), filename_bytes, cr_lf))
        m_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        write(b'Content-Type: %s%s' % (m_type.encode(), cr_lf))
        write(cr_lf)
        with open(filename, 'rb') as f:
            while True:
                chunk = f.read(16 * 1024)
                if not chunk:
                    break
                write(chunk)
        write(cr_lf)

    params = json_util.loads(params) if isinstance(params, str) else params
    assert isinstance(params, dict)
    for arg_name in params:
        value = params[arg_name]
        value = json_util.dumps(value) if isinstance(value, dict) else str(value)
        write(b'--%s%s' % (boundary_bytes, cr_lf))
        write(b'Content-Disposition: form-data; name="%s"{}{}%s{}'.replace(b'{}', cr_lf) %
              (arg_name.encode(), value.encode()))

    write(b'--%s--%s' % (boundary_bytes, cr_lf))
