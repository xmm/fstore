# -*- coding: utf-8 -*-
'''
Copyright (c) 2015
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''
from posix import statvfs
import os
from tempfile import mkstemp
import shutil
from flask import current_app
from api.hash_mapper import DBHashMapper, SoftLinksHashMapper
from werkzeug.exceptions import NotFound, BadRequest, ServiceUnavailable
from api.exceptions import ResourceExists, StorageUnavailableError
from api.resource import Resource, RetrieveResource
from errno import ENOSPC


DEFAULT_RESERVED = 20


def getMediaType(mimeType):
    if mimeType:
        return mimeType.partition('/')[0]


class Storage(object):
    """Represent storage for resources.

    Keyword arguments:
    mountPoint -- mount point of storage
    reserved -- reserved space (%)
    writable -- is writable or read only
    """
    _mountPoint = ''
    _reserved = 0
    _writable = False

    def __init__(
            self, mountPoint, reserved=DEFAULT_RESERVED, writable=False):
        self._mountPoint = mountPoint
        self._reserved = reserved
        self._writable = writable

    @property
    def mountPoint(self):
        return self._mountPoint

    @property
    def reserved(self):
        return self._reserved

    @property
    def writable(self):
        return self._writable

    def isAvailable(self, required):
        """Check availability of space for storing a resource
        without using reserved space.
        """
        if not self._writable:
            return False
        stat = statvfs(self.mountPoint)
        available = stat.f_frsize * stat.f_bavail - required
        # total = stat.f_frsize * stat.f_blocks
        free_space = available * 100.0 / (stat.f_frsize * stat.f_blocks)
        return free_space >= self.reserved


class BaseStorageCollection(object):
    _storagesDir = ''
    _collection = []
    _hashMapper = None
    tmpDir = 'tmp'

    def __init__(
            self, storageConfig, storagesDir,
            selectStorageStrategy, hashStrategy,
            genPathStrategy, genNameStrategy,
            converters):
        self._storagesDir = storagesDir
        self.selectStorageStrategy = selectStorageStrategy
        self.hashStrategy = hashStrategy
        self.genPathStrategy = genPathStrategy
        self.genNameStrategy = genNameStrategy
        self.converters = converters

        if storageConfig:
            self._collection = [
                Storage(
                    os.path.join(self.storagesDir, name), **params
                ) for name, params in storageConfig.items()
            ]
        else:
            self._collection = []

    @property
    def collection(self):
        return self._collection

    @property
    def storagesDir(self):
        return self._storagesDir

    @property
    def hashMapper(self):
        return self._hashMapper

    def selectStorage(self, resource, max_size=None):
        return self.selectStorageStrategy.select(self, resource, max_size)

    def makeTempInStorage(self, storage):
        tmpDir = os.path.join(storage.mountPoint, self.tmpDir)
        os.makedirs(tmpDir, mode=0o775, exist_ok=True)
        fd, tmpPath = mkstemp(dir=tmpDir)
        return fd, tmpPath

    def saveResource(self, resource):
        if self.converters.getConverter(*resource.mimeType) is None:
            raise BadRequest(description='Unknown mimeType of uploaded file.')

        storage = self.selectStorage(resource)
        resource.storage = storage

        fd, tmpPath = self.makeTempInStorage(storage)
        try:
            hashId = self.hashStrategy.calculate(resource, fd)
        finally:
            os.close(fd)

        prefixDir = self.genPathStrategy.generate(hashId)
        resource.prefixDir = prefixDir
        fileName = self.genNameStrategy.generate(hashId, resource.fileName)
        resource.fileName = fileName
        resource.location = os.path.join(prefixDir, fileName)
        dstPath = os.path.join(
            self.storagesDir, storage.mountPoint, prefixDir, fileName
        )
        resource.absLocation = dstPath

        if os.path.isfile(dstPath):
            os.remove(tmpPath)
            raise ResourceExists

        os.makedirs(os.path.dirname(dstPath), mode=0o775, exist_ok=True)
        shutil.move(tmpPath, dstPath)
        os.chmod(dstPath, 0o664)

        self.hashMapper.put(resource)
        return resource

    def retrieveResource(self, resource):
        if self.getResource(resource) is None:
            resource = self.convertResource(resource)

        return resource.location

    def getResource(self, resource):
        if self.hashMapper is None:
            raise NotImplemented
        absLocation = self.hashMapper.get(resource)
        resource.location = os.path.join(resource.prefixDir, resource.fileName)
        if absLocation is None:
            return None
        return absLocation

    def convertResource(self, resource):
        if self.genNameStrategy.isOriginal(resource.fileName):
            raise NotFound

        pattern = self.genNameStrategy.getOriginalPattern(
            resource.fileName)
        absLocation = self.hashMapper.search(resource, pattern)
        if absLocation is None:
            raise NotFound

        orig = os.path.basename(absLocation)

        origResource = Resource(RetrieveResource(resource.request))
        origResource.fileName = orig
        if self.getResource(origResource) is None:
            raise NotFound

        dst = self.genNameStrategy.decompose(resource.fileName)
        converter = self.converters.getConverter(subType=dst['extention'])
        if converter is None:
            raise StorageUnavailableError
        else:
            converter = converter(
                current_app.config['TRANSFORMATIONS'].get(converter.mediaType)
            )

        storage = self.selectStorage(resource, max_size=origResource.size)
        resource.storage = storage
        fd, tmpPath = self.makeTempInStorage(storage)
        tmpPathExt = os.path.extsep.join((tmpPath, dst['extention']))
        shutil.move(tmpPath, tmpPathExt)

        try:
            converter.convert(
                src=origResource.absLocation, sfmt=None,
                dst=tmpPathExt, dfmt=dst['format'],
            )
        except OSError as e:
            if e.errno == ENOSPC:
                raise ServiceUnavailable
        finally:
            os.close(fd)
        resource.absLocation = os.path.join(
            self.storagesDir, storage.mountPoint, resource.location)
        os.makedirs(
            os.path.dirname(resource.absLocation), mode=0o775, exist_ok=True)
        shutil.move(tmpPathExt, resource.absLocation)
        os.chmod(resource.absLocation, 0o664)
        try:
            self.hashMapper.put(resource)
        except ResourceExists:
            pass
        return resource


class DBHashStorageCollection(BaseStorageCollection):
    _db = None

    def __init__(self, db, *args, **kwargs):
        super(SoftLinksStorageCollection, self).__init__(*(args[1:]), **kwargs)
        self._db = db
        self._hashMapper = DBHashMapper(db)


class SoftLinksStorageCollection(BaseStorageCollection):

    def __init__(self, linkStorageDir, *args, **kwargs):
        super(SoftLinksStorageCollection, self).__init__(*(args[1:]), **kwargs)
        self._hashMapper = SoftLinksHashMapper(self)
        self.linkStorageDir = linkStorageDir
