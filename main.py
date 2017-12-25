# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'imajeason'

import re, os, time, datetime, random, sys

from splinter import Browser
from pyvirtualdisplay import Display
#from multiprocessing import Pool

import signal
from selenium.webdriver.chrome.options import Options
from utils.slideHandler import BaseGeetestCrack
from utils.logconfig import logging
from utils.mongodb import iproxy,detailinfo,urldone,errorurl,servicedone
from utils.timeouthandler import timeout
#设置日志目录，如果目录不存在，创建



#如果指定的列表页中获取到了其他的列表页，存储到列表里，并继续调用
pagesAll = []
#以及完成的列表页
pagesDone = []

#获取列表页以及内容页url
def mGanji(urlPage,addr, service):
    """
    获取列表页内容，然后获取列表页中的内容也url，如果能够获取到分页，则在完成获取内容页后进行自调用。
     :param urlPage: 
    :param addr: 
    :param service: 
    :return: 
    """
    #打开一个虚拟桌面
    display = Display(visible=0, size=(800, 800))
    display.start()

    # 获取全部可用代理,status=0
    proxyList = iproxy.find({"status":0}).limit(30)
    if not proxyList:
        time.sleep(600)
        proxyList = iproxy.find({"status": 0})
        if not proxyList:
            sys.exit(0)

    proxy_list = []
    for iii in proxyList:
        proxy_list.append(iii["iproxy"].encode("utf-8"))

    # 拆分代理的ip和端口
    proxy = random.choice(proxy_list)
    ip, port = proxy.split(":")

    print ("当前使用代理 %s:%s，获取列表页：%s" % (ip,port,urlPage))
    logging.info('当前使用代理:%s:%s,获取列表页：%s' % (ip,port,urlPage))
    #设置firefox 的参数，如果是chrome或者其他浏览器这个参数无法通用
    proxy_settings = {'network.proxy.type': 1,
     'network.proxy.no_proxies_on':'172.0.0.0/8,10.0.0.0/8,localhost,127.0.0.0/8,::1',
     'network.proxy.http':ip,'network.proxy.http_port':port,
     'network.proxy.ssl':'172.1.1.1','network.proxy.ssl_port':8080}

    #获取列表页内容，设置了60s的超时
    try:
        #browser = Browser(driver_name="firefox")
        browser = Browser(driver_name="firefox", profile_preferences=proxy_settings,timeout=60)
        browser.driver.set_page_load_timeout(50)
        browser.visit(urlPage)
        time.sleep(5)
    except:
        print ('获取列表页内容失败,errorurl表：%s:%s 列表页：%s' % (ip, port, urlPage))
        logging.info('获取列表页内容失败,errorurl表：%s:%s 列表页：%s' % (ip, port, urlPage))
        errorurl.insert_one({"url": urlPage, "addr": addr, "service": service, "iproxy": proxy})
        try:
            browser.quit()
        except:
            pass

        display.stop()
        return False

    time.sleep(1)

    #匹配两个内容页的列表，并合并列表
    urlList= browser.find_by_xpath('//*[@class="list-noimg"]/div[1]/p[1]/a')
    urlList2 = browser.find_by_xpath('//*[@class="list-img"]/div[1]/a')
    urlList.extend(urlList2)
    #目标内容的url列表
    urls = []
    for ii in  urlList:

        urlss = ii["href"].encode("utf-8")
        #try:
        print ("新增内容页： %s" % urlss)
        logging.info('新增内容页： %s' % (urlss))
        p1 = re.compile('http')
        p2 = re.compile('\d+x?\/$')
        p3 = re.compile('\/[^\/]+\/$')
        p4 = "/#tabl"

        if not re.search(p2, urlss):
            urlss = re.sub(p3, p4, urlss)
            print "网址修正为：%s" % urlss
        #if re.search(p1, urlss) and urlss not in urls:
        if urlss not in urls:
            urls.append(urlss)
            print ("加入待抓取列表：", urlss)
            logging.info('加入待抓取列表： %s' % (urlss))

    pageList= browser.find_by_xpath('//*[@class="pageBox"]/ul/li/a')
    for i in  pageList:
        urlPages = str(i["href"])
        p = r"http"

        try:
            if urlPages not in pagesAll and re.search(p,urlPages) and not urldone.find_one({"url": urlPages}):
                print ("获取到新的列表页:%s" % urlPages)
                logging.info('获取到新的列表页： %s' % (urlPages))
                pagesAll.append(urlPages)
        except:
            print ("Maybe none.")

    #close display broser
    browser.quit()
    display.stop()


    # f = Fetcher(threads=6, addr=addr, service=service)
    from multiprocessing.dummy import Pool as ThreadPool
    pool = ThreadPool(processes=5)
    results = []
    for url in urls:
        result = pool.apply_async(getContent, (url,addr,service))
        results.append(result)
    print ("开始抓取url内容，共%d条。" % len(urls))
    logging.info('开始抓取url内容，共%d条。' % len(urls))
    # pool.close()
    # pool.join()  # 调用join之前，先调用close函数，否则会出错。执行完close后不会有新的进程加入到pool,join函数等待所有子进程结束
    for i in results:
        i.wait()  # 等待线程函数执行完毕

    for i in results:
        if i.ready():  # 线程函数是否已经启动了
            if i.successful():  # 线程函数是否执行成功
                if i.get() == "stop":

                    sys.exit(0)

                #print(i.get())  # 线程函数返回值
    print "Sub-process(es) done."

    pagesDone.append(urlPage)
    urldone.insert_one({"url": urlPage,"addr":addr, "service":service})

    for i in pagesAll:
        if i not in pagesDone:
            mGanji(i, addr, service)
    return True

@timeout(100)
def getContent(url,addr,service):
    global detailinfo
    try:
        content = detailinfo.find_one({"url": url})
        if content:
            print ("跳过: %s"% url)
            logging.info('跳过: %s'% url)
            return False
    except:
        print ("不知道为什么跳到这了，可能是数据库卡了吧")
        logging.info('不知道为什么跳到这了，可能是数据库卡了吧')
        pass

    display = Display(visible=0, size=(800, 800))
    display.start()

    # 获取全部可用代理,status=0
    proxyList = iproxy.find({"status":0}).limit(30)
    proxy_list = []
    for iiii in proxyList:
        proxy_list.append(iiii["iproxy"].encode("utf-8"))

    # 拆分代理的ip和端口
    proxy = random.choice(proxy_list)
    ip, port = proxy.split(":")

    print ("代理:%s:%s，正在处理%s" % (ip, port, url))
    logging.info('代理:%s:%s，正在处理%s' % (ip, port, url))

    proxy_settings = {'network.proxy.type': 1,
                      'network.proxy.no_proxies_on': '172.0.0.0/8,10.0.0.0/8,localhost,127.0.0.0/8,::1',
                      'network.proxy.http': ip, 'network.proxy.http_port': port,
                      'network.proxy.ssl': '172.1.1.1', 'network.proxy.ssl_port': 8080}

    try:

        #browser = Browser(driver_name="firefox")
        browser = Browser(driver_name="firefox", profile_preferences=proxy_settings,timeout=60)
        browser.driver.set_page_load_timeout(50)

        browser.visit(url)
        time.sleep(3)
        title = browser.title
        print "标题:",title

        if re.findall("验证",title.encode("utf-8")):
            print "需要处理验证码了"
            try:
                browser.quit()
            except:
                pass
            display.stop()
            return "stop"
            #sys.exit()
        browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul').find_by_text('点击查看完整号码').click()
        content = browser.find_by_xpath('//*[@id="dzcontactus"]/div/ul')

        contentList = {}
        try:
            p1 = re.compile('(\<\/?[^>]+\>)')
            p2 = re.compile('\s+|&nbsp;')

            #print content
            for j in content.html.split("</li>"):
                item = p2.sub(' ', p1.sub(' ', j.strip()))
                try:
                    p3 = re.compile("：")
                    item = re.sub(p3, "@", item.encode("utf-8"))
                    k, v = item.split("@")
                    contentList[k] = v
                    print "%s:%s"% (k,v)
                    logging.info('%s:%s'% (k,v))
                except:
                    pass
        except:
            pass
        try:
            content = browser.find_by_xpath('//*[@id="real_service_about"]/span')
            item = p2.sub(' ', p1.sub(' ', content.html))
            contentList['detail'] = item
        except:
            pass
        try:
            if contentList[" 联系电话"]:
                contentList['phone'] = contentList[" 联系电话"]
                logging.info('联系电话：%s' % contentList['phone'])
                print ("联系电话：%s" % contentList['phone'])
            else:
                # print content.html
                #print browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[4]/div/span').html
                contentList['phone'] = str(browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[4]/div/span').html)

                logging.info('电话号码：%s' % contentList['phone'])
                print ("电话号码：%s" % contentList['phone'])
        except:
            try:
                # print "test",browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[2]/div/span').text
                contentList['phone'] = str(
                    browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[2]/div/span').text)
                logging.info('电话号码：%s' % contentList['phone'])
                print "电话号码：%s" % contentList['phone']
                try:
                    print browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[1]/div').text
                    contentList[' 商家地址'] = str(
                        browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[1]/div').text)
                    logging.info('商家地址：%s' % contentList[' 商家地址'])
                    print "商家地址：%s" % contentList[' 商家地址']
                except:
                    pass
                real_service_about = browser.find_by_xpath('//*[@id="real_service_about"]').html
                # print "real_service_about:%s" % real_service_about
                p1 = re.compile('(\<\/?[^>]+\>)')
                p2 = re.compile('\s+|&nbsp;')
                real_service_about = p2.sub(' ', p1.sub(' ', real_service_about.encode("utf-8")))
                contentList['real_service_about'] = real_service_about
                print "服务介绍：%s " % real_service_about
                logging.info('服务介绍：%s ' % real_service_about)
            except:
                print ("获取电话号码失败！")
                logging.info('获取电话号码失败!')
                errorurl.insert_one({"url": url, "addr": addr, "service": service, "iproxy": proxy})
                try:
                    browser.quit()
                except:
                    pass
                display.stop()
                return False
        try:
            contentList['title'] = title
            contentList['url'] = url
            contentList['addr'] = addr
            contentList['service'] = service
            contentList['iproxy'] = proxy
            # if detailinfo.find_one({"phone":contentList['phone']}):
            #     print "%s 重复抓取，删除重写"% contentList['phone']
            #     logging.info("%s 重复抓取，删除重写"% contentList['phone'])
            #     #detailinfo.remove({"phone":contentList['phone']})
            #     detailinfo.insert_one(contentList)
            # else:
            detailinfo.insert_one(contentList)
            print "%s 新增成功" % contentList['phone']
            logging.info("%s 新增成功" % contentList['phone'])
        except:
            print ("基本信息不太对。")
            logging.info('基本信息不太对!')

    except:
        try:
            errorurl.insert_one({"url": url, "addr": addr, "service": service, "iproxy": proxy})
            browser.quit()
        except:
            pass
        display.stop()
        print ("可能什么都没获取到！代理:%s:%s，%s" % (ip, port, url))
        logging.info("可能什么都没获取到！代理:%s:%s，%s" % (ip, port, url))
        return False

    try:
        browser.quit()
    except:
        pass
    display.stop()
    print "完成%s"% url
    return contentList



if __name__=='__main__':

    #pool=Pool()
    addrs = [
        "dongying",
        "weifang",
        "binzhou",
         "jinan",
         "qingdao",
         "weihai",
         "zibo",
         "zaozhuang",
         "yantai",
         "laiwu",
         "jining",
         "taian",
         "rizhao",
         "linyi",
         "dezhou",
         "liaocheng",
         "heze",
         "jiaozhouo",
         "jimo"]
    spservices = [
        "宠物",
        "招聘求职",
        "二手车",
        "租房一手二手房",
        "培训"
        "zhiyepeixun",
        "diannaowangluopeixun",
        "jixujiaoyurenzheng",
        "yingyouerjiaoyu",
    ]
    services = [
        # 维修
        "bingxiangweixiu",
        "dianshijiweixiu",
        "kongtiaoyiji",
        "kongtiaoweixiu",
        "kongtiaoqingxi",
        "xiyijiweixiu",
        "reshuiqiweixiu",
        "jiadianweixiu",
        #电脑it维修
        "weixiu",

        #家居维修
        "menchuangweixiu",
        "fangshuibulou",
        "dianluweixiu",
        "weiyujiejuwx",
        "nuanqishuiguanwx",
        "dengjuanzhuangwx",
        "shuiguanshuilongtouwx",
        "shuiguanshuilongtouwx",
        "jiajuwx",
        #管道
        "guandao",

        # 搬家
        "banjia",

        # 保洁
        "baojie",

        # 开锁
        "kaisuo",
        # 干洗
        "ganxi",
        # 修鞋
        "xiuxiexiusan",
        # 改衣
        "gaiyi",

        #家政
        "jiazheng",

        #装修
        "zhuangxiu",

        "zuchedaijia",

        # 物流
        "wuliu"

        #礼仪婚庆
        "liyihunqing",

        #印刷摄影
        "xiezhenhunsha",

        #驾校
        "jiaxiao",

        "bianminqita",

        "jiatingzhengti",
        "jiatingchuwei",
        "jiatinggaizao",
        "jiatingdimian",
        "jiatingqiangmian",
        "jiatingjiaju",
        "jiatingshuidian",
        "dengjuanzhuang",
        "menchuanganzhuang",

        "hunlicehua",
        "hunliyongpin",
        "hunyan",
        "zhuchi",
        "mote",
        "hunsha",
        "hunche",
        "hunlihuazhuang",
        "sheying",
        "dengguangyinxiang",
        "yuanyizhiwu",
        "huachezhuangshi",

        "baoxian",
        "shenghuopeisong",
        "fengshuiqiming",

        "shumashoujiweixiu",
        "bianminfuwu",
        "jiazhuangjiancai",

        "daijia",
        "qixiubaoyang",


        "gongshangdaili",
        "wangluobuxianweihu",
        "yinshua",
        "penhuizhaopai",
        "bangongweixiu",
        "diandang",
        "jianzhuwx",
        "lvshi",
        "shipinlei",
        "zhaoshangjiameng",
        "kuaiji",
        "wangzhanjianshe",
        "kuaiyin",
        "sheji",
        "liyiqingdian",
        "zhanlanzhanshi",
        "fanyi",
        "lipindingzhi",
        "huishou",
        "xiuxianyule",
        "yulecanyin",
        "peilian",
        "yundongxiuxian",
        "meirongmeifa",
        "jianshen",
        "lvyou",
        "shebeixulin",
        "penhuizhaopai",
        "zhanlanzhanshi",
        "yundongxiuxian",
        "dingjipiao",
        "liyihunqing",
        "xiezhenhunsha"
        ]
    doneS = ["bingxiangweixiu"]
    #services = services - doneS
    for addr in addrs:
        for service in services:

            content = servicedone.find_one({"key": str(addr) + str(service)})
            if content:
                msg = "%s-%s已经抓取过了" % (addr,service)
                print msg
                logging.info(msg)
                continue
            url = 'http://%s.ganji.com/%s/' % (addr, service)

            #global 数组:all和done，在执行过程中随时发现新的列表页就往all里加;
            #done数组，处理一页加一个
            mGanji(url, addr, service)

            serviced = {}
            serviced["service"] = service
            serviced["addr"] = addr
            serviced["key"] = str(addr) + str(service)
            #print serviced
            time.sleep(1)
            servicedone.insert_one(serviced)

            print ("%s-%s已完成，开始下一个项目"%(addr,service))
            logging.info("%s-%s已完成，开始下一个项目"%(addr,service))

