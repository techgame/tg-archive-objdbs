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

import os, sys
import uuid
import sqlite3
from . import sqlScripts as sql

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class SQLStorage(object):
    nextOid = None
    _sql_init = sql.initScripts

    def __init__(self, filename, dbid=None):
        filename = os.path.abspath(filename)
        self.dbFilename = filename
        db = sqlite3.connect(filename)
        db.isolation_level = "DEFERRED"

        db.text_factory = str

        self.db = db
        self._cursor = db.cursor()
        self.initialize()

        if self.dbid is None:
            if dbid is None:
                dbid = str(uuid.uuid4())
            self.dbid = dbid

    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def close(self):
        self._cursor = None
        self.db.close()
        self.db = None

    def initialize(self):
        exCur = sql.runScripts(self.readCursor, self._sql_init)

        self.fetchMetadata()
        self.nextOid = self.getMetaAttr('nextOid', 1000)
        if exCur.writeOps:
            self.newSession(self._cursor)

    def fetchMetadata(self):
        self._metadata = dict()
        r = self.readCursor.execute('select attr, value from odb_metadata')
        self._metadata = dict(r.fetchall())

    def getMetadata(self):
        return self._metadata.copy()
    def getMetaAttr(self, attr, default=None):
        return self._metadata.get(attr, default)
    def setMetaAttr(self, attr, value):
        r = self._metadata
        if r.get(attr, object()) == value:
            return False

        r[attr] = value
        r = self.writeCursor
        r.execute(
            'replace into odb_metadata '
            '  (attr, value) values (?, ?)', 
            (attr, value))
        return True
    def delMetaAttr(self, attr):
        r = self.writeCursor
        r.execute(
            'delete from odb_metadata '
            '  where attr=?', (attr,))
        return r.rowcount > 0

    def getDbid(self):
        return self.getMetaAttr('dbid')
    def setDbid(self, dbid):
        return self.setMetaAttr('dbid', dbid)
    dbid = property(getDbid, setDbid)

    def getWritable(self):
        return self.getMetaAttr('writable', True)
    def setWritable(self, writable=True):
        return self.setMetaAttr('writable', writable)
    writable = property(getWritable, setWritable)

    session = None
    def newSession(self, writeCursor):
        session = self.session
        if session is None and self.writable:
            session = uuid.uuid4() # new random uuid
            self.session = session
            r = writeCursor.execute(
                'insert into odb_sessions values (NULL, ?, ?)',
                (str(session), self.nextOid))
            self.ssid = r.lastrowid
            self.commit()
        return session

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def getReadCursor(self):
        r = self._cursor
        return r
    readCursor = property(getReadCursor)

    def getWriteCursor(self):
        r = self._cursor
        if self.session is None:
            if not self.newSession(r):
                r = None
        return r
    writeCursor = property(getWriteCursor)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def commit(self):
        self.setMetaAttr('nextOid', self.nextOid)
        self.db.commit()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def allOids(self):
        r = self.readCursor.execute(
            'select oid from oid_lookup_raw')
        return [e[0] for e in r.fetchall()]

    def allOidInfo(self):
        r = self.readCursor.execute(
            'select oid, stg_kind, otype from oid_lookup_view')
        return r.fetchall()

    def getOidInfo(self, oid):
        r = self.readCursor.execute(
            'select stg_kind, otype '
            '  from oid_lookup_view where oid=?', (oid,))
        return r.fetchone()

    def setOid(self, oid, stg_kind, otype):
        if oid is None:
            oid = self.nextOid
            self.nextOid = oid+1

        if not isinstance(oid, int): 
            raise ValueError("Object oid must be specified")
        if not isinstance(stg_kind, str): 
            raise ValueError("Object storage stg_kind must be specified")

        id_stg_kind = self._stgKindKeyFor(stg_kind)
        id_otype = self._otypeKeyFor(otype)

        r = self.writeCursor
        r.execute(
            'replace into oid_lookup_raw (oid, id_stg_kind, id_otype, ssid) '
            '  values(?, ?, ?, ?)', (oid, id_stg_kind, id_otype, self.ssid))
        return oid

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    _stgKindMap = None
    def getStgKindMap(self):
        stgKindMap = self._stgKindMap
        if stgKindMap is None:
            ex = self.readCursor.execute
            stgKindMap = dict(ex('select stg_kind, id_stg_kind from stg_kind_lookup'))
            self._stgKindMap = stgKindMap
        return stgKindMap
    stgKindMap = property(getStgKindMap)

    def _stgKindKeyFor(self, stg_kind):
        id_stg_kind = self.stgKindMap.get(stg_kind)
        if id_stg_kind is None:
            w = self.writeCursor
            w.execute('insert into stg_kind_lookup values (NULL, ?)', (stg_kind,))
            id_stg_kind = w.lastrowid
            self.stgKindMap[stg_kind] = id_stg_kind
        return id_stg_kind

    _otypeMap = None
    def getOtypeMap(self):
        otypeMap = self._otypeMap
        if otypeMap is None:
            ex = self.readCursor.execute
            otypeMap = dict(ex('select otype, id_otype from otype_lookup'))
            self._otypeMap = otypeMap
        return otypeMap
    otypeMap = property(getOtypeMap)

    def _otypeKeyFor(self, otype):
        id_otype = self.otypeMap.get(otype)
        if id_otype is None:
            w = self.writeCursor
            w.execute('insert into otype_lookup values (NULL, ?)', (otype,))
            id_otype = w.lastrowid
            self.otypeMap[otype] = id_otype
        return id_otype

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def removeOid(self, oid):
        r = self.writeCursor
        r.execute(
            'delete from oid_lookup_raw where oid=?', (oid,))
        r.execute(
            'delete from exports where oid_ref=?', (oid,))
        r.execute(
            'delete from mappings where oid_host=?', (oid,))

    def allURLPaths(self, incOid=True):
        if incOid:
            r = self.readCursor.execute(
                "select urlpath, oid_ref from exports")
            return r.fetchall()
        else:
            r = self.readCursor.execute(
                "select urlpath from exports")
            return [e[0] for e in r.fetchall()]

    def getAtURLPath(self, urlpath):
        r = self.readCursor.execute(
            "select oid, stg_kind, otype from exports_lookup"
            "  where urlpath=?", (urlpath,))
        return r.fetchone()

    def setURLPathForOid(self, urlpath, oid):
        if not urlpath: 
            return

        r = self.writeCursor
        r.execute(
            "replace into exports (urlpath, oid_ref, ssid)"
            "  values(?,?,?)", (urlpath, oid, self.ssid))
        r.execute(
            """insert into oidGraphMembers values (?)""", (oid,))

    def findLiteral(self, value, value_hash, value_type):
        r = self.readCursor.execute(
            'select oid from literals '
            '  where value_hash=? and value_type=?',
            (value_hash, value_type))
        r = r.fetchone()
        if r is not None:
            return r[0]

    def getLiteralAndType(self, oid):
        r = self.readCursor.execute(
            'select value, value_type '
            '  from literals where oid=?', (oid,))
        return self.decodeLiteralEntry(r.fetchone())

    def getLiteral(self, oid):
        r = self.readCursor.execute(
            'select value, value_type from literals ' 
            '  where oid=?', (oid,))
        return self.decodeLiteralEntry(r.fetchone())

    def setLiteral(self, value, value_hash, value_type, stg_kind):
        oid = self.findLiteral(value, value_hash, value_type)
        if oid is not None:
            return oid

        value = self.encodeLiteral(value, value_type)

        r = self.writeCursor
        oid = self.setOid(None, stg_kind, value_type)
        r.execute(
            'insert into literals (oid, value, value_type, value_hash, ssid)'
            '  values(?, ?, ?, ?, ?)', (oid, value, value_type, value_hash, self.ssid))
        return oid

    def encodeLiteral(self, value, value_type):
        if value_type == 'unicode':
            value = value.encode('utf-8')
        elif value_type == 'str':
            if '\x00' in value:
                value = buffer(value)
        return value
    def decodeLiteralEntry(self, entry):
        if entry is not None:
            return self.decodeLiteral(entry[0], entry[1])
    def decodeLiteral(self, value, value_type):
        if value_type == 'unicode':
            value = value.decode('utf-8')
        elif value_type == 'str':
            value = str(value)
        return value

    def getExternal(self, oid):
        r = self.readCursor.execute(
            'select url from externals '
            '  where oid=?', (oid,))
        r = r.fetchone()
        if r is not None:
            return r[0]
    def setExternal(self, oid, url):
        r = self.writeCursor
        r.execute(
            'insert into externals (oid, url, ssid)'
            '  values(?, ?, ?)', (oid, url, self.ssid))
        return oid

    def getWeakref(self, oid):
        r = self.readCursor.execute(
            'select v_oid, v_stg_kind, v_otype from weakrefs_lookup '
            '  where oid=?', (oid,))
        return r.fetchone()
    def setWeakref(self, oid, oid_ref):
        r = self.writeCursor
        r.execute(
            'insert into weakrefs (oid_host, oid_ref, ssid)'
            '  values(?, ?, ?)', (oid, oid_ref, self.ssid))
        return oid

    def getOrdered(self, oid):
        r = self.readCursor.execute(
            'select '
            '    v_oid, v_stg_kind, v_otype '
            '  from lists_lookup where oid_host=?', (oid,))
        return r.fetchall()
    def setOrdered(self, oid, valueOids):
        r = self.writeCursor
        r.execute(
            'delete from mappings '
            '  where oid_host=?', (oid,))

        ssid = self.ssid
        r.executemany(
            'insert into mappings values(NULL, ?, NULL, ?, ?)',
            ((oid, oid_v, ssid) for oid_v in valueOids))
        return oid

    def getMapping(self, oid):
        r = self.readCursor.execute(
            'select '
            '    k_oid, k_stg_kind, k_otype, '
            '    v_oid, v_stg_kind, v_otype '
            '  from mappings_lookup where oid_host=?', (oid,))
        return [(e[:3], e[3:]) for e in r.fetchall()]
    def setMapping(self, oid, itemOids):
        r = self.writeCursor
        r.execute(
            'delete from mappings '
            '  where oid_host=?', (oid,))

        ssid = self.ssid
        r.executemany(
            'insert into mappings values(NULL, ?, ?, ?, ?)',
            ((oid, oid_k, oid_v, ssid) for oid_k, oid_v in itemOids))
        return oid

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #~ Garbage collection
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def gcInit(self):
        self.gcRestart()

    def gcRestart(self):
        sql.gcRestart(self.writeCursor)

    def gc(self, reap=True):
        r = self.writeCursor
        if not r: return
        delta = self.gcIter(r)
        if not delta and reap:
            return self.gcReap(r)

    def gcFlush(self):
        l = 0
        r = None
        while r is None:
            r = self.gc()
            l += 1
        return r

    def gcCollect(self):
        self.gcRestart()
        return self.gcFlush()

    def gcIter(self, r):
        return sql.gcIter(r)

    def gcReap(self, r):
        self.db.commit()
        count, = r.execute('''select count(oid) from oidGraphMembers;''').fetchone()
        exports, = r.execute('''select count(oid_ref) from exports;''').fetchone()

        nCollected = 0
        if count > exports:
            r = r.execute('delete from oid_lookup_raw where oid not in oidGraphMembers')
            nCollected = max(0, r.rowcount)
            if nCollected: 
                sql.deleteGarbage(r)
                self.db.commit()

        self.gcRestart()
        return nCollected, count

