# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from mwebapp.environ import _RESPONSE_STATUSES, _HEADER_X_POWERED_BY


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
    raise HttpError(400)


def unauthorized():
    raise HttpError(401)


def forbidden():
    raise HttpError(403)


def notfound():
    raise HttpError(404)


def conflict():
    raise HttpError(409)


def internalerror():
    raise HttpError(500)


def redirect(location):
    raise RedirectError(301, location)


def found(location):
    raise RedirectError(302, location)


def seeother(location):
    raise RedirectError(303, location)
