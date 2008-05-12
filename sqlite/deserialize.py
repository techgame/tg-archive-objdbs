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
    stg = None
    objToOids = None
    oidToObj = None

    def __init__(self, stg, objToOids, oidToObj):
        self.stg = stg
        self.objToOids = objToOids
        self.oidToObj = oidToObj

    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    def load(self, oid):
        if isinstance(oid, basestring):
            return self.loadUrlPath(oid)

        stg_kind, otype = self.stg.getOidInfo(oid)
        result = self.loadEntry((oid, stg_kind, otype))
        return result

    def loadUrlPath(self, urlPath):
        unique = object()
        result = self.oidToObj.get(urlPath, unique)
        if result is not unique:
            return result

        e = self.stg.getAtURLPath(urlPath)
        result = self.loadEntry(e)
        return self._oidLoaded(urlPath, result)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Type
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    _loadByKindMap = {}
    def loadEntry(self, entry):
        oid, stg_kind, otype = entry

        unique = object()
        result = self.oidToObj.get(oid, unique)
        if result is not unique:
            return result

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
            return self._oidLoaded(oid, result)

        elif not isinstance(result, basestring):
            if otype == 'bool':
                result = bool(result)
            return self._oidLoaded(oid, result)

        else: assert False, (stg_kind, otype, result)

    @regKind('pickle')
    def _loadAs_pickle(self, oid, stg_kind, otype):
        result = self.stg.getLiteral(oid)
        result = pickle.loads(result)
        return self._oidLoaded(oid, result)

    @regKind('weakref')
    def _loadAs_weakref(self, oid, stg_kind, otype): 
        result = self.stg.getWeakref(oid)
        if otype == 'weakref':
            result = weakref.ref(result)
        else: assert False, (stg_kind, otype, result)

        return self._oidLoaded(oid, result)

    @regKind('tuple')
    def _loadAs_tuple(self, oid, stg_kind, otype): 
        result = tuple(self._stg_getOrdered(oid))
        return self._oidLoaded(oid, result)

    @regKind('list')
    def _loadAs_list(self, oid, stg_kind, otype): 
        result = self._stg_getOrdered(oid)
        if otype == 'list':
            result = list(result)
        elif otype == 'set':
            result = set(result)
        elif otype == 'frozenset':
            result = frozenset(result)

        else: assert False, (stg_kind, otype, result)

        return self._oidLoaded(oid, result)

    @regKind('map')
    def _loadAs_map(self, oid, stg_kind, otype): 
        result = self._stg_getMapping(oid)
        if otype == 'dict':
            result = dict(result)

        else: assert False, (stg_kind, otype, result)

        return self._oidLoaded(oid, result)


    @regKind('obj')
    def _loadAs_obj(self, oid, stg_kind, otype): 
        load = self.loadEntry
        reduction = self.stg.getMapping(oid)
        reduction = dict((load(k), v) for k, v in reduction)

        klass = self.lookupOType(otype)

        args = [load(v) for v in reduction.get('args', ())]
        obj = klass.__new__(klass, *args)
        self._oidLoaded(oid, obj)


        if 'state' in reduction:
            state = load(reduction['state'])
            if hasattr(obj, '__setstate__'):
                obj.__setstate__(state)
            else: obj.__dict__.update(state)

        if 'listitems' in reduction:
            listitems = load(reduction['listitems'])
            if hasattr(obj, 'extend'):
                obj.extend(listitems)
            else:
                for v in listitems:
                    obj.append(v)

        if 'dictitems' in reduction:
            dictitems = load(reduction['dictitems'])
            for k, v in dictitems.iteritems():
                obj[k] = v

        return obj

    del regKind

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Utilities
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _oidLoaded(self, oid, obj):
        self.setOidForObj(oid, obj)
        return obj

    def setOidForObj(self, obj, oid):
        try:
            self.objToOids[obj] = oid
        except TypeError:
            self.objToOids[id(obj)] = oid
        self.oidToObj[oid] = obj
        return oid

    def lookupOType(self, otype):
        path, dot, name = otype.rpartition('.')
        if dot:
            m = __import__(path, {}, {}, [name])
        else: m = __builtins__

        return getattr(m, name)

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

