# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'jerry'

import re
import time
import socket
import socks
import requests
import re, time
import  urllib2
from multiprocessing.dummy import Pool as ThreadPool
import getopt
import sys
from bs4 import BeautifulSoup
from utils.cmd import kill_crawler
from main import iproxy
reload(sys)
sys.setdefaultencoding('utf-8')

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
    socks.set_default_proxy(socks.SOCKS5, "192.168.199.190", 1080)
    socket.socket = socks.socksocket
    html = requests.get(url,headers=headers, timeout=30).text
    #	print html
    socks.set_default_proxy()
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

def checkProxy(sproxy):
    urltest = "http://weixin.ninev.cn/test"
    ip, port = sproxy.split(":")

    proxy = urllib2.ProxyHandler({'http': sproxy})
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)
    try:
        response = urllib2.urlopen(urltest,timeout = 20)
        content = response.read()

        # soup = BeautifulSoup(content, features="lxml")
        # tag1 = soup.find(name='h2')
    except:
        #print "open error."
        return sproxy,False
    print ip,content

    if ip == content:
        return sproxy,True
    else:
        return sproxy,False

def checkProxys():
    #proxy_list = iproxy.find()
    proxy_list = iproxy.find({"status":0})
    print "现有代理数量：",iproxy.find({"status":0}).count()

    pool = ThreadPool(processes=8)
    results = []
    count = 0
    for proxy in proxy_list:
        if count > 40:break

        proxy = proxy["iproxy"]
        result = pool.apply_async(checkProxy, args=(proxy,))
        results.append(result)
        count += 1
        # print "proxy:",proxy

    # pool.join()  # 调用join之前，先调用close函数，否则会出错。执行完close后不会有新的进程加入到pool,join函数等待所有子进程结束
    for i in results:
        i.wait()  # 等待线程函数执行完毕

    for i in results:
        if i.ready():  # 线程函数是否已经启动了
            if i.successful():  # 线程函数是否执行成功
                contentList = {}

                sproxy, res = i.get()
                # print sproxy,res
                contentList["iproxy"] = sproxy

                if res:
                    print "%s is ok!" % sproxy

                    iproxy.remove(contentList)
                    contentList["status"] = 0
                    iproxy.insert_one(contentList)
                else:

                    print "%s is bad!" % sproxy
                    time.sleep(0.1)
                    iproxy.delete_one(contentList)

    print "Sub-process(es) done."

    # get pages url

    print "现有代理数量：", iproxy.find({"status": 0}).count()

def getProxy(countries = ['China']):
    global iproxy
    print "现有代理数量：", iproxy.find({"status": 0}).count()
    if iproxy.find({"status": 0}).count() > 50:return True

    # 此处修改伪造的头字段,

    # country = ['China','Indonesia','United%20States','Russia','Thailand','India','Taiwan','Japan','France','Iran','Bangladesh','Poland','Romania','Venezuela','Germany','Ukraine','Argentina','Mexico','Australia','Colombia']
    for name in countries:
        url = "http://www.gatherproxy.com/zh/proxylist/country/?c=" + name
        html_code = get_request(url, headers)
        proxy_list = []
        proxy_list_json = []
        proxy_list_json = re_html_code(html_code, proxy_list_json)

        for i in proxy_list_json:
            contentList = {}
            # list_i = [PROXY_IP, PROXY_PORT, PROXY_COUNTRY, PROXY_TYPE, addtime, Last_test_time,proxy_status, Remarks]
            ip, port = i[0], str(i[1])
            sproxy = "%s:%s" % (ip, port)

            contentList["iproxy"] = sproxy.encode("utf-8")
            proxy_list.append(contentList["iproxy"])


        print "待处理代理数量：",len(proxy_list)

        pool = ThreadPool(processes=8)
        results = []

        for proxy in proxy_list:

            result = pool.apply_async(checkProxy, args=(proxy,))
            results.append(result)
            #print "proxy:",proxy

        # pool.join()  # 调用join之前，先调用close函数，否则会出错。执行完close后不会有新的进程加入到pool,join函数等待所有子进程结束
        for i in results:
            i.wait()  # 等待线程函数执行完毕

        for i in results:
            if i.ready():  # 线程函数是否已经启动了
                if i.successful():  # 线程函数是否执行成功
                    contentList = {}


                    sproxy,res = i.get()
                    #print sproxy,res
                    contentList["iproxy"] = sproxy


                    if res:
                        print "%s is ok!" % sproxy
                        iproxy.remove(contentList)
                        contentList["status"] = 0
                        iproxy.insert_one(contentList)
                    else:

                        print "%s is bad!" % sproxy

        print "Sub-process(es) done."

    print "现有代理数量：", iproxy.find({"status": 0}).count()

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "rhgca")
    except getopt.GetoptError:
        print 'test.py -g -c'
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'help test.py -g -c'
            sys.exit()
        elif opt in ("-c", "--check"):
            checkProxys()
        elif opt in ("-r", "--renew"):
            checkProxys()
        elif opt in ("-g", "--get"):
            countries = ['China']
            getProxy(countries)
        elif opt in ("-a", "--all"):
            print "get & check"
            kill_crawler()
            countries = ['China']
            getProxy(countries)
            checkProxys()

