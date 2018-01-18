## Overview

backup db 1.0

- use dump file to backup
- default file suffix name *.sql*
- the backup file cannot to directly import, like Navicat

## Features

- [x] Python3
- [x] Multiple data sources, Mysql or Postgresql
- [x] Timing backup
- [x] Delete old files
- [x] Error Send Email

## Before

pip install apscheduler

## Config file backup.json

```json
{
    "backup":[
        {
            "dbType": "postgresql",
            "dbDumpPath": "/usr/local/Cellar/postgresql/9.6.3/bin/pg_dump",
            "host": "localhost",  // never used, can be ""
            "port": "5432", // never used, can be ""
            "dbName": "mydb",
            "user": "postgres",
            "password": "1234",
            "backupPath": "./backup_mydb",
            "backupFileName": "mydb"
        },
        {
            "dbType": "mysql",
            "dbDumpPath": "/usr/local/mysql/bin/mysqldump",
            "host": "localhost", // never used, can be ""
            "port": "3306", // never used, can be ""
            "dbName": "mydb2",
            "user": "root",
            "password": "1234",
            "backupPath": "./backup_mydb2",
            "backupFileName": "mydb2"
        }
    ],
    "backupEveryDaysHours": "0,12", // fixed hour of every day , many can use "," interval
    "deleteBackupDaysAgo": 30, // delete the file 30 days ago
    "addressee": [   // addressee list
        "xxx@xxx.com"
    ],
    "addresser": {
        "server": "smtp.xxx.com",  // smtp server
        "sslPort": "465", // default ssl port
        "user": "xxx@xxx.com",
        "password": "",
        "allow": false  // allow send email
    }
}
```
## Quick Start

> python3 backup_db.py