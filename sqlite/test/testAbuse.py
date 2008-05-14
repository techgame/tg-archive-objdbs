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

def saveObjs(filename, tree):
    oreg = SQLObjectRegistry(filename)
    oreg.store(tree, 'root')
    oreg.close()
    return oreg.nextOid

def loadObjs(filename):
    oreg = SQLObjectRegistry(filename)
    root = oreg.load('root')
    oreg.close()
    return oreg.nextOid

if __name__=='__main__':
    #dbname = ':memory:'
    dbname = 'testAbuse.db'
    print
    print 'creating tree'
    tree = list(objTree(4, 0, 5))
    print 'tree nodes:', total
    print

    #print
    #print 'pickling'
    #s = time.time()
    #r = pickle.dumps(tree, 2)
    #r = len(r)
    #d = time.time() - s
    #print 'done', d, r
    #print

    print
    print 'saving'
    s = time.time()
    nextOid = saveObjs(dbname, tree)
    d = time.time() - s
    print 'done', d, nextOid
    print

    #print
    #print 'loading'
    #loadObjs(dbname)
    #print 'done'
    #print

