# -*- coding: utf-8 -*-
'''
Copyright (c) 2014
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''


from flask import Flask, json, jsonify
from flask.helpers import make_response
import os
import sys
import logging
from logging.handlers import SysLogHandler

from api.v0 import api_v0_bp, API_VERSION_V0
from api.storage import SoftLinksStorageCollection
from api.strategies import (TwoLevelHierarchyStrategy, StaticNameStrategy,
                            SelectRandomStorageStrategy)
from api.converters import ImageConverter, ConverterFactory
from api.hash_strategy import Xxhash64HashStrategy


__all__ = ['create_app']


def load_config(app, environment=None):
    if not environment:
        environment = os.environ.get('API_CONFIG')
    if not environment:
        environment = 'development'
    if environment.lower() != 'testing':
        print('CONFIG:', environment, file=sys.stderr)
    app.config.from_object('api.config.{}'.format(environment.capitalize()))
    app.config.from_pyfile(
        'config_{}.py'.format(environment.lower()),
        silent=True
    )


def create_app(environment=None):
    app = Flask(__name__)
    load_config(app, environment)
    if app.config['DEBUG'] and app.config.get('LOG_FILENAME'):
        handler = logging.FileHandler(app.config['LOG_FILENAME'])
    else:
        handler = SysLogHandler(
            address=app.config['LOG_ADDRESS'],
            facility=app.config['LOG_FACILITY'],
        )
    handler.setFormatter(logging.Formatter(app.config['LOGGING_FORMATTER']))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

#     def json_error_handler(e):
#         app.logger.error(str(e))
#         return make_response(
#             jsonify({'message': e.description}), e.code
#         )
#     for code in (400, 401, 402, 404, 405, 500):
#         app.error_handler_spec[None][code] = json_error_handler

#     @app.errorhandler(400)
#     def bad_request(error):
#         return make_response(jsonify({'error': 'Bad request'}), 400)

#     @app.errorhandler(404)
#     def not_found(e):
#         return make_response(jsonify({'error': 'Not found'}), 404)

    converters = ConverterFactory()
    converters.register(ImageConverter)

    app.bundles = app.config['BUNDLES']
    app.storages = SoftLinksStorageCollection(
        linkStorageDir=app.config['LINK_STORAGE_DIR'],
        storageConfig=app.config['STORAGES'],
        storagesDir=app.config['STORAGES_DIR'],
        selectStorageStrategy=SelectRandomStorageStrategy(),
        hashStrategy=Xxhash64HashStrategy(),
        genPathStrategy=TwoLevelHierarchyStrategy(),
        genNameStrategy=StaticNameStrategy(),
        converters=converters,
    )

    app.register_blueprint(api_v0_bp)

    return app
