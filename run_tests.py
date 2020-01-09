#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Usage:
# python -m run_tests.py --coverage
# python -m run_tests.py -k test_case_name

import os
import sys
import pytest

sys.path.append(os.path.dirname(__file__))

if __name__ == '__main__':
    args = sys.argv[1:]

    # Logic to run pytest with coverage turned on
    try:
        args.remove('--coverage')
    except ValueError:
        args += ['tests']
        # 要单独调试某个测试用例或用例集，可将下行的注释取消，改为相应的测试用例函数名或类名，提交代码前恢复注释
        # args += ['-k test_call_api_sync']
    else:
        args = ['--cov=controller', '--cov=utils', '--cov-report=term', '--cov-report=html', 'tests'] + args
    errcode = pytest.main(args)
    sys.exit(errcode)
