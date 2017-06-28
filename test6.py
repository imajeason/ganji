# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'jerry'

import re
import time
from threading import Thread, Lock
from Queue import Queue
from splinter import Browser
from pyvirtualdisplay import Display
from multiprocessing import Pool
from pymongo import MongoClient

import random
from bs4 import BeautifulSoup

client = MongoClient('localhost', 27017)
ganjiDB = client['ganjiwang']
linklists = ganjiDB['linklists']
detailinfo = ganjiDB['detailinfo']

pagesAll = []
pagesDone = []


def getContent(url):
    try:
        content = detailinfo.find_one({"url": url})
        if content:
            print "跳过: %s"% url
            return None
    except:
        pass
    display = Display(visible=0, size=(800, 800))
    display.start()
    proxy_list = [
        'http://125.88.74.122%83',
        'http://113.18.193.5%8080',
        'http://113.18.193.7%8080',
        'http://120.92.3.127%90'
    ]
    ip, port = (random.choice(proxy_list)).split("%")
    proxy_settings = {'network.proxy.type': 1,
                      'network.proxy.no_proxies_on': '172.0.0.0/8,10.0.0.0/8,localhost,127.0.0.0/8,::1',
                      'network.proxy.http': ip, 'network.proxy.http_port': port,
                      'network.proxy.ssl': '172.1.1.1', 'network.proxy.ssl_port': 8080}
    print "当前代理:%s:%s" % (ip, port)
    browser = Browser(driver_name="firefox", profile_preferences=proxy_settings)

    print "正在处理：", url
    contentList = {}
    browser.visit(url)
    time.sleep(3)
    # browser.execute_script(clickLog('m-my_login_login_tab'))
    title = browser.title
    print title.encode('utf-8')
    #print browser.find_by_xpath('//*[@class="d-nav"]/ul/li[1]/a').click()

    browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul').find_by_text('点击查看完整号码').click()

    content = browser.html
    browser.quit()
    display.stop()


    soup = BeautifulSoup(content, 'lxml')
    print soup
    return "==============***************================"
"""
    p1 = re.compile('(\<\/?[^>]+\>)')
    p2 = re.compile('\s+|&nbsp;')
    #print content
    for j in content.html.split("</li>"):
        item = p2.sub(' ', p1.sub(' ', j.strip()))
        #print "item==========",item
        try:
            p3 = re.compile("：")
            item = re.sub(p3, "@", item.encode("utf-8"))
            #print "===================%s" % item
            k, v = item.split("@")
            contentList[k] = v
            print "%s:%s"% (k,v)
        except:
            pass

    if not contentList:
        content = browser.find_by_xpath('//*[@id="real_service_about"]/span')
        item = p2.sub(' ', p1.sub(' ', content.html))
        contentList['detail'] = item
        print item
    # browser.close()

    try:
        real_service_about = browser.find_by_xpath('//*[@id="real_service_about"]').html
        #print "real_service_about:%s" % real_service_about
        p1 = re.compile('(\<\/?[^>]+\>)')
        p2 = re.compile('\s+|&nbsp;')
        real_service_about = p2.sub(' ', p1.sub(' ', real_service_about.encode("utf-8")))
        contentList['real_service_about'] = real_service_about
        print "服务介绍：%s " % real_service_about
    except:
        print "没有服务介绍呀~"
    try:
        contentList['title'] = title
    except:
        pass
    try:
        # print content.html
        contentList['phone'] = browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[4]/div/span').html
    except:
        print "获取电话号码失败！"

    contentList['url'] = url
    #print "TTTTTTTTTTTest", contentList

    detailinfo.insert_one(contentList)
    return contentList
"""
if __name__ == "__main__":
    url = "http://dongying.ganji.com/fuwu_dian/2558028785x/#tabl"
    getContent(url)