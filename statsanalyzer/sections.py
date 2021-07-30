import pandas as pd
import util
import sqlite

import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)

escape_html = False


def get_pgstatactivity(snapshot_path, start_time, end_time, host, database):
    pg_stat_activity_df = util.get_stat(
        snapshot_path, "pg_stat_activity", start_time, end_time
    )
    sqlite.load_df(pg_stat_activity_df)

    wait_events_str = sqlite.execute_to_df(
        """
        select 
            count(*) "total samples", 
            coalesce(wait_event,'CPU') "wait event",
            coalesce(wait_event_type,'CPU') "wait event type"
        from 
            df 
        group by wait_event order by 1 desc
    """
    ).to_html(index=False, classes="tftable", escape=escape_html)

    wait_events_type_str = sqlite.execute_to_df(
        """
        select 
            count(*)  "total samples", 
            coalesce(wait_event_type,'CPU') "wait event type"
        from 
            df 
        group by wait_event_type
        order by 1 desc
    """
    ).to_html(index=False, classes="tftable", escape=escape_html)

    sqlite.unload_df()

    return wait_events_str, wait_events_type_str


def get_snapshot_details(snapshot_path, start_time, end_time, host, database):
    global version_no

    snapshot_detail_df = pd.DataFrame()

    ## set the version
    version_df = util.get_stat(snapshot_path, "version", start_time, end_time)
    sqlite.load_df(version_df)

    if "aurora_version" in version_df.columns:
        is_aurora = True
        snapshot_detail_df["aurora version"] = [
            sqlite.execute_to_df("select distinct aurora_version from df", True)
        ]
    else:
        is_aurora = False

    version = sqlite.execute_to_df("select distinct version from df", True)
    version_no = int(version.split(" ")[1].split(".")[0])
    snapshot_detail_df["version"] = [(version.split()[0] + " " + version.split()[1])]
    total_snapshots = sqlite.execute_to_df(
        "select distinct count(distinct snapshot_time) from df", True
    )
    if total_snapshots < 2:
        raise Exception(
            "Not enough snapshots for a report. total snapshots = {}".format(
                total_snapshots
            )
        )
    sqlite.unload_df()

    ## set the snapshot details
    pg_stat_database_df = util.get_stat(
        snapshot_path, "pg_stat_database", start_time, end_time
    )
    ### set deltas for pg_stat_database
    util.set_delta(pg_stat_database_df, "blks_read", ["datname", "datid"])
    util.set_delta(pg_stat_database_df, "blks_hit", ["datname", "datid"])
    sqlite.load_df(pg_stat_database_df)
    snapshot_detail_df["host"] = [host]
    snapshot_detail_df["database"] = [database]
    snapshot_detail_df["total snapshots"] = [total_snapshots]
    first_snapshot = sqlite.execute_to_df(
        "select min(snapshot_time) from df", True
    )
    last_snapshot = sqlite.execute_to_df(
        "select max(snapshot_time) from df", True
    )
    snapshot_detail_df["first snapshot (utc)"] = [first_snapshot]
    snapshot_detail_df["last snapshot (utc)"] = [last_snapshot]

    ## check if stats were reset
    no_resets = sqlite.execute_to_df(
        "select count(distinct stats_reset) from df where datname='{}' and datid!=0".format(
            database
        ),
        True,
    )
    if no_resets > 1:
        raise Exception(
            "Stats were reset for database {} during the specified snapshot window.".format(
                database
            )
        )

    ## get database role timeline
    database_role_timeline_df = sqlite.execute_to_df(
        """
        select datetime(min(snapshot_time)) as "change time", 
        case when standby = 0 then 'False' else 'True' end standby 
        from df
        where datid!=0
    """
    )

    ## get I/O stats
    database_io_df = sqlite.execute_to_df(
        """
        select
            datname,
            datid,
            "block hit ratio (%)",
            "total heap read" as "total heap read bytes",
            "total heap hit" as "total heap hit bytes",
            convert_bytes("total heap read") "total heap read",
            convert_bytes("total heap hit") "total heap hit",
            get_percentage("bytes","total heap read") "% of total I/O"
        from (
        select 
            datname, 
            datid, 
            get_ratio(sum(delta_blks_read), sum(delta_blks_hit)) as "block hit ratio (%)",
            blocks_to_bytes(sum(delta_blks_hit)) as "total heap hit",
            blocks_to_bytes(sum(delta_blks_read)) as "total heap read",
            tot.bytes as "bytes"
        from df,  (select blocks_to_bytes(sum(delta_blks_read)) bytes from df) as tot
        where datid!=0
        and datname = '{database}'
        group by datname, datid
        ) as subt
    """.format(
            database=database
        )
    )

    remainder_io_df = sqlite.execute_to_df(
        """
        select
            datname,
            datid,
            "block hit ratio (%)",
            "total heap read" as "total heap read bytes",
            "total heap hit" as "total heap hit bytes",
            convert_bytes("total heap read") "total heap read",
            convert_bytes("total heap hit") "total heap hit",
            get_percentage("bytes","total heap read") "% of total I/O"
        from (
        select 
            datname, 
            datid, 
            get_ratio(sum(delta_blks_read), sum(delta_blks_hit)) as "block hit ratio (%)",
            blocks_to_bytes(sum(delta_blks_hit)) as "total heap hit",
            blocks_to_bytes(sum(delta_blks_read)) as "total heap read",
            tot.bytes as "bytes"
        from df, (select blocks_to_bytes(sum(delta_blks_read)) bytes from df) as tot
        where datid!=0
        and datname != '{database}'
        group by datname, datid
        ) as subt
    """.format(
            database=database
        )
    )

    ## convert df to string
    snapshot_details_str = snapshot_detail_df.to_html(
        index=False,
        classes="tftable",
        columns=["database", "total snapshots", "first snapshot (utc)", "last snapshot (utc)"],
        escape=escape_html,
    )
    cluster_details_str = snapshot_detail_df.drop(
        ["database", "total snapshots", "first snapshot (utc)", "last snapshot (utc)"], axis=1
    ).to_html(index=False, classes="tftable", escape=escape_html)

    projected_columns = [
        "datname",
        "datid",
        "block hit ratio (%)",
        "total heap read",
        "total heap hit",
        "% of total I/O",
    ]
    database_io_str = database_io_df.sort_values(
        by=["% of total I/O", "total heap read bytes", "total heap hit bytes"],
        ascending=[False, False, False],
    ).to_html(
        index=False, classes="tftable", columns=projected_columns, escape=escape_html
    )
    remainder_io_str = remainder_io_df.sort_values(
        by=["% of total I/O", "total heap read bytes", "total heap hit bytes"],
        ascending=[False, False, False],
    ).to_html(
        index=False, classes="tftable", columns=projected_columns, escape=escape_html
    )

    database_role_timeline_str = database_role_timeline_df.to_html(
        index=False,
        classes="tftable",
        columns=["change time", "standby"],
        escape=escape_html,
    )

    sqlite.unload_df()

    ## populate snapshot findings
    snapshot_details_findings = pd.DataFrame(columns=["category", "recommendation"])
    if is_aurora and database_io_df["block hit ratio (%)"].iloc[0] < 99:
        snapshot_details_findings.loc[0] = [
            "database",
            "Block hit ratio is below 99%. A low block hit ratio will contribute to more disk reads. It is recommended to review the shared_buffers parameter and top I/O bound SQLs for improvement",
        ]

    snapshot_details_findings_str = snapshot_details_findings.to_html(
        index=False, classes="tftable2", header=False, escape=escape_html
    )

    return (
        snapshot_details_str,
        cluster_details_str,
        database_role_timeline_str,
        database_io_str,
        remainder_io_str,
        snapshot_details_findings_str,
        is_aurora,
    )


def get_pgsettings(snapshot_path, start_time, end_time):
    pg_settings_df = util.get_stat(snapshot_path, "pg_settings", start_time, end_time)
    sqlite.load_df(pg_settings_df)

    a = pg_settings_df.groupby(
        ["name", "setting", "context", "category", "short_desc"], as_index=False
    ).nunique()
    a = a.sort_values(["category", "name"])

    pg_settings_str = a.to_html(
        index=False,
        classes="tftable",
        columns=["name", "setting", "context", "category", "short_desc"],
        escape=escape_html,
    )

    b = sqlite.execute_to_df(
        """
        select datetime(min(snapshot_time)) "change time", name, setting from df where name in (
            select name from (
                select 
                    count(*) cnt, 
                    name
                from (select distinct name, setting from df ) 
                group by name
            ) where cnt>1
        ) group by name, setting order by name, "change time" asc
    """
    )

    pg_setting_change_timeline_str = b.to_html(
        index=False,
        classes="tftable",
        columns=["change time", "name", "setting"],
        escape=escape_html,
    )

    sqlite.unload_df()
    return pg_setting_change_timeline_str, pg_settings_str


def get_sqlstats(snapshot_path, start_time, end_time, limit):
    global version_no

    total_exec_time_name = "total_time"
    min_exec_time_name = "min_time"
    max_exec_time_name = "max_time"
    stddev_exec_time_name = "stddev_time"

    if version_no >= 13:
        total_exec_time_name = "total_exec_time"
        min_exec_time_name = "min_exec_time"
        max_exec_time_name = "max_exec_time"
        stddev_exec_time_name = "stddev_exec_time"

    sql_stats_df = util.get_stat(
        snapshot_path, "pg_stat_statements", start_time, end_time
    )
    util.set_delta(sql_stats_df, "shared_blks_read", ["username", "queryid", "query"])
    util.set_delta(sql_stats_df, "shared_blks_hit", ["username", "queryid", "query"])
    util.set_delta(
        sql_stats_df, "shared_blks_written", ["username", "queryid", "query"]
    )
    util.set_delta(
        sql_stats_df, "shared_blks_dirtied", ["username", "queryid", "query"]
    )
    util.set_delta(sql_stats_df, "calls", ["username", "queryid", "query"])
    util.set_delta(sql_stats_df, total_exec_time_name, ["username", "queryid", "query"])
    util.set_delta(sql_stats_df, "snapshot_timestamp", ["username", "queryid", "query"])
    util.set_delta(sql_stats_df, "temp_blks_read", ["username", "queryid", "query"])
    util.set_delta(sql_stats_df, "temp_blks_written", ["username", "queryid", "query"])
    util.set_delta(sql_stats_df, "blk_read_time", ["username", "queryid", "query"])
    util.set_delta(sql_stats_df, "blk_write_time", ["username", "queryid", "query"])
    util.set_delta(sql_stats_df, "rows", ["username", "queryid", "query"])
    util.set_delta(sql_stats_df, min_exec_time_name, ["username", "queryid", "query"])
    util.set_delta(sql_stats_df, max_exec_time_name, ["username", "queryid", "query"])
    util.set_delta(
        sql_stats_df, stddev_exec_time_name, ["username", "queryid", "query"]
    )

    if version_no >= 13:
        util.set_delta(sql_stats_df, "wal_records", ["username", "queryid", "query"])
        util.set_delta(sql_stats_df, "wal_fpi", ["username", "queryid", "query"])
        util.set_delta(sql_stats_df, "wal_bytes", ["username", "queryid", "query"])

    sqlite.load_df(sql_stats_df)

    if version_no < 13:
        sql_stats_df = sqlite.execute_to_df(
            """
            select * from (
                select
                    blocks_to_bytes(sum(delta_shared_blks_written)) "total shared blocks written bytes",
                    blocks_to_bytes(sum(delta_shared_blks_read)) "total shared blocks read bytes",
                    blocks_to_bytes(sum(delta_shared_blks_hit)) "total shared blocks hit bytes",
                    blocks_to_bytes(sum(temp_blks_read)) "total temp blocks read bytes",
                    blocks_to_bytes(sum(temp_blks_written)) "total temp blocks written bytes",
                    convert_bytes(blocks_to_bytes(sum(delta_shared_blks_written))) "total shared blocks written",
                    convert_bytes(blocks_to_bytes(sum(delta_shared_blks_read))) "total shared blocks read",
                    convert_bytes(blocks_to_bytes(sum(delta_shared_blks_hit))) "total shared blocks hit",
                    convert_bytes(blocks_to_bytes(sum(temp_blks_read))) "total temp blocks read",
                    convert_bytes(blocks_to_bytes(sum(temp_blks_written))) "total temp blocks written",
                    get_ratio(sum(delta_shared_blks_read),sum(delta_shared_blks_hit)) "block hit ratio (%)",
                    cast(sum(delta_calls) as int) as "total calls",
                    divide(cast(sum(delta_calls) as int) , cast(sum(delta_total_time) as int)) as "ms per call",
                    divide(cast(sum(delta_calls) as int) , cast(sum(delta_shared_blks_hit) as int)) as "shared blocks hit/call",
                    divide(cast(sum(delta_calls) as int) , cast(sum(delta_shared_blks_read) as int)) as "shared blocks read/call",
                    divide(sum("delta_calls"), sum(delta_blk_read_time)) "ms read time/call",
                    divide(sum("delta_snapshot_timestamp"),sum("delta_calls")) "calls/second",
                    username, 
                    queryid,
                    query
                from df
                group by username, queryid, query
                order by 1 desc, 2 desc, 3 desc
            )
            where "total shared blocks read bytes" > 0 or "total shared blocks hit bytes" > 0 or
            "total shared blocks written bytes" > 0 or "total temp blocks read bytes" > 0 or
            "total temp blocks written bytes" >0
            limit {limit}
            """.format(
                limit=limit
            )
        )
    else:
        sql_stats_df = sqlite.execute_to_df(
            """
            select * from (
                select
                    blocks_to_bytes(sum(delta_shared_blks_written)) "total shared blocks written bytes",
                    blocks_to_bytes(sum(delta_shared_blks_read)) "total shared blocks read bytes",
                    blocks_to_bytes(sum(delta_shared_blks_hit)) "total shared blocks hit bytes",
                    blocks_to_bytes(sum(temp_blks_read)) "total temp blocks read bytes",
                    blocks_to_bytes(sum(temp_blks_written)) "total temp blocks written bytes",
                    convert_bytes(blocks_to_bytes(sum(delta_shared_blks_written))) "total shared blocks written",
                    convert_bytes(blocks_to_bytes(sum(delta_shared_blks_read))) "total shared blocks read",
                    convert_bytes(blocks_to_bytes(sum(delta_shared_blks_hit))) "total shared blocks hit",
                    convert_bytes(blocks_to_bytes(sum(temp_blks_read))) "total temp blocks read",
                    convert_bytes(blocks_to_bytes(sum(temp_blks_written))) "total temp blocks written",
                    get_ratio(sum(delta_shared_blks_read),sum(delta_shared_blks_hit)) "block hit ratio (%)",
                    cast(sum(delta_calls) as int) as "total calls",
                    divide(cast(sum(delta_calls) as int) , cast(sum(delta_total_exec_time) as int)) as "ms per call",
                    divide(cast(sum(delta_calls) as int) , cast(sum(delta_shared_blks_hit) as int)) as "shared blocks hit/call",
                    divide(cast(sum(delta_calls) as int) , cast(sum(delta_shared_blks_read) as int)) as "shared blocks read/call",
                    divide(sum("delta_calls"), sum(delta_blk_read_time)) "ms read time/call",
                    divide(sum("delta_snapshot_timestamp"),sum("delta_calls")) "calls/second",
                    cast(sum(delta_wal_records) as int) "total wal records",
                    cast(sum(delta_wal_fpi) as int) "total full-page images",
                    sum(delta_wal_bytes) "total wal generated bytes",
                    convert_bytes(sum(delta_wal_bytes)) "total wal generated",
                    username, 
                    queryid,
                    query
                from df
                group by username, queryid, query
                order by 1 desc, 2 desc, 3 desc, 4 desc
            )
            where "total shared blocks read bytes" > 0 or "total shared blocks hit bytes" > 0 or
            "total shared blocks written bytes" > 0 or "total temp blocks read bytes" > 0 or
            "total temp blocks written bytes" >0
            limit {limit}
            """.format(
                limit=limit
            )
        )

    sql_stats_df["queryid"] = sql_stats_df["queryid"].fillna(0).astype("int64")

    if version_no < 13:
        projected_columns = [
            "username",
            "queryid",
            "total shared blocks read",
            "total shared blocks hit",
            "total shared blocks written",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total shared blocks read bytes"] > 0
        sql_stats_r_str = (
            sql_stats_df.loc[filter]
            .sort_values("total shared blocks read bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total shared blocks hit",
            "total shared blocks read",
            "total shared blocks written",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total shared blocks hit bytes"] > 0
        sql_stats_h_str = (
            sql_stats_df.loc[filter]
            .sort_values("total shared blocks hit bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total shared blocks written bytes"] > 0
        sql_stats_w_str = (
            sql_stats_df.loc[filter]
            .sort_values("total shared blocks written bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total shared blocks written bytes"] > 0
        sql_stats_w_str = (
            sql_stats_df.loc[filter]
            .sort_values("total shared blocks written bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total shared blocks written bytes"] > 0
        sql_stats_w_str = (
            sql_stats_df.loc[filter]
            .sort_values("total shared blocks written bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total temp blocks read",
            "total temp blocks written",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total temp blocks read bytes"] > 0
        sql_stats_tr_str = (
            sql_stats_df.loc[filter]
            .sort_values("total temp blocks read bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total temp blocks written",
            "total temp blocks read",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total temp blocks written bytes"] > 0
        sql_stats_tw_str = (
            sql_stats_df.loc[filter]
            .sort_values("total temp blocks written bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total temp blocks written",
            "total temp blocks read",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total temp blocks written bytes"] > 0
        sql_stats_tw_str = (
            sql_stats_df.loc[filter]
            .sort_values("total temp blocks written bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total shared blocks read",
            "total shared blocks hit",
            "total shared blocks written",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        findings_top_io_sql_str = (
            sql_stats_df.sort_values("total shared blocks read", ascending=False)
            .head(5)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        sql_stats_wg_str = None
    else:
        projected_columns = [
            "username",
            "queryid",
            "total shared blocks read",
            "total shared blocks hit",
            "total shared blocks written",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "total wal records",
            "total full-page images",
            "total wal generated",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total shared blocks read bytes"] > 0
        sql_stats_r_str = (
            sql_stats_df.loc[filter]
            .sort_values("total shared blocks read bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total shared blocks hit",
            "total shared blocks read",
            "total shared blocks written",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "total wal records",
            "total full-page images",
            "total wal generated",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total shared blocks hit bytes"] > 0
        sql_stats_h_str = (
            sql_stats_df.loc[filter]
            .sort_values("total shared blocks hit bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "total wal records",
            "total full-page images",
            "total wal generated",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total shared blocks written bytes"] > 0
        sql_stats_w_str = (
            sql_stats_df.loc[filter]
            .sort_values("total shared blocks written bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "total wal records",
            "total full-page images",
            "total wal generated",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total shared blocks written bytes"] > 0
        sql_stats_w_str = (
            sql_stats_df.loc[filter]
            .sort_values("total shared blocks written bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "total wal records",
            "total full-page images",
            "total wal generated",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total shared blocks written bytes"] > 0
        sql_stats_w_str = (
            sql_stats_df.loc[filter]
            .sort_values("total shared blocks written bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total temp blocks read",
            "total temp blocks written",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "total wal records",
            "total full-page images",
            "total wal generated",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total temp blocks read bytes"] > 0
        sql_stats_tr_str = (
            sql_stats_df.loc[filter]
            .sort_values("total temp blocks read bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total temp blocks written",
            "total temp blocks read",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "total wal records",
            "total full-page images",
            "total wal generated",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total temp blocks written bytes"] > 0
        sql_stats_tw_str = (
            sql_stats_df.loc[filter]
            .sort_values("total temp blocks written bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total temp blocks written",
            "total temp blocks read",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "total wal records",
            "total full-page images",
            "total wal generated",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total temp blocks written bytes"] > 0
        sql_stats_tw_str = (
            sql_stats_df.loc[filter]
            .sort_values("total temp blocks written bytes", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total wal generated",
            "total wal records",
            "total full-page images",
            "total temp blocks written",
            "total temp blocks read",
            "total shared blocks written",
            "total shared blocks hit",
            "total shared blocks read",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        filter = sql_stats_df["total wal generated bytes"] > 0
        sql_stats_wg_str = (
            sql_stats_df.loc[filter]
            .sort_values("total wal generated", ascending=False)
            .head(limit)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

        projected_columns = [
            "username",
            "queryid",
            "total shared blocks read",
            "total shared blocks hit",
            "total shared blocks written",
            "total temp blocks read",
            "total temp blocks written",
            "block hit ratio (%)",
            "total calls",
            "ms per call",
            "calls/second",
            "total wal records",
            "total full-page images",
            "total wal generated",
            "shared blocks hit/call",
            "shared blocks read/call",
            "ms read time/call",
            "query",
        ]
        findings_top_io_sql_str = (
            sql_stats_df.sort_values("total shared blocks read", ascending=False)
            .head(5)
            .to_html(
                index=False,
                classes="tftable",
                columns=projected_columns,
                escape=escape_html,
            )
        )

    sqlite.unload_df()
    return (
        sql_stats_r_str,
        sql_stats_h_str,
        sql_stats_w_str,
        sql_stats_tr_str,
        sql_stats_tw_str,
        sql_stats_wg_str,
        findings_top_io_sql_str,
    )


def get_bgwriter(snapshot_path, start_time, end_time, is_aurora):
    bgwriter_stats_df = util.get_stat(
        snapshot_path, "pg_stat_bgwriter", start_time, end_time
    )

    util.set_delta(bgwriter_stats_df, "checkpoints_timed", "stats_reset")
    util.set_delta(bgwriter_stats_df, "checkpoints_req", "stats_reset")
    util.set_delta(bgwriter_stats_df, "buffers_checkpoint", "stats_reset")
    util.set_delta(bgwriter_stats_df, "buffers_clean", "stats_reset")
    util.set_delta(bgwriter_stats_df, "buffers_backend", "stats_reset")
    util.set_delta(bgwriter_stats_df, "snapshot_timestamp", "stats_reset")
    sqlite.load_df(bgwriter_stats_df)

    bgwriter_stats_df = sqlite.execute_to_df(
        """
        select 
            max(stats_reset) as "last reset",
            cast(sum(delta_checkpoints_timed) as int) as "total checkpoints timed",
            cast(sum(delta_checkpoints_req) as int) as "total checkpoints requested",
            convert_bytes(blocks_to_bytes(sum(delta_buffers_checkpoint))) as "total written by checkpoint",
            convert_bytes(blocks_to_bytes(sum(delta_buffers_checkpoint))) as "total written by bgwriter",
            convert_bytes(blocks_to_bytes(sum(delta_buffers_checkpoint))) as "total written by backends",
            get_ratio(sum(delta_checkpoints_req),sum(delta_checkpoints_timed)) "checkpoint timed/requested ratio",
            divide(sum("delta_snapshot_timestamp"),(sum(delta_checkpoints_req))+(sum(delta_checkpoints_timed)))*60 "checkpoints/second"

        from
            df
        """
    )

    bgwriter_stats_str = bgwriter_stats_df.to_html(
        index=False, classes="tftable", escape=escape_html
    )

    bgwriter_findings_df = pd.DataFrame(columns=["category", "recommendation"])
    if (
        not is_aurora
        and bgwriter_stats_df["checkpoint timed/requested ratio"].iloc[0] < 90
    ):
        bgwriter_findings_df.loc[0] = [
            "bgwriter",
            "Less than 90% of checkpoints are timed. Ensure that max_wal_size and checkpoint_timeout are properly set. Checkpointing too often will cause additional I/O.",
        ]
    bgwriter_findings_str = bgwriter_findings_df.to_html(
        index=False, classes="tftable2", header=False, escape=escape_html
    )

    sqlite.unload_df()

    return bgwriter_stats_str, bgwriter_findings_str


def get_indexstats(snapshot_path, start_time, end_time, limit):
    index_stats_df = util.get_stat(snapshot_path, "index_stats", start_time, end_time)
    util.set_delta(
        index_stats_df, "idx_blks_hit", ["schemaname", "relname", "indexrelname"]
    )
    util.set_delta(
        index_stats_df, "idx_blks_read", ["schemaname", "relname", "indexrelname"]
    )
    sqlite.load_df(index_stats_df)

    index_stats_df = sqlite.execute_to_df(
        """
        select * from (
            select
                oid,
                schemaname||'.'||relname||'.'||indexrelname as "index name",
                blocks_to_bytes(sum(delta_idx_blks_read)) as "total index read bytes",
                blocks_to_bytes(sum(delta_idx_blks_hit)) as "total index hit bytes",
                get_ratio(sum(delta_idx_blks_read),sum(delta_idx_blks_hit)) as "block hit ratio (%)",
                convert_bytes(blocks_to_bytes(sum(delta_idx_blks_read))) as "total index read",
                convert_bytes(blocks_to_bytes(sum(delta_idx_blks_hit))) as "total index hit"
            from df
            group by "index name"
            order by 4 desc
        ) where "total index read" > 0 or "total index hit" > 0
        """
    )

    projected_columns = ["index name", "total index read", "block hit ratio (%)"]
    filter = index_stats_df["total index read bytes"] > 0
    index_stats_r_str = (
        index_stats_df[filter]
        .sort_values(["total index read bytes"], ascending=False)
        .head(limit)
        .to_html(
            columns=projected_columns,
            index=False,
            classes="tftable",
            escape=escape_html,
        )
    )

    projected_columns = ["index name", "total index hit", "block hit ratio (%)"]
    filter = index_stats_df["total index hit bytes"] > 0
    index_stats_h_str = (
        index_stats_df[filter]
        .sort_values(["total index hit bytes"], ascending=False)
        .head(limit)
        .to_html(
            columns=projected_columns,
            index=False,
            classes="tftable",
            escape=escape_html,
        )
    )

    ## index usage
    index_usage_df = sqlite.execute_to_df(
        """
        select "table name", count(*) "total unused indexes" from (
                select
                distinct 
                    schemaname||'.'||relname||'.'||indexrelname as "index name",
                    schemaname||'.'||relname "table name"
                from df where indkey != 0 and conname is null and not indisunique and idx_scan = 0
                and schemaname not in ('pg_catalog','pg_toast')
            ) group by "table name"
            order by 2 desc
        """
    )

    ## index usage
    index_usage_2_df = sqlite.execute_to_df(
        """
        select 
            distinct 
                    schemaname||'.'||relname "table name",
                    schemaname||'.'||relname||'.'||indexrelname as "index name"
                from df where indkey != 0 and conname is null and not indisunique and idx_scan = 0
                and schemaname not in ('pg_catalog','pg_toast')
                order by 1 asc
                limit 500
        """
    )

    index_usage_str = index_usage_df.head(limit).to_html(
        index=False, classes="tftable", escape=escape_html
    )
    index_usage_2_str = index_usage_2_df.head(limit).to_html(
        index=False, classes="tftable", escape=escape_html
    )

    index_stats_findings_df = pd.DataFrame(columns=["category", "recommendation"])
    if index_usage_df["total unused indexes"].sum() > 0:
        index_stats_findings_df.loc[0] = [
            "index",
            """\
                Unused indexes found. \
                It is advised to drop unused indexes as they will contribute to unnecessary additional I/O.""",
        ]

    if (
        index_stats_df[index_stats_df["block hit ratio (%)"] < 99].count()["index name"]
        > 0
    ):
        index_stats_findings_df.loc[1] = [
            "index",
            """Indexes with low buffer hit ratio found. See "I/O"->"by Index" for more details.""",
        ]

    index_stats_findings_str = index_stats_findings_df.to_html(
        index=False, classes="tftable2", header=False, escape=escape_html
    )

    sqlite.unload_df()

    return (
        index_stats_r_str,
        index_stats_h_str,
        index_usage_str,
        index_usage_2_str,
        index_stats_findings_str,
    )


def get_tablestats(snapshot_path, start_time, end_time, limit):
    table_stats_df = util.get_stat(snapshot_path, "table_stats", start_time, end_time)
    util.set_delta(table_stats_df, "heap_blks_hit", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "heap_blks_read", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "idx_blks_hit", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "idx_blks_read", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "toast_blks_hit", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "toast_blks_read", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "tidx_blks_hit", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "tidx_blks_read", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "autovacuum_count", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "autoanalyze_count", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "vacuum_count", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "analyze_count", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "n_dead_tup", ["schemaname", "relname"])
    util.set_delta(table_stats_df, "n_live_tup", ["schemaname", "relname"])
    sqlite.load_df(table_stats_df)

    vacuum_stats_df = sqlite.execute_to_df(
        """
        select * from (
        select  
            schemaname||'.'||relname as "table name",
            cast(totals."all vacuums" as int) "total vacuums",
            cast(sum(delta_vacuum_count) as int) "total manual vacuums",
            cast(divide(totals.vacuum, cast(sum(delta_vacuum_count) as int) )*100 as int) "% of manual vacuum",
            cast(sum(delta_autovacuum_count) as int) "total autovacuums",
            cast(divide(totals.autovacuum, cast(sum(delta_autovacuum_count) as int) )*100 as int) "% of autovacuum",
            cast(avg(n_dead_tup) as int) "average dead rows",
            cast(avg(get_ratio(n_live_tup, n_dead_tup)) as int) "dead row ratio (%)"
        from df, (
            select 
                sum(delta_vacuum_count) "vacuum",
                sum(delta_autovacuum_count) "autovacuum",
                sum(delta_vacuum_count) + sum(delta_autovacuum_count) "all vacuums"
            from df
        ) as totals
        where schemaname not like '%pg_toast%'
        group by schemaname, relname
        )
        where "total manual vacuums" > 0 or "total autovacuums" > 0
        group by "table name"
        order by 8 desc, 7 desc
    """
    )

    table_stats_df = sqlite.execute_to_df(
        """
        select * from (
            select
                schemaname||'.'||relname as "table name",
                blocks_to_bytes(sum(delta_heap_blks_read)) as "total heap read bytes",
                blocks_to_bytes(sum(delta_heap_blks_hit)) as "total heap hit bytes",
                convert_bytes(blocks_to_bytes(sum(delta_heap_blks_read))) as "total heap read",
                convert_bytes(blocks_to_bytes(sum(delta_heap_blks_hit))) as "total heap hit",
                get_ratio(sum(delta_heap_blks_read),sum(delta_heap_blks_hit)) as "heap block hit ratio (%)",
                
                blocks_to_bytes(sum(delta_idx_blks_read)) as "total index read bytes",
                blocks_to_bytes(sum(delta_idx_blks_hit)) as "total index hit bytes",
                convert_bytes(blocks_to_bytes(sum(delta_idx_blks_read))) as "total index read",
                convert_bytes(blocks_to_bytes(sum(delta_idx_blks_hit))) as "total index hit",
                get_ratio(sum(delta_idx_blks_read),sum(delta_idx_blks_hit)) as "index block hit ratio (%)",
                
                blocks_to_bytes(sum(delta_toast_blks_read)) as "total toast read bytes",
                blocks_to_bytes(sum(delta_toast_blks_hit)) as "total toast hit bytes",
                convert_bytes(blocks_to_bytes(sum(delta_toast_blks_read))) as "total toast read",
                convert_bytes(blocks_to_bytes(sum(delta_toast_blks_hit))) as "total toast hit",
                get_ratio(sum(delta_toast_blks_read),sum(delta_toast_blks_hit)) as "toast block hit ratio (%)",
                
                blocks_to_bytes(sum(delta_tidx_blks_read)) as "total toast index read bytes",
                blocks_to_bytes(sum(delta_tidx_blks_hit)) as "total toast index hit bytes",
                convert_bytes(blocks_to_bytes(sum(delta_tidx_blks_read))) as "total toast index read",
                convert_bytes(blocks_to_bytes(sum(delta_tidx_blks_hit))) as "total toast index hit",
                get_ratio(sum(delta_tidx_blks_read),sum(delta_tidx_blks_hit)) as "toast index block hit ratio (%)"
            from df
            group by "table name"
            order by 1 desc
        ) 
        where "total heap read bytes" > 0 
        or    "total index read bytes" > 0
        or    "total toast read bytes" > 0
        or    "total toast index read bytes" > 0
        or    "total heap hit bytes" > 0 
        or    "total index hit bytes" > 0
        or    "total toast hit bytes" > 0
        or    "total toast index hit bytes" > 0
        """
    )
    sqlite.unload_df()

    sqlite.load_df(table_stats_df)

    projected_columns = ["table name", "total heap read", "heap block hit ratio (%)"]
    filter = table_stats_df["total heap read bytes"] > 0
    table_stats_hr_str = (
        table_stats_df[filter]
        .sort_values(["total heap read bytes"], ascending=False)
        .head(limit)
        .to_html(
            index=False,
            classes="tftable",
            columns=projected_columns,
            escape=escape_html,
        )
    )

    projected_columns = ["table name", "total index read", "index block hit ratio (%)"]
    filter = table_stats_df["total index read bytes"] > 0
    table_stats_ir_str = (
        table_stats_df[filter]
        .sort_values(["total index read bytes"], ascending=False)
        .head(limit)
        .to_html(
            index=False,
            classes="tftable",
            columns=projected_columns,
            escape=escape_html,
        )
    )

    projected_columns = ["table name", "total toast read", "toast block hit ratio (%)"]
    filter = table_stats_df["total toast read bytes"] > 0
    table_stats_tr_str = (
        table_stats_df[filter]
        .sort_values(["total toast read bytes"], ascending=False)
        .head(limit)
        .to_html(
            index=False,
            classes="tftable",
            columns=projected_columns,
            escape=escape_html,
        )
    )

    projected_columns = [
        "table name",
        "total toast index read",
        "toast index block hit ratio (%)",
    ]
    filter = table_stats_df["total toast index read bytes"] > 0
    table_stats_tir_str = (
        table_stats_df[filter]
        .sort_values(["total toast index read bytes"], ascending=False)
        .head(limit)
        .to_html(
            index=False,
            classes="tftable",
            columns=projected_columns,
            escape=escape_html,
        )
    )

    projected_columns = ["table name", "total heap hit", "heap block hit ratio (%)"]
    filter = table_stats_df["total heap hit bytes"] > 0
    table_stats_hh_str = (
        table_stats_df[filter]
        .sort_values(["total heap hit bytes"], ascending=False)
        .head(limit)
        .to_html(
            index=False,
            classes="tftable",
            columns=projected_columns,
            escape=escape_html,
        )
    )

    projected_columns = ["table name", "total index hit", "index block hit ratio (%)"]
    filter = table_stats_df["total index hit bytes"] > 0
    table_stats_ih_str = (
        table_stats_df[filter]
        .sort_values(["total index hit bytes"], ascending=False)
        .head(limit)
        .to_html(
            index=False,
            classes="tftable",
            columns=projected_columns,
            escape=escape_html,
        )
    )

    projected_columns = ["table name", "total toast hit", "toast block hit ratio (%)"]
    filter = table_stats_df["total toast hit bytes"] > 0
    table_stats_th_str = (
        table_stats_df[filter]
        .sort_values(["total toast hit bytes"], ascending=False)
        .head(limit)
        .to_html(
            index=False,
            classes="tftable",
            columns=projected_columns,
            escape=escape_html,
        )
    )

    projected_columns = [
        "table name",
        "total toast index hit",
        "toast index block hit ratio (%)",
    ]
    filter = table_stats_df["total toast index hit bytes"] > 0
    table_stats_tih_str = (
        table_stats_df[filter]
        .sort_values(["total toast index hit bytes"], ascending=False)
        .head(limit)
        .to_html(
            index=False,
            classes="tftable",
            columns=projected_columns,
            escape=escape_html,
        )
    )

    vacuum_stats_str = vacuum_stats_df.to_html(
        index=False, classes="tftable", escape=escape_html
    )

    table_stats_findings_df = pd.DataFrame(columns=["category", "recommendation"])
    if (
        table_stats_df[table_stats_df["heap block hit ratio (%)"] < 99].count()[
            "table name"
        ]
        > 1
        or table_stats_df[table_stats_df["heap block hit ratio (%)"] < 99].count()[
            "table name"
        ]
        > 1
        or table_stats_df[table_stats_df["heap block hit ratio (%)"] < 99].count()[
            "table name"
        ]
        > 1
        or table_stats_df[table_stats_df["heap block hit ratio (%)"] < 99].count()[
            "table name"
        ]
        > 1
    ):

        table_stats_findings_df.loc[0] = [
            "table",
            """Tables with low cache hit ratio found. See "I/O"->"by Table for more details.""",
        ]

    table_stats_findings_str = table_stats_findings_df.to_html(
        index=False, classes="tftable2", header=False, escape=escape_html
    )

    sqlite.unload_df()
    return (
        table_stats_hr_str,
        table_stats_ir_str,
        table_stats_tir_str,
        table_stats_tr_str,
        table_stats_hh_str,
        table_stats_ih_str,
        table_stats_th_str,
        table_stats_tih_str,
        vacuum_stats_str,
        table_stats_findings_str,
    )
