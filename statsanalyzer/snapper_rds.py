import boto3
import time
import os
import uuid
import argparse
import sys
from datetime import datetime


parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument("-i", help="List of rds instances")

parser.add_argument(
    "-U",
    default=os.getenv("PGUSER", None),
    help="stats database user. Default is the environment variable PGUSER",
)

parser.add_argument(
    "-P",
    default=os.getenv("PGPASSWORD", None),
    help="stats database user password. Default is the environment variable PGPASSWORD",
)

parser.add_argument("--sa-snapper-snapshot-root", "-r", help="Snapshot Root path")

parser.add_argument(
    "--sa-snapper-database-list", "-d", help="List of Databases to snapshot"
)

parser.add_argument(
    "--sa-snapper-report-output-dir", "-o", help="List of Databases to snapshot"
)

parser.add_argument(
    "--sa-snapper-no-snapshots",
    "-sn",
    default=2,
    help="Number of snapshots. Default is 2",
)

parser.add_argument(
    "--sa-snapper-snapshots-interval",
    "-si",
    default=30,
    help="Interval between snapshots in seconds. Default is 30 seconds",
)

args = parser.parse_args()
sys.argv = [sys.argv[0]]

# we delay the import until after the arg parsing to avoid the help option showing the capture help menu
import capture
import report

now = datetime.now()
date_time = now.strftime("%m_%d_%Y_%H_%M_%S")

instances = args.i
username = args.U
password = args.P
snapshot_root = args.sa_snapper_snapshot_root
snapshot_root = os.path.join(snapshot_root, str(uuid.uuid4()))
databases = args.sa_snapper_database_list
report_output = args.sa_snapper_report_output_dir
snapshots = int(args.sa_snapper_no_snapshots)
sleep = int(args.sa_snapper_snapshots_interval)

config = {}
hosts = []
instance_list = instances.split(",")

client = boto3.client("rds")

for instance in instance_list:
    response = client.describe_db_instances(DBInstanceIdentifier=instance)
    dbi = response.get("DBInstances")[0]
    engine_type = dbi.get("Engine")
    if engine_type == "postgres":
        engine_type = "postgresql"
    port = str(dbi.get("Endpoint").get("Port"))
    hosts.append(dbi.get("Endpoint").get("Address") + ":" + port)
    engine_major_version = dbi.get("EngineVersion").split(".")[0]
    database_list = databases.split(",")

config.update(
    {
        "username": username,
        "password": password,
        "hosts": hosts,
        "snapshot_root": snapshot_root,
        "database_list": database_list,
        "engine_major_version": engine_major_version,
        "engine_type": engine_type,
    }
)

for x in range(0, snapshots):
    (
        connections,
        snapshot_root,
        sql_doc,
        search_path,
        search_path_len,
        statement_timeout,
        stats_to_run,
    ) = capture.main(config)
    for connection in connections:
        capture.snapshot(
            connection,
            snapshot_root,
            sql_doc,
            search_path,
            search_path_len,
            statement_timeout,
            stats_to_run,
        )
    time.sleep(sleep)

list_of_out = []

for database in database_list:
    for host in hosts:
        host = host.split(":")[0]
        snapshot_root_database = os.path.join(
            snapshot_root, "host=" + host, "database=" + database
        )
        file = os.path.join(
            report_output, host + "_" + database + "_" + date_time + ".html"
        )
        list_of_out.append(file)
        report.main(snapshot_root_database, file)

print("\n\n*** list of generated reports:")
for out in list_of_out:
    print(out)

print("""\n\nrun "rm -rf {}" to remove snapshot files""".format(snapshot_root))
