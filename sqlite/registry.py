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


class SQLObjectRegistry(object):
    def __init__(self, filename, dbid=None):
        self.dbid = dbid or filename
        self.objToOids = {}
        self.oidToObj = OidMapping()
        self._initFileStorage(filename)

    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    def _initFileStorage(self, filename):
        self.db = sqlite3.connect(filename)
        self.db.isolation_level = "DEFERRED"

        self.stg = SQLStorage(self.db)
        self._save = ObjectSerializer(self)
        self._load = ObjectDeserializer(self)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def commit(self): self.stg.commit()
    def gc(self): self.stg.gc()
    def gcFull(self): self.stg.gcFull()
    def gcCollect(self): self.stg.gcCollect()
    def allURLPaths(self):
        return self.stg.allURLPaths()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def store(self, obj, urlpath=None):
        return self._save.store(obj, urlpath)
    def load(self, oid, depth=1):
        return self._load.loadOid(oid, depth)

    def close(self):
        del self.objToOids
        del self.oidToObj

        self.stg.close()
        self.db.close()
        del self.stg
        del self.db

