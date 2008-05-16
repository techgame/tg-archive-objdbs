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
from .proxy import ObjOidRef

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjectDeserializer(object):
    OidRef = ObjOidRef

    def __init__(self, registry):
        self._transitiveOids = set()
        self._deferredRefs = {}
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

        self._loadDeferred()
        return result

    def loadUrlPath(self, urlPath, depth=1):
        cr = self.oidToObj[urlPath]
        if cr is not None:
            return cr

        entry = self.stg.getAtURLPath(urlPath)
        if entry is None:
            return None

        result = self.loadEntry(entry, depth)
        self.oidToObj.add(urlPath, result)

        self._loadDeferred()
        return result

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Type
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _loadDeferred(self):
        work = self._deferredRefs
        if not work: return

        loadOidRef = self._loadAs_OidRef
        while work:
            oid, (depth, oidRef) = work.popitem()
            loadOidRef(oidRef, oid, depth)

    def _deferRef(self, oidRef, oid, depth):
        self._deferredRefs[oid] = depth, oidRef

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    _loadByKindMap = {}
    def loadEntry(self, entry, depth):
        oid, stg_kind, otype = entry

        if not oid:
            return None

        cr = self.oidToObj[oid]
        if cr is not None or not oid:
            return cr

        fn, useProxy = self._loadByKindMap[stg_kind]

        if oid in self._transitiveOids:
            # transitive oid references -- return it without registering it
            return fn(self, oid, stg_kind, otype, depth-1)

        elif useProxy:
            oidRef = self.OidRef(self, oid)
            result = oidRef.proxy()
            self.setOidForObj(result, otype, oid, id(result))

            if depth != 0:
                self._deferRef(oidRef, oid, depth-1)

            return result

        else:
            result = fn(self, oid, stg_kind, otype, depth-1)

            self.setOidForObj(result, otype, oid)
            return result

    def loadOidRef(self, oidRef):
        oid = oidRef.oid
        depth, oidRef = self._deferredRefs.pop(oid, (1, oidRef))
        return self._loadAs_OidRef(oidRef, oid, depth)

    def _loadAs_OidRef(self, oidRef, oid, depth):
        stg_kind, otype = self.stg.getOidInfo(oid)
        fn, useProxy = self._loadByKindMap[stg_kind]
        if useProxy is False:
            raise RuntimeError("Oid for proxy load is marked as a non-proxy load method")

        ref = fn(self, oid, stg_kind, otype, depth)
        oidRef.ref = ref
        return ref

    def regKind(kind, useProxy, map=_loadByKindMap):
        def registerFn(fn):
            map[kind] = fn, useProxy
            return fn
        return registerFn

    @regKind('null', False)
    def _loadAs_none(self, oid, stg_kind, otype, depth):
        return None

    @regKind('lit', False)
    def _loadAs_literal(self, oid, stg_kind, otype, depth):
        result = self.stg.getLiteral(oid)
        if otype in ('str', 'unicode'):
            return result

        elif not isinstance(result, basestring):
            if otype == 'bool':
                result = bool(result)
            return result

        else: assert False, (stg_kind, otype, result)

    @regKind('pickle', True)
    def _loadAs_pickle(self, oid, stg_kind, otype, depth):
        result = self.stg.getLiteral(oid)
        result = pickle.loads(result)
        return result

    @regKind('weakref', False)
    def _loadAs_weakref(self, oid, stg_kind, otype, depth):
        result = self.stg.getWeakref(oid)
        if otype == 'weakref':
            result = weakref.ref(result)
        else: assert False, (stg_kind, otype, result)

        return result

    @regKind('tuple', False)
    def _loadAs_tuple(self, oid, stg_kind, otype, depth):
        result = tuple(self._stg_getOrdered(oid, depth))
        return result

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

        return result

    @regKind('map', True)
    def _loadAs_map(self, oid, stg_kind, otype, depth):
        result = self._stg_getMapping(oid, depth)
        if otype == 'dict':
            result = dict(result)

        else: assert False, (stg_kind, otype, result)

        return result

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Reduction
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @regKind('obj', True)
    def _loadAs_obj(self, oid, stg_kind, otype, depth):
        load = self.loadEntry
        reduction = self.stg.getMapping(oid)
        reduction = dict((load(k,-1), v) for k, v in reduction)

        klass = self.lookupOType(otype)

        args = [load(v, -1) for v in reduction.get('args', ())]
        obj = klass.__new__(klass, *args)

        if depth >= 0:
            sdepth = depth + 1
        else: sdepth = -1

        tempOids = self._transitiveOids
        if 'state' in reduction:
            rEntry = reduction['state']
            tempOids.add(rEntry[0])

            state = load(rEntry, sdepth)
            if hasattr(obj, '__setstate__'):
                obj.__setstate__(state)
            else: 
                obj.__dict__.update(state)
            del state
            tempOids.discard(rEntry[0])


        if 'listitems' in reduction:
            rEntry = reduction['listitems']
            tempOids.add(rEntry[0])

            listitems = load(rEntry, sdepth)
            if hasattr(obj, 'extend'):
                obj.extend(listitems)
            else:
                for v in listitems:
                    obj.append(v)
            del listitems
            tempOids.discard(rEntry[0])

        if 'dictitems' in reduction:
            rEntry = reduction['dictitems']
            tempOids.add(rEntry[0])

            dictitems = load(rEntry, sdepth)
            for k, v in dictitems.iteritems():
                obj[k] = v
            del dictitems
            tempOids.discard(rEntry[0])

        return obj

    del regKind

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Utilities
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def setOidForObj(self, obj, otype, oid, okey=None):
        if okey is None:
            try: okey = hash(obj)
            except TypeError: 
                okey = id(obj)
        self.objToOids[otype, okey] = oid
        self.oidToObj.add(oid, obj)
        return oid

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

