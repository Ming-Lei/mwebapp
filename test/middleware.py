# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from mwebapp.webapp import ctx


class PathAutoCompleter(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, *args, **kwargs):
        request = ctx.request
        path = request.path_info
        if not path.endswith('/') and not path.startswith('/static'):
            request.path_info = path + '/'
        return self.app()
