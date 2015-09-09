# -*- coding: utf-8 -*-
'''
Copyright (c) 2014
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''
import unittest
import shutil
import xxhash
import subprocess
from unittest.mock import MagicMock
from os import path, makedirs, readlink
from posix import symlink
from flask import current_app
from flask.ext.testing import TestCase
from flask.helpers import url_for

from api import create_app
from api.v0 import api_v0_prefix
from api.v0.const import bp_name
from api.storage import Storage
from api.strategies import SelectRandomStorageStrategy
from api.exceptions import StorageUnavailableError


def get_hash(filename):
    hash = xxhash.xxh64()  # @ReservedAssignment
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * hash.block_size), b''):
            hash.update(chunk)
    return hash.hexdigest()

STORAGE_SIZE = 100
MOUNT_CMD = 'sudo mount -t tmpfs -o size={size}K tmpfs {mnt}'
UMOUNT_CMD = 'sudo umount {mnt}'


class ImagesTest(TestCase):

    def create_app(self):
        return create_app(environment='testing')

    def setUp(self):
        self.mounted = []
        self.prefix = api_v0_prefix
        self.storage = 'store1'
        self.storages_dir = current_app.config['STORAGES_DIR']
        self.link_storage_dir = current_app.config['LINK_STORAGE_DIR']
        current_app.config['TRANSFORMATIONS'] = {
            'image': {
                'ext': {'action': 'ext', 'ext': True},
                '150': {'action': 'size', 'params': (150, 150), 'ext': True},
            }
        }

        self.original = '000'
        self.test_img = path.join(
            current_app.root_path,
            '..',
            'tests',
            current_app.config['TEST_IMG'])

    def init_img_store(self):
        shutil.rmtree(self.storages_dir, ignore_errors=True)
        shutil.rmtree(self.link_storage_dir, ignore_errors=True)

        self.fsum = get_hash(self.test_img)
        file_dir = path.join(
            self.storages_dir, self.storage,
            self.fsum[0], self.fsum[1])
        makedirs(file_dir, exist_ok=True)
        link_dir = path.join(
            self.link_storage_dir, self.fsum[0], self.fsum[1])
        makedirs(file_dir, exist_ok=True)
        makedirs(link_dir, exist_ok=True)

        file_name = path.extsep.join((
            self.fsum,
            self.original,
            self.test_img.rpartition(path.extsep)[2]
        ))
        self.file_path = file_path = path.join(file_dir, file_name)
        link_path = path.join(link_dir, file_name)
        shutil.copyfile(self.test_img, file_path)
        symlink(file_path, link_path)

    def tearDown(self):
        self.umount_all()
        shutil.rmtree(self.storages_dir, ignore_errors=True)
        shutil.rmtree(self.link_storage_dir, ignore_errors=True)

    def create_storage(self, name, storage_size=STORAGE_SIZE, **params):
        mount_dir = path.join(self.storages_dir, name)
        makedirs(mount_dir, exist_ok=True)
        subprocess.check_call(
            MOUNT_CMD.format(size=storage_size, mnt=mount_dir),
            shell=True,
        )
        self.mounted.append(mount_dir)
        return Storage(
            mount_dir, **params
        )

    def umount_all(self):
        for mount_point in self.mounted:
            subprocess.call(
                UMOUNT_CMD.format(mnt=mount_point), shell=True)
            shutil.rmtree(mount_point, ignore_errors=True)
        self.mounted = []

#    @unittest.skip
    def test_01_storage(self):
        s = self.create_storage('storage1', reserved=10, writable=False)
        self.assertFalse(s.isAvailable(0))
        self.assertFalse(s.isAvailable(50 * 1024))
        self.assertFalse(s.isAvailable(100 * 1024))

        s = self.create_storage('storage2', reserved=10, writable=True)
        self.assertTrue(s.isAvailable(0))
        self.assertTrue(s.isAvailable(10 * 1024))
        self.assertTrue(s.isAvailable(89 * 1024))
        self.assertTrue(s.isAvailable(90 * 1024))
        self.assertFalse(s.isAvailable(91 * 1024))
        self.assertFalse(s.isAvailable(100 * 1024))

        s = self.create_storage('storage3', reserved=90, writable=True)
        self.assertTrue(s.isAvailable(0))
        self.assertTrue(s.isAvailable(1 * 1024))
        self.assertTrue(s.isAvailable(10 * 1024))
        self.assertFalse(s.isAvailable(99 * 1024))

#    @unittest.skip
    def test_02_SelectRandomStorageStrategy(self):
        storages = MagicMock(collection=[])
        resource = MagicMock(size=100)

        self.assertRaises(
            StorageUnavailableError,
            SelectRandomStorageStrategy().select,
            storages, resource
        )

        storageConfig = dict(store1={'writable': False})
        collection = [
            Storage(
                path.join(self.storages_dir, name), **params
            ) for name, params in storageConfig.items()
        ]
        storages = MagicMock(collection=collection)

        self.assertRaises(
            StorageUnavailableError,
            SelectRandomStorageStrategy().select,
            storages, resource
        )

        storageConfig = dict(
            store1={'writable': False},
            store2={'writable': True},
            store3={'writable': True},
        )
        collection = [
            self.create_storage(
                name, **params
            ) for name, params in storageConfig.items()
        ]
        fpath = path.join(self.storages_dir, 'store2', 'waste')
        with open(fpath, 'wb') as f:
            f.write(b'0' * (1024 * 90))
        storages = MagicMock(collection=collection)
        storage = SelectRandomStorageStrategy().select(storages, resource)
        self.assertEqual(path.basename(storage.mountPoint), 'store3')
        self.assertTrue(storage._writable)

#    @unittest.skip
    def test_03_get_images(self):
        storageConfig = {
            self.storage: {'reserved': 0, 'writable': True},
        }
        collection = [
            self.create_storage(
                name, storage_size=900, **params
            ) for name, params in storageConfig.items()
        ]
        current_app.storages._collection = collection
        self.init_img_store()

        print(
            'test_01_get_images',
            url_for(
                '.'.join((bp_name, 'images')),
                filename=path.extsep.join((
                    self.fsum,
                    self.original,
                    self.test_img.rpartition(path.extsep)[2],
                )),
            ),
        )
        # GET original image
        response = self.client.get(
            url_for(
                '.'.join((bp_name, 'images')),
                filename=path.extsep.join((
                    self.fsum,
                    self.original,
                    self.test_img.rpartition(path.extsep)[2],
                )),
            ),
        )
        print(2)
        self.assert200(response)
        print(3, response.headers['X-Accel-Redirect'])
        # TODO: !!! self.assertEqual(response.headers['X-Accel-Redirect'], self.file_path)

        # GET image in new format (png)
        filename = path.extsep.join((self.fsum, 'ext', 'png'))
        response = self.client.get(
            url_for(
                '.'.join((bp_name, 'images')),
                filename=filename,
            ),
        )
        print(4, response.get_data(), response.headers, response.mimetype)
        self.assert200(response)
        link = path.join(
            self.link_storage_dir, filename[0], filename[1], filename)
        self.assertTrue(path.islink(link))
        self.assertTrue(path.isfile(readlink(link)))

        # GET image in new size
        filename = path.extsep.join(
            (self.fsum, '150', self.test_img.rpartition(path.extsep)[2]))
        response = self.client.get(
            url_for(
                '.'.join((bp_name, 'images')),
                filename=filename,
            ),
        )
        print(5, response.get_data(), response.headers, response.mimetype)
        self.assert200(response)
        link = path.join(
            self.link_storage_dir, filename[0], filename[1], filename)
        self.assertTrue(path.islink(link))
        self.assertTrue(path.isfile(readlink(link)))

        # GET image in new size and format (png)
        filename = path.extsep.join((self.fsum, '150', 'png'))
        response = self.client.get(
            url_for(
                '.'.join((bp_name, 'images')),
                filename=filename,
            ),
        )
        print(6, response.get_data(), response.headers, response.mimetype)
        self.assert200(response)
        link = path.join(
            self.link_storage_dir, filename[0], filename[1], filename)
        self.assertTrue(path.islink(link))
        self.assertTrue(path.isfile(readlink(link)))

        # GET not exists original image
        response = self.client.get(
            url_for(
                '.'.join((bp_name, 'images')),
                filename=path.extsep.join((
                    '00not_exists_file',
                    self.original,
                    'jpg',
                )),
            ),
        )
        print(7)
        self.assert404(response)

        # GET new format of not exists original image
        response = self.client.get(
            url_for(
                '.'.join((bp_name, 'images')),
                filename=path.extsep.join((
                    '00not_exists_file',
                    '800x600',
                    'jpg',
                )),
            ),
        )
        print(8, response.get_data())
        self.assert404(response)

#    @unittest.skip
    def test_04_upload_images(self):
        storageConfig = dict(
            store1={'reserved': 0, 'writable': True},
        )
        collection = [
            self.create_storage(
                name, **params
            ) for name, params in storageConfig.items()
        ]
        current_app.storages._collection = collection

        # unauthorized access
        response = self.client.post(
            url_for('.'.join((bp_name, 'images'))),
            buffered=True,
            content_type='multipart/form-data',
            data={'image_file': (open(self.test_img, "rb"), 'xxx.jpg')}
        )
        self.assert401(response)

        response = self.client.post(
            url_for('.'.join((bp_name, 'images'))),
            buffered=True,
            content_type='multipart/form-data',
            data={
                'login': 'test_user',
                'password': 'wrong',
                'image_file': (open(self.test_img, "rb"), 'xxx.jpg')
            },
        )
        self.assert401(response)

        response = self.client.post(
            url_for('.'.join((bp_name, 'images'))),
            buffered=True,
            content_type='multipart/form-data',
            data={
                'login': 'unknown',
                'password': 'wrong',
                'image_file': (open(self.test_img, "rb"), 'xxx.jpg')
            },
        )
        self.assert401(response)

        # upload new
        response = self.client.post(
            url_for('.'.join((bp_name, 'images'))),
            buffered=True,
            content_type='multipart/form-data',
            data={
                'login': 'test_user',
                'password': 'test_password',
                'image_file': (open(self.test_img, "rb"), 'xxx.jpg')
            },
            #headers={'Content-Length': path.getsize(self.test_img)},
        )
        self.assertStatus(response, 201)
        print(8, response.get_data(), response.headers)
        self.assertNotEqual(response.headers.get('location'), None)
        # TODO: test is file exists

        # upload duplicate
        response = self.client.post(
            url_for('.'.join((bp_name, 'images'))),
            buffered=True,
            content_type='multipart/form-data',
            data={
                'login': 'test_user',
                'password': 'test_password',
                'image_file': (open(self.test_img, "rb"), 'xxx.jpg')
            },
        )
        self.assert200(response)
        print(9, response.get_data(), response.headers)

if __name__ == '__main__':
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
