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
from TG.objdbs.objProxy import ProxyComplete

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjOidRef(object):
    host = None
    oid = None
    ref = None
    otype = None
    def __init__(self, host, oid, otype=None):
        self.host = host
        self.oid = oid
        self.wrproxy = None
        #if otype is not None:
        #    self.otype = otype

    def __repr__(self):
        if self.otype is None:
            return "<ref oid: %r host: %r open: %s>" % (self.oid, self.host, self.ref is not None)
        else:
            return "<ref oid: %r host: %r open: %s otype: %s>" % (self.oid, self.host, self.ref is not None, self.otype)

    def __getProxy__(self): 
        return self

    def proxy(self):
        pxy = self.wrproxy
        if pxy is not None:
            obj = pxy()
            if obj is not None:
                return obj

        obj = ObjOidProxy(self)
        self.wrproxy = weakref.ref(obj)
        return obj

    def load(self, autoload=True):
        ref = self.ref
        if ref is None and autoload:
            ref = self.host.loadOidRef(self)
        return ref

    def __getstate__(self):
        raise NotImplementedError("__getstate__ on ObjOidRef should never be called")

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjOidProxy(ProxyComplete):
    def __init__(self, oidref):
        self.__setProxy__(oidref)

    def __repr__(self):
        return repr(self.__getProxy__())

    def __hash__(self):
        raise TypeError("ObjOidProxy objects are unhashable")

    def __reduce_ex__(self, proto):
        obj = self.__proxy__()
        return obj.__reduce_ex__(proto)

    def __getstate__(self):
        raise NotImplementedError("__getstate__ on ObjOidProxy should never be called")

    def __proxyOrNone__(self):
        objRef = self.__getProxy__()
        if objRef is not None:
            return objRef.load(False)
    def __proxy__(self):
        objRef = self.__getProxy__()
        return objRef.load(True)

    def __getattr__(self, name):
        obj = self.__proxy__()
        return getattr(obj, name)

