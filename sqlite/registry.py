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

import gc

from .oidMappings import OidMapping, ObjMapping
from .commands import ThreadedCommands
from .serialize import ObjectSerializer
from .deserialize import ObjectDeserializer
from .sqlStorage import SQLStorage

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class SQLObjectRegistryBase(object):
    def __init__(self, filename, dbid=None):
        self._tinit()
        self._tcall(self._initFileStorage, filename, dbid)

    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    def externalUrlFns(self, host):
        self._load.resolveExternalUrl = host.resolveExternalUrl
        self._load.onLoadedObject = host.onLoadedObject
        self._load.onLoadedObjRef = host.onLoadedObjRef

        self._save.urlForExternal = host.urlForExternal
        self._save.urlForExternalRef = host.urlForExternalRef

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @property
    def dbid(self):
        return self.stg.dbid

    def commit(self): 
        return self._tcall(self._save.commit)

    def gc(self): 
        return self._tcall(self.stg.gc)
    def gcFull(self): 
        return self._tcall(self.stg.gcFull)
    def gcCollect(self): 
        return self._tcall(self.stg.gcCollect)
    def allURLPaths(self):
        allURLPaths = self._tcall(self.stg.allURLPaths)
        return [url for url,oid in allURLPaths]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __getitem__(self, key):
        if isinstance(key, basestring):
            if key.isdigit():
                key = int(key)
        return self.load(key)
    def __setitem__(self, key, obj):
        return self.store(obj, key)
    def __delitem__(self, key, obj):
        return self.remove(obj)

    def load(self, oid, depth=1):
        return self._tcall(self._load.loadOid, oid, depth)
    def store(self, obj, urlpath=None):
        return self._tcall(self._save.store, obj, urlpath)
    def storeAll(self, iter, named=None):
        return self._tcall(self._save.storeAll, iter, named)
    def remove(self, obj):
        return self._tcall(self._save.remove, obj)

    def close(self):
        return self._tcall(self._tclose)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Mediator Implementation
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    stg = None
    _save = None
    _load = None

    def _initFileStorage(self, filename, dbid=None):
        stg = SQLStorage(filename, dbid)
        self.stg = stg

        stg.objToOid = ObjMapping()
        stg.oidToObj = OidMapping()

        self._save = ObjectSerializer(self)
        self._load = ObjectDeserializer(self)

    def _close(self):
        self._load.close()
        self._save.close()

        self.stg.oidToObj.clear()
        self.stg.objToOid.clear()

        del self._load
        del self._save

        self.stg.close()

        del self.stg

    def _idle(self):
        ##self.stg.gc()
        pass

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Thread Management
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _tinit(self):
        raise NotImplementedError('Subclass Responsibility: %r' % (self,))
    def _tcall(self, fn, *args, **kw):
        raise NotImplementedError('Subclass Responsibility: %r' % (self,))
    def _tsend(self, fn, *args, **kw):
        raise NotImplementedError('Subclass Responsibility: %r' % (self,))
    def _tclose(self):
        raise NotImplementedError('Subclass Responsibility: %r' % (self,))

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Pool Threaded
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class SQLObjectRegistry(SQLObjectRegistryBase):
    _tcmds = None

    def _tinit(self):
        klass = self.__class__
        tcmds = klass._tcmds
        if tcmds is None:
            tcmds = ThreadedCommands(timeout=1.0)
            klass._tcmds = tcmds

        tcmds.connect(self._idle, self._close)

    def _tsend(self, fn, *args, **kw):
        return self._tcmds.send(fn, *args, **kw)

    def _tcall(self, fn, *args, **kw):
        return self._tcmds.call(fn, *args, **kw)

    def _tclose(self):
        tcmds = self._tcmds
        tcmds.disconnect(self._idle, self._close)

