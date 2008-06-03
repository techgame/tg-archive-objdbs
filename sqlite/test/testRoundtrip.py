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

from pprint import pprint
import weakref
from TG.objdbs.sqlite import SQLObjectRegistry

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TestObject(object):
    n = 0

def saveObjs(filename):
    oreg = SQLObjectRegistry(filename)

    tobj = oreg.load('tobj')
    if tobj is None:
        tobj = TestObject()
    else:
        tobj.n += 1

    wrobj = oreg.load('wrtobj')
    if wrobj is None:
        wrobj = weakref.ref(tobj)
    assert wrobj() is tobj

    tobj.desc = 'a fun object: %s' % (tobj.n,)
    print tobj.desc

    oreg.store(tobj, 'tobj')

    oreg.commit()
    oreg.gcCollect()
    oreg.close()

if __name__=='__main__':
    saveObjs('db_testRoundtrip.db')

