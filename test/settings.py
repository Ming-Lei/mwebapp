# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'

database = {
    'user': 'root',
    'password': 'password',
    'database': 'test',
    'host': '127.0.0.1',
    'port': '3306'
}

app = (
    'views.index',
    'views.admin',
)

middleware = (
    'middleware.TestMiddleware',
)
