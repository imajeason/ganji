# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'imajeason'

from splinter import Browser
from pyvirtualdisplay import Display
#from multiprocessing import Pool
from pymongo import MongoClient
import logging
import re, os, time, datetime, random



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



client=MongoClient('localhost',27017,connect=False)
ganjiDB=client['Ganji']
detailinfo=ganjiDB['detailinfo']