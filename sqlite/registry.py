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
import weakref
import sqlite3

from serialize import ObjectSerializer
from deserialize import ObjectDeserializer
from sqlStorage import SQLStorage

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class OidMapping(dict):
    def __init__(self):
        self._woids = weakref.WeakValueDictionary()

    def __missing__(self, oid):
        return self._woids.get(oid, None)

    def add(self, oid, obj):
        try:
            self._woids[oid] = obj
        except TypeError:
            self[oid] = obj

    def clear(self):
        self._woids.clear()
        return dict.clear(self)

    def commit(self):
        for oid, v in self._woids.items():
            if not isinstance(oid, int):
                continue
            if hasattr(v, '__getProxy__'):
                v = v.__getProxy__()
                v.commit()

class SQLObjectRegistry(object):
    def __init__(self, filename, dbid=None):
        self.objToOids = {}
        self.oidToObj = OidMapping()
        self._initFileStorage(filename, dbid)

    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    def _initFileStorage(self, filename, dbid=None):
        self.db = sqlite3.connect(filename)
        self.db.isolation_level = "DEFERRED"

        self.stg = SQLStorage(self.db)

        self.dbid = self.stg.dbid
        if self.dbid is None:
            self.dbid = dbid or filename 
            self.stg.dbid = self.dbid

        self._save = ObjectSerializer(self)
        self._load = ObjectDeserializer(self)

    def externalUrlFns(self, urlForExternal, objForUrl):
        self._save.urlForExternal = urlForExternal
        self._load.resolveExternalUrl = objForUrl

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def getMetadata(self):
        """returns a copy of the metadata"""
        return self.stg.getMetadata()
    meta = property(getMetadata) 

    def getMetaAttr(self, attr, default=None):
        return self.stg.getMetaAttr(attr, default)
    def setMetaAttr(self, attr, value):
        return self.stg.setMetaAttr(attr, value)
    def delMetaAttr(self, attr):
        return self.stg.delMetaAttr(attr)

    def commit(self): 
        self.oidToObj.commit()
        return self._save.commit()
    def gc(self): 
        return self.stg.gc()
    def gcFull(self): 
        return self.stg.gcFull()
    def gcCollect(self): 
        return self.stg.gcCollect()
    def allURLPaths(self):
        return [url for url,oid in self.stg.allURLPaths()]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def __getitem__(self, key):
        return self.load(key)
    def __setitem__(self, key, obj):
        return self.store(obj, key)
    def __delitem__(self, key, obj):
        return self.remove(obj)

    def store(self, obj, urlpath=None):
        return self._save.store(obj, urlpath)
    def remove(self, obj):
        return self._save.remove(obj)
    def storeAll(self, iter, named=None):
        return self._save.storeAll(iter, named)
    def load(self, oid, depth=1):
        return self._load.loadOid(oid, depth)

    def clearCaches(self):
        self.oidToObj.clear()

    def close(self):
        self.clearCaches()
        self.commit()

        self._load.close()
        self._save.close()

        self.stg.close()
        self.db.close()

        del self._load
        del self._save
        del self.stg
        del self.db

