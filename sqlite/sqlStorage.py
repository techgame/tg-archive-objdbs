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
from . import sqlCreateStorage

deleteGarbage = sqlCreateStorage.deleteGarbage

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class SQLStorage(object):
    nextOid = None
    _sql_init = [
        'sqliteSetup',
        'createMetaTables',
        'createLookupTables',
        'createStorageTables',
        'createExternalTables',
        'createLookupViews',
        'createOidReferenceViews',
        'createReachabilityTable',
        ]

    def __init__(self, filename, dbid=None):
        filename = os.path.abspath(filename)
        self.dbFilename = filename
        db = sqlite3.connect(filename)
        db.isolation_level = "DEFERRED"

        self.db = db
        self._cursor = db.cursor()
        self.initialize()

        if self.dbid is None:
            self.dbid = dbid or filename 

    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def close(self):
        self._cursor = None
        self.db.close()
        self.db = None

    def initialize(self):
        writeOps = 0
        cursor = self.readCursor
        for attrName in self._sql_init:
            sqlOps = getattr(sqlCreateStorage, attrName)
            for sql in sqlOps:
                if isinstance(sql, tuple):
                    sqlGuard, sql = sql

                    try: cursor.executescript(sqlGuard)
                    except sqlite3.OperationalError, e: pass
                    else: continue

                    try: 
                        cursor.executescript(sql)
                        writeOps += 1
                    except sqlite3.OperationalError, e:
                        print >> sys.stderr, "Error while executing creation script: %r on db: %s" % (attrName, self.dbFilename)
                        raise
                else:
                    try: cursor.executescript(sql)
                    except sqlite3.OperationalError, e:
                        print >> sys.stderr, "Error while executing initialization script: %r on db: %s" % (attrName, self.dbFilename)
                        raise

        self.fetchMetadata()
        self.nextOid = self.getMetaAttr('nextOid', 1000)
        if writeOps:
            self.newSession(cursor)

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
            print 'writable session:', (session, self.dbFilename)
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
            'select oid from oid_lookup')
        return [e[0] for e in r.fetchall()]

    def allOidInfo(self):
        r = self.readCursor.execute(
            'select * from oid_lookup')
        return r.fetchall()

    def getOidInfo(self, oid):
        r = self.readCursor.execute(
            'select stg_kind, otype '
            '  from oid_lookup where oid=?', (oid,))
        return r.fetchone()

    def setOid(self, oid, stg_kind, otype):
        if oid is None:
            oid = self.nextOid
            self.nextOid = oid+1

        if not isinstance(oid, int): 
            raise ValueError("Object oid must be specified")
        if not isinstance(stg_kind, str): 
            raise ValueError("Object storage stg_kind must be specified")

        r = self.writeCursor
        r.execute(
            'replace into oid_lookup (oid, stg_kind, otype, ssid) '
            '  values(?, ?, ?, ?)', (oid, stg_kind, otype, self.ssid))
        return oid

    def removeOid(self, oid):
        r = self.writeCursor
        r.execute(
            'delete from oid_lookup where oid=?', (oid,))
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
            '  where value=? and value_hash=? and value_type=?',
            (value, value_hash, value_type))
        r = r.fetchone()
        if r is not None:
            return r[0]

    def getLiteralAndType(self, oid):
        r = self.readCursor.execute(
            'select value, value_type '
            '  from literals where oid=?', (oid,))
        return r.fetchone()

    def getLiteral(self, oid):
        r = self.readCursor.execute(
            'select value from literals ' 
            '  where oid=?', (oid,))
        r = r.fetchone()
        if r is not None:
            return r[0]
    def setLiteral(self, value, value_hash, value_type, stg_kind):
        oid = self.findLiteral(value, value_hash, value_type)
        if oid is not None:
            return oid

        r = self.writeCursor
        oid = self.setOid(None, stg_kind, value_type)
        r.execute(
            'insert into literals (oid, value, value_type, value_hash, ssid)'
            '  values(?, ?, ?, ?, ?)', (oid, value, value_type, value_hash, self.ssid))
        return oid

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
        r = self.writeCursor
        if not r: return
        r.execute('''
            delete from oidGraphMembers;''')
        r.execute('''
            insert into oidGraphMembers 
                select oid_ref from exports;''')

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
        d = 0
        r = r.execute('''
            insert into oidGraphMembers
                select oid_key from mappings
                    where oid_host in oidGraphMembers
                        and oid_key not in oidGraphMembers;''')
        d += r.rowcount

        r = r.execute('''
            insert into oidGraphMembers
                select oid_value from mappings
                    where oid_host in oidGraphMembers 
                        and oid_value not in oidGraphMembers;''')
        d += r.rowcount
        return d

    def gcReap(self, r):
        self.db.commit()
        count, = r.execute('''select count(oid) from oidGraphMembers;''').fetchone()
        exports, = r.execute('''select count(oid_ref) from exports;''').fetchone()

        nCollected = 0
        if count > exports:
            r = r.execute('delete from oid_lookup where oid not in oidGraphMembers')
            nCollected = max(0, r.rowcount)
            if nCollected: 
                r.executescript(deleteGarbage)
                self.db.commit()

        self.gcRestart()
        return nCollected, count

