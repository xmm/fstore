# -*- coding: utf-8 -*-
'''
Copyright (c) 2015
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''
from io import SEEK_END, SEEK_SET
import os
from tools.cache import cached_property
from builtins import setattr


class Resource(object):
    _hashId = None
    _state = None

    def __init__(self, state):
        """Initialize a Resource instance by werkzeug.FileStorage object"""
        self._state = state

    @property
    def state(self):
        return self._state

    def __getattr__(self, name):
        return getattr(self._state, name)

    def __setattr__(self, name, value):
        if name == '_state':
            super().__setattr__(name, value)
        else:
            setattr(self._state, name, value)

    @property
    def stream(self):
        return self._state.request.stream


class ResourceState(object):
    def hashId(self, resource):
        raise NotImplementedError

    def size(self):
        raise NotImplementedError

    def fileName(self):
        raise NotImplementedError


class SaveResource(ResourceState):
    def __init__(self, request):
        self.request = request

    @cached_property
    def size(self):
        stream = self.request.stream
        if self.request.content_length:
            return self.request.content_length
        else:
            try:
                size = stream.seek(0, SEEK_END)
                stream.seek(0, SEEK_SET)
                return size
            except AttributeError:
                pass
        return None

    @cached_property
    def fileName(self):
        return self.request.filename

    @cached_property
    def mimeType(self):
        mimetype = self.request.mimetype.partition('/')
        return mimetype[0], mimetype[2]


class RetrieveResource(ResourceState):
    def __init__(self, request):
        self.request = request

    @cached_property
    def size(self):
        try:
            size = os.path.getsize(self.absLocation)
        except AttributeError:
            size = None
        return size

    @cached_property
    def fileName(self):
        return os.path.basename(self.request.path)
