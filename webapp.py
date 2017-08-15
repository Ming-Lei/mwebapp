# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
import re
import os
import sys
import time
import threading
import traceback
import subprocess

if sys.version > '3':
    unicode = str
    import _thread as thread
else:
    import thread

ctx = threading.local()

_re_route = re.compile(r'(\:[a-zA-Z_]\w*)')

_RESPONSE_STATUSES = {
    # Informational
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing',

    # Successful
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi Status',
    226: 'IM Used',

    # Redirection
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',

    # Client Error
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    418: "I'm a teapot",
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    426: 'Upgrade Required',

    # Server Error
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    507: 'Insufficient Storage',
    510: 'Not Extended',
}

_RE_RESPONSE_STATUS = re.compile(r'^\d\d\d(\ [\w\ ]+)?$')

_RESPONSE_HEADERS = (
    'Accept-Ranges',
    'Age',
    'Allow',
    'Cache-Control',
    'Connection',
    'Content-Encoding',
    'Content-Language',
    'Content-Length',
    'Content-Location',
    'Content-MD5',
    'Content-Disposition',
    'Content-Range',
    'Content-Type',
    'Date',
    'ETag',
    'Expires',
    'Last-Modified',
    'Link',
    'Location',
    'P3P',
    'Pragma',
    'Proxy-Authenticate',
    'Refresh',
    'Retry-After',
    'Server',
    'Set-Cookie',
    'Strict-Transport-Security',
    'Trailer',
    'Transfer-Encoding',
    'Vary',
    'Via',
    'Warning',
    'WWW-Authenticate',
    'X-Frame-Options',
    'X-XSS-Protection',
    'X-Content-Type-Options',
    'X-Forwarded-Proto',
    'X-Powered-By',
    'X-UA-Compatible',
)

_HEADER_X_POWERED_BY = ('X-Powered-By', 'python/webapp')


class HttpError(Exception):
    def __init__(self, code):
        super(HttpError, self).__init__()
        self.status = '%d %s' % (code, _RESPONSE_STATUSES[code])

    def header(self, name, value):
        if not hasattr(self, '_headers'):
            self._headers = [_HEADER_X_POWERED_BY]
        self._headers.append((name, value))

    @property
    def headers(self):
        if hasattr(self, '_headers'):
            return self._headers
        return []

    def __str__(self):
        return self.status

    __repr__ = __str__


class RedirectError(HttpError):
    def __init__(self, code, location):
        super(RedirectError, self).__init__(code)
        self.location = location

    def __str__(self):
        return '%s, %s' % (self.status, self.location)

    __repr__ = __str__


def badrequest():
    return HttpError(400)


def unauthorized():
    return HttpError(401)


def forbidden():
    return HttpError(403)


def notfound():
    return HttpError(404)


def conflict():
    return HttpError(409)


def internalerror():
    return HttpError(500)


def redirect(location):
    return RedirectError(301, location)


def found(location):
    return RedirectError(302, location)


def seeother(location):
    return RedirectError(303, location)


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


def _to_str(s):
    if isinstance(s, unicode):
        return s
    return s.decode('utf-8')


def _to_byte(s):
    if isinstance(s, bytes):
        return s
    return s.encode('utf-8')


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
        self.debug = False
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
        server = make_server(self.host, self.port, self.application)
        print('run server on http://%s:%s' % (self.host, self.port))
        server.serve_forever()

    def application(self, environ, start_response):
        # 请求处理
        ctx.request = environ
        request_method = environ['REQUEST_METHOD']
        path_info = environ['PATH_INFO']
        # py3 需要转换编码
        if sys.version > '3':
            path_info = path_info.encode('iso-8859-1').decode('utf8')
        try:
            # 匹配处理程序
            r = self.match(path_info, request_method)
            r = _to_byte(r)
            status = '200 OK'
            headers = [('Content-Type', 'text/html; charset=utf-8')]
            start_response(status, headers)
            return [r]
        except RedirectError as e:
            # 重定向
            start_response(e.status, [{('Location', e.location)}])
            return []
        except HttpError as e:
            # http error
            error = '<html><body><h1>' + e.status + '</h1></body></html>'
            error = _to_byte(error)
            start_response(e.status, e.headers)
            return [error]
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
            start_response('500 Internal Server Error', [])
            return [error]
