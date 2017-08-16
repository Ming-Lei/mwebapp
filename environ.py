# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
import re
import sys
import cgi
import datetime

if sys.version > '3':
    unicode = str
    import urllib.parse as urllib
else:
    import urllib


def _to_str(s):
    if isinstance(s, unicode):
        return s
    return s.decode('utf-8')


def _to_byte(s):
    if isinstance(s, bytes):
        return s
    return s.encode('utf-8')


def header_encode(value):
    if sys.version > '3':
        return _to_str(value)
    else:
        return _to_byte(value)


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

_RESPONSE_HEADER_DICT = dict(zip(map(lambda x: x.upper(), _RESPONSE_HEADERS), _RESPONSE_HEADERS))

_HEADER_X_POWERED_BY = ('X-Powered-By', 'python/webapp')


def _quote(s, encoding='utf-8'):
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return urllib.quote(s)


def _unquote(s, encoding='utf-8'):
    return urllib.unquote(s).decode(encoding)


class Dict(dict):
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


class MultipartFile(object):
    def __init__(self, storage):
        self.filename = _to_str(storage.filename)
        self.file = storage.file


class Request(object):
    def __init__(self, environ):
        self._environ = environ

    def _parse_input(self):
        def _convert(item):
            if isinstance(item, list):
                return [_to_str(i.value) for i in item]
            if item.filename:
                return MultipartFile(item)
            return _to_str(item.value)

        fs = cgi.FieldStorage(fp=self._environ['wsgi.input'], environ=self._environ, keep_blank_values=True)
        inputs = dict()
        for key in fs:
            inputs[key] = _convert(fs[key])
        return inputs

    def _get_raw_input(self):
        if not hasattr(self, '_raw_input'):
            self._raw_input = self._parse_input()
        return self._raw_input

    def __getitem__(self, key):
        r = self._get_raw_input()[key]
        if isinstance(r, list):
            return r[0]
        return r

    def get(self, key, default=None):
        r = self._get_raw_input().get(key, default)
        if isinstance(r, list):
            return r[0]
        return r

    def gets(self, key):
        r = self._get_raw_input()[key]
        if isinstance(r, list):
            return r[:]
        return [r]

    def input(self, **kw):
        copy = Dict(**kw)
        raw = self._get_raw_input()
        for k, v in raw.iteritems():
            copy[k] = v[0] if isinstance(v, list) else v
        return copy

    def get_body(self):
        fp = self._environ['wsgi.input']
        return fp.read()

    @property
    def remote_addr(self):
        return self._environ.get('REMOTE_ADDR', '0.0.0.0')

    @property
    def document_root(self):
        return self._environ.get('DOCUMENT_ROOT', '')

    @property
    def query_string(self):
        return self._environ.get('QUERY_STRING', '')

    @property
    def environ(self):
        return self._environ

    @property
    def request_method(self):
        return self._environ['REQUEST_METHOD']

    @property
    def path_info(self):
        path = urllib.unquote(self._environ.get('PATH_INFO', ''))
        if sys.version > '3':
            path = path.encode('iso-8859-1').decode('utf8')
        return path

    @property
    def host(self):
        return self._environ.get('HTTP_HOST', '')

    def _get_headers(self):
        if not hasattr(self, '_headers'):
            hdrs = {}
            for k, v in self._environ.iteritems():
                if k.startswith('HTTP_'):
                    # convert 'HTTP_ACCEPT_ENCODING' to 'ACCEPT-ENCODING'
                    hdrs[k[5:].replace('_', '-').upper()] = v.decode('utf-8')
            self._headers = hdrs
        return self._headers

    @property
    def headers(self):
        return dict(**self._get_headers())

    def header(self, header, default=None):
        return self._get_headers().get(header.upper(), default)

    def _get_cookies(self):
        if not hasattr(self, '_cookies'):
            cookies = {}
            cookie_str = self._environ.get('HTTP_COOKIE')
            if cookie_str:
                for c in cookie_str.split(';'):
                    pos = c.find('=')
                    if pos > 0:
                        cookies[c[:pos].strip()] = _unquote(c[pos + 1:])
            self._cookies = cookies
        return self._cookies

    @property
    def cookies(self):
        return Dict(**self._get_cookies())

    def cookie(self, name, default=None):
        return self._get_cookies().get(name, default)


class Response(object):
    def __init__(self):
        self._status = '200 OK'
        self._headers = {'CONTENT-TYPE': 'text/html; charset=utf-8'}

    @property
    def headers(self):
        L = [(_RESPONSE_HEADER_DICT.get(k, k), v) for k, v in self._headers.items()]
        if hasattr(self, '_cookies'):
            for v in self._cookies.itervalues():
                L.append(('Set-Cookie', v))
        L.append(_HEADER_X_POWERED_BY)
        return L

    def header(self, name):
        key = name.upper()
        if not key in _RESPONSE_HEADER_DICT:
            key = name
        return self._headers.get(key)

    def unset_header(self, name):
        key = name.upper()
        if not key in _RESPONSE_HEADER_DICT:
            key = name
        if key in self._headers:
            del self._headers[key]

    def set_header(self, name, value):
        key = name.upper()
        if not key in _RESPONSE_HEADER_DICT:
            key = name
        self._headers[key] = header_encode(value)

    @property
    def content_type(self):
        return self.header('CONTENT-TYPE')

    @content_type.setter
    def content_type(self, value):
        if value:
            self.set_header('CONTENT-TYPE', value)
        else:
            self.unset_header('CONTENT-TYPE')

    @property
    def content_length(self):
        return self.header('CONTENT-LENGTH')

    @content_length.setter
    def content_length(self, value):
        self.set_header('CONTENT-LENGTH', str(value))

    def delete_cookie(self, name):
        self.set_cookie(name, '__deleted__', expires=0)

    def set_cookie(self, name, value, max_age=None, expires=None, path='/', domain=None, secure=False, http_only=True):
        if not hasattr(self, '_cookies'):
            self._cookies = {}
        L = ['%s=%s' % (_quote(name), _quote(value))]
        if expires is not None:
            if isinstance(expires, (float, int)):
                L.append('Expires=%s' % datetime.datetime.strftime(
                    '%a, %d-%b-%Y %H:%M:%S GMT'))
            if isinstance(expires, (datetime.date, datetime.datetime)):
                L.append('Expires=%s' % expires.strftime('%a, %d-%b-%Y %H:%M:%S'))
        elif isinstance(max_age, int):
            L.append('Max-Age=%d' % max_age)
        L.append('Path=%s' % path)
        if domain:
            L.append('Domain=%s' % domain)
        if secure:
            L.append('Secure')
        if http_only:
            L.append('HttpOnly')
        self._cookies[name] = '; '.join(L)

    def unset_cookie(self, name):
        if hasattr(self, '_cookies'):
            if name in self._cookies:
                del self._cookies[name]

    @property
    def status_code(self):
        return int(self._status[:3])

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        if isinstance(value, int):
            if value >= 100 and value <= 999:
                st = _RESPONSE_STATUSES.get(value, '')
                if st:
                    self._status = '%d %s' % (value, st)
                else:
                    self._status = str(value)
            else:
                raise ValueError('Bad response code: %d' % value)
        elif isinstance(value, (bytes, unicode)):
            value = header_encode(value)
            if _RE_RESPONSE_STATUS.match(value):
                self._status = value
            else:
                raise ValueError('Bad response code: %s' % value)
        else:
            raise TypeError('Bad type of response code.')
