# -*- coding: utf-8 -*-
'''
Copyright (c) 2015
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''

from api.interfaces import IResourceConverter
#from tools.cache import Singleton
#from six import with_metaclass
from PIL import Image
from collections import OrderedDict
import sys
from os import path
from werkzeug.exceptions import NotFound

PY2 = sys.version_info[0] == 2
if PY2:
    from itertools import ifilter as filter  # @UnresolvedImport


class ConverterFactory(OrderedDict):

    def register(self, converter):
        self[converter.mediaType] = converter

    def getConverter(self, mediaType=None, subType=None):
        if mediaType:
            converter = self.get(mediaType)(self)
            if subType:
                return converter if subType in converter.subTypes else None
            return converter
        elif subType:
            try:
                return next(
                    filter(lambda v: subType in v.subTypes, self.values()))
            except StopIteration:
                pass

    def getConverterSubType(self, subType):
        try:
            return next(filter(lambda v: subType in v.subTypes, self.values()))
        except StopIteration:
            pass


class ImageConverter(IResourceConverter):
    mediaType = 'image'
    subTypes = {'jpg', 'jpeg', 'png', 'gif', 'tiff'}

    def __init__(self, config):
        self.config = config
        if self.config is None:
            raise KeyError(
                'Configuration not found for converting "{}" media type.'
                .format(self.mediaType))

    def isMatch(self, mediaType, subType=None):
        if subType is None:
            return mediaType == self.mediaType
        else:
            return mediaType == self.mediaType and subType in self.subTypes

    def get_new_size(self, orig, frame):
        w_ratio = float(orig[0]) / frame[0]
        h_ratio = float(orig[1]) / frame[1]
        if w_ratio > h_ratio:
            return (frame[0], int(float(orig[1]) / w_ratio)), w_ratio
        else:
            return (int(float(orig[0]) / h_ratio), frame[0]), h_ratio

    def convert(self, src, sfmt, dst, dfmt):
        im = Image.open(src)
        im = im.copy()
        tf = self.config.get(dfmt)
        if (
            tf is None or (
                tf.get('ext') != True and
                path.splitext(src)[1] != path.splitext(dst)[1])
        ):
            raise NotFound
        action = tf['action']
        if action == 'size':
            new_size, ratio = self.get_new_size(im.size, tf['params'])
            if ratio > 1:
                im.thumbnail(new_size)
            else:
                im = im.resize(new_size)
        elif action == 'ext':
            pass
        else:
            raise NotImplementedError
        try:
            im.save(dst)
        except OSError:
            # print(e)
            raise
        except Exception:
            # print(e)
            raise

ConverterFactory().register(ImageConverter)
