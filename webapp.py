# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'


class WSGIApplication():
    def __init__(self, host='127.0.0.1', port=9000):
        self.host = host
        self.port = port

    def run(self):
        # 使用python内置的wsgi服务
        from wsgiref.simple_server import make_server
        server = make_server(self.host, self.port, self.application)
        print('run server on http://%s:%s' % (self.host, self.port))
        server.serve_forever()

    def application(self, environ, start_response):
        # 请求处理
        status = '200 OK'
        response_headers = [('Content-Type', 'text/plain')]
        start_response(status, response_headers)
        return ['Hello world from a simple WSGI application!\n'.encode('utf-8')]


if __name__ == '__main__':
    app = WSGIApplication()
    app.run()
