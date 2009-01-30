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
        #if not replace:
        #    if oid in self:
        #        assert self[oid] is obj, (oid, self[oid], obj)
        #    if oid in self._woids:
        #        assert self._woids[oid] is obj, (oid, self._woids[oid], obj)
        try:
            self._woids[oid] = obj
            self.pop(oid, None)
        except TypeError:
            self[oid] = obj
            self._woids.pop(oid, None)

    def addByStore(self, oid, obj, replace=False):
        #if not replace:
        #    if oid in self:
        #        assert self[oid] is obj, (oid, self[oid], obj)
        #    if oid in self._woids:
        #        assert self._woids[oid] is obj, (oid, self._woids[oid], obj)

        self[oid] = obj
        self._woids.pop(oid, None)

    def clear(self):
        self._woids.clear()
        return dict.clear(self)

    def commitOpen(self, save):
        for oid, v in self.items():
            newOid = save.storeOpen(v)
            #if v is not None:
            #    assert newOid == oid, (oid, newOid, type(v))

        for oid, v in self._woids.items():
            if isinstance(v, ObjOidProxy):
                continue
            if isinstance(oid, basestring):
                continue
            newOid = save.storeOpen(v)
            #assert newOid == oid, (oid, newOid, type(v))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjMapping(dict):
    def find(self, obj):
        key = self.keyForObj(obj)
        return self.get(key)

    def addByStore(self, oid, obj, replace=False):
        key = self.keyForObj(obj)
        if not replace and key in self:
            last = self[key]
            if (oid != last) and (self.oidToObj[last] is not None):
                raise RuntimeError("Replacement of existing key:%r prev:%r new:%r obj: %r" % (key, last, oid, obj))

        self[key] = oid
        ##assert self.find(obj) == oid

    def addByLoad(self, oid, obj, replace=False):
        key = self.keyForObj(obj, True)
        if not replace and key in self:
            last = self[key]
            if (oid != last) and (self.oidToObj[last] is not None):
                print RuntimeError("Replacement of existing key:%r prev:%r new:%r obj: %r" % (key, last, oid, obj))
                #raise RuntimeError("Replacement of existing key:%r prev:%r new:%r obj: %r" % (key, last, oid, obj))

        self[key] = oid
        ##assert self.find(obj) == oid

    _basicTypeBases = set([int, long, float, complex, basestring, str, unicode])
    def keyForObj(self, obj, retain=False):
        otype = type(obj)
        baseType = otype.__mro__[-2:][0]
        if baseType in self._basicTypeBases:
            key = (otype.__name__, obj)
            return key

        elif obj is None:
            key = None
            return key

        elif otype in (ObjOidProxy, ObjOidRef):
            key = ('oid', obj.__getProxy__().oid)
            return key

        else:
            key = id(obj)
            if retain:
                self[None, key] = obj

        #if key in self:
        #    oid = self[key]
        #    last = self.oidToObj[oid]
        #    if last is not None and last is not obj:
        #        if otype in (ObjOidProxy, ObjOidRef) and obj.__proxy__() is last:
        #            pass
        #        else:
        #            raise AssertionError("Inconsistent:", (last, obj, otype))

        return key

