#!/opt/python3.5/bin/python3.5
# -*- coding: utf-8 -*-
#

import re

import threading
import subprocess
import queue
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import Column, String, INTEGER, SMALLINT, DATETIME, create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool

Base = declarative_base()
MAX_THREAD_NUM = 30  # set maximal thread num, proposed value is 20~30
ZONE_FLAG = 'KS-' + datetime.now().strftime("%Y-%m-%d")


class IPMICheckerThread(threading.Thread):
    """ customer thread class
    """
    def __init__(self, worker):
        super(IPMICheckerThread, self).__init__()
        self.worker = worker

    def run(self):
        self.worker()


class IPMI_CHECK_RESULT(Base):

    __tablename__ = 'ipmi_check_result'
    id = Column(INTEGER, primary_key=True, nullable=False, autoincrement=True)
    ipmi_ip = Column(String(15), nullable=False)
    status_code = Column(SMALLINT, default=-1)
    ipmi_cmd = Column(String(255))
    output = Column(String(255))
    date = Column(DATETIME)
    zone_flag = Column(String(64))


class IPMIChecker:

    def __init__(self, username=r'ADMIN', password=r'ADMIN'):
        self.username = username
        self.password = password
        self.p = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
        self.ips = list()
        self.mysql = r'mysql+mysqlconnector://ipmi:IPMI_CHECK@localhost:3306/ipmi_check'
        self.queue = queue.Queue()

    @contextmanager
    def db_session(self):
        db = create_engine(self.mysql, convert_unicode=True, poolclass=NullPool)
        conn = db.connect()
        session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=db))
        yield session
        session.close()
        conn.close()

    def do_action(self, ip, lan):
        """ worker function
        """
        ipmi_cmd_prefix = r'ipmitool -U ' + self.username + ' -P ' + self.password + ' -H ' + ip + lan
        ipmi_check_cmd = '-'
        rtcode = 0
        try:
            ipmi_action = r' fru print'
            ipmi_check_cmd = ipmi_cmd_prefix + ipmi_action
            output = subprocess.check_output(args=ipmi_check_cmd, stderr=subprocess.STDOUT, shell=True, timeout=180)
        except subprocess.CalledProcessError as e:
            try:
                ipmi_action = r' sdr elist'
                ipmi_check_cmd = ipmi_cmd_prefix + ipmi_action
                output = subprocess.check_output(args=ipmi_check_cmd, stderr=subprocess.STDOUT, shell=True, timeout=180)
            except subprocess.CalledProcessError as e:
                try:
                    ipmi_action = r' user list'
                    ipmi_check_cmd = ipmi_cmd_prefix + ipmi_action
                    output = subprocess.check_output(args=ipmi_check_cmd, stderr=subprocess.STDOUT, shell=True, timeout=180)
                except subprocess.CalledProcessError as e:
                    try:
                        ipmi_action = r' lan print'
                        ipmi_check_cmd = ipmi_cmd_prefix + ipmi_action
                        output = subprocess.check_output(args=ipmi_check_cmd, stderr=subprocess.STDOUT, shell=True, timeout=180)
                    except subprocess.CalledProcessError as e:
                        output = e.output
                        rtcode = e.returncode
                    except subprocess.TimeoutExpired as e:
                        rtcode = -1
                        output = str(e)
                except subprocess.TimeoutExpired as e:
                    rtcode = -1
                    output = str(e)
            except subprocess.TimeoutExpired as e:
                rtcode = -1
                output = str(e)
        except subprocess.TimeoutExpired as e:
            rtcode = -1
            output = str(e)
        return dict(
            code = rtcode,
            cmd = ipmi_check_cmd,
            output = output
        )

    def do_ipmi_check(self):

        while not self.queue.empty():
            ip = self.queue.get()
            result = self.do_action(ip, r' -I lanplus')
            if result['code']:
                result = self.do_action(ip, r' -I lan')
                if result['code']:
                    result = self.do_action(ip, r'')

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.db_session() as db:
                db.add(IPMI_CHECK_RESULT(ipmi_ip=ip, status_code=result['code'], ipmi_cmd=result['cmd'], output=result['output'], date=now, zone_flag=ZONE_FLAG))
                db.commit()
                db.flush()

    def start(self):
        if not self.queue.empty():
            self.queue = queue.Queue()
        try:
            with open('hosts.txt', 'r') as fp:
                for line in fp.readlines():
                    line = line.strip()
                    self.ips.append(line)
        except IOError as e:
            print(e)
            return
        threads = list()
        for ip in self.ips:
            if not re.match(self.p, ip):
                print('%15s: Got an invalid ip address, continue...' % ip)
                continue
            self.queue.put(ip)

        ip_num = len(self.ips)
        print('Read %s ip address from hosts.txt.' % ip_num)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print('Here we start: %s' % now)
        thread_num = MAX_THREAD_NUM if ip_num > MAX_THREAD_NUM else ip_num
        for i in range(thread_num):
            thread = IPMICheckerThread(self.do_ipmi_check)
            thread.start()  # start thread...
            threads.append(thread)

        for thread in threads:
            thread.join()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print('Here we ended: %s' % now)

if __name__ == '__main__':
    rd = IPMIChecker()
    rd.start()

