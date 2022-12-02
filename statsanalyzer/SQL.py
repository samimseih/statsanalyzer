CAPTURE_VERSION = 1.1

pg_stat_database = """
select 
    '{}' capture_version, 
    current_database(), 
    pg_is_in_recovery() standby, 
    age(b.datfrozenxid) oldest_transaction_age, 
    * 
from pg_stat_database a, pg_database b 
where a.datid=b.oid
""".format(
    CAPTURE_VERSION
)

pg_stat_activity = """
select '{}' capture_version, wait_event, wait_event_type, datid, datname, query from pg_stat_activity where state='active' 
""".format(
    CAPTURE_VERSION
)

pg_stat_bgwriter = """
select '{}' capture_version,  * from pg_stat_bgwriter
""".format(
    CAPTURE_VERSION
)

pg_settings = """
select '{}' capture_version,  name,setting,context,category,short_desc from pg_settings
""".format(
    CAPTURE_VERSION
)

pg_stat_progress_vacuum = """
select '{}' capture_version,  b.schemaname,b.relname,a.* from pg_stat_progress_vacuum a, pg_stat_all_tables b where a.relid=b.relid ;
""".format(
    CAPTURE_VERSION
)

pg_stat_statements_common = """
				select '{}' capture_version,  * from 
				(select 
					b.usename username,
					a.userid,
					a.queryid,
					a.shared_blks_read, 
					a.shared_blks_hit,
					a.shared_blks_written,
					a.shared_blks_dirtied,
                    a.temp_blks_read,
                    a.temp_blks_written,
                    a.blk_read_time,
                    a.blk_write_time,
                    a.rows,
                    a.min_time,
                    a.max_time,
                    a.stddev_time,
					a.calls,
					a.total_time,
                    a.query
				from pg_stat_statements a , pg_user b
				where a.userid = b.usesysid
				and a.dbid = ( select oid from pg_database where datname = current_database() )
				) as pg_stat_statements where calls > 0
				""".format(
    CAPTURE_VERSION
)
pg_stat_statements_gte13 = """
                select '{}' capture_version,  * from
                (select
                    b.usename username,
                    a.userid,
                    a.queryid,
                    a.shared_blks_read,
                    a.shared_blks_hit,
                    a.shared_blks_written,
                    a.shared_blks_dirtied,
                    a.temp_blks_read,
                    a.temp_blks_written,
                    a.blk_read_time,
                    a.blk_write_time,
                    a.rows,
                    a.plans,
                    a.min_exec_time,
                    a.max_exec_time,
                    a.stddev_exec_time,
                    a.min_plan_time,
                    a.max_plan_time,
                    a.stddev_plan_time,
                    a.calls,
                    a.total_exec_time,
                    a.total_plan_time,
                    a.wal_records,
                    a.wal_fpi,
                    a.wal_bytes,
                    a.query
                from pg_stat_statements a , pg_user b
                where a.userid = b.usesysid
                and a.dbid = ( select oid from pg_database where datname = current_database() )
                ) as pg_stat_statements where calls > 0
                """.format(
    CAPTURE_VERSION
)
table_stats_common = """
				select '{}' capture_version, * from 
				(select 
					b.*,
					a.heap_blks_read,
					a.heap_blks_hit,
					a.idx_blks_read,
					a.idx_blks_hit,
					a.toast_blks_read,
					a.toast_blks_hit,
					a.tidx_blks_read,
					a.tidx_blks_hit
					from pg_statio_all_tables a, pg_stat_all_tables b 
					where a.relid = b.relid and a.schemaname = b.schemaname and a.relname = b.relname) as table_stats
				""".format(
    CAPTURE_VERSION
)
index_stats_common = """
					select  '{}' capture_version, * from
					(select 
					  d.conname,
					  b.schemaname,
                      b.relid,
                      b.indexrelid,
					  b.relname,
					  b.indexrelname,
					  b.idx_scan, 
					  b.idx_tup_read,
					  b.idx_tup_fetch,
					  a.idx_blks_read, 
					  a.idx_blks_hit, 
					  c.indisunique, 
					  c.indisprimary, 
					  c.indisvalid, 
					  c.indkey::text as indkey
					  from pg_statio_all_indexes a, pg_index c, pg_stat_all_indexes b full outer join pg_catalog.pg_constraint d on d.conindid=b.indexrelid 
					  where c.indrelid=a.relid 
					  and c.indexrelid=a.indexrelid 
					  and a.relid = b.relid 
					  and a.schemaname = b.schemaname 
					  and a.relname = b.relname 
					  and a.indexrelname = b.indexrelname 
					  and a.indexrelid=b.indexrelid) as index_stats
				  """.format(
    CAPTURE_VERSION
)


class APG:
    v10 = {
        "pg_stat_statements": {"sql": pg_stat_statements_common},
        "table_stats": {"sql": table_stats_common},
        "index_stats": {"sql": index_stats_common},
        "pg_stat_database": {"sql": pg_stat_database},
        "pg_stat_bgwriter": {"sql": pg_stat_bgwriter},
        "pg_stat_activity": {"sql": pg_stat_activity},
        "pg_stat_progress_vacuum": {"sql": pg_stat_progress_vacuum},
        "pg_settings": {"sql": pg_settings},
        "version": {
            "sql": "select aurora_version(), version(), '{}' capture_version".format(
                CAPTURE_VERSION
            )
        },
    }

    v11 = {
        "pg_stat_statements": {"sql": pg_stat_statements_common},
        "table_stats": {"sql": table_stats_common},
        "index_stats": {"sql": index_stats_common},
        "pg_stat_database": {"sql": pg_stat_database},
        "pg_stat_bgwriter": {"sql": pg_stat_bgwriter},
        "pg_stat_activity": {"sql": pg_stat_activity},
        "pg_stat_progress_vacuum": {"sql": pg_stat_progress_vacuum},
        "pg_settings": {"sql": pg_settings},
        "version": {
            "sql": "select aurora_version(), version(), '{}' capture_version".format(
                CAPTURE_VERSION
            )
        },
    }

    v12 = {
        "pg_stat_statements": {"sql": pg_stat_statements_common},
        "table_stats": {"sql": table_stats_common},
        "index_stats": {"sql": index_stats_common},
        "pg_stat_database": {"sql": pg_stat_database},
        "pg_stat_bgwriter": {"sql": pg_stat_bgwriter},
        "pg_stat_activity": {"sql": pg_stat_activity},
        "pg_stat_progress_vacuum": {"sql": pg_stat_progress_vacuum},
        "pg_settings": {"sql": pg_settings},
        "version": {
            "sql": "select aurora_version(), version(), '{}' capture_version".format(
                CAPTURE_VERSION
            )
        },
    }


class CPG:
    v10 = {
        "pg_stat_statements": {"sql": pg_stat_statements_common},
        "table_stats": {"sql": table_stats_common},
        "index_stats": {"sql": index_stats_common},
        "pg_stat_database": {"sql": pg_stat_database},
        "pg_stat_bgwriter": {"sql": pg_stat_bgwriter},
        "pg_stat_activity": {"sql": pg_stat_activity},
        "pg_stat_progress_vacuum": {"sql": pg_stat_progress_vacuum},
        "pg_settings": {"sql": pg_settings},
        "version": {
            "sql": "select version(), '{}' capture_version".format(CAPTURE_VERSION)
        },
    }

    v11 = {
        "pg_stat_statements": {"sql": pg_stat_statements_common},
        "table_stats": {"sql": table_stats_common},
        "index_stats": {"sql": index_stats_common},
        "pg_stat_database": {"sql": pg_stat_database},
        "pg_stat_bgwriter": {"sql": pg_stat_bgwriter},
        "pg_stat_activity": {"sql": pg_stat_activity},
        "pg_stat_progress_vacuum": {"sql": pg_stat_progress_vacuum},
        "pg_settings": {"sql": pg_settings},
        "version": {
            "sql": "select version(), '{}' capture_version".format(CAPTURE_VERSION)
        },
    }

    v12 = {
        "pg_stat_statements": {"sql": pg_stat_statements_common},
        "table_stats": {"sql": table_stats_common},
        "index_stats": {"sql": index_stats_common},
        "pg_stat_database": {"sql": pg_stat_database},
        "pg_stat_bgwriter": {"sql": pg_stat_bgwriter},
        "pg_stat_activity": {"sql": pg_stat_activity},
        "pg_stat_progress_vacuum": {"sql": pg_stat_progress_vacuum},
        "pg_settings": {"sql": pg_settings},
        "version": {
            "sql": "select version(), '{}' capture_version".format(CAPTURE_VERSION)
        },
    }

    v13 = {
        "pg_stat_statements": {"sql": pg_stat_statements_gte13},
        "table_stats": {"sql": table_stats_common},
        "index_stats": {"sql": index_stats_common},
        "pg_stat_database": {"sql": pg_stat_database},
        "pg_stat_bgwriter": {"sql": pg_stat_bgwriter},
        "pg_stat_activity": {"sql": pg_stat_activity},
        "pg_stat_progress_vacuum": {"sql": pg_stat_progress_vacuum},
        "pg_settings": {"sql": pg_settings},
        "version": {
            "sql": "select version(), '{}' capture_version".format(CAPTURE_VERSION)
        },
    }

    v14 = {
        "pg_stat_statements": {"sql": pg_stat_statements_gte13},
        "table_stats": {"sql": table_stats_common},
        "index_stats": {"sql": index_stats_common},
        "pg_stat_database": {"sql": pg_stat_database},
        "pg_stat_bgwriter": {"sql": pg_stat_bgwriter},
        "pg_stat_activity": {"sql": pg_stat_activity},
        "pg_stat_progress_vacuum": {"sql": pg_stat_progress_vacuum},
        "pg_settings": {"sql": pg_settings},
        "version": {
            "sql": "select version(), '{}' capture_version".format(CAPTURE_VERSION)
        },
    }

    v15 = {
        "pg_stat_statements": {"sql": pg_stat_statements_gte13},
        "table_stats": {"sql": table_stats_common},
        "index_stats": {"sql": index_stats_common},
        "pg_stat_database": {"sql": pg_stat_database},
        "pg_stat_bgwriter": {"sql": pg_stat_bgwriter},
        "pg_stat_activity": {"sql": pg_stat_activity},
        "pg_stat_progress_vacuum": {"sql": pg_stat_progress_vacuum},
        "pg_settings": {"sql": pg_settings},
        "version": {
            "sql": "select version(), '{}' capture_version".format(CAPTURE_VERSION)
        },
    }
