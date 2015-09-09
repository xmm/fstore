# -*- coding: utf-8 -*-
'''
Copyright (c) 2014
@author: Marat Khayrullin <xmm.dev@gmail.com>
'''

from api import create_app


application = create_app()

if __name__ == '__main__':
    application.run()
