# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from models import User
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
    user_list = User.find_by('where id<?', 1000)
    return render_json(user_list)


@index.get('/redirect/')
def redirect_test():
    return redirect(url_for(admin_index.path, ('admin',)))


@index.route('/:name/')
def other(name):
    request = ctx.request
    if request.request_method == 'POST':
        file = request.get('test')
        with open(file.filename, 'wb') as f:
            f.write(file.body)
    content = {
        'name': name,
        'topics': ['Python', 'Geometry', 'Juggling'],
    }
    return render_html('template/other.html', content)


admin = Route(startpath='/admin')


@admin.get('/:name/')
def admin_index(name):
    return '<h1>welcome %s to admin</h1>' % name
