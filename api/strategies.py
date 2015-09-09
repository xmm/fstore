# -*- coding: utf-8 -*-
'''
Copyright (c) 2015
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''

from api.interfaces import IResourcePathGeneratingStrategy,\
    IResourceNamingStrategy, ISelectStorageStrategy
from api.exceptions import StorageUnavailableError
import os
import random

BUFFER_SIZE = 16384


class SelectRandomStorageStrategy(ISelectStorageStrategy):

    def select(self, storages, resource, max_size=None):
        """select a storage for the resource
        params: max_size - need for new files else takes from resource.size
        """
        required = resource.size if max_size is None else max_size
        avalable = [s for s in storages.collection if s.isAvailable(required)]
        if avalable:
            return random.choice(avalable)
        else:
            raise StorageUnavailableError()


class TwoLevelHierarchyStrategy(IResourcePathGeneratingStrategy):

    def generate(self, hashId):
        return os.path.join(hashId[0], hashId[1])


class StaticNameStrategy(IResourceNamingStrategy):
    orig_mark = '000'

    def generate(self, hashId, filename):
        return os.path.extsep.join((
            hashId, self.orig_mark, filename.rpartition(os.path.extsep)[2],))

    def decompose(self, hashFileName):
        hashId, fmt, ext = hashFileName.split(os.path.extsep)
        return dict(hashId=hashId, format=fmt, extention=ext)

    def getOriginal(self, hashFileName):
        hashId, _fmt, ext = hashFileName.split(os.path.extsep)
        return os.path.extsep.join((hashId, self.orig_mark, ext))

    def getOriginalPattern(self, hashFileName):
        hashId, _fmt, _ext = hashFileName.split(os.path.extsep)
        return os.path.extsep.join((hashId, self.orig_mark, '*'))

    def isOriginal(self, hashFileName):
        _hashId, fmt, _ext = hashFileName.split(os.path.extsep)
        return fmt == self.orig_mark
