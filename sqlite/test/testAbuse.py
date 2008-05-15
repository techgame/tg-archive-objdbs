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

class Node(list):
    def __init__(self, i, d):
        self.i = i
        self.d = d

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Main 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

total = 0
def objTree(n, d, depth):
    global total
    total += n
    for i in xrange(n):
        obj = Node(i, d)
        if d+1 < depth-1:
            obj.extend(objTree(n, d+1, depth))
        yield obj

def saveObjs(filename, tree, tname='root'):
    oreg = SQLObjectRegistry(filename)
    oidStart = oreg.nextOid
    oreg.store(tree, tname)
    oidEnd = oreg.nextOid
    #oreg.gc()
    oreg.close()
    return oidStart, oidEnd

def loadObjs(filename):
    oreg = SQLObjectRegistry(filename)
    oidStart = oreg.nextOid
    root = oreg.load('root')
    oidEnd = oreg.nextOid
    oreg.close()
    return oidStart, oidEnd

if __name__=='__main__':
    dbname = ':memory:'
    dbname = 'testAbuse.db'

    for loop in range(5):
        print 'creating tree:',
        tree = list(objTree(4, 0, 8))
        print total

        print 'saving'
        s = time.time()
        oidStart, oidEnd = saveObjs(dbname, tree, 'root-%s'%(loop%3,))
        d = time.time() - s
        oidDelta = oidEnd - oidStart
        print 'done:', d, 
        print 'oidDelta:', oidDelta, oidDelta/d
        #print 'oidEnd:', oidEnd
        print

