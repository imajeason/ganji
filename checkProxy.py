#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#-------------------------------------------------------------------------
#   程序：referer_forge.py
#   版本：0.1
#   作者：ly
#   日期：编写日期2016/11/10
#   语言：Python 2.7.x
#   操作：python referer_forge.py
#   功能：从www.gatherproxy.com网站采集代理信息并存入数据库
#-------------------------------------------------------------------------
import re
import time, sys
from threading import Thread, Lock
from Queue import Queue
from splinter import Browser
from pyvirtualdisplay import Display
from multiprocessing import Pool
from pymongo import MongoClient

import random

client = MongoClient('localhost', 27017)
ganjiDB = client['ganjiwang']
linklists = ganjiDB['linklists']
detailinfo = ganjiDB['detailinfo']
import logging,datetime
import signal,os

from main import detailinfo,errorurl,iproxy


# --------------------------------------------------
# 中文编码设置
reload(sys)
sys.setdefaultencoding('utf-8')
Type = sys.getfilesystemencoding()


#获取全部代理
proxyList = iproxy.find({"status":0})
for proxy in proxyList:
    proxy = proxy["iproxy"]
    #print proxy["iproxy"]
    url = "http://bj.ganji.com"
    display = Display(visible=0, size=(800, 800))
    display.start()

    ip, port = proxy.split(":")
    proxy_settings = {'network.proxy.type': 1,
                      'network.proxy.no_proxies_on': '172.0.0.0/8,10.0.0.0/8,localhost,127.0.0.0/8,::1',
                      'network.proxy.http': ip, 'network.proxy.http_port': port,
                      'network.proxy.ssl': '172.1.1.1', 'network.proxy.ssl_port': 8080}
    print "代理:%s:%s，正在处理%s" % (ip, port, url)
    logging.info('代理:%s:%s，正在处理%s' % (ip, port, url))
    try:
        #browser = Browser(driver_name="firefox")
        browser = Browser(driver_name="firefox", profile_preferences=proxy_settings, timeout=40)
        contentList = {}
        browser.visit(url)
        time.sleep(5)
        # browser.execute_script(clickLog('m-my_login_login_tab'))
        title = browser.title
        print title.encode('utf-8')

        #获取该代理成功使用的次数
        #detailinfo.find_one({"url": url})
        
    except:
        print "%s 代理错误啊，删了吧" % proxy

    try:
        browser.quit()
    except:
        pass
    display.stop()