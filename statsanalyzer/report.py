import os
import util
from jinja2 import Template
import sections
import template

import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)


def main(snapshot_root=None, output=None):
    if snapshot_root:
        os.environ["SA_REPORT_SNAPSHOT_PATH"] = snapshot_root
    if output:
        os.environ["SA_REPORT_OUTPUT"] = output
    """
        INIT
    """
    host, database, start_time, end_time, limit, output, snapshot_path = util.init()

    """
        SNAPSHOT DETAILS
    """
    (
        snapshot_detail_str,
        cluster_details_str,
        database_role_timeline_str,
        database_io_str,
        remainder_io_str,
        snapshot_details_findings_str,
        is_aurora,
    ) = sections.get_snapshot_details(
        snapshot_path, start_time, end_time, host, database
    )

    wait_events_str, wait_events_type_str = sections.get_pgstatactivity(
        snapshot_path, start_time, end_time, host, database
    )

    """
        PG SETTINGS
    """
    pg_setting_change_timeline_str, pg_settings_str = sections.get_pgsettings(
        snapshot_path,
        start_time,
        end_time,
    )

    """
        SQL STATS
    """
    (
        sql_stats_r_str,
        sql_stats_h_str,
        sql_stats_w_str,
        sql_stats_tr_str,
        sql_stats_tw_str,
        sql_stats_wg_str,
        findings_top_io_sql_str,
    ) = sections.get_sqlstats(snapshot_path, start_time, end_time, limit)

    """ 
        BGWRITER
    """
    bgwriter_stats_str, bgwriter_findings_str = sections.get_bgwriter(
        snapshot_path, start_time, end_time, is_aurora
    )

    """ 
	   INDEX STATS
    """
    (
        index_stats_r_str,
        index_stats_h_str,
        index_usage_str,
        index_usage_2_str,
        index_stats_findings_str,
    ) = sections.get_indexstats(snapshot_path, start_time, end_time, limit)

    """ 
        TABLE STATS
    """
    (
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
    ) = sections.get_tablestats(snapshot_path, start_time, end_time, limit)

    """
        Report Render
    """
    tmplt = template.tmplt

    t = Template(tmplt)
    htmlout = t.render(
        limit=limit,
        snapshot_details=snapshot_detail_str,
        database_role_timeline=database_role_timeline_str,
        cluster_details=cluster_details_str,
        index_reads=index_stats_r_str,
        index_hits=index_stats_h_str,
        index_usage=index_usage_str,
        index_usage_2=index_usage_2_str,
        table_heap_reads=table_stats_hr_str,
        table_index_reads=table_stats_ir_str,
        table_toast_reads=table_stats_tr_str,
        table_toast_index_reads=table_stats_tir_str,
        table_heap_hits=table_stats_hh_str,
        table_index_hits=table_stats_ih_str,
        table_toast_hits=table_stats_th_str,
        table_toast_index_hits=table_stats_tih_str,
        table_stats_findings=table_stats_findings_str,
        index_stats_findings=index_stats_findings_str,
        bgwriter_stats=bgwriter_stats_str,
        sql_r_io_stats=sql_stats_r_str,
        sql_h_io_stats=sql_stats_h_str,
        sql_w_io_stats=sql_stats_w_str,
        sql_tr_stats=sql_stats_tr_str,
        sql_tw_stats=sql_stats_tw_str,
        vacuum_stats=vacuum_stats_str,
        parameters=pg_settings_str,
        pg_setting_change_timeline=pg_setting_change_timeline_str,
        findings_top_io_sql=findings_top_io_sql_str,
        database_io=database_io_str,
        remainder_io=remainder_io_str,
        snapshot_details_findings=snapshot_details_findings_str,
        bgwriter_findings=bgwriter_findings_str,
        wait_events=wait_events_str,
        wait_events_type=wait_events_type_str,
        sql_stats_wg=sql_stats_wg_str,
        is_aurora=is_aurora,
    )

    if not output.lower().split("s3://")[0] == "":
        f = open(output, "w")
    else:
        import s3fs

        fs = s3fs.S3FileSystem()
        f = fs.open(output, "w")

    with f as text_file:
        text_file.write(htmlout)


# Program Entry Point
if __name__ == "__main__":
    main()
