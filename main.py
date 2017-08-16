# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from webapp import WSGIApplication
from views import index, admin
from middleware import load_middleware

app = WSGIApplication()

app.register(index)
app.register(admin)

middleware = app.middleware
load_middleware(middleware)

if __name__ == '__main__':
    app.run(debug=True)
