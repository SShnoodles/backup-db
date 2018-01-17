#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2018/1/5 上午9:57
# @Author  : ssnoodles
# pip install apscheduler
import json
import os
import logging
import time
import datetime
from datetime import timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
import smtplib
import socket
from email.mime.text import MIMEText
from email.utils import formataddr

# log
LOG_FILE = "./backup.log"
# config path
CONFIG_PATH = "./backup.json"
# config key
BACKUP = "backup"
ADDRESSER = "addresser"

MYSQL = "mysql"
POSTGRESQL = "postgresql"
BACKUP_DB_TYPE = "dbType"
BACKUP_DB_DUMP_PATH = "dbDumpPath"
BACKUP_HOST = "host"
BACKUP_PORT = "port"
BACKUP_DB_NAME = "dbName"
BACKUP_USER = "user"
BACKUP_PASSWORD = "password"
BACKUP_BACKUP_PATH = "backupPath"
BACKUP_BACKUP_FILE_NAME = "backupFileName"

BACKUP_EVERY_DAYS_HOURS = "backupEveryDaysHours"
DELETE_DAYS_AGO = "deleteBackupDaysAgo"
ADDRESSEE = "addressee"

ADDRESSER_USER = "user"
ADDRESSER_PASSWORD = "password"
ADDRESSER_SERVER = "server"
ADDRESSER_SSLPORT = "sslPort"
ADDRESSER_Allow = "allow"


# scheduler
scheduler = BlockingScheduler()

# log config
handler = logging.FileHandler(LOG_FILE, "a", encoding="UTF-8")
formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)


# load config
def load_base_config():
    with open(CONFIG_PATH, "r") as configJson:
        config = json.load(configJson)
        backup = config[BACKUP]
        addresser = config[ADDRESSER]
        backupEveryDaysHours = config[BACKUP_EVERY_DAYS_HOURS]
        deleteDaysAgo = config[DELETE_DAYS_AGO]
        addressee = config[ADDRESSEE]
        logging.info("loading config...")
        return backup, backupEveryDaysHours, deleteDaysAgo, addressee, addresser

backup, backupEveryDaysHours, deleteDaysAgo, addressee, addresser = load_base_config()


# if dir does not exist, create it.
def check_path(backup_path):
    if not os.path.isdir(backup_path):
        os.makedirs(backup_path)


# backup db
def backup_db():
    now_time_file = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    for b in backup:
        check_path(b[BACKUP_BACKUP_PATH])
        if b[BACKUP_DB_TYPE] == MYSQL:
            cmd = '"{}" -u{} -p{} {} > "{}/{}_{}.sql"'.format(b[BACKUP_DB_DUMP_PATH], b[BACKUP_USER], b[BACKUP_PASSWORD], b[BACKUP_DB_NAME], b[BACKUP_BACKUP_PATH], b[BACKUP_BACKUP_FILE_NAME], now_time_file)
        elif b[BACKUP_DB_TYPE] == POSTGRESQL:
            cmd = '"{}" -U {} --inserts {} > "{}/{}_{}.sql"'.format(b[BACKUP_DB_DUMP_PATH], b[BACKUP_USER], b[BACKUP_DB_NAME], b[BACKUP_BACKUP_PATH], b[BACKUP_BACKUP_FILE_NAME], now_time_file)
        else:
            logging.warning("backup db type is not MYSQL or POSTGRESQL")
            return

        if os.system(cmd) == 0:
            logging.info("backup db success command => {}".format(cmd))
        else:
            if addresser[ADDRESSER_Allow]:
                if not send_mail('backup db failed!!!', 'backup {} db failed！'.format(','.join(names))):
                    logging.info('send email failed, title => {}, text => {}'.format('backup db failed!!!', 'backup {} db failed！'.format(','.join(names))))
            logging.error("backup db failed command => {}".format(cmd))


# delete backup files
def delete_backup():
    for b in backup:
        files = os.listdir(b[BACKUP_BACKUP_PATH])
        for f in files:
            path = os.path.join(b[BACKUP_BACKUP_PATH], f)
            file_names = f.split('_')
            time_str = file_names[file_names.__len__() - 1].replace(".sql", "")
            t = time.strptime(time_str, "%Y-%m-%d-%H-%M-%S")
            y, m, d = t[0:3]
            day_before = datetime.datetime.now() - timedelta(days=deleteDaysAgo)
            if datetime.datetime(y, m, d) < day_before:
                os.remove(path)
                logging.info("backup db file remove => {}".format(path))


# start scheduler
def start():
    scheduler.add_job(backup_db, 'cron', hour=backupEveryDaysHours)
    scheduler.add_job(delete_backup, 'cron', hour='0')
    scheduler.start()


# listen scheduler
def my_listener(event):
    if event.exception:
        logging.info('The job crashed :(, {}'.format(event.exception))
        names = []
        for b in backup:
            names.append(b[BACKUP_DB_NAME])

        if addresser[ADDRESSER_Allow]:
            if not send_mail('backup db failed!!!', 'backup {} db failed！'.format(','.join(names))):
                logging.info('send email failed, title => {}, text => {}'.format('backup db failed!!!', 'backup {} db failed！'.format(','.join(names))))
    else:
        logging.info('The job worked :)')


# get ip
def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        if s:
            s.close()
    return ip


# send email
def send_mail(title, text):
    text = '{} IP：{} Time：{}'.format(text, get_host_ip(), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    result = True
    try:
        msg = MIMEText(text, 'plain', 'utf-8')
        msg['From'] = formataddr(["backup", addresser[ADDRESSER_USER]])
        msg['Subject'] = title

        server = smtplib.SMTP_SSL(addresser[ADDRESSER_SERVER], addresser[ADDRESSER_SSLPORT])
        server.login(addresser[ADDRESSER_USER], addresser[ADDRESSER_PASSWORD])
        server.sendmail(addresser[ADDRESSER_USER], addressee, msg.as_string())
    except Exception as e:
        logging.info(e)
        result = False
    finally:
        if server:
            server.quit()
    return result


if __name__ == '__main__':
    scheduler.add_listener(my_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    start()

