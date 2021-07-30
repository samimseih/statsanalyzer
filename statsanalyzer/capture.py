import os
import ssl
import uuid
import json
import util
from captureconfig import args as cargs
from pathlib import Path
import AWS
from pandas import read_sql
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
import sqlalchemy
from datetime import timezone


def connect(connection_url, search_path, search_path_len, statement_timeout):
    # Create SSL Context
    ssl_context = ssl.SSLContext()
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    # Load appropriate Cert
    cadata = AWS.get_rds_cert()

    # if the user did not pass a cert, disable CERT_REQUIRED mode
    if cadata is None:
        ssl_context.verify_mode = ssl.CERT_NONE
        print("WARNING: SSL may not be used for the connection!")
    else:
        ssl_context.load_verify_locations(cadata)

    url = URL.create(**connection_url)

    # establish the connection
    if cadata is None:
        engine = create_engine(url)
    else:
        engine = create_engine(url, connect_args={"ssl_context": ssl_context})

    connection = engine.connect()

    # set some reasonable and safe limits to the session
    connection.execute("SET TRANSACTION READ ONLY")
    if statement_timeout is None:
        statement_timeout = 10000
    connection.execute("set statement_timeout={}".format(statement_timeout))
    connection.execute("set idle_in_transaction_session_timeout=20000")
    if search_path_len > 0:
        connection.execute(search_path)

    return connection


def snapshot(
    connection,
    snapshot_root,
    sql_doc,
    search_path,
    search_path_len,
    statement_timeout,
    stat_to_run=[],
):
    print(
        "running next snapshot {}{}{}".format(
            connection.get("host"), "/", connection.get("database")
        )
    )

    """"
	First, grab the connection
	"""
    _connection_ = connect(connection, search_path, search_path_len, statement_timeout)

    """"
	Second, Loop through all the stats to collect. 
	"""
    if stat_to_run == []:
        stat_to_run = list(sql_doc.keys())

    for stat in sql_doc:
        if stat in stat_to_run:
            print("... running next stat {}".format(stat))
            sql = sql_doc[stat]["sql"]

            """ Get the snapshot data in a single transaction """
            _connection_.execute("begin")
            snapshot_time = _connection_.execute(
                "select now() at time zone 'utc' as snapshot_time"
            ).fetchall()[0][0]
            snapshot_time_epoch = int(
                snapshot_time.replace(tzinfo=timezone.utc).timestamp()
            )
            pd = read_sql(sql, _connection_)
            pd.insert(0, "snapshot_time", snapshot_time)
            _connection_.execute("commit")

            parent_directory = "{snapshot_root}/host={host}/database={database}/stat={stat}/year={year}/month={month}/day={day}/hour={hour}/minute={minute}".format(
                snapshot_root=snapshot_root,
                host=connection.get("host"),
                database=connection.get("database"),
                stat=stat,
                month=snapshot_time.month,
                day=snapshot_time.day,
                year=snapshot_time.year,
                hour=snapshot_time.hour,
                minute=snapshot_time.minute,
            )

            """
		  if not s3 path, precreate the parent directory
		  """

            if not snapshot_root.lower().split("s3://")[0] == "":
                filesep = os.path.sep
                print(".... creating parent directory {}".format(parent_directory))
                parent_directory = Path(util.set_path_for_platform(parent_directory))
                parent_directory.mkdir(parents=True, exist_ok=True)
            else:
                filesep = "/"

            full_file_name = "{parent_directory}{filesep}{snapshot_time_epoch}_{file_name}.csv.gz".format(
                parent_directory=parent_directory,
                filesep=filesep,
                snapshot_time_epoch=snapshot_time_epoch,
                file_name=uuid.uuid4(),
            )
            print(".... writing snapshot {}".format(full_file_name))

            pd.to_csv(full_file_name, compression="gzip", index=False)


def main(config=None):

    connections = []

    stats_to_run = config_store_method = cargs.stats_to_run
    if stats_to_run is None:
        stats_to_run = []
    else:
        stats_to_run = stats_to_run.split(",")

    config_store_method = cargs.sa_config_store_method
    sa_config = cargs.sa_config
    aws_region = cargs.aws_region
    if sa_config is None and config is None:
        raise Exception("A path to a configuration must be passed")
    if config_store_method == "aws_secretsmanager":
        CONFIG = AWS.get_secret(sa_config, aws_region)
    elif config_store_method == "local_config":
        if config:
            CONFIG = config
        else:
            with open(sa_config) as f:
                CONFIG = json.load(f)
    else:
        raise Exception("Invalid Config Store Method")

    """ 
	Load all the necessary keys from the config
	"""
    username = CONFIG["username"]
    password = CONFIG["password"]
    drivername = cargs.driver
    hosts = CONFIG["hosts"]
    snapshot_root = CONFIG["snapshot_root"]
    database_list = CONFIG["database_list"]
    # search path
    search_path_len = 0
    search_path = None
    try:
        search_path = CONFIG["search_path"]
        search_path_len = len(search_path)
        search_path = "set search_path=" + ",".join(search_path)
    except KeyError:
        pass
    # statement timeout
    statement_timeout = None
    try:
        statement_timeout = CONFIG["statement_timeout"]
    except KeyError:
        pass

    """
	Load all the endpoints
	"""

    for host in hosts:
        for database in database_list:
            connections.append(
                {
                    "username": CONFIG.get("username"),
                    "drivername": drivername,
                    "host": host.split(":")[0],
                    "port": host.split(":")[1],
                    "database": database,
                    "password": CONFIG.get("password"),
                }
            )

    found_engine_types = []
    found_major_versions = []
    for c in connections:
        _connection_ = connect(c, search_path, search_path_len, statement_timeout)
        pd = read_sql("select version()", _connection_)
        engine_major_version = int(pd.iloc[0]["version"].split(" ")[1].split(".")[0])

        engine_type = "aurora-postgresql"

        try:
            read_sql("select aurora_version()", _connection_)
        except sqlalchemy.exc.ProgrammingError as e:
            """42883 is Postgres Error code for undefined_function """
            if int(json.loads(str(e.__dict__["orig"]).replace("'", '"')).get('C')) == 42883:
                engine_type = "postgresql"
            else:
                raise
        found_engine_types.append(engine_type)
        found_major_versions.append(engine_major_version)

    etl = list(dict.fromkeys(found_engine_types))
    mvl = list(dict.fromkeys(found_major_versions))

    if len(etl) > 1 or len(mvl) > 1:
        raise Exception("Snapshot configuration includes instances of different engine types or major versions")

    """
	Load the SQL class based on engine type 
	"""
    if engine_type == "aurora-postgresql":
        from SQL import APG as sql
    elif engine_type == "postgresql":
        from SQL import CPG as sql
    else:
        raise Exception("Invalid engine_type {}", engine_type)

    """
	Load the SQL Doc from the SQL class based on engine version
	"""
    not_supported_errm = "version {} is not supported for {}"

    if engine_major_version == 10:
        sql_doc = sql.v10
    elif engine_major_version == 11:
        sql_doc = sql.v11
    elif engine_major_version == 12:
        sql_doc = sql.v12
    elif engine_major_version == 13:
        sql_doc = sql.v13
    elif engine_major_version == 14:
        sql_doc = sql.v14
    elif engine_major_version == 15:
        sql_doc = sql.v15

    """
	pass back the connections and the sql doc to process 
	"""
    return (
        connections,
        snapshot_root,
        sql_doc,
        search_path,
        search_path_len,
        statement_timeout,
        stats_to_run,
    )

# Program Entry Point
if __name__ == "__main__":
    (
        connections,
        snapshot_root,
        sql_doc,
        search_path,
        search_path_len,
        statement_timeout,
        stats_to_run,
    ) = main()
    for connection in connections:
        snapshot(
            connection,
            snapshot_root,
            sql_doc,
            search_path,
            search_path_len,
            statement_timeout,
            stats_to_run,
        )
