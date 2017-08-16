# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from template_engine import render
from webapp import Route, ctx

index = Route()


@index.get('/')
def home():
    request = ctx.request
    addr = request['REMOTE_ADDR']
    return render('template/index.html', {'addr': addr})


@index.get('/:name/')
def other(name):
    content = {
        'name': name,
        'topics': ['Python', 'Geometry', 'Juggling'],
    }
    return render('template/other.html', content)


admin = Route(startpath='/admin')


@admin.get('/:name/')
def admin_index(name):
    return '<h1>welcome %s to admin</h1>' % name
