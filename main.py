# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from webapp import WSGIApplication
from views import index, admin

app = WSGIApplication()

app.register(index)
app.register(admin)

if __name__ == '__main__':
    app.run(debug=True)
