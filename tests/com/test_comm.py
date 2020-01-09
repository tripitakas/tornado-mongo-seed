#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tests.testcase import APITestCase
from controller import validate as v
import controller.errors as e
import logging


class TestCommon(APITestCase):
    def test_validate(self):
        data = {'name': '1234567890', 'phone': '1', 'email': '1', 'password': '', 'age': 8, 'old_password': ''}
        rules = [
            (v.not_empty, 'name', 'password'),
            (v.not_both_empty, 'old_password', 'password'),
            (v.is_name, 'name'),
            (v.is_phone_or_email, 'phone'),
            (v.is_phone, 'phone'),
            (v.is_email, 'email'),
            (v.is_password, 'name'),
            (v.is_digit, 'phone'),
            (v.between, 'age', 10, 100),
            (v.not_equal, 'password', 'old_password'),
            (v.equal, 'password', 'age'),
            (v.in_list, 'email', ['a', 'b'])
        ]

        errs = v.validate(data, rules)
        self.assertEqual(set(errs.keys()), {'age', 'email', 'name', 'password', 'phone', 'old_password'})
        for k, t in errs.items():
            self.assertIs(t.__class__, tuple)
            self.assertIs(t[0].__class__, int)
            self.assertIs(t[1].__class__, str)

    def test_db(self):
        self._app.db.tmp.drop()
        logging.error('test')

    def test_show_api(self):
        self.assert_code(200, self.fetch('/'))
        self.assert_code(200, self.fetch('/api?_raw=1'))

    def test_404(self):
        self.assert_code(404, self.fetch('/api_err'))
        self.assert_code(404, self.fetch('/api/err'))
        self.assert_code(404, self.fetch('/api/err', body={}))

    def test_login(self):
        if self.get_code(self.fetch('/api/user/login?next=/')) == 200:
            self.assert_code(200, self.fetch('/?sso_id=5dc3a702f524debab6a74f2d&sso_name=张三&roles='))
