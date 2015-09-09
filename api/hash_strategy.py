# -*- coding: utf-8 -*-
'''
Copyright (c) 2015
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''
from api.interfaces import IHashStrategy
import os
import hashlib


class BaseHashStrategy(IHashStrategy):
    """Abstract class. Calculate a hash of a resource.stream content.
    Copy the stream to dst if the dst is not None. The dst can be fd, path or
    file type. A class attribute hashClass must be defined in a derived class.
    For example:

    class Md5HashStrategy(BaseHashStrategy):
        hashClass = hashlib.md5
    """
    hashClass = None
    BUFFER_SIZE = 16384

    @property
    def hashClass(self):
        if self.hashClass is None:
            raise NotImplementedError
        return self.hashClass

    def calculate(self, resource, dst):
        if self.hashClass is None:
            raise ValueError('Hash function not defined.')
        hashId = self.hashClass()

        needClose = False
        if dst is not None:
            if isinstance(dst, int):
                fd = dst
            elif isinstance(dst, file):  # @UndefinedVariable
                fd = dst.fileno()
            else:
                fd = open(dst, 'w')
                needClose = True

        try:
            while 1:
                buf = resource.stream.read(self.BUFFER_SIZE)
                if not buf:
                    break
                hashId.update(buf)
                if dst is not None:
                    os.write(fd, buf)
            resource.hashId = digest = hashId.hexdigest()
            return digest
        finally:
            if needClose:
                os.close(fd)


class Md5HashStrategy(BaseHashStrategy):
    hashClass = hashlib.md5


try:
    import xxhash

    class Xxhash64HashStrategy(BaseHashStrategy):
        hashClass = xxhash.xxh64
except ImportError:
    pass
