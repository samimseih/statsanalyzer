import os
import glob
import argparse
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import boto3
import pandas as pd
import numpy as np

import warnings

warnings.filterwarnings("ignore")


def set_path_for_platform(dos_path, encoding=None):
    if os.name == "nt":
        if not isinstance(dos_path, str) and encoding is not None:
            dos_path = dos_path.decode(encoding)
        path = os.path.abspath(dos_path)
        if path.startswith(u"\\\\"):
            return u"\\\\?\\UNC\\" + path[2:]
        return u"\\\\?\\" + path
    else:
        return dos_path


def init():
    parser = argparse.ArgumentParser(
        description="A Utility to Generate an I/O report",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--sa-report-snapshot-root",
        "-r",
        default=os.getenv("SA_REPORT_SNAPSHOT_PATH", None),
        help="Snapshot Root path",
    )
    _stime = (
        datetime.utcnow().replace(microsecond=0) - timedelta(minutes=120)
    ).strftime("%m/%d/%Y %H:%M:%S")

    parser.add_argument(
        "--sa-report-start-time",
        "-s",
        default=os.getenv("SA_REPORT_START_TIME", _stime),
        help="Report start time",
    )
    _etime = (datetime.utcnow().replace(microsecond=0)).strftime("%m/%d/%Y %H:%M:%S")

    parser.add_argument(
        "--sa-report-end-time",
        "-e",
        default=os.getenv("SA_REPORT_END_TIME", _etime),
        help="Report end time",
    )

    parser.add_argument("--sa-report-limit", "-l", default=50, help="Report limit")

    parser.add_argument(
        "--sa-report-output",
        "-o",
        default=os.getenv("SA_REPORT_OUTPUT", "/tmp/io_report.html"),
        help="Report Output",
    )
    args = parser.parse_args()

    snapshot_path = args.sa_report_snapshot_root

    if snapshot_path is None:
        raise Exception("Snapshot Path ( SA_REPORT_SNAPSHOT_PATH ) must be supplied")

    host, database = get_host_and_database(snapshot_path)

    start_time = args.sa_report_start_time
    end_time = args.sa_report_end_time
    start_time = (
        datetime.strptime(start_time, "%m/%d/%Y %H:%M:%S")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )
    end_time = (
        datetime.strptime(end_time, "%m/%d/%Y %H:%M:%S")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )
    limit = int(args.sa_report_limit)
    output = args.sa_report_output

    return host, database, start_time, end_time, limit, output, snapshot_path


def get_host_and_database(snapshot_path):
    host = snapshot_path.split("host=")[1].split(os.path.sep)[0]
    database = (
        snapshot_path.split("host=")[1].split(os.path.sep)[1].split("database=")[1]
    )
    return host, database


def set_delta(df, column, groupby_column):
    prev_col_name = "prev_" + column
    delta_col_name = "delta_" + column

    df[prev_col_name] = df.groupby(groupby_column)[column].shift(1)
    df[delta_col_name] = df[column] - df[prev_col_name]
    df[delta_col_name] = df[delta_col_name].fillna(0)

    return df


def get_from_s3(prefix, bucket, start_time, end_time):
    s3 = boto3.resource("s3")
    _bucket_ = s3.Bucket(bucket)

    for object_summary in _bucket_.objects.filter(Prefix=prefix):
        file_epoch = int(object_summary.key.split("/")[-1].split("_")[0])
        if file_epoch >= start_time and file_epoch <= end_time:
            file_path = "s3://{}/{}".format(bucket, object_summary.key)
            yield pd.read_csv(file_path)


def get_from_local(directory, start_time, end_time):
    file_list = []
    for file in glob.glob(directory):
        file_epoch = int(file.split(os.path.sep)[-1].split("_")[0])
        if file_epoch >= start_time and file_epoch <= end_time:
            file_list.append({"timestamp": int(file_epoch), "file_name": file})
    df = pd.DataFrame(file_list)

    if df.empty:
        return

    for file in df.sort_values("timestamp")["file_name"]:
        yield pd.read_csv(set_path_for_platform(file))


def get_stat(snapshot_path, stat, start_time, end_time):
    if snapshot_path.lower().split("s3://")[0] == "":
        bucket = snapshot_path.lower().split("s3://")[1].split("/")[0]
        host, database = get_host_and_database(snapshot_path)
        prefix = "host={}/database={}/stat={}".format(host, database, stat)

        df_list = []
        for df in get_from_s3(prefix, bucket, start_time, end_time):
            df_list.append(df)

        if df_list == []:
            raise Exception("No snapshots found")

        df = pd.concat(df_list)

        df["snapshot_timestamp"] = (
            pd.to_datetime(df["snapshot_time"]).values.astype(np.int64)
            // 10 ** 6
            / 1000
        )

        return df
    else:
        directory = snapshot_path + "{}stat={}{}*{}*{}*{}*{}*{}*".format(
            os.path.sep,
            stat,
            os.path.sep,
            os.path.sep,
            os.path.sep,
            os.path.sep,
            os.path.sep,
            os.path.sep,
        )
        df_list = []
        for df in get_from_local(directory, start_time, end_time):
            df_list.append(df)

        if df_list == []:
            raise Exception("No snapshots found")

        df = pd.concat(df_list)
        df = df.sort_values(["snapshot_time"])

        df["snapshot_timestamp"] = (
            pd.to_datetime(df["snapshot_time"]).values.astype(np.int64)
            // 10 ** 6
            / 1000
        )

        return df

# Analytic Function Helpers


def get_ratio(b, a):
    if b == 0:
        return 100

    rt = round((a / (a + b) * 100), 2)

    if rt == 0:
        return 0
    else:
        return rt


def divide(b, a):
    if b == 0:
        b = 1
    return round((a / b), 2)


def get_percentage(b, a):
    if b == 0:
        b = 1
    return round((a / b) * 100, 2)


def blocks_to_bytes(a):
    return a * 8192


def convert_bytes(size):
    for x in ["bytes", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0

    return size
