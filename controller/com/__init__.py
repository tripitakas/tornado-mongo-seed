#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 在 controller.com 包实现公共性页面响应类，生成前端页面，modules 为重用网页片段的渲染类

from . import home

views = [
    home.HomeHandler,
]
handlers = [
    home.LoginHandler,
]
modules = {
}
