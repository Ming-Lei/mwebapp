# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
import os
import mimetypes

from webapp import ctx
from environ import _to_byte, _to_str


class load_middleware():
    def __init__(self, middleware):
        middleware.before_request(static_middleware)


def static_middleware(request):
    path = request.path_info
    if path == '/favicon.ico':
        path = '/static' + path
    if path.startswith('/static'):
        fpath = _to_str('.' + path)
        if not os.path.isfile(fpath):
            error = '<html><body><h1>404 Not Found</h1></body></html>'
            error = _to_byte(error)

            ctx.response.status = 404
            ctx.response.set_header('Location', '404 Not Found')
            ctx.responce_html = [error]
        else:
            fext = os.path.splitext(fpath)[1]
            content_type = mimetypes.types_map.get(fext.lower(), 'application/octet-stream')

            ctx.response.status = 200
            ctx.response.set_header('CONTENT-TYPE', content_type)
            ctx.responce_html = [open(fpath, 'rb').read()]
