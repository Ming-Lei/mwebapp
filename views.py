# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from webapp import Route, ctx

index = Route()


@index.get('/')
def home():
    request = ctx.request
    addr = request['REMOTE_ADDR']
    return '<h1>hello world</h1>' + '\n the ip you from ' + addr


@index.get('/:name/')
def other(name):
    return '<h1>hello %s</h1>' % name


admin = Route(startpath='/admin')


@admin.get('/:name/')
def admin_index(name):
    return '<h1>welcome %s to admin</h1>' % name
