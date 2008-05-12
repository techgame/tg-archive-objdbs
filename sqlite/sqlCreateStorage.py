createLookupTables = """
create table if not exists oid_lookup (
    oid integer,
    stg_kind text not null,
    otype text not null,

    primary key (oid) on conflict replace
);
"""

createStorageTables = """
create table if not exists literals (
    oid integer,
    value,
    value_hash integer,
    value_type text,

    primary key (oid) on conflict replace
);

create table if not exists weakrefs (
    oid_host integer,
    oid_ref integer,

    primary key (oid_host) on conflict replace
);

create table if not exists lists (
    tidx integer primary key,
    oid_host integer,
    oid_value integer
);

create table if not exists mappings (
    tidx integer primary key,
    oid_host integer,
    oid_key integer,
    oid_value integer
);
"""

# Cross database concerns 
createExternalTables = """
create table if not exists externals (
    oid integer,
    url TEXT,

    primary key (oid) on conflict replace
);

create table if not exists exports (
    urlpath TEXT,
    oid_ref integer,

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

    from lists
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
        oid, stg_kind, otype

    from exports as tbl
    join oid_lookup
        on oid = tbl.oid_ref;
"""

# Views for determining referenced objects - does not handle self-refs
createOidReferenceViews = """
create view if not exists oid_references as 
    select oid_value as oid from lists 
  union 
    select oid_key as oid from mappings 
  union
    select oid_value as oid from mappings 
  union 
    select oid_ref as oid from exports 
  sort on oid;

create view if not exists oid_unreferenced as 
    select oid from oid_lookup
        where oid >= 1000
        except select oid from oid_references;
"""

