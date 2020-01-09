#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@desc: 首页
@time: 2018/6/23
"""

import re
import inspect
from operator import itemgetter
from controller.base import BaseHandler


class InvalidPageHandler(BaseHandler):
    def prepare(self):
        pass  # ignore roles

    def get(self):
        self.set_status(404, reason='Not found')
        if '/api/' in self.request.path:
            return self.finish()
        self.render('_error.html', code=404, message=self.request.path + ' 页面不存在')

    def post(self):
        self.get()


class ApiTable(BaseHandler):
    URL = '/api'

    def get(self):
        """ 显示后端API和前端路由 """

        def get_doc():
            assert func.__doc__, str(func) + ' no comment'
            return func.__doc__.strip().split('\n')[0]

        handlers = []
        for cls in self.application.handlers:
            handler = cls(self.application, self.request)
            file = 'controller' + re.sub(r'^.+controller', '', inspect.getsourcefile(cls))
            file += '\n' + inspect.getsource(cls).split('\n')[0][:-1]
            for method in handler._get_methods().split(','):
                method = method.strip()
                if method != 'OPTIONS':
                    assert method.lower() in cls.__dict__, cls.__name__
                    func = cls.__dict__[method.lower()]
                    func_name = re.sub(r'<|function |at .+$', '', str(func)).strip()
                    self.add_handlers(cls, file, func_name, get_doc, handlers, method)
        handlers.sort(key=itemgetter(0))
        self.render('_api.html', version=self.application.version, handlers=handlers)

    @staticmethod
    def add_handlers(cls, file, func_name, get_doc, handlers, method):
        def add_handler(url, idx=0):
            handlers.append((url, func_name, idx, file, get_doc()))

        if isinstance(cls.URL, list):
            for i, url_ in enumerate(cls.URL):
                add_handler(url_, i + 1)
        else:
            add_handler(cls.URL)
