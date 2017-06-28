#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-05-26 16:16:59
# Project: ganjibingxiang

from pyspider.libs.base_handler import *
import re, random, signal, time
from splinter import Browser
from pyvirtualdisplay import Display


class Handler(BaseHandler):
    crawl_config = {
        # 'proxy': 'http://113.18.193.7:8080'
    }

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('http://dongying.ganji.com/jiadianweixiu/', callback=self.index_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            if re.match("http://dongying.ganji.com/\w+/$", each.attr.href, re.U):
                self.crawl(each.attr.href, callback=self.list_page)

    def list_page(self, response):
        for each in response.doc('.list-noimg .list-info-title').items():
            self.crawl(each.attr.href, callback=self.detail_page)

        for each in response.doc('.list-img .list-info-title').items():
            self.crawl(each.attr.href, callback=self.detail_page)

        for each in response.doc('li > a > span').items():
            self.crawl(each.attr.href, callback=self.list_page)

    def handler(signum, frame):
        raise AssertionError

    @config(priority=2)
    def detail_page(self, response):
        url = response.url
        contentList = {}
        display = Display(visible=0, size=(800, 800))
        display.start()
        proxy_list = [
            'http://125.88.74.122%83',
            'http://113.18.193.5%8080',
            'http://113.18.193.7%8080',
            'http://120.92.3.127%90'
        ]
        ip, port = (random.choice(proxy_list)).split("%")
        proxy = str(ip) + ":" + str(port)
        proxy_settings = {'network.proxy.type': 1,
                          'network.proxy.no_proxies_on': '172.0.0.0/8,10.0.0.0/8,localhost,127.0.0.0/8,::1',
                          'network.proxy.http': ip, 'network.proxy.http_port': port,
                          'network.proxy.ssl': '172.1.1.1', 'network.proxy.ssl_port': 8080}

        try:
            #browser = Browser(driver_name="firefox", timeout=60)
            browser = Browser(driver_name="firefox", profile_preferences=proxy_settings, timeout=40)
            browser.visit(url)
        except:
             return {
                 "url": response.url,
                 "title": "",
                 "phone": "",
                 "content": contentList,
                 "proxy": proxy,
             }

        try:
            time.sleep(5)
            title = browser.title
            contentList['title'] = title
            browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul').find_by_text('点击查看完整号码').click()
            content = browser.find_by_xpath('//*[@id="dzcontactus"]/div/ul')

            p1 = re.compile('(\<\/?[^>]+\>)')
            p2 = re.compile('\s+|&nbsp;')
            # print content
            for j in content.html.split("</li>"):
                item = p2.sub(' ', p1.sub(' ', j.strip()))
                try:
                    p3 = re.compile("：")
                    item = re.sub(p3, "@", item.encode("utf-8"))
                    k, v = item.split("@")
                    contentList[k] = v
                except:
                    pass

            try:
                real_service_about = browser.find_by_xpath('//*[@id="real_service_about"]').html
                p1 = re.compile('(\<\/?[^>]+\>)')
                p2 = re.compile('\s+|&nbsp;')
                real_service_about = p2.sub(' ', p1.sub(' ', real_service_about.encode("utf-8")))
                contentList['real_service_about'] = real_service_about
                if not contentList['real_service_about']:
                    content = browser.find_by_xpath('//*[@id="real_service_about"]/span')
                    item = p2.sub(' ', p1.sub(' ', content.html))
                    contentList['detail'] = item

            except:
                pass



            try:
                phone = str(browser.find_by_xpath('//*[@class="d-top-area"]/div[2]/ul/li[4]/div/span').html)
            except:

                try:
                    browser.quit()
                except:
                    pass
                display.stop()
                return {
                    "url": response.url,
                    "title": title,
                    "phone": "no phone",
                    "content": contentList,
                    "proxy": proxy,
                }


        except:
            try:
                browser.quit()
            except:
                pass
            display.stop()

            return {
                "url": response.url,
                "title": "no title",
                "phone": None,
                "content": contentList,
                "proxy": proxy,
            }

        return {
            "url": response.url,
            "title": title,
            "phone": phone,
            "content": contentList,
            "proxy": proxy,
        }


