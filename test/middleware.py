# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from mwebapp.webapp import ctx


class TestMiddleware():
    def __init__(self, app):
        self.app = app

    def __call__(self, *args, **kwargs):
        request = ctx.request
        path = request.path_info
        print(path)
        return self.app()
