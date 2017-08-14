# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from webapp import app


@app.get('/')
def index():
    return '<h1>hello world</h1>'


@app.get('/:name/')
def other(name):
    return '<h1>hello %s</h1>' % name


if __name__ == '__main__':
    app.run()
