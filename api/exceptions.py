# -*- coding: utf-8 -*-
'''
Copyright (c) 2015
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''


class StorageException(Exception):
    pass


class StorageUnavailableError(StorageException):
    pass


class ResourceExists(StorageException):
    pass
