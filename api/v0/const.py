# -*- coding: utf-8 -*-
'''
Copyright (c) 2014
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''

API_VERSION_V0 = 0
API_VERSION = API_VERSION_V0

bp_name = 'api_v0'
api_v0_prefix = '{prefix}/v{version}'.format(
    prefix='/api',  # current_app.config['URL_PREFIX'],
    version=API_VERSION_V0
)
