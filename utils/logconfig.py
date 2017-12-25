# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'imajeason'

import logging
import os
import datetime

mydir = os.path.split(os.path.realpath(__file__))[0]
logname_old = mydir + '/../log/getganji'+ str(datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'))+'.log'
logname = 'getganji.log'
if not os.path.isdir(mydir+'/../log'): os.mkdir(mydir+'/../log')
#移动旧log到log目录下
if os.path.isfile(logname):os.rename(logname,logname_old)

#目录级别info
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s %(levelname)s %(message)s',
                    #datefmt='%a,%d %b %Y %H %M:%s',
                    filename=logname,
                    filemode='a')

