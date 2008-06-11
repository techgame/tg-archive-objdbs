##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##
##~ Copyright (C) 2002-2008  TechGame Networks, LLC.              ##
##~                                                               ##
##~ This library is free software; you can redistribute it        ##
##~ and/or modify it under the terms of the BSD style License as  ##
##~ found in the LICENSE file included with this distribution.    ##
##~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import weakref
import pickle 
from .proxy import ObjOidRef, ObjOidProxy

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class reduction_list(list):
    __slots__ = ()

class reduction_dict(list):
    __slots__ = ()

class ObjectSerializer(object):
    _reduceProtocol = 2

    def __init__(self, reg):
        self._keepitclose = []
        self._deferredStores = []

        stg = reg.stg
        self.stg = stg
        self.objToOid = stg.objToOid
        self.oidToObj = stg.oidToObj

    def __repr__(self):
        return self.stg.dbid

    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    def close(self):
        self.stg = None

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def oidForObj(self, obj, create=True):
        oid = self.objToOid.find(obj)
        if oid is None and create:
            oid = self._storeObject(obj)
        return oid

    def setOidForObj(self, obj, otype, oid, replace=False):
        self.oidToObj.addByStore(oid, obj, replace)
        self.objToOid.addByStore(oid, obj, replace)
        return oid

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def storeAll(self, iter, named=None):
        for obj in iter:
            oid = self._storeObject(obj)
            self.storeDeferred()

        if named is not None:
            if hasattr(named, 'iteritems'):
                named = named.iteritems()

            setPath = self.stg.setURLPathForOid
            for path, obj in named:
                oid = self._storeObject(obj)
                setPath(path, oid)
                self.storeDeferred()

    def store(self, obj, urlPath=None):
        self.storeDeferred()
        oid = self._storeObject(obj)
        if urlPath is not None:
            self.stg.setURLPathForOid(urlPath, oid)

        self.clearDeferred()
        return oid

    def storeOpen(self, obj, urlPath=None):
        oid = self._storeObject(obj)
        if urlPath is not None:
            self.stg.setURLPathForOid(urlPath, oid)

        self.storeDeferred()
        return oid

    def remove(self, obj):
        oid = self.oidForObj(obj, False)
        if oid is None: 
            return None

        self.objToOid.remove(obj)
        self.oidToObj.remove(oid, obj)
        self.stg.removeOid(oid)
        return oid

    def _storeObject(self, obj):
        oid = self.storeExternal(obj)
        if oid is not None:
            return oid

        oid = self.storeByType(obj)
        if oid is not None:
            return oid

        oid = self.storeByReduce(obj)
        if oid is not None:
            return oid

        raise Exception("Unable to store object", obj)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def commit(self):
        self.storeDeferred()
        self.oidToObj.commitOpen(self)
        self.stg.commit()

    def clearDeferred(self):
        del self._deferredStores[:]
    def storeDeferred(self):
        work = self._deferredStores
        while work:
            fn, args = work.pop()
            fn(*args)

    #def _defer(self, fn, *args):
    #    fn(*args)
    def _defer(self, fn, *args):
        self._deferredStores.append((fn, args))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Type
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def urlForExternal(self, obj):
        return None

    def storeExternal(self, obj):
        if isinstance(obj, (ObjOidProxy, ObjOidRef)):
            url = obj.__getProxy__().url
        else:
            url = self.urlForExternal(obj)

        if url is None:
            return None

        assert False, ('external:', url)
        oid = self.oidForObj(obj, False)
        if oid is not None:
            return oid

        oid = self._stg_oid(obj, 'external')
        self.stg.setExternal(oid, url)
        return oid

    _storeByTypeMap = {}
    def storeByType(self, obj):
        objType = type(obj)
        fn = self._storeByTypeMap.get(objType)
        if fn is not None: 
            return fn(self, obj)

    def regType(types, map=_storeByTypeMap):
        def registerFn(fn):
            for t in types:
                map[t] = fn
            return fn
        return registerFn

    @regType([type(None)])
    def _storeAs_noneValue(self, value):
        return self.stg.setOid(0, 'null', '')

    @regType([bool, int, float, str, unicode])
    def _storeAs_literalValue(self, value):
        return self._stg_setLiteral(value, None, 'lit')

    @regType([complex])
    def _storeAs_pickleValue(self, obj):
        pobj = buffer(pickle.dumps(obj, 2))
        return self._stg_setLiteral(
            pobj, type(obj).__name__, 'pickle')

    @regType([tuple])
    def _storeAs_tuple(self, obj):
        oid = self.oidForObj(obj, False)
        if oid is not None:
            return oid

        oid = self._stg_oid(obj, 'tuple')
        self._defer(self._stg_setOrdered, oid, obj)
        return oid

    @regType([list, set, frozenset])
    def _storeAs_ordered(self, obj):
        oid = self._stg_oid(obj, 'list')
        self._defer(self._stg_setOrdered, oid, obj)
        return oid

    @regType([dict])
    def _storeAs_mapping(self, obj):
        oid = self._stg_oid(obj, 'map')
        self._defer(self._stg_setMapping, oid, obj.iteritems())
        return oid

    @regType([weakref.ref])
    def _storeAs_weakref(self, obj):
        oid = self._stg_oid(obj, 'weakref')
        oid_ref = self.oidForObj(obj())
        self.stg.setWeakref(oid, oid_ref)
        return oid

    @regType([ObjOidProxy, ObjOidRef])
    def _storeAs_oidRef(self, obj):
        return obj.__getProxy__().oid

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Reduction
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def storeByReduce(self, obj):
        oid = self._stg_oid(obj, 'obj')
        self._defer(self._storeAs_reduction, oid, obj)
        return oid

    def _storeAs_reduction(self, oid, obj):
        reduction = self._asReductionMap(*self._reduceObj(obj))
        self._stg_setMapping(oid, reduction)
        return oid

    def _reduceObj(self, obj):
        fn = getattr(obj, '__reduce_ex__', None)
        if fn is not None:
            return fn(self._reduceProtocol)

        fn = getattr(obj, '__reduce__', None)
        if fn is not None:
            return fn()

        raise Exception("Cannot store %r object: %r" % (obj.__class__.__name__, obj))

    def _asReductionMap(self, fn, newArgs, state=None, listitems=None, dictitems=None):
        if type(state) is dict:
            state = reduction_dict(state.items())

        reduction = [
            ('args', reduction_list(newArgs[1:])), 
            ('state', state),
            ('listitems', listitems and reduction_list(listitems) or None),
            ('dictitems', dictitems and reduction_dict(dictitems) or None)]
        reduction = [(k,v) for k,v in reduction if v]
        return reduction

    @regType([reduction_list])
    def _storeAs_reductionList(self, obj):
        oid = self._stg_oid(obj, 'reduction', 'list', True)
        self._stg_setOrdered(oid, obj)
        return oid

    @regType([reduction_dict])
    def _storeAs_reductionDict(self, obj):
        oid = self._stg_oid(obj, 'reduction', 'dict', True)
        self._stg_setMapping(oid, obj)
        return oid

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Utilites
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def otypeForObj(self, obj):
        klass = obj.__class__
        m = klass.__module__
        if m != '__builtin__':
            return m+'.'+klass.__name__
        else: return klass.__name__

    def _stg_oid(self, obj, stg_kind, otype=None, transient=False):
        if otype is None:
            otype = self.otypeForObj(obj)
        oid = self.oidForObj(obj, False)
        oid = self.stg.setOid(oid, stg_kind, otype)
        if transient:
            return oid
        return self.setOidForObj(obj, otype, oid)

    def _stg_setOrdered(self, oid, listitems):
        oidOf = self.oidForObj
        valueOids = [oidOf(v) for v in listitems]
        self.stg.setOrdered(oid, valueOids)
        return valueOids

    def _stg_setMapping(self, oid, dictitems):
        oidOf = self.oidForObj
        itemOids = [(oidOf(k), oidOf(v)) for k, v in dictitems]
        self.stg.setMapping(oid, itemOids)
        return itemOids

    def _stg_setLiteral(self, value, value_type, stg_kind):
        oid = self.oidForObj(value, False)
        if oid is not None:
            return oid

        if value_type is None:
            value_type = type(value).__name__
        oid = self.stg.setLiteral(value, hash(value), value_type, stg_kind)
        return self.setOidForObj(value, value_type, oid)

    del regType


