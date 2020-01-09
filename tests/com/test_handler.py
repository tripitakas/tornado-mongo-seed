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
            assert r is not None  # to test send_db_error
            self.send_data_response(dict(res=data['res']))
        except AssertionError as err:
            self.send_db_error(err)
        except DbError as err:
            self.send_db_error(err)


class TestHandler(APITestCase):
    def get_app(self):
        return APITestCase.get_app(self, extra_handlers=[DummyHandler])

    def tearDown(self):
        self._app.db.dummy.delete_one(dict(name='a'))
        super(TestHandler, self).tearDown()

    def test_dummy_api(self):
        self.assert_code(e.not_allowed_empty, self.fetch('/api/test/dummy', body={}))
        self.assert_code(e.not_allowed_empty, self.fetch('/api/test/dummy', body={'name': 'a'}))
        self.assert_code(e.db_error, self.fetch('/api/test/dummy', body={'data': {'name': 'a', 'res': 10}}))
        self._app.db.dummy.insert_one(dict(name='a'))
        r = self.fetch('/api/test/dummy', body={'data': {'name': 'a', 'res': 10}})
        self.assert_code(200, r)
        self.assertEqual(self.parse_response(r)['res'], 10)
