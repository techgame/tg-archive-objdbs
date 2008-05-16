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

import uuid
from . import sqlCreateStorage as _sql

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class SQLStorage(object):
    nextOid = None
    _sql_init = [
        _sql.sqliteSetup,
        _sql.createMetaTables,
        _sql.createLookupTables,
        _sql.createStorageTables,
        _sql.createExternalTables,
        _sql.createLookupViews,
        _sql.createOidReferenceViews,
        _sql.createReachabilityTable,
        ]

    def __init__(self, db):
        self.db = db
        self.cursor = db.cursor()
        self.initialize()

    def __getstate__(self):
        raise RuntimeError("Tried to store storage mechanism: %r" % (self,))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def initialize(self):
        for sql in self._sql_init:
            self.cursor.executescript(sql)

        self.fetchMetadata()
        self.nextOid = self.getMetaAttr('nextOid', 1000)
        self.newSession()
        self.gcInit()

    def fetchMetadata(self):
        r = self.cursor.execute('select attr, value from odb_metadata')
        self._metadata = dict(r.fetchall())

    def getMetaAttr(self, attr, default=None):
        return self._metadata.get(attr, default)
    def setMetaAttr(self, attr, value):
        r = self._metadata
        if r.get(attr, object()) != value:
            r[attr] = value
            self.cursor.execute(
                'replace into odb_metadata '
                '  (attr, value) values (?, ?)', 
                (attr, value))

    def getDbid(self):
        return self.getMetaAttr('dbid')
    def setDbid(self, dbid):
        return self.setMetaAttr('dbid', dbid)
    dbid = property(getDbid, setDbid)

    def newSession(self):
        self.commit()

        self.session = uuid.uuid4() # new random uuid
        r = self.cursor.execute(
            'insert into odb_sessions values (NULL, ?, ?)',
            (str(self.session), self.nextOid))
        self.ssid = r.lastrowid
        self.commit()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def commit(self):
        self.setMetaAttr('nextOid', self.nextOid)
        self.db.commit()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def allOids(self):
        r = self.cursor.execute(
            'select oid from oid_lookup')
        return [e[0] for e in r.fetchall()]

    def allOidInfo(self):
        r = self.cursor.execute(
            'select * from oid_lookup')
        return r.fetchall()

    def getOidInfo(self, oid):
        r = self.cursor.execute(
            'select stg_kind, otype '
            '  from oid_lookup where oid=?', (oid,))
        return r.fetchone()

    def setOid(self, obj, oid, stg_kind, otype):
        if oid is None:
            oid = self.nextOid
            self.nextOid = oid+1

        if not isinstance(oid, int): 
            raise ValueError("Object oid must be specified")
        if not isinstance(stg_kind, str): 
            raise ValueError("Object storage stg_kind must be specified")

        self.cursor.execute(
            'replace into oid_lookup (oid, stg_kind, otype, ssid) '
            '  values(?, ?, ?, ?)', (oid, stg_kind, otype, self.ssid))
        return oid

    def allURLPaths(self, incOid=True):
        if incOid:
            r = self.cursor.execute(
                "select urlpath, oid_ref from exports")
            return r.fetchall()
        else:
            r = self.cursor.execute(
                "select urlpath from exports")
            return [e[0] for e in r.fetchall()]

    def getAtURLPath(self, urlpath):
        r = self.cursor.execute(
            "select oid, stg_kind, otype from exports_lookup"
            "  where urlpath=?", (urlpath,))
        return r.fetchone()

    def setURLPathForOid(self, urlpath, oid):
        r = self.cursor
        r.execute(
            "replace into exports (urlpath, oid_ref, ssid)"
            "  values(?,?,?)", (urlpath, oid, self.ssid))
        r.execute(
            """insert into oidGraphMembers values (?)""", (oid,))

    def findLiteral(self, value, value_hash, value_type):
        r = self.cursor.execute(
            'select oid from literals '
            '  where value=? and value_hash=? and value_type=?',
            (value, value_hash, value_type))
        r = r.fetchone()
        if r is not None:
            return r[0]

    def getLiteralAndType(self, oid):
        r = self.cursor.execute(
            'select value, value_type '
            '  from literals where oid=?', (oid,))
        return r.fetchone()

    def getLiteral(self, oid):
        r = self.cursor.execute(
            'select value from literals ' 
            '  where oid=?', (oid,))
        r = r.fetchone()
        if r is not None:
            return r[0]
    def setLiteral(self, value, value_hash, value_type, stg_kind):
        oid = self.findLiteral(value, value_hash, value_type)
        if oid is not None:
            return oid

        oid = self.setOid(value, None, stg_kind, value_type)
        self.cursor.execute(
            'insert into literals (oid, value, value_type, value_hash, ssid)'
            '  values(?, ?, ?, ?, ?)', (oid, value, value_type, value_hash, self.ssid))
        return oid

    def getWeakref(self, oid):
        r = self.cursor.execute(
            'select v_oid, v_stg_kind, v_otype from weakrefs_lookup '
            '  where oid=?', (oid,))
        return r.fetchone()
    def setWeakref(self, oid, oid_ref):
        self.cursor.execute(
            'insert into weakrefs (oid_host, oid_ref, ssid)'
            '  values(?, ?, ?)', (oid, oid_ref, self.ssid))
        return oid

    def getOrdered(self, oid):
        r = self.cursor.execute(
            'select '
            '    v_oid, v_stg_kind, v_otype '
            '  from lists_lookup where oid_host=?', (oid,))
        return r.fetchall()
    def setOrdered(self, oid, valueOids):
        r = self.cursor
        r.execute(
            'delete from mappings '
            '  where oid_host=?', (oid,))

        ssid = self.ssid
        r.executemany(
            'insert into mappings values(NULL, ?, NULL, ?, ?)',
            ((oid, oid_v, ssid) for oid_v in valueOids))
        return oid

    def getMapping(self, oid):
        r = self.cursor.execute(
            'select '
            '    k_oid, k_stg_kind, k_otype, '
            '    v_oid, v_stg_kind, v_otype '
            '  from mappings_lookup where oid_host=?', (oid,))
        return [(e[:3], e[3:]) for e in r.fetchall()]
    def setMapping(self, oid, itemOids):
        r = self.cursor
        r.execute(
            'delete from mappings '
            '  where oid_host=?', (oid,))

        ssid = self.ssid
        r.executemany(
            'insert into mappings values(NULL, ?, ?, ?, ?)',
            ((oid, oid_k, oid_v, ssid) for oid_k, oid_v in itemOids))
        return oid

    def gcInit(self):
        r = self.cursor
        self.gcRestart()

    def gcRestart(self):
        #print 'gcRestart:'
        r = self.cursor
        r.execute('''
            delete from oidGraphMembers;''')
        r.execute('''
            insert into oidGraphMembers 
                select oid_ref from exports;''')

    def gc(self):
        r = self.cursor
        delta = self.gcIter(r)
        if not delta:
            return self.gcReap(r)

    def gcFlush(self):
        l = 0
        r = None
        while r is None:
            r = self.gc()
            l += 1
        #print 'gcFlush loops:', l, 'removed:', n
        return r

    def gcCollect(self):
        self.gcRestart()
        return self.gcFlush()

    def gcIter(self, r):
        d = 0
        r.execute('''
            insert into oidGraphMembers
                select oid_key from mappings
                    where oid_host in oidGraphMembers
                        and oid_key not in oidGraphMembers;''')
        d += r.rowcount

        r.execute('''
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
        if count <= exports:
            self.gcRestart()
            return 0, count

        r.execute('delete from oid_lookup where oid not in oidGraphMembers')
        n = max(0, r.rowcount)
        if not n: 
            return 0, count

        r.executescript(_sql.deleteGarbage)
        self.db.commit()
        return n, count

    if 0:
        def gc_old(self):
            oidOut = self.oidReachability()
            if not oidOut:
                return

            r = self.cursor
            r.executemany(
                'delete from oid_lookup where oid=?',
                ((oid,) for oid in oidOut))
            r.executescript(_sql.deleteUnreferenced)

            self.db.commit()

        def oidReachability(self):
            entries = []
            r = self.cursor
            entries.extend(r.execute(
                'select 0, oid_ref from exports '))
            entries.extend(r.execute(
                'select oid_host, oid_key from mappings where oid_key!=NULL'))
            entries.extend(r.execute(
                'select oid_host, oid_value from mappings '))

            result = set(v for e in entries for v in e)
            hashtable = dict((oid, set()) for oid in result)
            for oh, ov in entries:
                hashtable[oh].add(ov)

            result.remove(0)
            working = hashtable[0]
            result -= working

            while working:
                oid = working.pop()
                level = hashtable.pop(oid, None)
                if level:
                    level &= result
                    working.update(level)
                    result -= level

            return result

