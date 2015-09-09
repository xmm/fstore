# -*- coding: utf-8 -*-
'''
Copyright (c) 2015
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''

from flask import current_app, request
from flask.views import MethodView
from werkzeug import abort
from werkzeug.exceptions import HTTPException

from api.exceptions import StorageUnavailableError, ResourceExists
from api.resource import Resource, SaveResource, RetrieveResource
from tools.xsendfile import x_accel_redirect
from tools.auth import login_required


class ImagesView(MethodView):

    @login_required
    def post(self):
        try:
            upload = request.files['image_file']

            resource = Resource(SaveResource(upload))

            try:
                current_app.storages.saveResource(resource)
                return 'OK', 201, {'location': resource.fileName}
            except StorageUnavailableError as e:
                abort(503)
            except ResourceExists:
                return 'OK', 200, {'location': resource.fileName}

        except Exception as e:
            abort(400)

    def get(self, filename):
        try:
            resource = Resource(RetrieveResource(request))
            try:
                current_app.storages.retrieveResource(resource)
                response = x_accel_redirect(resource.location, resource.size)
                return response
            except StorageUnavailableError as e:
                abort(503)

        except HTTPException as e:
            # print(e)
            raise
        except Exception as e:
            abort(500)
