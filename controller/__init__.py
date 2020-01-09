#!/usr/bin/env python
# -*- coding: utf-8 -*-

from controller.com import invalid
from controller import com

views = com.views

handlers = com.handlers
handlers += [invalid.ApiTable]

modules = com.modules

InvalidPageHandler = invalid.InvalidPageHandler
