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

import sys
import weakref
import pickle 
from .proxy import ObjOidRef, ObjOidProxy

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class ObjectDeserializer(object):
    def __init__(self, reg):
        self._transitiveOids = set()
        self._deferredRefs = {}

        stg = reg.stg
        self.reg = reg
        self.stg = reg.stg
        self.objToOid = stg.objToOid
        self.oidToObj = stg.oidToObj

    def __repr__(self):
        return self.stg.dbid

    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    def close(self):
        self.stg = None

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def onLoadedObject(self, oid, obj):
        return obj

    def onLoadedObjRef(self, oid, objRef):
        return objRef

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def loadOid(self, oid, default=None, depth=1):
        if isinstance(oid, basestring):
            return self.loadUrlPath(oid, default, depth)

        if not oid:
            return None

        cr = self.oidToObj.get(oid, None)
        if cr is not None:
            return cr

        stg_kind, otype = self.stg.getOidInfo(oid)
        result = self.loadEntry((oid, stg_kind, otype), depth)

        self._loadDeferred()
        return result

    def loadUrlPath(self, urlPath, default=None, depth=1):
        cr = self.oidToObj[urlPath]
        if cr is not None:
            return cr

        entry = self.stg.getAtURLPath(urlPath)
        if entry is None:
            return default

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
    def loadEntry(self, entry, depth, tempOids=None):
        oid, stg_kind, otype = entry

        if not oid:
            return None

        cr = self.oidToObj[oid]
        if cr is not None:
            return cr

        if tempOids is not None:
            tempOids.add(oid)

        fn, useProxy = self._loadByKindMap[stg_kind]

        if useProxy:
            objRef = ObjOidRef(self, oid, otype)
            objRef = self.onLoadedObjRef(oid, objRef)
            result = objRef.proxy()
        else:
            result = fn(self, oid, stg_kind, otype, depth-1)

        self.setOidForObj(result, otype, oid)

        if tempOids is not None:
            tempOids.discard(oid)
        return result

    def loadOidRef(self, oidRef):
        """Used by ObjOidRef to load state"""
        oid = oidRef.oid
        depth, oidRef = self._deferredRefs.pop(oid, (1, oidRef))
        return self.reg._tcall(self._loadAs_OidRef, oidRef, oid, depth)
    
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

    @regKind('type', False)
    def _loadAs_type(self, oid, stg_kind, otype, depth):
        vref = self.stg.getLiteral(oid)
        klass = self.lookupOType(vref)
        return klass

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

        result = self.resolveExternalUrl(url)
        return result

    def resolveExternalUrl(self, url):
        return None

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Storage by Reduction
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @regKind('reduction', False)
    def _loadAs_reduction(self, oid, stg_kind, otype, depth):
        if otype == 'dict':
            result = self._stg_getMapping(oid, depth)
            try:
                result = dict(result)
            except TypeError:
                mappingList = result
                result = dict()
                for (k,v) in mappingList:
                    try: result[k] = v
                    except TypeError: 
                        print >> sys.stdout
                        print >> sys.stdout, 'Error deserializing in loadAs_reduction key: %r value type: %r' % (k, type(v))
                        print >> sys.stdout
            return result
        elif otype == 'list':
            result = self._stg_getOrdered(oid, depth)
            result = list(result)
        else: 
            assert False, (stg_kind, otype, result)

        self._transitiveOids.add(oid)
        return result

    @regKind('obj', True)
    def _loadAs_obj(self, oid, stg_kind, otype, depth):
        tempOids = self._transitiveOids
        load = self.loadEntry
        reduction = self.stg.getMapping(oid)
        reduction = dict((load(k,-1), v) for k, v in reduction)

        klass = self.lookupOType(otype)

        args = reduction.get('args')
        if args is not None:
            args = list(load(args, 1, tempOids))
        else: args = []

        reconstruct = reduction.get('fn')
        if reconstruct is not None:
            fn = load(reconstruct, 1)
            reconstruct = self.lookupOType(fn)
        else: 
            fn = None
            reconstruct = klass.__new__
            args.insert(0, klass)

        try:
            obj = reconstruct(*args)
        except Exception:
            print >> sys.stdout
            print >> sys.stdout, 'Error deserializing in loadAs_reduction key: %r value type: %r' % (k, type(v))
            print >> sys.stdout, "reconstruct:", repr(reconstruct)
            print >> sys.stdout, "  reduction:", repr(reduction,)
            print >> sys.stdout, "  fn:", repr(fn,)
            print >> sys.stdout, "  klass:", repr(klass,)
            print >> sys.stdout, "  args:", repr(args,)
            print >> sys.stdout
            raise

        if depth >= 0:
            sdepth = depth + 1
        else: sdepth = -1

        if 'flags' in reduction:
            flags = load(reduction['flags'], sdepth, tempOids)
            flags = flags.split(';')
        else: flags = []

        if 'state' in reduction:
            state = load(reduction['state'], sdepth, tempOids)
            if 'stateEx' in flags:
                stateEx = (getattr(e, '__proxyItem__', e) for e in state)
                state = type(state)(stateEx)

            else: state = dict(state)

            if hasattr(obj, '__setstate__'):
                obj.__setstate__(state)
            else: 
                obj.__dict__.update(state)
            reduction['state'] = state
            del state


        if 'listitems' in reduction:
            listitems = load(reduction['listitems'], sdepth, tempOids)

            if hasattr(obj, 'extend'):
                obj.extend(listitems)
            else:
                for v in listitems:
                    obj.append(v)
            reduction['listitems'] = listitems
            del listitems

        if 'dictitems' in reduction:
            dictitems = load(reduction['dictitems'], sdepth, tempOids)
            for k, v in dictitems.iteritems():
                obj[k] = v
            reduction['dictitems'] = dictitems
            del dictitems

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
        if obj is None:
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
                print >> sys.stdout
                print >> sys.stdout, 'Error in lookupOType:', (path, dot, name)
                print >> sys.stdout
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

