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
from .proxy import ObjOidProxy

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjectDeserializer(object):
    _reduceProtocol = 2
    dbid = None
    stg = None
    objToOids = None
    oidToObj = None
    Proxy = ObjOidProxy

    def __init__(self, registry):
        self.dbid = registry.dbid
        self.stg = registry.stg
        self.objToOids = registry.objToOids
        self.oidToObj = registry.oidToObj

    def __repr__(self):
        return self.dbid
    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    def loadOid(self, oid, depth=1):
        if isinstance(oid, basestring):
            return self.loadUrlPath(oid, depth)

        stg_kind, otype = self.stg.getOidInfo(oid)
        result = self.loadEntry((oid, stg_kind, otype), depth)
        return result

    def loadUrlPath(self, urlPath, depth=1):
        unique = object()
        result = self.oidToObj.get(urlPath, unique)
        if result is not unique:
            return result

        entry = self.stg.getAtURLPath(urlPath)
        if entry is None:
            return None

        result = self.loadEntry(entry, depth)
        self.oidToObj[urlPath] = result
        return result

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Type
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    _loadByKindMap = {}
    def loadEntry(self, entry, depth):
        oid, stg_kind, otype = entry

        unique = object()
        result = self.oidToObj.get(oid, unique)
        if result is not unique:
            return result

        fn, allowProxy = self._loadByKindMap[stg_kind]
        if allowProxy:
            if depth == 0:
                return self.Proxy(self, oid)

        result = fn(self, oid, stg_kind, otype, depth-1)
        return result

    def regKind(kind, allowProxy, map=_loadByKindMap):
        def registerFn(fn):
            map[kind] = fn, allowProxy
            return fn
        return registerFn

    @regKind('lit', False)
    def _loadAs_literal(self, oid, stg_kind, otype, depth):
        result = self.stg.getLiteral(oid)
        if otype in ('str', 'unicode'):
            return self._oidLoaded(result, otype, oid)

        elif not isinstance(result, basestring):
            if otype == 'bool':
                result = bool(result)
            return self._oidLoaded(result, otype, oid)

        else: assert False, (stg_kind, otype, result)

    @regKind('pickle', True)
    def _loadAs_pickle(self, oid, stg_kind, otype, depth):
        result = self.stg.getLiteral(oid)
        result = pickle.loads(result)
        return self._oidLoaded(result, otype, oid)

    @regKind('weakref', False)
    def _loadAs_weakref(self, oid, stg_kind, otype, depth):
        result = self.stg.getWeakref(oid)
        if otype == 'weakref':
            result = weakref.ref(result)
        else: assert False, (stg_kind, otype, result)

        return self._oidLoaded(result, otype, oid)

    @regKind('tuple', False)
    def _loadAs_tuple(self, oid, stg_kind, otype, depth):
        result = tuple(self._stg_getOrdered(oid, depth))
        return self._oidLoaded(result, otype, oid)

    @regKind('list', True)
    def _loadAs_list(self, oid, stg_kind, otype, depth):
        result = self._stg_getOrdered(oid, depth)
        if otype == 'list':
            result = list(result)
        elif otype == 'set':
            result = set(result)
        elif otype == 'frozenset':
            result = frozenset(result)

        else: assert False, (stg_kind, otype, result)

        return self._oidLoaded(result, otype, oid)

    @regKind('map', True)
    def _loadAs_map(self, oid, stg_kind, otype, depth):
        result = self._stg_getMapping(oid, depth)
        if otype == 'dict':
            result = dict(result)

        else: assert False, (stg_kind, otype, result)

        return self._oidLoaded(result, otype, oid)


    @regKind('obj', True)
    def _loadAs_obj(self, oid, stg_kind, otype, depth):
        load = self.loadEntry
        reduction = self.stg.getMapping(oid)
        reduction = dict((load(k,-1), v) for k, v in reduction)

        klass = self.lookupOType(otype)

        args = [load(v, -1) for v in reduction.get('args', ())]
        obj = klass.__new__(klass, *args)
        self._oidLoaded(obj, otype, oid)

        if depth >= 0:
            sdepth = depth + 1
        else: sdepth = -1

        if 'state' in reduction:
            state = load(reduction['state'], sdepth)
            if hasattr(obj, '__setstate__'):
                obj.__setstate__(state)
            else: obj.__dict__.update(state)

        if 'listitems' in reduction:
            listitems = load(reduction['listitems'], sdepth)
            if hasattr(obj, 'extend'):
                obj.extend(listitems)
            else:
                for v in listitems:
                    obj.append(v)

        if 'dictitems' in reduction:
            dictitems = load(reduction['dictitems'], sdepth)
            for k, v in dictitems.iteritems():
                obj[k] = v

        return obj

    del regKind

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Utilities
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def setOidForObj(self, obj, otype, oid):
        try: okey = hash(obj)
        except TypeError: 
            okey = id(obj)
        self.objToOids[otype, okey] = oid
        self.oidToObj[oid] = obj
        return oid

    def _oidLoaded(self, obj, otype, oid):
        self.setOidForObj(obj, otype, oid)
        return obj

    def lookupOType(self, otype):
        path, dot, name = otype.rpartition('.')
        if dot:
            m = __import__(path, {}, {}, [name])
        else: m = __builtins__

        return getattr(m, name)

    def _stg_getOrdered(self, oid, depth):
        load = self.loadEntry
        result = self.stg.getOrdered(oid)
        result = [load(v, depth) for v in result]
        return result

    def _stg_getMapping(self, oid, depth):
        load = self.loadEntry
        result = self.stg.getMapping(oid)
        result = [(load(k, depth or 1), load(v, depth)) for k, v in result]
        return result

