# -*- coding: utf-8 -*-


class Config(object):
    DEBUG = False
    PORT = 5000
    HOST = '0.0.0.0'
    # URL_PREFIX = '/api'

    LOG_FILENAME = 'fstore.log'  # used if DEBUG=True
    LOG_ADDRESS = '/dev/log'  # used for logging.handlers.SysLogHandler
    LOG_FACILITY = 'local1'
    LOGGER_NAME = 'fstore.api'
    LOGGING_FORMATTER = \
        '%(levelname)s %(pathname)s:%(lineno)d %(funcName)s %(message)s'

    USE_X_SENDFILE = True
    STORAGES_DIR = '/stores'
    LINK_STORAGE_DIR = '/store'

    USERS_DB = {}
    BUNDLE_RESERVED = 10  # How much % of disk space to reserve
    BUNDLES = {'store1': {'write_mode': True}}
    LINK_STORAGE_DIR = '/srv/link_storage'
    STORAGES_DIR = '/srv/storages'
    STORAGES = {}
    TRANSFORMATIONS = {
        'image': {
            'ext': {'action': 'ext', 'ext': True},
            '150': {'action': 'size', 'params': (150, 150), 'ext': True},
        }
    }


class Development(Config):
    DEBUG = True
    LOG_FILENAME = '/srv/log/fstore.log'
    SECRET_KEY = 'development'
    SSL_VERIFYHOST = 0
    USERS_DB = {'sm': 'pass'}
    STORAGES = {'store1': {'reserved': 5, 'writable': True}}


class Production(Config):
    # hold private settings in the config_production.py file
    pass


class Testing(Config):
    TESTING = True
    PRESERVE_CONTEXT_ON_EXCEPTION = False
    DEBUG = True
    LOG_FILENAME = '/srv/log/fstore.log'
    SECRET_KEY = 'testing'
    SSL_VERIFYHOST = 0
    TEST_IMG = 'test.jpg'

    LINK_STORAGE_DIR = '/tmp/link_storage'
    STORAGES_DIR = '/tmp/storages'
    STORAGES = {}
    USERS_DB = {'test_user': 'test_password'}
