# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'imajeason'

import subprocess
import sys, os
import datetime,time

def kill_crawler():
    cmd = 'ps -ef | grep firefox |grep -v grep'
    f = os.popen(cmd)
    txt = f.readlines()
    #print "gg"
    nowtime = datetime.datetime.now()
    #print nowtime
    for line in txt:
        colum = line.split()
        pid = colum[1]
        fid = colum[2]
        #print "进程id:%s 父进程id:%s" % (pid,fid)
        sidtime = colum[4]
        sidtime = "%s %s:00" % (nowtime.date(),sidtime)
        #print sidtime
        haverun =  nowtime - datetime.datetime.strptime(sidtime,"%Y-%m-%d %H:%M:%S")
        if haverun.seconds > 600:
            print haverun
            cmd = "kill -9 %d" % int(pid)
            rc = os.system(cmd)
            if rc == 0:
                print "stop \"%s\" success!!" % pid
            else:
                print "stop \"%s\" failed!!" % pid

    print "开始处理defunct"
    cmd2 = 'ps -ef | grep defunct |grep -v grep | grep firefox'
    f2 = os.popen(cmd2)
    txt = f2.readlines()

    for line in txt:
        colum = line.split()
        print colum
        pid = colum[1]
        fid = colum[2]
        print "进程id:%s 父进程id:%s" % (pid,fid)

        cmd3 = "kill -9 %d" % int(fid)
        rc = os.system(cmd3)
        if rc == 0:
            print "stop \"%s\" success!!" % fid
        else:
            print "stop \"%s\" failed!!" % fid


if __name__ == '__main__':

    # if not len(sys.argv) == 2:
    #     print u'输入要结束的任务编号，0代表停止所有'
        #sys.exit()
    # id = sys.argv[1]
    kill_crawler()

