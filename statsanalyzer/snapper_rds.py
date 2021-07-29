import boto3
import time
import os
import uuid
import argparse
import sys
import shutil
import util
import concurrent.futures
from datetime import datetime
from pathlib import Path

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

parser.add_argument(
    "-S",
    help="SecretManager Secret Name",
)

parser.add_argument(
    "--sa-snapper-snapshot-root", "-r", help="Snapshot Root path", default=Path.cwd()
)

parser.add_argument(
    "--sa-snapper-database-list", "-d", help="List of Databases to snapshot"
)

parser.add_argument(
    "--sa-snapper-report-output-dir",
    "-o",
    help="List of Databases to snapshot",
    default=Path.cwd(),
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

parser.add_argument(
    "--sa-no-delete-snapshots",
    action='store_true',
    help="Delete the snapshots.",
)

parser.add_argument(
    "--aws_region",
    default=os.getenv("AWS_REGION", "us-east-1"),
    help="""AWS Region of the SecretsManager. Default value: us-east-1""",
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


if args.S:
    import AWS

    config = CONFIG = AWS.get_secret(args.S, args.aws_region)
    config["snapshot_root"] = snapshot_root
    database_list = config["database_list"]
    hosts = config["hosts"]
else:

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

(
    connections,
    snapshot_root,
    sql_doc,
    search_path,
    search_path_len,
    statement_timeout,
    stats_to_run,
) = capture.main(config)


def _capture_(
    connection,
    snapshot_root,
    sql_doc,
    search_path,
    search_path_len,
    statement_timeout,
    stats_to_run,
    snapshots,
    sleep,
):

    for x in range(snapshots):
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


threads = []

with concurrent.futures.ThreadPoolExecutor(max_workers=len(connections)) as pool:
    for connection in connections:
        threads.append(
            pool.submit(
                _capture_,
                connection,
                snapshot_root,
                sql_doc,
                search_path,
                search_path_len,
                statement_timeout,
                stats_to_run,
                snapshots,
                sleep,
            )
        )

print("Done capturing snapshots")
print("Generating reports")

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

if args.sa_no_delete_snapshots is True:
    print("""\n\nrun "rm -rf {}" to remove snapshot files""".format(snapshot_root))
else:
    print("removing {}".format(snapshot_root))
    shutil.rmtree(util.set_path_for_platform(snapshot_root))
