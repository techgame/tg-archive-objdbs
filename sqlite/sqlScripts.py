#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Imports 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import sqlite3

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~ Definitions 
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

initScripts = []

def register(lst):
    def addFn(fn):
        lst.append(fn)
        return fn
    return addFn

class ExCursor(object):
    writeOps = 0
    def __init__(self, cur):
        self.cur = cur

    def test(self, sql):
        try:
            self.cur.executescript(sql)
        except sqlite3.OperationalError, e: 
            return False
        else: 
            return True

    def run(self, sql, isWrite=True):
        if sql:
            self.cur.executescript(sql)
            if isWrite:
                self.writeOps += 1

    def runIfElse(self, sqlIf, sqlThen, sqlElse):
        r = self.test(sqlIf)
        if r: 
            self.run(sqlThen)
        else: 
            self.run(sqlElse)
        return r
    def runIf(self, sqlIf, sqlThen):
        runIfElse(sqlIf, sqlThen, None)
    def runIfNot(self, sqlIf, sqlElse):
        return self.runIfElse(sqlIf, None, sqlElse)
    def runIfNotSWH(self, sqlIf, sqlElse):
        print
        print "**"*20, "SWH"
        print sqlIf
        self.run(sqlIf)
        print
        return self.runIfElse(sqlIf, None, sqlElse)

    def reduce(self, lst):
        for fn in lst:
            fn(self)
        return self

def runScripts(cur, lst):
    return ExCursor(cur).reduce(lst)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@register(initScripts)
def sqliteSetup(ex):
    ex.run("""
        PRAGMA locking_mode = EXCLUSIVE;
        PRAGMA synchronous = NORMAL;
        PRAGMA encoding = "UTF-8"; 
        """)

@register(initScripts)
def createMetaTables(ex):
    ex.runIfNot("select * from odb_metadata limit(1);", """
            create table if not exists odb_metadata (
                attr TEXT,
                value,
                primary key (attr) on conflict replace
            );""")
    ex.runIfNot("select * from odb_sessions limit(1);", """
        create table if not exists odb_sessions (
            ssid integer primary key,
            session TEXT,
            nextOid integer
        ); """)

@register(initScripts)
def createLookupTables(ex):
    ex.runIfNot("select * from oid_lookup_raw limit(1);", """
        create table if not exists oid_lookup_raw (
            oid integer,
            id_stg_kind integer,
            id_otype integer,

            ssid integer,
            primary key (oid) on conflict replace
        ); """)
    ex.runIfNot("select * from stg_kind_lookup limit(1);", '''
        create table stg_kind_lookup (
            id_stg_kind integer,
            stg_kind text unique on conflict ignore,

            primary key (id_stg_kind) on conflict ignore);
        ''')
    ex.runIfNot("select * from otype_lookup limit(1);", '''
        create table otype_lookup (
            id_otype integer,
            otype text unique on conflict ignore,

            primary key (id_otype) on conflict ignore);
        ''')
    ex.runIfNot("select * from oid_lookup_view limit(1);", '''
        create view oid_lookup_view as 
            select
                src.oid as oid,
                sl.stg_kind as stg_kind,
                ol.otype as otype,
                src.ssid as ssid

            from oid_lookup_raw as src
                join stg_kind_lookup as sl
                    on src.id_stg_kind = sl.id_stg_kind
                join otype_lookup as ol
                    on src.id_otype = ol.id_otype;
        ''')


    if ex.test("select * from oid_lookup limit(1);"):
        # we need to update this database to the new scheme
        ex.run('''
            insert into stg_kind_lookup (stg_kind)
                select distinct stg_kind as stg_kind from oid_lookup;''')
        ex.run('''
            insert into otype_lookup (otype)
                select distinct otype as otype from oid_lookup; ''')
        ex.run('''
            insert into oid_lookup_raw
                (oid, id_stg_kind, id_otype, ssid)

                select oid, sl.id_stg_kind as id_stg_kind, ol.id_otype as id_otype, ssid
                    from oid_lookup as src
                    join stg_kind_lookup as sl
                        on sl.stg_kind = src.stg_kind
                    join otype_lookup as ol
                        on ol.otype = src.otype;
                ''')
        ex.run('''
            drop table oid_lookup;
            drop view lists_lookup;
            drop view mappings_lookup;
            drop view weakrefs_lookup;
            drop view exports_lookup;
            drop view oids;
            ''')


@register(initScripts)
def createStorageTables(ex):
    ex.runIfNot("select * from literals limit(1);", """
        create table if not exists literals (
            oid integer,
            value,
            value_hash integer,
            value_type text,

            ssid integer,

            primary key (oid) on conflict replace
        );""")
    ex.runIfNot("select * from weakrefs limit(1);", """
        create table if not exists weakrefs (
            oid_host integer,
            oid_ref integer,

            ssid integer,
            primary key (oid_host) on conflict replace
        );
        """) 
    ex.runIfNot("select * from mappings limit(1);", """
        create table if not exists mappings (
            tidx integer primary key,
            oid_host integer,
            oid_key integer,
            oid_value integer,
            ssid integer
        );
        create index if not exists mappings_oid_host
            on mappings (oid_host);
        """)

# Cross database concerns 
@register(initScripts)
def createExternalTables(ex):
    ex.runIfNot("select * from externals limit(1);", """
        create table if not exists externals (
            oid integer,
            url TEXT,

            ssid integer,

            primary key (oid) on conflict replace
        );""")
    ex.runIfNot("select * from exports limit(1);", """
        create table if not exists exports (
            urlpath TEXT,
            oid_ref integer,

            ssid integer,

            primary key (urlpath) on conflict replace
        );""")

# views for referencing through lists, mappings, and weakrefs to the oid_lookup_raw table
@register(initScripts)
def createLookupViews(ex):
    ex.runIfNot("select * from lists_lookup limit(1);", """
        create view lists_lookup as
            select 
                oid_host,
                v.oid as v_oid, 
                v.stg_kind as v_stg_kind,
                v.otype as v_otype

            from mappings
            join oid_lookup_view as v
                on v.oid = oid_value;
        """)

    ex.runIfNot("select * from mappings_lookup limit(1);", """
        create view mappings_lookup as
            select 
                oid_host,

                k.oid as k_oid, 
                k.stg_kind as k_stg_kind,
                k.otype as k_otype,

                v.oid as v_oid, 
                v.stg_kind as v_stg_kind,
                v.otype as v_otype

            from mappings
            join oid_lookup_view as k
                on k.oid = oid_key

            join oid_lookup_view as v
                on v.oid = oid_value;
        """) 

    ex.runIfNot("select * from weakrefs_lookup limit(1);", """
        create view weakrefs_lookup as
            select 
                oid_host,

                v.oid as v_oid, 
                v.stg_kind as v_stg_kind,
                v.otype as v_otype

            from weakrefs
            join oid_lookup_view as v
                on v.oid = oid_ref;
        """) 

    ex.runIfNot("select * from exports_lookup limit(1);", """
        create view exports_lookup as
            select 
                urlpath, oid, stg_kind, otype

            from exports as tbl
            join oid_lookup_view
                on oid = tbl.oid_ref;
        """)

# Views for determining referenced objects - does not handle self-refs
@register(initScripts)
def createOidReferenceViews(ex):
    ex.runIfNot("select * from oids limit(1);", """
        create view oids as
            select oid from oid_lookup_raw;""")

@register(initScripts)
def createReachabilityTable(ex):
    ex.run("""
        create temp table if not exists oidGraphMembers (
            oid integer,
            primary key (oid) on conflict replace
        ); """)

def gcRestart(cur):
    if not cur: return False
    cur.execute('''
        delete from oidGraphMembers;''')
    cur.execute('''
        insert into oidGraphMembers 
            select oid_ref from exports;''')
    return True

def gcIter(cur):
    d = 0
    if not cur: return d
    cur = cur.execute('''
        insert into oidGraphMembers
            select oid_key from mappings
                where oid_host in oidGraphMembers
                    and oid_key not in oidGraphMembers;''')
    d += r.rowcount

    cur = cur.execute('''
        insert into oidGraphMembers
            select oid_value from mappings
                where oid_host in oidGraphMembers 
                    and oid_value not in oidGraphMembers;''')
    d += r.rowcount
    return d

def deleteGarbage(cur):
    if not cur: return
    cur.executescript( """
        delete from literals where oid not in oidGraphMembers;
        delete from weakrefs where oid_host not in oidGraphMembers;
        delete from mappings where oid_host not in oidGraphMembers;
        delete from externals where oid not in oidGraphMembers;
        delete from exports where oid_ref not in oids;
        """)

