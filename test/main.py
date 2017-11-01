# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from mwebapp.webapp import WSGIApplication
import settings

app = WSGIApplication()
app.load_settings(settings)

if __name__ == '__main__':
    app.run()
