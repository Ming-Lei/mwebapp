# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from mwebapp.webapp import ctx


class load_middleware():
    # 加载中间件
    def __init__(self, interceptor):
        interceptor(test_middleware)


def test_middleware(next):
    request = ctx.request
    path = request.path_info
    print(path)
    return next()
