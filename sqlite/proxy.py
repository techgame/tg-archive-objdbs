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

from TG.objdbs.objProxy import ProxyComplete

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjOidRef(object):
    __slots__ = ('host', 'oid', 'obj')

    def __init__(self, host, oid):
        self.host = host
        self.oid = oid
        self.obj = None

    def __repr__(self):
        if self.obj is None:
            return "<ref oid: %r host: %r>" % (self.oid, self.host)
        else: 
            return "@%r %r" % (self.oid, self.obj)

    def __call__(self, autoload=True):
        obj = self.obj
        if obj is None and autoload:
            obj = self.host.loadOid(self.oid)
            self.obj = obj
        return obj

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjOidProxy(ProxyComplete):
    def __init__(self, host, oid):
        self.__setProxy__(ObjOidRef(host, oid))

    def __repr__(self):
        return repr(self.__getProxy__())
    def __proxyOrNone__(self):
        objRef = self.__getProxy__()
        if objRef is not None:
            return objRef(True)

    def __proxy__(self):
        objRef = self.__getProxy__()
        return objRef(True)

    def __getattr__(self, name):
        obj = self.__proxy__()
        return getattr(obj, name)

