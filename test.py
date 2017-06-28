# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'jerry'


import time
from splinter import Browser
import re
from pyvirtualdisplay import Display
display=Display(visible=0,size=(800,800))
display.start()


#browser = Browser(user_agent='Mozilla/5.0 (X11; Linux x86_64; rv:36.0) Gecko/20100101 Firefox/36.0')
browser = Browser(driver_name="firefox")
browser.visit('http://dongying.ganji.com/wuba_info/580129406890897217/')
time.sleep(5)
#browser.execute_script(clickLog('m-my_login_login_tab'))
title=browser.title

print title.encode('utf-8')
browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul').find_by_text('点击查看完整号码').click()
#content = browser.find_by_id('dzcontactus').find_by_xpath('/li')
content = browser.find_by_xpath('//*[@id="dzcontactus"]/div/ul/li')
res = []

for i in content:
    p1 = re.compile('(\<\/?[^>]+\>)')
    p2 = re.compile('\s+|&nbsp;')
    item = p2.sub(' ',p1.sub(' ', i.html))
    if item:
        res.append(item)

if not res:
    content = browser.find_by_xpath('//*[@id="real_service_about"]/span')
    p1 = re.compile('(\<\/?[^>]+\>)')
    p2 = re.compile('\s+|&nbsp;')
    res = p2.sub(' ',p1.sub(' ', content.html))
    print res
display.stop()