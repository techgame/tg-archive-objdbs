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

import time
from pprint import pprint
import pickle
import weakref
from TG.objdbs.sqlite import SQLObjectRegistry

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class LNode(list):
    def __init__(self, i, d):
        self.i = i
        self.d = d

class DNode(dict):
    def __init__(self, i, d):
        self.i = i
        self.d = d

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Main 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

total = 0
def objLTree(n, d, depth):
    global total
    total += n
    for i in xrange(n):
        obj = LNode(i, d)
        if d+1 < depth-1:
            obj.extend(objLTree(n, d+1, depth))
        yield obj

def objDTree(n, d, depth):
    global total
    total += n
    for i in xrange(n):
        obj = DNode(i, d)
        if d+1 < depth-1:
            obj.update(objDTree(n, d+1, depth))
        yield i, obj

if __name__=='__main__':
    #dbname = ':memory:'
    dbname = 'db_testAbuse.db'

    print 'creating root...'
    root = {
        'ltree': list(objLTree(2, 0, 10)),
        'dtree': dict(objDTree(3, 0, 8)),
        }
    print 'created root:', total

    print 'initial opening'
    #oreg = SQLObjectRegistry(dbname)
    oreg = None

    for loop in xrange(3):
        if oreg is not None:
            oreg.close()

        print
        print 'opening'
        oreg = SQLObjectRegistry(dbname)

        print 'saving'
        oidStart = oreg.nextOid

        tstart = time.time()
        oreg.store(root, 'root-%s'%(loop%2,))
        tdelta = time.time() - tstart
        oidDelta = oreg.nextOid - oidStart

        print 'done:', tdelta, 
        print 'oidDelta:', oidDelta, oidDelta/tdelta
        print

        if 0:
            tstart = time.time()
            n,c = oreg.stg.gcFlush()
            tdelta = (time.time() - tstart) or 1
            print 'gcFlush seconds: %1.1f,  oid/sec: %.0f,  cull: %s rooted: %s ' % (tdelta, (n+c)/tdelta, n, c)

        print

    if oreg is not None:
        tstart = time.time()
        n,c = oreg.stg.gcCollect()
        tdelta = (time.time() - tstart) or 1
        print 'gcCollect seconds: %1.1f,  oid/sec: %.0f,  cull: %s rooted: %s ' % (tdelta, (n+c)/tdelta, n, c)
        oreg.commit()

    if oreg is not None:
        oreg.close()

