# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
import os
import mimetypes

from webapp import ctx
from environ import _to_str
from httperror import notfound


class load_middleware():
    def __init__(self, interceptor):
        interceptor(test_middlewate)
        interceptor(static_middleware)


def static_middleware(next):
    request = ctx.request
    path = request.path_info
    if path == '/favicon.ico':
        path = '/static' + path
    if path.startswith('/static'):
        fpath = _to_str('.' + path)
        if not os.path.isfile(fpath):
            raise notfound()
        else:
            fext = os.path.splitext(fpath)[1]
            content_type = mimetypes.types_map.get(fext.lower(), 'application/octet-stream')

            ctx.response.status = 200
            ctx.response.set_header('CONTENT-TYPE', content_type)
            return open(fpath, 'rb').read()
    return next()


def test_middlewate(next):
    request = ctx.request
    path = request.path_info
    print(path)
    return next()
