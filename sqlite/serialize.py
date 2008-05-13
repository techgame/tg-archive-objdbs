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

class ObjectSerializer(object):
    _reduceProtocol = 2
    stg = None
    objToOids = None
    oidToObj = None

    def __init__(self, stg, objToOids, oidToObj):
        self.stg = stg
        self.objToOids = objToOids
        self.oidToObj = oidToObj

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

    def store(self, obj, urlpath=None):
        oid = self._storeObject(obj)
        if urlpath is not None:
            self.stg.setURLPathForOid(urlpath, oid)
        return oid

    def storeExternal(self, obj):
        return None

    def storeByReduce(self, obj):
        return self._storeAs_reduction(obj, *self._reduceObj(obj))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Type
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
        return self._stg_setOrdered(oid, list(obj))

    @regType([list, set, frozenset])
    def _storeAs_orderedValue(self, obj):
        oid = self._stg_oid(obj, 'list')
        return self._stg_setOrdered(oid, list(obj))

    @regType([dict])
    def _storeAs_mappingValue(self, obj):
        oid = self._stg_oid(obj, 'map')
        return self._stg_setMapping(oid, obj.iteritems())

    @regType([weakref.ref])
    def _storeAs_weakref(self, obj):
        oid = self._stg_oid(obj, 'weakref')
        oid_ref = self.oidForObj(obj())
        self.stg.setWeakref(oid, oid_ref)
        return oid

    del regType

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _storeAs_reduction(self, obj, fn, newArgs, state=None, listitems=None, dictitems=None):
        if fn.__name__ != '__newobj__':
            raise NotImplementedError("Outside support for reduce protocol 2")

        klass = newArgs[0]
        if klass is not type(obj):
            raise Exception("Reduction class is not identical to the type of obj")

        args = newArgs[1:]
        if args and args[0] is obj:
            # caution!
            raise Exception("Reduction directly includes obj instance!")

        otype = self.otypeForObj(obj)
        reduction = [
            #('ns', otype),
            ('args', args), ('state', state),
            ('listitems', listitems and list(listitems)),
            ('dictitems', dictitems and dict(dictitems))]
        reduction = [(k,v) for k,v in reduction if v]

        oid = self._stg_oid(obj, 'obj', otype)
        self._stg_setMapping(oid, reduction)
        return oid

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Utilites
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _reduceObj(self, obj):
        fn = getattr(obj, '__reduce_ex__', None)
        if fn is not None:
            return fn(self._reduceProtocol)

        fn = getattr(obj, '__reduce__', None)
        if fn is not None:
            return fn()

        raise Exception("Cannot store %r object: %r" % (obj.__class__.__name__, obj))

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

