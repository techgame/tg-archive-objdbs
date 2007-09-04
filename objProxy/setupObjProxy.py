#!/usr/bin/env python
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
##~ Copyright (C) 2002-2007  TechGame Networks, LLC.              ##
##~                                                               ##
##~ This library is free software; you can redistribute it        ##
##~ and/or modify it under the terms of the BSD style License as  ##
##~ found in the LICENSE file included with this distribution.    ##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import sys
from distutils.core import setup, Extension
import Pyrex.Distutils.build_ext

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

pyVersion = sys.version_info[:2]
objProxyExtension = Extension(
    name= 'TG.objdbs.objProxy._objProxy%d%d' % pyVersion, 
    sources= ['_objProxy%d%d.pyx' % pyVersion],
    )

PackageInfo = dict(
    name= 'TG.objdbs.objProxy',
    version= '0.4',
    author= 'Shane Holloway',
    author_email= 'shane.holloway@techgame.net',
    package_dir= {'TG.objdbs.objProxy': '.'},
    modules= ['TG.objdbs.objProxy'],
    ext_modules= [objProxyExtension],
    cmdclass= {'build_ext': Pyrex.Distutils.build_ext}
    )

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Main 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__=='__main__':
    setup(**PackageInfo)

