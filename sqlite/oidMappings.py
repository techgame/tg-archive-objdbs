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

import weakref
from .proxy import ObjOidRef, ObjOidProxy

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class OidMapping(dict):
    def __init__(self):
        self._woids = weakref.WeakValueDictionary()

    def __missing__(self, oid):
        return self._woids.get(oid, None)

    def addByLoad(self, oid, obj, replace=False):
        #if replace:
        #    print 'setByLoad:', (oid, id(obj), type(obj).__name__)
        #else: print 'addByLoad:', (oid, id(obj), type(obj).__name__)

        if not replace:
            if oid in self:
                assert self[oid] is obj, (oid, self[oid])
            if oid in self._woids:
                assert self._woids[oid] is obj, (oid, self._woids[oid])
        try:
            self._woids[oid] = obj
            self.pop(oid, None)
        except TypeError:
            self[oid] = obj
            self._woids.pop(oid, None)

    def addByStore(self, oid, obj, replace=False):
        #if replace:
        #    print 'setByStore:', (oid, id(obj), type(obj).__name__)
        #else: print 'addByStore:', (oid, id(obj), type(obj).__name__)

        if not replace:
            if oid in self:
                assert self[oid] is obj, (oid, self[oid])
            if oid in self._woids:
                assert self._woids[oid] is obj, (oid, self._woids[oid])

        self[oid] = obj
        self._woids.pop(oid, None)

    def clear(self):
        self._woids.clear()
        return dict.clear(self)

    def commitOpen(self, save):
        for oid, v in self.items():
            newOid = save.storeOpen(v)
            if v is not None:
                assert newOid == oid, (oid, newOid, type(v))

        for oid, v in self._woids.items():
            if isinstance(v, ObjOidProxy):
                continue
            if isinstance(oid, basestring):
                continue
            newOid = save.storeOpen(v)
            assert newOid == oid, (oid, newOid, type(v))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjMapping(dict):
    def find(self, obj):
        key = self.keyForObj(obj)
        return self.get(key)

    def addByStore(self, oid, obj, replace=False):
        key = self.keyForObj(obj)
        if not replace and key in self:
            if oid != self[key]:
                raise RuntimeError("Replacement of existing key: %s oid: %s entry: %s" % (key, oid, self[key]))
        #if replace:
        #    print ' ::setByStore:', (key, oid, type(obj).__name__)
        #else: print ' ::addByStore:', (key, oid, type(obj).__name__)
        self[key] = oid
        ##self[key, None] = obj

        assert self.find(obj) == oid

    def addByLoad(self, oid, obj, replace=False):
        key = self.keyForObj(obj)
        if not replace and key in self:
            if oid != self[key]:
                print RuntimeError("Replacement of existing key: %s oid: %s entry: %s" % (key, oid, self[key]))
                #raise RuntimeError("Replacement of existing key: %s oid: %s entry: %s" % (key, oid, self[key]))
        #if replace:
        #    print ' ::setByLoad:', (key, oid, type(obj).__name__)
        #else: print ' ::addByLoad:', (key, oid, type(obj).__name__)
        self[key] = oid
        ##self[key, None] = obj

        assert self.find(obj) == oid

    def keyForObj(self, obj):
        otype = type(obj)
        if otype in (int, long, float, complex, str, unicode):
            return (otype.__name__, obj)
        else:
            return id(obj)

