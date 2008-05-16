sqliteSetup = """
PRAGMA locking_mode = EXCLUSIVE;
PRAGMA synchronous = NORMAL;
PRAGMA encoding = "UTF-8"; 
"""

createMetaTables = """
create table if not exists odb_metadata (
    attr TEXT,
    value,
    primary key (attr) on conflict replace
);

create table if not exists odb_sessions (
    ssid integer primary key,
    session TEXT,
    nextOid integer
);
"""

createLookupTables = """
create table if not exists oid_lookup (
    oid integer,
    stg_kind text not null,
    otype text not null,

    ssid integer,
    primary key (oid) on conflict replace
);
"""

createStorageTables = """
create table if not exists literals (
    oid integer,
    value,
    value_hash integer,
    value_type text,

    ssid integer,

    primary key (oid) on conflict replace
);

create table if not exists weakrefs (
    oid_host integer,
    oid_ref integer,

    ssid integer,
    primary key (oid_host) on conflict replace
);

create table if not exists mappings (
    tidx integer primary key,
    oid_host integer,
    oid_key integer,
    oid_value integer,
    ssid integer
);
create index if not exists mappings_oid_host
    on mappings (oid_host);
"""

# Cross database concerns 
createExternalTables = """
create table if not exists externals (
    oid integer,
    url TEXT,

    ssid integer,

    primary key (oid) on conflict replace
);

create table if not exists exports (
    urlpath TEXT,
    oid_ref integer,

    ssid integer,

    primary key (urlpath) on conflict replace
);
"""

# views for referencing through lists, mappings, and weakrefs to the oid_lookup table
createLookupViews = """
create view if not exists lists_lookup as
    select 
        oid_host,
        v.oid as v_oid, 
        v.stg_kind as v_stg_kind,
        v.otype as v_otype

    from mappings
    join oid_lookup as v
        on v.oid = oid_value;

create view if not exists mappings_lookup as
    select 
        oid_host,

        k.oid as k_oid, 
        k.stg_kind as k_stg_kind,
        k.otype as k_otype,

        v.oid as v_oid, 
        v.stg_kind as v_stg_kind,
        v.otype as v_otype

    from mappings
    join oid_lookup as k
        on k.oid = oid_key

    join oid_lookup as v
        on v.oid = oid_value;

create view if not exists weakrefs_lookup as
    select 
        oid_host,

        v.oid as v_oid, 
        v.stg_kind as v_stg_kind,
        v.otype as v_otype

    from weakrefs
    join oid_lookup as v
        on v.oid = oid_ref;

create view if not exists exports_lookup as
    select 
        urlpath, oid, stg_kind, otype

    from exports as tbl
    join oid_lookup
        on oid = tbl.oid_ref;
"""

# Views for determining referenced objects - does not handle self-refs
createOidReferenceViews = """
create view if not exists oids as
  select oid from oid_lookup;
"""

createReachabilityTable = """
create temp table if not exists oidGraphMembers (
    oid integer,
    primary key (oid) on conflict replace
);
"""

deleteGarbage = """
delete from literals where oid not in oidGraphMembers;
delete from weakrefs where oid_host not in oidGraphMembers;
delete from mappings where oid_host not in oidGraphMembers;
delete from externals where oid not in oidGraphMembers;
delete from oidGraphMembers;
"""

