# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'jerry'

import re
import time, random
from splinter import Browser

from pyvirtualdisplay import Display

from multiprocessing import Pool
import time

#browser = Browser(user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:36.0) Gecko/20100101 Firefox/36.0')


pagesAll = []
pagesDone = []

def mGanji(urlPage):
    display = Display(visible=0, size=(800, 800))
    display.start()
    proxy_list=[
        'http://125.88.74.122%83',
        'http://113.18.193.5%8080',
        'http://113.18.193.7%8080',
        'http://120.92.3.127%90'
     ]
    ip, port = (random.choice(proxy_list)).split("%")
    print ("当前使用代理 %s:%s，获取列表页：%s" % (ip,port,urlPage))
    proxy_settings = {'network.proxy.type': 1,
     'network.proxy.no_proxies_on':'172.0.0.0/8,10.0.0.0/8,localhost,127.0.0.0/8,::1',
     'network.proxy.http':ip,'network.proxy.http_port':port,
     'network.proxy.ssl':'172.1.1.1','network.proxy.ssl_port':8080}

    #获取列表页内容
    try:
        browser = Browser(driver_name="firefox",timeout=60)
        #browser = Browser(driver_name="firefox", profile_preferences=proxy_settings, timeout=60)
        browser.visit(urlPage)

    except:
        print ("列表页获取失败了，可能是代理错误")
        try:
            browser.quit()
        except:
            pass

        display.stop()
        return True
    time.sleep(3)
    # browser.execute_script(clickLog('m-my_login_login_tab'))
    # title = browser.title

    #print "go..."
    print  browser.find_by_xpath('//*[@class="list-img"]/div[2]/p[1]/a').text

    urlList = browser.find_by_xpath('//*[@class="list-img"]/div[2]/p[1]/a')
    #print "url列表:",urlList

    urls = []
    for ii in  urlList:
        urlss = ii["href"].encode("utf-8")
        #try:

        #print ("新增内容页： %s" % urlss)
        #logging.info('新增内容页： %s' % (urlss))
        p1 = re.compile('http')
        p2 = re.compile('\d+x\/$')
        p3 = re.compile('\/[^\/]+\/$')
        p4 = "/#tabl"

        if not re.search(p2, urlss):
            urlss = re.sub(p3, p4, urlss)
            #print "网址修正为：%s" % urlss
        if re.search(p1, urlss) and urlss not in urls:
            urls.append(urlss)
            print "加入待抓取列表：%s" % urlss
    browser.quit()
    display.stop()



if __name__=='__main__':

    url = "http://dongying.ganji.com/baojie/"
    mGanji(url)