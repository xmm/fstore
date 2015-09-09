# -*- coding: utf-8 -*-
'''
Copyright (c) 2015
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''

import os
from api.exceptions import ResourceExists
from fnmatch import fnmatch


class IBaseHashMapper(object):
    def get(self, key):
        raise NotImplementedError

    def put(self, key, value):
        raise NotImplementedError

    def __contains__(self, key):
        raise NotImplementedError


class DBHashMapper(IBaseHashMapper):
    "This is a draft example only"

    def __init__(self, storages, db):
        self.db = db

    def get(self, resource):
        raise NotImplementedError
        location = self.db.execute(
            'SELECT value FROM map WHERE key = {}', resource.fileName
        )
        return location

    def put(self, resource):
        raise NotImplementedError
        self.db.execute(
            'INSERT INTO map (key, value) VALUES ({}, {})',
            resource.fileName, resource.location
        )


class SoftLinksHashMapper(IBaseHashMapper):
    def __init__(self, storages):
        self.storages = storages

    def get(self, resource):
        """Returns absolute path of real location of the resource.
        Initialize the resource attributes if resource exists.
        """
        hashId = self.storages.genNameStrategy\
            .decompose(resource.fileName)\
            .get('hashId')
        resource.hashId = hashId

        prefixDir = self.storages.genPathStrategy.generate(hashId)
        resource.prefixDir = prefixDir

        linkPath = os.path.join(
            self.storages.linkStorageDir, prefixDir, resource.fileName)
        if not os.path.islink(linkPath):
            return None
        absLocation = os.readlink(linkPath)
        if not os.path.isfile(absLocation):
            return None
        resource.absLocation = absLocation

        return absLocation

    def put(self, resource):
        """Returns absolute path of created link to the resource"""
        linkPath = os.path.join(
            self.storages.linkStorageDir, resource.location)

        if not os.path.islink(linkPath):
            os.makedirs(os.path.dirname(linkPath), mode=0o775, exist_ok=True)
            try:
                os.symlink(resource.absLocation, linkPath)
            except FileExistsError:
                raise ResourceExists
            return linkPath
        raise ResourceExists

    def search(self, resource, pattern):
        """Returns absolute path of real location of a first resource
        that match the pattern.
        Initialize the resource attributes if resource exists.
        """
        hashId = self.storages.genNameStrategy\
            .decompose(resource.fileName)\
            .get('hashId')
        resource.hashId = hashId

        prefixDir = self.storages.genPathStrategy.generate(hashId)
        resource.prefixDir = prefixDir

        linkPath = os.path.join(
            self.storages.linkStorageDir, prefixDir)
        if not os.path.isdir(linkPath):
            return None

        for file in os.listdir(linkPath):
            if fnmatch(file, pattern):
                break
        linkPath = os.path.join(linkPath, file)

        if not os.path.islink(linkPath):
            return None
        absLocation = os.readlink(linkPath)
        if not os.path.isfile(absLocation):
            return None
        resource.absLocation = absLocation

        return absLocation
