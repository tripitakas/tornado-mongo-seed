#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado.web import urlencode
from controller.base import BaseHandler


class HomeHandler(BaseHandler):
    URL = ['/', '/home']

    def get(self):
        """ 首页 """
        self.redirect('/api')


class LoginHandler(BaseHandler):
    URL = '/api/user/login'

    def get(self):
        """转到SSO登录页面"""
        next_url = self.get_query_argument('next')
        next_url += ('&' if '?' in next_url else '?') + 'info=1'
        url = self.get_login_url()
        url += ('&' if '?' in url else '?') + urlencode(dict(next=next_url))
        self.redirect(url)
