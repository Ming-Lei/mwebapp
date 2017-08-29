# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from db import create_engine
from webapp import WSGIApplication
from views import index, admin
from middleware import load_middleware

app = WSGIApplication()

app.register(index)
app.register(admin)

interceptor = app.interceptor
load_middleware(interceptor)

create_engine('root', 'password', 'test')

if __name__ == '__main__':
    app.run(debug=True)
