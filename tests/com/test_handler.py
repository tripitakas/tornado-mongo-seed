#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tests.testcase import APITestCase
from controller.base import BaseHandler, DbError
from controller import validate as v
import controller.errors as e


class DummyHandler(BaseHandler):
    URL = '/api/test/dummy'

    def post(self):
        """测试数据返回"""
        data = self.get_request_data()
        v.validate(data, [
            (v.not_empty, 'name')
        ], self)

        try:
            r = self.db.dummy.find_one(dict(name=data['name']))
            assert r  # to test send_db_error
            self.call_back_api('/api?_raw=1', lambda d: self.db.dummy.delete_one(name=data['name']))
            self.send_data_response()
        except AssertionError as err:
            self.send_db_error(err)
        except DbError as err:
            self.send_db_error(err)


class TestHandler(APITestCase):
    def get_app(self):
        return APITestCase.get_app(self, extra_handlers=[DummyHandler])

    def test_dummy_api(self):
        self.assert_code(e.not_allowed_empty, self.fetch('/api/test/dummy', body={}))
        self.assert_code(e.not_allowed_empty, self.fetch('/api/test/dummy', body={'name': 'a'}))
        self.assert_code(e.db_error, self.fetch('/api/test/dummy', body={'data': {'name': 'a'}}))
        self._app.db.dummy.insert_one(dict(name='a'))
        self.assert_code(200, self.fetch('/api/test/dummy', body={'data': {'name': 'a'}}))
