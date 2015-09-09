# -*- coding: utf-8 -*-
'''
Copyright (c) 2015
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''
import mimetypes
from os import path
from werkzeug import Headers
from flask import current_app


def x_accel_redirect(filename, size):
    """Use x-sendfile feature of nginx server"""

    mimetype = mimetypes.guess_type(filename)[0]
    if mimetype is None:
        mimetype = 'application/octet-stream'

    headers = Headers()
    headers['X-Accel-Redirect'] = path.join('/', filename)

    if current_app.config['TESTING']:
        headers['Content-Length'] = size

    rv = current_app.response_class(
        None, mimetype=mimetype, headers=headers, direct_passthrough=True)
    return rv
