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
    url = None

    def __init__(self, host, oid):
        self.host = host
        self.oid = oid
        self.ref = None
        self.wrproxy = None

    #def __repr__(self):
    #    if self.ref is None:
    #        return "<ref oid: %r host: %r open: %s>" % (self.oid, self.host, self.ref is None)
    #    else: return "@%r %r" % (self.oid, self.ref)

    def __repr__(self):
        return "<ref oid: %r host: %r open: %s>" % (self.oid, self.host, self.ref is not None)

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

    forbidLoading = 0
    def load(self, autoload=True):
        ref = self.ref
        if ref is None and autoload:
            assert self.__class__.forbidLoading == 0
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

