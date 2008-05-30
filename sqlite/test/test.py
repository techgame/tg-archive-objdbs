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
    pass

class TestList(list):
    pass

class TestDict(dict):
    pass

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Main 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def saveObjs(filename):
    oreg = SQLObjectRegistry(filename)
    oreg.store(None)
    oreg.store(True)
    oreg.store(False)
    oreg.store('a string')
    oreg.store(u'a unicode string')
    oreg.store(42)
    oreg.store(19.42)
    oreg.store(4+2j)

    oreg.store(())
    oreg.store(('a tuple', 0xf, 42.))
    oreg.store(range(5))
    oreg.store({'neato': 42, 'keen': True})

    oreg.store(set(range(5)))
    oreg.store(frozenset(range(5)))

    tobj = TestObject()
    tobj.desc = 'a fun object'
    oreg.store(tobj, 'tobj')

    tlist = TestList()
    tlist.desc = '[20, 30) by twos'
    tlist.extend(range(20,30,2))
    oreg.store(tlist, 'tlist')

    tdict = TestDict()
    tdict.update((n, v) for n,v in zip('abcde', range(100,1000,100)))
    oreg.store(tdict, 'tdict')

    mobj = TestObject()
    mobj.testObj = tobj
    mobj.testDict = tdict
    mobj.testList = tlist
    mobj.mobj = mobj
    mobj.recurse = [1, mobj, [2, mobj, [3, mobj, [4, mobj]]]]
    mobj.name = 'lala'
    oreg.store(mobj, 'mobj')

    wr = weakref.ref(mobj)
    oreg.store(wr)

    oreg.commit()
    oreg.close()

def loadObjs(filename):
    oreg = SQLObjectRegistry(filename)
    print
    for url in oreg.allURLPaths():
        print
        print 'load url:', url
        r = oreg.load(url)
        pprint((r, vars(r)))

        rl = getattr(r, 'recurse', None)
        if rl is not None:
            print
            print 'recurse:', list(rl)
            pprint((r, vars(r)))
            print
    print
    oreg.commit()
    oreg.close()

if __name__=='__main__':
    saveObjs('db_test.db')
    loadObjs('db_test.db')

