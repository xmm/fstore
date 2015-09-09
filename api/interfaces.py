# -*- coding: utf-8 -*-
'''
Copyright (c) 2015
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''


class ISelectStorageStrategy(object):

    def select(self, storages, resource, max_size=None):
        return NotImplementedError


class IHashStrategy():
    def calculate(self, resource, dst):
        return NotImplementedError


class IResourcePathGeneratingStrategy(object):

    def generate(self, hashId):
        raise NotImplementedError


class IResourceNamingStrategy(object):

    def generate(self, hashId, filename):
        raise NotImplementedError


class IResourceStoringStrategy(object):

    def store(self, storage, resource):
        raise NotImplementedError


class IResourceConverter(object):

    def convert(self, src, sfmt, dst, dfmt):
        raise NotImplementedError
