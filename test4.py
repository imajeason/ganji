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

client = MongoClient('localhost', 27017)
ganjiDB = client['ganjiwang']
linklists = ganjiDB['linklists']
detailinfo = ganjiDB['detailinfo']
import logging,datetime
import signal,os


mydir = os.path.split(os.path.realpath(__file__))[0]
logname_old = mydir + '/log/getganji'+ str(datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'))+'.log'
logname = 'getganji.log'
if not os.path.isdir(mydir+'/log'): os.mkdir(mydir+'/log')
if os.path.isfile(logname):os.rename(logname,logname_old)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s %(levelname)s %(message)s',
                    #datefmt='%a,%d %b %Y %H %M:%s',
                    filename=logname,
                    filemode='a')

pagesAll = []
pagesDone = []


def getContent(url):
    try:
        #content = detailinfo.find_one({"url": url})
        if content:
            print "跳过: %s"% url
            logging.info('跳过: %s'% url)
            return False
    except:
        print "不知道为什么跳到这了，可能是数据库卡了吧"
        logging.info('不知道为什么跳到这了，可能是数据库卡了吧')
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
        #print browser.find_by_xpath('//*[@class="d-nav"]/ul/li[1]/a').click()

        browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul').find_by_text('点击查看完整号码').click()
        content = browser.find_by_xpath('//*[@id="dzcontactus"]/div/ul')
        # content = browser.find_by_id('dzcontactus').find_by_xpath('/li')

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
                logging.info('%s:%s'% (k,v))
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
            logging.info('服务介绍：%s ' % real_service_about)
        except:
            print "没有服务介绍呀~"
            logging.info('没有服务介绍!')

        try:
            # print content.html
            print browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[4]/div/span[1]').html
            contentList['phone'] = browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[4]/div/span').html
            logging.info('电话号码：%s' % contentList['phone'])
            print "电话号码：%s" % contentList['phone']
        except:
            print "获取电话号码失败！"
            logging.info('获取电话号码失败!')

        try:
            contentList['title'] = title
            contentList['url'] = url


            detailinfo.insert_one(contentList)


        except:
            print "基本信息不太对。"
            logging.info('基本信息不太对!')

    except:
        try:
            browser.quit()
        except:
            pass
        display.stop()
        print "可能什么都没获取到！Nooooooooooooooooooooooooo"
        logging.info('可能什么都没获取到!Nooooooooooooooooooooooooo')
        return False

    try:
        browser.quit()
    except:
        pass
    display.stop()
    return contentList
if __name__ == "__main__":
    url = "http://dongying.ganji.com/fuwu_dian/648512601x/#tabl"
    getContent(url)