# -*- coding: utf-8 -*-
'''
Copyright (c) 2015
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''

from functools import wraps
from flask import current_app, request
from werkzeug import abort


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kw):
        login = request.form.get('login')
        password = request.form.get('password')
        if (
            login and password and
            current_app.config['USERS_DB'].get(login) == password
        ):
            return f(*args, **kw)
        return abort(401)
    return wrapper
