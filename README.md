# StatsAnalyzer

Statsanalyzer is a tool to enable the collection, storing and reporting on Postgres workload metrics.

The collected statistics allow DBAs and developers to effectively generate useful insights from the collected metrics.
Statsanalyzer can be scheduled in continuous collection mode or on-demand.

[Supported Versions](#supported-versions)

[Getting Started](#getting-started)

[Capturing Snapshots with Local Config File](#start-using-for-postgres-local)

[Capturing Snapshots with AWS/SecretsManager](#start-using-for-postgres-on-aws-rds-sm)

[Generating a Snapshot Report](#generate-report)

[Common Usage Example](#common-usage-example)

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

<h2 id="start-using-for-postgres-local">Capturing Snapshots with Local Config File</h2>

To start using StatsAnalyzer with a local config file:

#### 1. Create the monitoring user on the database. The user must be part of the ```pg_monitor``` role

```
postgres=> create user statscollector password 'MySecretPassword';
CREATE ROLE
postgres=> grant pg_monitor to statscollector ;
GRANT ROLE
postgres=> create extension pg_stat_statements;
CREATE EXTENSION
```

#### 2. Create a configuration file called /tmp/myconfig. In out example, the host is 127.0.0.1 ( a DNS name can also be supplied ) and the port the instance is listening on ( default Postgres 5432 ).
```
{
   "username":"statscollector",
   "password":"MySecretPassword",
   "hosts":[
      "127.0.0.1:5432"
   ],
   "snapshot_root":"/tmp/mypath",
   "database_list":[
      "postgres"
   ]
}
```

#### 3. Run the capture utility by supplying the ```/tmp/myconfig``` configuration file.
```
./capture -c /tmp/myconfig
```

<h2 id="start-using-for-postgres-on-aws-rds-sm">Capturing Snapshots with AWS/SecretsManager</h2>

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

#### 3. Create AWS/SecretsManeger Secret

The SecretManager JSON should include the following fields:

**username** : The username of the Database monitoring user.  the Step 1
**password** : The password of the Database monitoring user. Created in Step 1
**hosts** : The list of hosts to run a snapshot for. Providing a list is useful if you wish to take snapshots for read-replicas.
**snapshot_root**: The root to write the snapshot to. This value is only used by the **capture** utility.
**database_list**: List of databases on the Postgres cluster to take snapshots for.

```
{
  "username": "statscollector",
  "password": "MySecretPassword",
  "hosts": [
    "demo1-instance-1.abcdefghijk.us-east-1.rds.amazonaws.com:5432"
  ],
  "snapshot_root": "tmp",
  "database_list": [
    "demodb1"
  ]
}
```

Below is a sample Secret

![Alt text](images/secret.png?raw=true "Title")

<h2 id="generate-report">Generating a Snapshot Report</h2>

There are multiple methods to generate snapshots and reports. These are the **snapper_rds** utility or **scheduled** using cron.

A sample report can be found here: https://htmlpreview.github.io/?https://github.com/samimseih/statsanalyzer/blob/master/samples/report.html


<details>
  <summary><b>snapper_rds</b> is intended to be used for real-time reporting. The utility generates snapshots and a report in a single run. This method is intended for a users who do not wish to maintain snapshots long term. snapper_rds currently only supports AWS/RDS insatnces.</summary>

```
usage: snapper_rds.py [-h] [-i I] [-U U] [-P P] [-S S] [--sa-snapper-snapshot-root SA_SNAPPER_SNAPSHOT_ROOT]
                      [--sa-snapper-database-list SA_SNAPPER_DATABASE_LIST]
                      [--sa-snapper-report-output-dir SA_SNAPPER_REPORT_OUTPUT_DIR] [--sa-snapper-no-snapshots SA_SNAPPER_NO_SNAPSHOTS]
                      [--sa-snapper-snapshots-interval SA_SNAPPER_SNAPSHOTS_INTERVAL] [--sa-no-delete-snapshots SA_NO_DELETE_SNAPSHOTS]
                      [--aws_region AWS_REGION]

optional arguments:
  -h, --help            show this help message and exit
  -i I                  List of rds instances
  -U U                  stats database user. Default is the environment variable PGUSER
  -P P                  stats database user password. Default is the environment variable PGPASSWORD
  -S S                  SecretManager Secret Name
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
  --sa-no-delete-snapshots SA_NO_DELETE_SNAPSHOTS
                        Delete the snapshots. Default is False
  --aws_region AWS_REGION
                        AWS Region of the SecretsManager. Default value: us-east-1
 ```
For example, to report on the instances in the Aurora cluster "demo1". In this example, 6 snapshots will be taken at 10 second intervals. The output is the location of the HTML report summarizing the snapshots.

 In this example, the AWS/SecretsManager secret called **prod/cluster1** is used for snapper_rds
  
 ```
 export AWS_PROFILE=snapshotprofile
./snapper_rds -S prod/cluster1
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
 </details>

<h2 id="common-usage-example">Common Usage Example</h2>

Therere are a few ways to run StatsAnalyzer, but a very common and useful way is to generate a report in real-time. Below is an example of generating a report for a 60 second period using a configuration file called myconf created in the [Capturing Snapshots with Local Config File](#start-using-for-postgres-local) section of this guide.

```
./capture -c myconf && \
sleep 60 && \
./capture -c myconf && \
./report --sa-report-snapshot-root /tmp/mypath/host=127.0.0.1/database=postgres
```



 
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

