# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'jerry'

import re, os, time, datetime, random, sys
from threading import Thread,Lock
import threading
from Queue import Queue
from splinter import Browser
from pyvirtualdisplay import Display
#from multiprocessing import Pool
from pymongo import MongoClient
import logging
import signal

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



client=MongoClient('localhost',27017)
#client=MongoClient('localhost',27017,connect=False)
ganjiDB=client['Ganji']
detailinfo=ganjiDB['detailinfo']
servicedone=ganjiDB['servicedone']
urldone=ganjiDB['urldone']
iproxy=ganjiDB['iproxy']
errorurl=ganjiDB['errorurl']

pagesAll = []
pagesDone = []

#signal超时处理
def handler(signum, frame):
    raise AssertionError

class Timeout(Exception):
    """function run timeout"""
class KThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.killed = False
    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        # Force the Thread to install our trace.
        self.run = self.__run
        threading.Thread.start(self)
    def __run(self):
        """Hacked run function, which installs the trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup
    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        else:
            return None
    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace
    def kill(self):
        self.killed = True
def timeout(timeout, default=None, try_except=False):
    """Timeout decorator, parameter in timeout."""
    def timeout_decorator(func):
        def new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
            result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))
        """Wrap the original function."""
        def func_wrapper(*args, **kwargs):
            result = []
            # create new args for _new_func, because we want to get the func
            # return val to result list
            new_kwargs = {
                'oldfunc': func,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }
            thd = KThread(target=new_func, args=(), kwargs=new_kwargs)
            thd.start()
            thd.join(timeout)
            # timeout or finished?
            isAlive = thd.isAlive()
            thd.kill()
            if isAlive:
                if try_except is True:
                    raise Timeout("{} Timeout: {} seconds.".format(func, timeout))
                return default
            else:
                return result[0]
        func_wrapper.__name__ = func.__name__
        func_wrapper.__doc__ = func.__doc__
        return func_wrapper
    return timeout_decorator


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
    proxyList = iproxy.find({"status":0})
    proxy_list = []
    for iii in proxyList:
        proxy_list.append(iii["iproxy"].encode("utf-8"))

    # 拆分代理的ip和端口
    proxy = random.choice(proxy_list)
    ip, port = proxy.split(":")

    print ("当前使用代理 %s:%s，获取列表页：%s" % (ip,port,urlPage))
    logging.info('当前使用代理:%s:%s,获取列表页：%s' % (ip,port,urlPage))
    proxy_settings = {'network.proxy.type': 1,
     'network.proxy.no_proxies_on':'172.0.0.0/8,10.0.0.0/8,localhost,127.0.0.0/8,::1',
     'network.proxy.http':ip,'network.proxy.http_port':port,
     'network.proxy.ssl':'172.1.1.1','network.proxy.ssl_port':8080}

    #获取列表页内容，设置了60s的超时
    try:
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(60)
        #browser = Browser(driver_name="firefox")
        browser = Browser(driver_name="firefox", profile_preferences=proxy_settings,timeout=60)
        browser.visit(urlPage)
        signal.alarm(0)
    except:
        print ('可能是超时了：%s:%s 列表页：%s' % (ip, port, urlPage))
        logging.info('可能是超时了：%s:%s 列表页：%s' % (ip, port, urlPage))
        errorurl.insert_one({"url": urlPage, "addr": addr, "service": service, "iproxy": proxy})
        try:
            browser.quit()
        except:
            pass

        display.stop()
        return False
    time.sleep(5)
    # browser.execute_script(clickLog('m-my_login_login_tab'))
    # title = browser.title

    #print "go..."
    urlList= browser.find_by_xpath('//*[@class="list-noimg"]/div[1]/p[1]/a')
    #print "url列表:",urlList
    urls = []
    for ii in  urlList:
        urlss = ii["href"].encode("utf-8")
        #try:
        print ("新增内容页： %s" % urlss)
        logging.info('新增内容页： %s' % (urlss))
        p1 = re.compile('http')
        p2 = re.compile('\d+x\/$')
        p3 = re.compile('\/[^\/]+\/$')
        p4 = "/#tabl"

        if not re.search(p2, urlss):
            urlss = re.sub(p3, p4, urlss)
            #print "网址修正为：%s" % urlss
        if re.search(p1, urlss) and urlss not in urls:
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

    #fetch ad content.
    print ("开始抓取url内容，共%d条。" % len(urls))
    logging.info('开始抓取url内容，共%d条。' % len(urls))
    f = Fetcher(threads=6, addr=addr, service=service)
    # print hosts.split()
    for url in urls:
        f.push(url)
    ilistcount = len(urls)
    count = 0
    while f.taskleft():
        url, con = f.pop()
        print ("Done======%s" % (url))
        logging.info("Done======%s" % url)
        count += 1
        print "当前已输出%s/%s"%(count,ilistcount)
        logging.info("当前已输出%s/%s"%(count,ilistcount))
        time.sleep(0.1)
        # get pages url

    pagesDone.append(urlPage)
    urldone.insert_one({"url": urlPage,"addr":addr, "service":service})


    for i in pagesAll:
        if i not in pagesDone:
            mGanji(i, addr, service)

    return True

class Fetcher:
    def __init__(self, threads, addr, service):
        self.lock = Lock()
        self.q_req = Queue()
        self.q_ans = Queue()
        self.threads = threads
        self.addr = addr
        self.service = service

        for i in range(threads):
            t = Thread(target=self.threadget)
            t.setDaemon(True)
            t.start()
        self.running = 0

    def __del__(self):
        time.sleep(0.5)
        self.q_req.join(3)
        self.q_ans.join(3)

    def taskleft(self):
        return self.q_req.qsize() + self.q_ans.qsize() + self.running

    def push(self, url):
        self.q_req.put(url)

    def pop(self):
        return self.q_ans.get()

    def threadget(self):
        while True:
            url = self.q_req.get()
            # with self.lock:
            self.lock.acquire()
            self.running += 1
            self.lock.release()
            con = getContent(url, self.addr, self.service)
            # self.lock.release()
            self.q_ans.put((url,con))
            # with self.lock:
            self.lock.acquire()
            self.running -= 1
            self.lock.release()
            self.q_req.task_done()
            time.sleep(0.1)  # don't spam

@timeout(60)
def getContent(url,addr,service):
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
    proxyList = iproxy.find({"status":0})
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
        browser = Browser(driver_name="firefox", profile_preferences=proxy_settings, timeout=40)

        contentList = {}
        browser.visit(url)
        time.sleep(5)
        # browser.execute_script(clickLog('m-my_login_login_tab'))
        title = browser.title
        print (title.encode('utf-8'))
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
                print ("%s:%s"% (k,v))
                logging.info('%s:%s'% (k,v))
            except:
                pass

        if not contentList:
            content = browser.find_by_xpath('//*[@id="real_service_about"]/span')
            item = p2.sub(' ', p1.sub(' ', content.html))
            contentList['detail'] = item
            print (item)
        # browser.close()

        try:
            real_service_about = browser.find_by_xpath('//*[@id="real_service_about"]').html
            #print "real_service_about:%s" % real_service_about
            p1 = re.compile('(\<\/?[^>]+\>)')
            p2 = re.compile('\s+|&nbsp;')
            real_service_about = p2.sub(' ', p1.sub(' ', real_service_about.encode("utf-8")))
            contentList['real_service_about'] = real_service_about
            print ("服务介绍：%s " % real_service_about)
            logging.info('服务介绍：%s ' % real_service_about)
        except:
            print ("没有服务介绍呀~")
            logging.info('没有服务介绍!')

        try:
            # print content.html
            #print browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[4]/div/span').html
            contentList['phone'] = str(browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[4]/div/span').html)

            logging.info('电话号码：%s' % contentList['phone'])
            print ("电话号码：%s" % contentList['phone'])
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
            detailinfo.insert_one(contentList)
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
        print ("可能什么都没获取到！Nooooooooooooooooooooooooo")
        logging.info('可能什么都没获取到!Nooooooooooooooooooooooooo')
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
    addrs = ["binzhou",
             "dongying",
             "weifang",
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
    services = ["banjia",
                "jiazheng",
                "wuliu",
                "weixiu",
                "jiajuwx",
                "guandao",
                "fengshuiqiming",
                "baoxian",
                "shenghuopeisong",
                "baojie",
                "jiadianweixiu",
                "shumashoujiweixiu",
                "bianminfuwu",
                "zhuangxiu",
                "jiazhuangjiancai",
                "zuchedaijia",
                "daijia",
                "qixiubaoyang",
                "liyihunqing",
                "xiezhenhunsha",
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
            servicedone.insert_one(serviced)
            print ("%s-%s已完成，开始下一个项目"%(addr,service))
            logging.info("%s-%s已完成，开始下一个项目"%(addr,service))

    """
    channel_list = [['http://%s.ganji.com/%s/' % (addr, service) for addr in addrs for service in services]]
    #print channel_list

    for url in channel_list:
        pagesAll.append(url)
        while len(pagesDone) != len(pagesAll):
            for urlsingle in pagesAll:
                if urlsingle not in pagesDone:
                    print "获取URL列表中：%s" % urlsingle
                    mGanji(urlsingle)
                    print "等待片刻..."
                    #print pagesAll, pagesDone
    """

