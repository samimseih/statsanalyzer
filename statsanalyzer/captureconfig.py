import argparse
import os

parser = argparse.ArgumentParser(
    description="A Utility to Capture Postgres table-level statistics",
    formatter_class=argparse.RawTextHelpFormatter,
)
parser.add_argument(
    "--sa-ssl-cert",
    "-ssl",
    default=os.getenv("SA_SSL_CERT", None),
    help="SSL Certificate Path to the Postgres instance. Default value: None",
)
parser.add_argument(
    "--sa-config-store-method",
    "-m",
    default=os.getenv("SA_CONFIG_STORE_METHOD", "local_config"),
    help="""SSL Certificate Path to the Postgres instance.
Accepted Values: local_config, aws_secretsmanager.
Default Value: local_config""",
)
parser.add_argument(
    "--sa-config",
    "-c",
    help="""Location of the Configuration file.
If --sa-config-store-method/-m is local_config, supply the local path of the configuration file.
If --sa-config-store-method/-m is aws_secretsmanager, supply the AWS/SecretsManager secret name.
A Configuration is a Json Document with the following key/value pairs:
username: The Monitoring database user with the pg_monitor role
password: Password of the Monitoring database user
engine_type: postgresql of aurora-postgresql
engine_major_version: The major version of Postgres, i.e. 11 for Postgres 11
hosts: A list of hosts to run a capture for. The format is <hostname>/<port>
database_list: A list of databases to capture.
snapshot_root: A path to write the snapshots to, such as an s3:// path or a local path.
{
  	"username": "MyMonitoringUser",
 	"password": "MySecretPassword",
  	"hosts": [
    	"hostname.writer.mydomain.com:5432",
    	"hostname.reader.mydomain.com:5432",
  	],
  	"snapshot_root": "s3://mysnapshotpath",
  	"database_list": [
    	"mydb1"
  	],
  	"engine_major_version": engineVersion,
  	"engine_type": "engineType"
}""",
)
parser.add_argument(
    "--aws_region",
    "-r",
    default=os.getenv("AWS_REGION", "us-east-1"),
    help="""AWS Region of the SecretsManager. 
Default value: us-east-1""",
)
parser.add_argument(
    "--driver",
    "-d",
    default="postgresql+pg8000",
    help="""Default SQLAlchemy driver. 
Default value: postgresql+pg8000""",
)
parser.add_argument(
    "--stats-to-run",
    "-s",
    default=None,
    help="""A comma seperated list of stats to run""",
)
args = parser.parse_args()
