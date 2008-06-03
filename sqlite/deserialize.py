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
from .proxy import ObjOidRef, ObjOidProxy

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjectDeserializer(object):
    def __init__(self, registry):
        self._transitiveOids = set()
        self._deferredRefs = {}
        self.dbid = registry.dbid
        self.stg = registry.stg
        self._save = registry._save
        self.objToOid = registry.objToOid
        self.oidToObj = registry.oidToObj

    def __repr__(self):
        return self.dbid

    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    def close(self):
        self._save = None
        self.stg = None

    def onLoadedObject(self, oid, obj):
        return obj

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def loadOid(self, oid, depth=1):
        if isinstance(oid, basestring):
            return self.loadUrlPath(oid, depth)

        if not oid:
            return None

        cr = self.oidToObj.get(oid, None)
        if cr is not None:
            return cr

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
        self.oidToObj.addByLoad(urlPath, result)

        self._loadDeferred()
        return result

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Type
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _loadDeferred(self):
        work = self._deferredRefs
        if not work: return

        loadRef = self._loadAs_OidRef
        while work:
            oid, (depth, oidRef) = work.popitem()
            loadRef(oidRef, oid, depth)

    def _deferRef(self, oidRef, oid, depth):
        self._deferredRefs[oid] = depth, oidRef

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    _loadByKindMap = {}
    def loadEntry(self, entry, depth):
        oid, stg_kind, otype = entry

        if not oid:
            return None

        cr = self.oidToObj[oid]
        if cr is not None:
            return cr

        fn, useProxy = self._loadByKindMap[stg_kind]

        if useProxy:
            result = ObjOidRef(self, oid).proxy()
        else:
            result = fn(self, oid, stg_kind, otype, depth-1)

        self.setOidForObj(result, otype, oid)
        return result

    def loadOidRef(self, oidRef):
        """Used by ObjOidRef to load state"""
        oid = oidRef.oid
        depth, oidRef = self._deferredRefs.pop(oid, (1, oidRef))
        return self._loadAs_OidRef(oidRef, oid, depth)
 
    
    def _loadAs_OidRef(self, oidRef, oid, depth):
        stg_kind, otype = self.stg.getOidInfo(oid)
        fn, useProxy = self._loadByKindMap[stg_kind]
        if useProxy is False:
            raise RuntimeError("Oid for proxy load is marked as a non-proxy load method")

        obj = fn(self, oid, stg_kind, otype, depth-1)
        self.setOidForObj(obj, otype, oid, True)
        oidRef.ref = obj
        return obj

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
        otype = __builtins__[otype]
        result = otype(result)
        return result

    @regKind('pickle', True)
    def _loadAs_pickle(self, oid, stg_kind, otype, depth):
        result = self.stg.getLiteral(oid)
        result = pickle.loads(result)
        return result

    @regKind('weakref', False)
    def _loadAs_weakref(self, oid, stg_kind, otype, depth):
        result = self.stg.getWeakref(oid)
        if otype == 'weakref':
            try:
                result = weakref.ref(result)
            except TypeError:
                pass

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

    @regKind('external', True)
    def _loadAs_external(self, oid, stg_kind, otype, depth):
        url = self.stg.getExternal(oid)

        assert False, ('external:', oid, url)
        result = self.resolveExternalUrl(url)
        if isinstance(result, (ObjOidRef, ObjOidProxy)):
            result.__getProxy__().url = url
        return result

    def resolveExternalUrl(self, url):
        return None

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Reduction
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @regKind('reduction', False)
    def _loadAs_reduction(self, oid, stg_kind, otype, depth):
        result = self._stg_getMapping(oid, depth)

        if otype == 'dict':
            result = dict(result)
        elif otype == 'list':
            result = list(result)
        else: 
            assert False, (stg_kind, otype, result)

        self._transitiveOids.add(oid)
        return result

    @regKind('obj', True)
    def _loadAs_obj(self, oid, stg_kind, otype, depth):
        load = self.loadEntry
        reduction = self.stg.getMapping(oid)
        reduction = dict((load(k,-1), v) for k, v in reduction)

        klass = self.lookupOType(otype)

        args = [load(v, 2) for v in reduction.get('args', ())]
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
            #reduction['state'] = state
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
            #reduction['listitems'] = listitems
            del listitems
            tempOids.discard(rEntry[0])

        if 'dictitems' in reduction:
            rEntry = reduction['dictitems']
            tempOids.add(rEntry[0])

            dictitems = load(rEntry, sdepth)
            for k, v in dictitems.iteritems():
                obj[k] = v
            #reduction['dictitems'] = dictitems
            del dictitems
            tempOids.discard(rEntry[0])

        return self.onLoadedObject(oid, obj)

    del regKind

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Utilities
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def oidForObj(self, obj):
        oid = self.objToOid.find(obj)
        return oid

    def setOidForObj(self, obj, otype, oid, replace=False):
        if oid in self._transitiveOids:
            return oid

        self.oidToObj.addByLoad(oid, obj, replace)
        self.objToOid.addByLoad(oid, obj, replace)
        return oid

    def lookupOType(self, otype):
        path, dot, name = otype.rpartition('.')
        if not dot:
            m = __builtins__
        else: 
            try:
                m = __import__(path, {}, {}, [name])
            except Exception:
                print (path, dot, name)
                raise

        try:
            return getattr(m, name)
        except AttributeError:
            raise AttributeError("Module %r has not attribute %r" % (m, name))

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

