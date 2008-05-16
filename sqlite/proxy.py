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
    __slots__ = ('host', 'oid', 'ref', 'wrproxy')

    def __init__(self, host, oid):
        self.host = host
        self.oid = oid
        self.ref = None
        self.wrproxy = None

    def __repr__(self):
        if self.ref is None:
            return "<ref oid: %r host: %r>" % (self.oid, self.host)
        else: 
            return "@%r %r" % (self.oid, self.ref)

    def proxy(self):
        pxy = self.wrproxy
        if pxy is not None:
            obj = pxy()
            if obj is not None:
                return obj

        obj = ObjOidProxy(self)
        self.wrproxy = weakref.ref(obj, self._collect)
        return obj

    def _collect(self, wr=None):
        print 'collect:', repr(self)
    def __call__(self, autoload=True):
        ref = self.ref
        if ref is None and autoload:
            ref = self.host.loadOidRef(self)
        return ref

    def __getstate__(self):
        raise NotImplementedError("__getstate__ on ObjOidRef should never be called")
    def __reduce_ex__(self, proto):
        ref = self.ref
        if ref is None:
            assert False, "I have to load it to save it??"

        return ref.__reduce_ex__(proto)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjOidProxy(ProxyComplete):
    def __init__(self, oidref):
        self.__setProxy__(oidref)

    def __repr__(self):
        return repr(self.__getProxy__())

    def __getstate__(self):
        raise NotImplementedError("__getstate__ on ObjOidProxy should never be called")
    def __reduce_ex__(self, proto):
        objRef = self.__getProxy__()
        return objRef.__reduce_ex__(proto)

    def __proxyOrNone__(self):
        objRef = self.__getProxy__()
        if objRef is not None:
            return objRef(False)
    def __proxy__(self):
        objRef = self.__getProxy__()
        return objRef(True)

    def __getattr__(self, name):
        obj = self.__proxy__()
        return getattr(obj, name)

