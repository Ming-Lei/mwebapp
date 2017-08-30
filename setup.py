# -*- coding: utf-8 -*-
# __author__ = 'MingLei Ji'
from setuptools import setup, find_packages

setup(
    name='mweb.py',
    version='1.0',
    author='MingLei Ji',
    author_email='ming3055@foxmail.com',
    url='https://github.com/Ming-Lei/mwebapp',
    packages=find_packages(),
    description='Web framework written by self practice',
    install_requires=['mysql-connector'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)
