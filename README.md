# StatsAnalyzer

Statsanalyzer is a tool to enable the collection, storing and reporting on Postgres workload metrics.

The collected statistics allow DBAs and developers to effectively generate useful insights from the collected metrics.
Statsanalyzer can be scheduled in continuous collection mode or on-demand.

[Supported Versions](#supported-versions)

[Getting Started](#getting-started)

[Start Using for Postgres on RDS](#start-using-for-postgres-on-rds)

<h2 id="supported-versions">Supported Versions</h2>

Postgres 10 and higher

<h2 id="getting-started">Getting Started</h2>

### Download Executables
[Go here](https://github.com/samimseih/statsanalyzer/releases/tag/latest) to download Executables for AL2, Macos or Windows 64bit.

Alternatively, follow the steps below to build the executables from source.
### Building from Source

It is recommended to build the executables for your platform using the steps below.

1. #### [Install Python3.8 or Higher](https://www.python.org/downloads/) 
2. #### Build For your platform
- #### For Amazon Linux 2 or MacOS
```
python -m venv statsanalyzer_runtime
. statsanalyzer_runtime/bin/activate
git clone https://github.com/samimseih/statsanalyzer
cd statsanalyzer
./build.sh 
```
- #### For Windows
```
python -m venv statsanalyzer_runtime
statsanalyzer_runtime\Scripts\activate.bat
git clone https://github.com/samimseih/statsanalyzer
cd statsanalyzer
build.bat
```
3. Executables will be located in a directory called **dist**
```
dist
├── capture
├── report
└── snapper_rds
```
<h2 id="start-using-for-postgres-on-rds">Start Using For Postgres on AWS/RDS</h2>

To start using StatsAnalyzer on an AWS Postgres RDS instance, including Aurora Postgres, follow the steps below:

#### 1. Create the monitoring user on the database. The user must be part of the ```pg_monitor``` role

```
postgres=> create user statscollector password 'MySecretPassword';
CREATE ROLE
postgres=> grant pg_monitor to statscollector ;
GRANT ROLE
postgres=> create extension pg_stat_statements;
CREATE EXTENSION
```

#### 2. Configure the AWS client 
Configure the AWS client to use the snapper_rds utility, to deploy the configuration in SecretsManager or to store snapshots in S3.
```
aws configure --profile snapshotprofile
```

```AWS Access Key ID``` and ```AWS Secret Access Key``` are the credentials to the AWS account that will be given read permissions to a SecretManager secret and read/write permissions to the S3 bucket.


#### 3. Generate Snapshots and Reports
There are multiple methods to generate snapshots and reports. These are the **snapper_rds** utility or **scheduled** using cron.

[A sample report can be found here](https://htmlpreview.github.io/?https://github.com/samimseih/statsanalyzer/blob/master/samples/report.html)


<details>
  <summary><b>snapper_rds</b> is intended to be used for real-time reporting. The utility generates snapshots and a report in a single run. This method is intended for a users who do not wish to maintain snapshots long term. snapper_rds currently only supports AWS/RDS insatnces.</summary>

```
usage: snapper_rds [-h] [-i I] [-U U] [-P P] [--sa-snapper-snapshot-root SA_SNAPPER_SNAPSHOT_ROOT]
                         [--sa-snapper-database-list SA_SNAPPER_DATABASE_LIST]
                         [--sa-snapper-report-output-dir SA_SNAPPER_REPORT_OUTPUT_DIR]
                         [--sa-snapper-no-snapshots SA_SNAPPER_NO_SNAPSHOTS]
                         [--sa-snapper-snapshots-interval SA_SNAPPER_SNAPSHOTS_INTERVAL]

optional arguments:
  -h, --help            show this help message and exit
  -i I                  List of rds instances
  -U U                  stats database user. Default is the environment variable PGUSER
  -P P                  stats database user password. Default is the environment variable PGPASSWORD
  --sa-snapper-snapshot-root SA_SNAPPER_SNAPSHOT_ROOT, -r SA_SNAPPER_SNAPSHOT_ROOT
                        Snapshot Root path
  --sa-snapper-database-list SA_SNAPPER_DATABASE_LIST, -d SA_SNAPPER_DATABASE_LIST
                        List of Databases to snapshot
  --sa-snapper-report-output-dir SA_SNAPPER_REPORT_OUTPUT_DIR, -o SA_SNAPPER_REPORT_OUTPUT_DIR
                        List of Databases to snapshot
  --sa-snapper-no-snapshots SA_SNAPPER_NO_SNAPSHOTS, -sn SA_SNAPPER_NO_SNAPSHOTS
                        Number of snapshots. Default is 2
  --sa-snapper-snapshots-interval SA_SNAPPER_SNAPSHOTS_INTERVAL, -si SA_SNAPPER_SNAPSHOTS_INTERVAL
                        Interval between snapshots in seconds. Default is 30 seconds
 ```
For example, to report on the instances in the Aurora cluster "demo1". In this example, 6 snapshots will be taken at 10 second intervals. The output is the location of the HTML report summarizing the snapshots.
 
 ![Alt text](images/rds_screenshot.png?raw=true "Title")

 ```
 export AWS_PROFILE=snapshotprofile
./snapper_rds \
    -i demo1-instance-1,demo1-instance-1-us-east-1a \
    -U statscollector \
    -P MySecretPassword \
    -r /tmp \
    -d demodb1 \
    -o $HOME/Downloads \
    -sn 6 \
    -si 10
...
......
.........
  
*** list of generated reports:
/Users/simseih/Downloads/demo1-instance-1.abcdefghijk.us-east-1.rds.amazonaws.com_demodb1_07_24_2021_10_55_22.html
/Users/simseih/Downloads/demo1-instance-1-us-east-1a.abcdefghijk.us-east-1.rds.amazonaws.com_demodb1_07_24_2021_10_55_22.html

run "rm -rf /tmp/4eaafb3a-a8ac-4c11-8cee-91193ed5642c" to remove snapshot files
```
 </details>
 
 <details>
  <summary><b>scheduled</b> is intended to be used for a long-term capturing of statistics data.</summary>

The capture utility is used to capture the snapshots. The general guideline is to run at 60 minutes intervals. 

i.e. In this example cron is used.
```
*/60 * * * * $HOME/Downloads/capture -m aws_secretsmanager -c prod/cluster1
```

The report utility is used to report on the snapshots.

```
./report \
-r /tmp/pgsnapshots/host=demo1-instance-1.abcdefghijk.us-east-1.rds.amazonaws.com/database=demodb1/ \
-o $HOME/Downloads/report.html
```

In order to use the capture utility, a confirguration file must be created. The configuration is in JSON format and can be stored locally or in AWS/SecretsManager

  <b>Configuration Json Document</b>
  i.e.
```
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
}

```
example of a configuration stored in AWS/SecretsManager
 ![Alt text](images/secret.png?raw=true "Title")
  
  <b>Capture Utility</b>
```
usage: capture.py [-h] [--sa-ssl-cert SA_SSL_CERT] [--sa-config-store-method SA_CONFIG_STORE_METHOD] [--sa-config SA_CONFIG]
                  [--aws_region AWS_REGION] [--driver DRIVER] [--stats-to-run STATS_TO_RUN]

A Utility to Capture Postgres table-level statistics

optional arguments:
  -h, --help            show this help message and exit
  --sa-ssl-cert SA_SSL_CERT, -ssl SA_SSL_CERT
                        SSL Certificate Path to the Postgres instance. Default value: None
  --sa-config-store-method SA_CONFIG_STORE_METHOD, -m SA_CONFIG_STORE_METHOD
                        SSL Certificate Path to the Postgres instance.
                        Accepted Values: local_config, aws_secretsmanager.
                        Default Value: local_config
  --sa-config SA_CONFIG, -c SA_CONFIG
                        Location of the Configuration file.
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
                        }
  --aws_region AWS_REGION, -r AWS_REGION
                        AWS Region of the SecretsManager.
                        Default value: us-east-1
  --driver DRIVER, -d DRIVER
                        Default SQLAlchemy driver.
                        Default value: postgresql+pg8000
  --stats-to-run STATS_TO_RUN, -s STATS_TO_RUN
                        A comma seperated list of stats to run
```
  <b>Report Utility</b>
```
usage: report.py [-h] [--sa-report-snapshot-root SA_REPORT_SNAPSHOT_ROOT] [--sa-report-start-time SA_REPORT_START_TIME]
                 [--sa-report-end-time SA_REPORT_END_TIME] [--sa-report-limit SA_REPORT_LIMIT] [--sa-report-output SA_REPORT_OUTPUT]

A Utility to Generate an I/O report

optional arguments:
  -h, --help            show this help message and exit
  --sa-report-snapshot-root SA_REPORT_SNAPSHOT_ROOT, -r SA_REPORT_SNAPSHOT_ROOT
                        Snapshot Root path
  --sa-report-start-time SA_REPORT_START_TIME, -s SA_REPORT_START_TIME
                        Report start time
  --sa-report-end-time SA_REPORT_END_TIME, -e SA_REPORT_END_TIME
                        Report end time
  --sa-report-limit SA_REPORT_LIMIT, -l SA_REPORT_LIMIT
                        Report limit
  --sa-report-output SA_REPORT_OUTPUT, -o SA_REPORT_OUTPUT
                        Report Output
```
 </details>

 
## License

MIT License

Copyright (c) 2021 samimseih

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

