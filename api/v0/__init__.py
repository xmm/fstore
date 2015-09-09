# -*- coding: utf-8 -*-
'''
Copyright (c) 2014
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''

from flask import Blueprint
from datetime import datetime
from .const import bp_name, api_v0_prefix, API_VERSION_V0
from .image import ImagesView

__all__ = [
    'API_VERSION_V0', 'bp_name', 'api_v0_prefix', 'api_v0_bp',
    'ImagesView',
]

api_v0_bp = Blueprint(bp_name, __name__, url_prefix=api_v0_prefix)

images_view = ImagesView.as_view('images')
api_v0_bp.add_url_rule('/images/<filename>', view_func=images_view, methods=['GET'])
api_v0_bp.add_url_rule('/images/', view_func=images_view, methods=['POST'])
