# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
import re
import os
import sys
import time
import json
import threading
import traceback
import mimetypes
import subprocess

from mwebapp.template_engine import render
from mwebapp.environ import _to_byte, Request, Response, _to_str
from mwebapp.httperror import notfound, badrequest, RedirectError, HttpError

if sys.version > '3':
    import _thread as thread
else:
    import thread

ctx = threading.local()
ctx.request = Request({})
ctx.response = Response()

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


def render_html(path, content):
    ctx.response.content_type = 'text/html; charset=utf-8'
    return render(path, content)


def render_json(content):
    content = json.dumps(content)
    ctx.response.content_type = 'application/json'
    return content


def url_for(re_path, groups):
    match_list = _re_route.findall(re_path)
    match_len = len(match_list)
    groups_len = len(groups)
    if match_len != groups_len:
        raise TypeError('groups takes at most %s argument (%s given)' % (match_len, groups_len))
    for index, match in enumerate(match_list):
        re_path = re_path.replace(match, groups[index])
    return re_path


def static_middleware(next):
    request = ctx.request
    path = request.path_info
    if path == '/favicon.ico':
        path = '/static' + path
    if path.startswith('/static'):
        fpath = _to_str('.' + path)
        if not os.path.isfile(fpath):
            raise notfound()
        else:
            fext = os.path.splitext(fpath)[1]
            content_type = mimetypes.types_map.get(fext.lower(), 'application/octet-stream')

            ctx.response.status = 200
            ctx.response.set_header('CONTENT-TYPE', content_type)
            return open(fpath, 'rb').read()
    return next()


class Route(object):
    # 路由处理类
    def __init__(self, startpath=''):
        self.startpath = startpath
        self._get_static = {}
        self._post_static = {}
        self._get_dynamic = {}
        self._post_dynamic = {}

    def route(self, path, method=None):
        # 路由装饰器 根据路由及请求方式保存其对应关系
        if not method:
            method = ['GET', 'POST']

        def _decorator(func):
            allpath = self.startpath + path
            func.path = allpath
            is_static = _re_route.search(allpath) is None
            if is_static:
                # 静态路由直接保存
                if 'GET' in method:
                    self._get_static[allpath] = func
                if 'POST' in method:
                    self._post_static[allpath] = func
            else:
                # 动态路由需正则转换
                if 'GET' in method:
                    re_path = re.compile(_build_regex(allpath))
                    self._get_dynamic[re_path] = func
                if 'POST' in method:
                    re_path = re.compile(_build_regex(allpath))
                    self._post_dynamic[re_path] = func
            return func

        return _decorator

    def get(self, path):
        _decorator = self.route(path, ['GET'])
        return _decorator

    def post(self, path):
        _decorator = self.route(path, ['POST'])
        return _decorator


class WSGIApplication(object):
    def __init__(self, host='127.0.0.1', port=9000):
        self.fn = self.match
        self.debug = False
        self.host = host
        self.port = port
        self._get_static = {}
        self._post_static = {}
        self._get_dynamic = {}
        self._post_dynamic = {}
        self.interceptor_list = [static_middleware]

    def register(self, route):
        # Route路由表注册
        self._get_static.update(route._get_static)
        self._post_static.update(route._post_static)
        self._get_dynamic.update(route._get_dynamic)
        self._post_dynamic.update(route._post_dynamic)

    def interceptor(self, func):
        self.interceptor_list.append(func)

    def _build_interceptor_fn(self, func, next):
        # 中间件装饰器
        def _wrapper():
            return func(next)

        return _wrapper

    def _build_interceptor_chain(self):
        # 中间件包装函数
        L = self.interceptor_list
        L.reverse()
        for f in L:
            self.fn = self._build_interceptor_fn(f, self.fn)

    def match(self):
        # 根据请求地址及方式匹配对应的处理函数
        request = ctx.request
        methods = request.request_method
        url = request.path_info
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
            raise notfound()
        if methods == 'POST':
            fn = self._post_static.get(url, None)
            if fn:
                return fn()
            for re_path, fn in self._post_dynamic.items():
                args = re_path.match(url)
                if args:
                    return fn(*(args.groups()))
            raise notfound()
        raise badrequest()

    def run(self, debug=False):
        self.debug = debug
        if self.debug:
            self.reloader_run()
        else:
            self.runserver()

    def reloader_run(self, interval=1):
        # 自动重启服务
        if os.environ.get('WEB_CHILD') == 'true':
            # 监控进程
            files = dict()
            # 记录引用文件的最近更新时间
            for module in sys.modules.values():
                file_path = getattr(module, '__file__', None)
                if file_path and os.path.isfile(file_path):
                    file_split = os.path.splitext(file_path)
                    if file_split[1] in ('.py', '.pyc', '.pyo'):
                        file_path = file_split[0] + '.py'
                        files[file_path] = os.stat(file_path).st_mtime
            # 创建线程启动wsgi
            thread.start_new_thread(self.runserver, ())
            while True:
                # 监控文件变化
                time.sleep(interval)
                for file_path, file_mtime in files.items():
                    if not os.path.exists(file_path):
                        print("File changed: %s (deleted)" % file_path)
                    elif os.stat(file_path).st_mtime > file_mtime:
                        print("File changed: %s (modified)" % file_path)
                    else:
                        continue
                    print("Restarting...")
                    time.sleep(interval)
                    # 结束当前进程，主进程中重新启动
                    sys.exit(3)
        while True:
            args = [sys.executable] + sys.argv
            environ = os.environ.copy()
            environ['WEB_CHILD'] = 'true'
            # 创建阻塞的监控进程
            exit_status = subprocess.call(args, env=environ)
            if exit_status != 3:
                sys.exit(exit_status)

    def runserver(self):
        # 使用python内置的wsgi服务
        from wsgiref.simple_server import make_server
        server = make_server(self.host, self.port, self.get_application(self.debug))
        print('run server on http://%s:%s' % (self.host, self.port))
        server.serve_forever()

    def get_application(self, debug=False):
        # wsgi 入口 no reloader
        self.debug = debug
        # 加载中间件
        self._build_interceptor_chain()

        def application(environ, start_response):
            ctx.request = Request(environ)
            ctx.response = Response()
            # 请求处理
            try:
                r = self.fn()
                r = _to_byte(r)
                ctx.responce_html = [r]
            except RedirectError as e:
                # 重定向
                ctx.response.status = e.status
                ctx.response.set_header('Location', e.location)
                ctx.responce_html = []
            except HttpError as e:
                # http error
                error = '<html><body><h1>' + e.status + '</h1></body></html>'
                error = _to_byte(error)
                ctx.response.status = e.status
                ctx.responce_html = [error]
            except Exception as e:
                # 系统错误
                if self.debug:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    exception_list = traceback.format_exception(exc_type, exc_value, exc_traceback)
                    stacks = ''.join(exception_list)
                    error = '''<html><body><h1>500 Internal Server Error</h1>
                                <div style="font-family:Monaco, Menlo, Consolas, 'Courier New', monospace;"><pre>''' \
                            + stacks.replace('<', '&lt;').replace('>', '&gt;') + '''</pre></div></body></html>'''
                else:
                    error = '<html><body><h1>500 Internal Server Error</h1></body></html>'
                error = _to_byte(error)
                ctx.response.status = 500
                ctx.responce_html = [error]
            finally:
                # 返回处理结果
                status = ctx.response.status
                headers = ctx.response.headers
                responce_html = ctx.responce_html
                start_response(status, headers)
                # 清空ctx
                del ctx.request
                del ctx.response
                del ctx.responce_html
                return responce_html

        return application
