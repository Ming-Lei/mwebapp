# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from mwebapp.webapp import WSGIApplication

app = WSGIApplication()

if __name__ == '__main__':
    app.run(debug=True)
else:
    application = app.get_application(debug=True)
