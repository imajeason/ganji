# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'imajeason'

from pymongo import MongoClient

#初始化mongodb
#client=MongoClient('localhost',27017)
client=MongoClient('localhost',27017,connect=False)
ganjiDB=client['Ganji']
#数据表
detailinfo=ganjiDB['detailinfo']
#某地区某项服务的已完成表
servicedone=ganjiDB['servicedone']
#已完成的url表
urldone=ganjiDB['urldone']
#代理服务器表，http代理
iproxy=ganjiDB['iproxy']
#获取失败的url表
errorurl=ganjiDB['errorurl']