# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from webapp import Route

index = Route()


@index.get('/')
def home():
    return '<h1>hello world</h1>'


@index.get('/:name/')
def other(name):
    return '<h1>hello %s</h1>' % name


admin = Route(startpath='/admin')


@admin.get('/:name/')
def admin_index(name):
    return '<h1>welcome %s to admin</h1>' % name
