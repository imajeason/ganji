#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2017-05-27 16:29:10
# Project: 58banjia

from pyspider.libs.base_handler import *
import re


class Handler(BaseHandler):
    crawl_config = {
    }

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('http://dy.58.com/banjia/pn1', callback=self.index_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            if re.match("http://dy.58.com/banjia/pn", each.attr.href, re.U):
                self.crawl(each.attr.href, callback=self.list_page)

    def list_page(self, response):
        for each in response.doc('.cleft > .clearfix .bjtit > span').items():
            if re.match("http://dy.58.com/banjia/", each.attr.href, re.U):
                self.crawl(each.attr.href, callback=self.detail_page)

        for each in response.doc('.listInfo > * > a.bjtit > .tit').items():
            if re.match("http://dy.58.com/banjia/", each.attr.href, re.U):
                self.crawl(each.attr.href, callback=self.detail_page)

        for each in response.doc('div.pager > a > span').items():
            if re.match("http://dy.58.com/banjia/pn", each.attr.href, re.U):
                self.crawl(each.attr.href, callback=self.list_page)

    @config(priority=2)
    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc('html > body > .basicinfo > .mainTitle > h1').text(),
            "content": response.doc('.d-info').text(),
            "phone": response.doc('.pos-r > .phone').text(),
        }
