# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'jerry'

import re
import sys,os,time
import socket
import socks
import requests
from splinter import Browser
from pyvirtualdisplay import Display

from main import detailinfo,errorurl,iproxy

# 此处修改伪造的头字段,
headers = {
    'Host':"www.gatherproxy.com",#需要修改为当前网站主域名
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0",
	"referer" : '123.123.123.123'#随意的伪造值
}


#发起请求,
def get_request(url,headers):
    '''参数引入及头信息'''
    socks.set_default_proxy(socks.SOCKS5, "192.168.199.135", 1080)
    socket.socket = socks.socksocket
    html=requests.get(url,headers=headers, timeout=30).text
    #	print html
    return html


# 将页面源代码正则匹配并解析,返回列表,其中每一项是json的数据
def re_html_code(html_code,proxy_list_json):

    re_str = '(?<=insertPrx\().*\}'
    proxy_list = re.findall(re_str,html_code)
    null = ''

#{'PROXY_STATUS': 'OK', 'PROXY_CITY': '', 'PROXY_TIME': '548', 'PROXY_STATE': '', 'PROXY_REFS': '', 'PROXY_TYPE': 'Transparent', 'PROXY_COUNTRY': 'China', 'PROXY_LAST_UPDATE': '1 59', 'PROXY_UPTIMELD': '105/16', 'PROXY_UID': '', 'PROXY_PORT': '1F90', 'PROXY_IP': '61.158.173.14'}

    for i in proxy_list:
        json_list = eval(i)

        PROXY_IP = json_list['PROXY_IP']
        PROXY_PORT = json_list['PROXY_PORT']
        PROXY_PORT = int(PROXY_PORT,16)

        PROXY_COUNTRY = json_list['PROXY_COUNTRY']
        PROXY_TYPE= json_list['PROXY_TYPE']
        addtime = time.ctime()
        Last_test_time = json_list['PROXY_LAST_UPDATE']
        proxy_status = '1'
        Remarks = 'ly'
        # `id`, `proxy_ip`, `proxy_port`, `proxy_country`, `proxy_type`, `addtime`, `Last_test_time`, `proxy_status`, `Remarks`

        list_i = [PROXY_IP,PROXY_PORT,PROXY_COUNTRY,PROXY_TYPE,addtime,Last_test_time,proxy_status,Remarks]

        proxy_list_json.append(list_i)

#    print proxy_list_json
    return proxy_list_json

print(iproxy.find().count())

if __name__ == '__main__':

    proxy_list = [
        '125.88.74.122:83',
        '113.18.193.5:8080',
        '120.92.3.127:90',
        '113.239.47.106:8998',
        '119.5.0.58:808',
        '111.23.10.98:80',
        '111.23.10.112:8080',
        '111.23.10.43:80',
        '111.23.10.11:80',
        '111.23.10.202:8080',
        '111.23.10.17:80',
        '111.23.10.28:8080',
        '175.155.24.122:808',
        '175.155.214.89:808',
        '175.155.25.18:808',
        '111.23.10.26:8080',
        '42.59.111.148:808',
        '60.184.173.63:808',
        '118.89.53.148:3128',
        '183.95.80.165:8080',
        '101.64.199.168:8998',
        '113.207.43.166:8080',
        '183.62.196.10:3128',
        '110.187.31.190:808',
        '113.121.20.84:808',
        '115.50.187.84:8998',
        '116.16.52.112:8998',
    ]
    for ii in proxy_list:
        contentList = {}
        sproxy = ii
        # proxy_list.append(proxy)
        content = iproxy.find_one({"iproxy": sproxy})
        contentList["iproxy"] = sproxy
        contentList["status"] = 0
        if content:
            print "%s already in db." % sproxy
        else:
            iproxy.insert_one(contentList)
            print "%s insert sucessfully." % sproxy
            # print i
            # insert_ll(install_str,i,conn,cur)

    country = ['China']
    #country = ['China','Indonesia','United%20States','Russia','Thailand','India','Taiwan','Japan','France','Iran','Bangladesh','Poland','Romania','Venezuela','Germany','Ukraine','Argentina','Mexico','Australia','Colombia']



    for name in country:
        url = "http://www.gatherproxy.com/zh/proxylist/country/?c="+name

        html_code = get_request(url,headers)
        proxy_list_json = []
        proxy_list = {}
        now_url = url
        proxy_list_json = re_html_code(html_code,proxy_list_json)
        urltest = "http://bj.ganji.com/"
        for i in proxy_list_json:

            display = Display(visible=0, size=(800, 800))
            display.start()
            contentList = {}
            # list_i = [PROXY_IP, PROXY_PORT, PROXY_COUNTRY, PROXY_TYPE, addtime, Last_test_time,proxy_status, Remarks]
            sproxy = "%s:%s" % (i[0], i[1])

            ip,port = i[0], str(i[1])
            print ("代理:%s:%s，正在处理%s" % (i[0], i[1], urltest))
            print type(i[0]),type(i[1])

            proxy_settings = {'network.proxy.type': 1,
                              'network.proxy.no_proxies_on': '172.0.0.0/8,10.0.0.0/8,localhost,127.0.0.0/8,::1',
                              'network.proxy.http': ip, 'network.proxy.http_port': port,
                              'network.proxy.ssl': '172.1.1.1', 'network.proxy.ssl_port': 8080}

            # browser = Browser(driver_name="firefox")
            browser = Browser(driver_name="firefox", profile_preferences=proxy_settings,timeout=40)
            browser.visit(urltest)

            try:
                browser.quit()
            except:
                pass

            display.stop()

            contentList = {}
            # browser.execute_script(clickLog('m-my_login_login_tab'))
            title = browser.title
            print "test baidu success:%s"%(title.encode('utf-8'))
            # proxy_list.append(proxy)
            content = iproxy.find_one({"iproxy": sproxy})
            contentList["iproxy"] = sproxy.encode("utf-8")
            contentList["status"] = 0
            if content:
                print "%s already in db." % sproxy
            else:
                #iproxy.insert_one(contentList)
                print "%s insert sucessfully." % sproxy





"""
var res=db.iproxy.find();  
while(res.hasNext()){  
      var res1=db.iproxy.find();   
      var re=res.next();  
      while(res1.hasNext()){  
              var re1=res1.next();  
              if(re.iproxy==re1.iproxy){   
                   db.iproxy.remove({"iproxy":re1.iproxy});   
               }  
       }   
       db.iproxy.insert(re);   
}  
"""
