# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
import re

_re_route = re.compile(r'(\:[a-zA-Z_]\w*)')


def _build_regex(path):
    # 将路由转换为可以匹配地址的正则
    re_list = ['^']
    var_list = []
    is_var = False
    for v in _re_route.split(path):
        if is_var:
            var_name = v[1:]
            var_list.append(var_name)
            re_list.append(r'(?P<%s>[^\/]+)' % var_name)
        else:
            s = ''
            for ch in v:
                if re.match('\w', ch):
                    s += ch
                else:
                    s += '\\' + ch
            re_list.append(s)
        is_var = not is_var
    re_list.append('$')
    return ''.join(re_list)


class Route(object):
    # 路由处理类
    def __init__(self, startpath=''):
        self.startpath = startpath
        self._get_static = {}
        self._post_static = {}
        self._get_dynamic = {}
        self._post_dynamic = {}

    def route(self, path, method):
        # 路由装饰器 根据路由及请求方式保存其对应关系
        def _decorator(func):
            allpath = self.startpath + path
            is_static = _re_route.search(allpath) is None
            if is_static:
                # 静态路由直接保存
                if method == 'GET':
                    self._get_static[allpath] = func
                if method == 'POST':
                    self._post_static[allpath] = func
            else:
                # 动态路由需正则转换
                if method == 'GET':
                    re_path = re.compile(_build_regex(allpath))
                    self._get_dynamic[re_path] = func
                if method == 'POST':
                    re_path = re.compile(_build_regex(allpath))
                    self._post_dynamic[re_path] = func
            return func

        return _decorator

    def get(self, path):
        _decorator = self.route(path, 'GET')
        return _decorator

    def post(self, path):
        _decorator = self.route(path, 'POST')
        return _decorator


class WSGIApplication(object):
    def __init__(self, host='127.0.0.1', port=9000):
        self.host = host
        self.port = port
        self._get_static = {}
        self._post_static = {}
        self._get_dynamic = {}
        self._post_dynamic = {}

    def register(self, route):
        # Route路由表注册
        self._get_static.update(route._get_static)
        self._post_static.update(route._post_static)
        self._get_dynamic.update(route._get_dynamic)
        self._post_dynamic.update(route._post_dynamic)

    def match(self, url, methods):
        # 根据请求地址及方式匹配对应的处理函数
        if methods == 'GET':
            # 优先匹配静态路由
            fn = self._get_static.get(url, None)
            if fn:
                return fn()
            for re_path, fn in self._get_dynamic.items():
                args = re_path.match(url)
                if args:
                    # 传参调用处理函数
                    return fn(*(args.groups()))
        if methods == 'POST':
            fn = self._post_static.get(url, None)
            if fn:
                return fn()
            for re_path, fn in self._post_dynamic.items():
                args = re_path.match(url)
                if args:
                    return fn(*(args.groups()))
        return '404'

    def run(self):
        # 使用python内置的wsgi服务
        from wsgiref.simple_server import make_server
        server = make_server(self.host, self.port, self.application)
        print('run server on http://%s:%s' % (self.host, self.port))
        server.serve_forever()

    def application(self, environ, start_response):
        # 请求处理
        request_method = environ['REQUEST_METHOD']
        path_info = environ['PATH_INFO']
        # 匹配处理程序
        r = self.match(path_info, request_method)
        status = '200 OK'
        headers = [('Content-Type', 'text/html; charset=utf-8')]
        start_response(status, headers)
        return [r.encode('utf-8')]
