# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
import time

from mwebapp.orm import Model, IntegerField, StringField, FloatField


class User(Model):
    id = IntegerField(primary_key=True, updatable=False)
    name = StringField()
    email = StringField(updatable=False)
    passwd = StringField(default=lambda: '******')
    last_modified = FloatField()

    def pre_insert(self):
        self.last_modified = time.time()
