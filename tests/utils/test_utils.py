#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@time: 2019/05/07
"""
from tests.testcase import APITestCase
from datetime import datetime
from utils import helper as h
from utils.http_helper import call_api_async, call_api_sync


class TestHelper(APITestCase):
    def test_prop(self):
        obj = {'a': 1, 'b': {'x': 2, 'y': dict(name='a')}}
        self.assertEqual(h.prop(obj, 'a'), 1)
        self.assertEqual(h.prop(obj, 'b.x'), 2)
        self.assertEqual(h.prop(obj, 'b.c'), None)
        self.assertEqual(h.prop(obj, 'b.y.name'), 'a')

    def test_date_time(self):
        self.assertEqual(h.get_date_time(date_time=datetime(2020, 1, 8, 12)), '2020-01-08 12:00:00')
        self.assertEqual(h.get_date_time(date_time=datetime(2020, 1, 8, 12), diff_seconds=1), '2020-01-08 12:00:01')

    def test_gen_id(self):
        self.assertEqual(h.gen_id('a'), '3VXyMYer0EbOBQn6')
        self.assertEqual(h.gen_id(b'a'), '3VXyMYer0EbOBQn6')

    def test_call_api_sync(self):
        self.assertIsInstance(call_api_sync('http://localhost:123'), ConnectionError)
        if isinstance(call_api_sync('http://localhost:8000/user/login'), str):
            r = call_api_sync('http://localhost:8000/api/user/login', body={})
            self.assertIn('error', r)
            self.assertEqual(r.get('code'), 1001)

            call_api_sync('http://localhost:8000/api/user/login', body={'a': 1}, files={'f': __file__})
