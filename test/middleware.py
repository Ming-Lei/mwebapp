# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from mwebapp.webapp import ctx


def test_middleware(next):
    request = ctx.request
    path = request.path_info
    print(path)
    return next()
