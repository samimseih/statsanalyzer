# StatsAnalyzer

Statsanalyzer is a tool to enable the collection, storing and reporting on Postgres workload metrics.

The collected statistics allow DBAs and developers to effectively generate useful insights from the collected metrics.
Statsanalyzer can be scheduled in continuous collection mode or on-demand.

[Supported Versions](#supported-versions)

[Getting Started](#getting-started)

[Capturing Snapshots with Local Config File](#start-using-for-postgres-local)

[Capturing Snapshots with AWS/SecretsManager](#start-using-for-postgres-on-aws-rds-sm)

[Generating a Snapshot Report](#generate-report)

[Help Menu](#help-menu)


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
└── statsanalyzer
    ├── capture
    ├── report
    ├── < rest of the Python modules >
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
cd dist
./statsanalyzer/capture -c /tmp/myconfig
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

```
username : The username of the Database monitoring user.  the Step 1
password : The password of the Database monitoring user. Created in Step 1
hosts : The list of hosts to run a snapshot for. Providing a list is useful if you wish to take snapshots for read-replicas.
snapshot_root: The root to write the snapshot to. This value is only used by the **capture** utility.
database_list: List of databases on the Postgres cluster to take snapshots for.
```

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

Run a capture using the secrets manager. In the below example the name of the secret is ```prod/cluster1```

```
./statsanalyzer/capture -m aws_secretsmanager -c prod/cluster1
```

<h2 id="generate-report">Generating a Snapshot Report</h2>

There are multiple methods to generate snapshots and reports.

A sample report can be found here: https://htmlpreview.github.io/?https://github.com/samimseih/statsanalyzer/blob/master/samples/report.html

<summary><b>scripted</b> is intended to be used for a single snapshot window</summary>

```
cd dist; \
./statsanalyzer/capture -c myconf \
sleep 120
./statsanalyzer/capture -c myconf \
./statsanalyzer/capture -r <snapshot directory>
```
 
<summary><b>scheduled</b> is intended to be used for a long-term capturing of statistics data.</summary>

The capture utility is used to capture the snapshots. The general guideline is to run at 60 minutes intervals. 

i.e. In this example cron is used.
```
*/60 * * * * dist/statsanalyzer/capture -m aws_secretsmanager -c prod/cluster1
```

<summary><b>reporting</b> To report on a specific snapshot</summary>

```
dist/statsanalyzer/report \
-r /tmp/pgsnapshots/host=demo1-instance-1.abcdefghijk.us-east-1.rds.amazonaws.com/database=demodb1/ \
-o $HOME/Downloads/report.html
```

<h2 id="help-menu">Help Menu</h2>

For the help menu, use the ```--help``` flag:

```
./dist/statsanalyzer/capture --help
```

or

```
./dist/statsanalyzer/report --help
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

