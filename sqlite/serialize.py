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

from types import InstanceType
import weakref
import pickle 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class linear_dict(list):
    __slots__ = ()

class ObjectSerializer(object):
    _reduceProtocol = 2
    dbid = None
    stg = None
    objToOids = None
    oidToObj = None

    def __init__(self, registry):
        self._deferred = []
        self.dbid = registry.dbid
        self.stg = registry.stg
        self.objToOids = registry.objToOids
        self.oidToObj = registry.oidToObj

    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    def oidForObj(self, obj, create=True):
        otype = self.otypeForObj(obj)
        try: okey = hash(obj)
        except TypeError: 
            okey = id(obj)

        oid = self.objToOids.get((otype, okey))

        if oid is None and create:
            oid = self._storeObject(obj)
        return oid

    def setOidForObj(self, obj, otype, oid):
        try: okey = hash(obj)
        except TypeError: 
            okey = id(obj)
        self.objToOids[otype, okey] = oid
        self.oidToObj[oid] = obj
        return oid

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def store(self, obj, urlPath=None):
        oid = self._storeObject(obj)
        if urlPath is not None:
            self.oidToObj[urlPath] = obj
            self.stg.setURLPathForOid(urlPath, oid)

        self.commit()
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
        self._storeDeferred()
        self.stg.commit()

    def _storeDeferred(self):
        work = self._deferred
        while work:
            fn, args = work.pop()
            fn(*args)

    def _defer(self, fn, *args):
        self._deferred.append((fn, args))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Type
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def storeExternal(self, obj):
        return None

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

    @regType([type(None), bool, int, float, str, unicode])
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

    @regType([linear_dict])
    def _storeAs_linearMapping(self, obj):
        oid = self._stg_oid(obj, 'map', 'dict')
        self._defer(self._stg_setMapping, oid, obj)
        return oid

    @regType([weakref.ref])
    def _storeAs_weakref(self, obj):
        oid = self._stg_oid(obj, 'weakref')
        oid_ref = self.oidForObj(obj())
        self.stg.setWeakref(oid, oid_ref)
        return oid

    del regType

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
        if fn.__name__ != '__newobj__':
            raise NotImplementedError("Outside support for reduce protocol 2")

        reduction = [
            ('args', newArgs[1:]), ('state', state),
            ('listitems', listitems and list(listitems)),
            ('dictitems', dictitems and linear_dict(dictitems))]
        reduction = [(k,v) for k,v in reduction if v]
        return reduction

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Utilites
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def otypeForObj(self, obj):
        klass = obj.__class__
        m = klass.__module__
        if m != '__builtin__':
            return m+'.'+klass.__name__
        else: return klass.__name__

    def _stg_oid(self, obj, stg_kind, otype=None):
        if otype is None:
            otype = self.otypeForObj(obj)
        oid = self.oidForObj(obj, False)
        oid = self.stg.setOid(obj, oid, stg_kind, otype)
        return self.setOidForObj(obj, otype, oid)

    def _stg_setOrdered(self, oid, listitems):
        oidOf = self.oidForObj
        valueOids = [oidOf(v) for v in listitems]
        self.stg.setOrdered(oid, valueOids)
        return oid

    def _stg_setMapping(self, oid, dictitems):
        oidOf = self.oidForObj
        itemOids = [(oidOf(k), oidOf(v)) for k, v in dictitems]
        self.stg.setMapping(oid, itemOids)
        return oid

    def _stg_setLiteral(self, value, value_type, stg_kind):
        oid = self.oidForObj(value, False)
        if oid is not None:
            return oid

        if value_type is None:
            value_type = type(value).__name__
        oid = self.stg.setLiteral(value, hash(value), value_type, stg_kind)
        return self.setOidForObj(value, value_type, oid)

