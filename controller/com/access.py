#!/usr/bin/env python
# -*- coding: utf-8 -*-


# url占位符
url_placeholder = {
    'num': '[0-9]+',
}


def prepare_access(handler, req_path, method):
    pass


def can_access(handler, req_path, method):
    role = '访客' if not handler.current_user else (handler.current_user.get('roles') or '普通用户') + ',访客'
    return True
