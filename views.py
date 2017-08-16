# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from httperror import redirect
from webapp import Route, ctx, render_html, render_json, url_for
index = Route()


@index.get('/')
def home():
    request = ctx.request
    addr = request.remote_addr
    return render_html('template/index.html', {'addr': addr})


@index.get('/api/')
def api():
    content = {
        'name': 'api',
        'topics': ['Python', 'Geometry', 'Juggling'],
    }
    return render_json(content)


@index.get('/redirect/')
def redirect_test():
    return redirect(url_for(admin_index.path, ('admin',)))


@index.get('/:name/')
def other(name):
    content = {
        'name': name,
        'topics': ['Python', 'Geometry', 'Juggling'],
    }
    return render_html('template/other.html', content)


admin = Route(startpath='/admin')


@admin.get('/:name/')
def admin_index(name):
    return '<h1>welcome %s to admin</h1>' % name
