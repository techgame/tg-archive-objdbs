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
import pickle 

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjectDeserializer(object):
    _reduceProtocol = 2
    oids = None
    stg = None

    def __init__(self, oids, stg):
        self.oids = oids
        self.stg = stg

    def load(self, oid):
        stg_kind, otype = self.stg.getOidInfo(oid)
        return self.loadEntry((oid, stg_kind, otype))

    def loadUrlPath(self, urlPath):
        e = self.stg.getAtURLPath(urlPath)
        return self.loadEntry(e)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Type
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    _loadByKindMap = {}
    def loadEntry(self, entry):
        oid, stg_kind, otype = entry
        fn = self._loadByKindMap.get(stg_kind)
        if fn is not None: 
            return fn(self, oid, stg_kind, otype)

    def regKind(kind, map=_loadByKindMap):
        def registerFn(fn):
            map[kind] = fn
            return fn
        return registerFn

    @regKind('lit')
    def _loadAs_literal(self, oid, stg_kind, otype):
        result = self.stg.getLiteral(oid)
        if otype in ('str', 'unicode'):
            return result

        elif not isinstance(result, basestring):
            if otype == 'bool':
                return bool(result)
            else:
                return result

        assert False, (stg_kind, otype, result)

    @regKind('pickle')
    def _loadAs_pickle(self, oid, stg_kind, otype):
        result = self.stg.getLiteral(oid)
        result = pickle.loads(result)
        return result

    @regKind('weakref')
    def _loadAs_weakref(self, oid, stg_kind, otype): 
        result = self.stg.getWeakref(oid)
        print (oid, stg_kind, otype, result)
        if otype == 'weakref':
            #return weakref.ref(result)
            pass
        return (stg_kind, otype, result)

    @regKind('tuple')
    def _loadAs_tuple(self, oid, stg_kind, otype): 
        result = self._stg_getOrdered(oid)
        return tuple(result)

    @regKind('list')
    def _loadAs_list(self, oid, stg_kind, otype): 
        result = self._stg_getOrdered(oid)
        if otype == 'list':
            return list(result)
        elif otype == 'set':
            return set(result)
        elif otype == 'frozenset':
            return frozenset(result)

        assert False, (stg_kind, otype, result)

    @regKind('map')
    def _loadAs_map(self, oid, stg_kind, otype): 
        result = self._stg_getMapping(oid)
        if otype == 'dict':
            return dict(result)

        assert False, (stg_kind, otype, result)

    @regKind('classic')
    def _loadAs_classic(self, oid, stg_kind, otype): 
        result = self._stg_getMapping(oid)
        return (stg_kind, otype, result)

    @regKind('obj')
    def _loadAs_obj(self, oid, stg_kind, otype): 
        result = self._stg_getMapping(oid)
        return (stg_kind, otype, result)

    del regKind

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Utilities
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _stg_getOrdered(self, oid):
        load = self.loadEntry
        result = self.stg.getOrdered(oid)
        result = [load(v) for v in result]
        return result

    def _stg_getMapping(self, oid):
        load = self.loadEntry
        result = self.stg.getMapping(oid)
        result = [(load(k), load(v)) for k, v in result]
        return result

