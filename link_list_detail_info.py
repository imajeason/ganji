#coding=utf-8 

import requests
from bs4 import BeautifulSoup
import time
from pymongo import MongoClient
import random
client=MongoClient('localhost',27017)
ganjiDB=client['ganjiDB']
linklists=ganjiDB['linklists']
detailinfo=ganjiDB['detailinfo']
headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'}
proxy_list=[    
    'http://125.88.74.122:83',
    'http://113.18.193.5:8080',
    'http://113.18.193.7:8080',
    'http://120.92.3.127:90'
    ]
proxy_ip=random.choice(proxy_list)
proxies={'http':proxy_ip}#启用代理，规避赶集网针对单个IP的访问限制

def page_link(channel):
    for cate in range(1,3):
        link_url = ['{}a{}o{}'.format(channel, cate,)][0]
        #print(link_url)
        link_list(link_url)

def link_list(url):
    time.sleep(2)
    web_data=requests.get(url,headers=headers)
    # print(web_data.status_code)#返回结果code 200
    soup=BeautifulSoup(web_data.text,'lxml')
    # mark=soup.find('a','next')#返回结果为字符串<a class="next"href="/jiaju/a1o31/"><span>下一页</span></a>
    # print(mark)
    if soup.find('a','next')and url.split('/')[-1][1]=='1':#满足两个条件1、当前页不是最后一页2、当前页属于个人类目
        lists=soup.select('td.t a.t')#与商家类目过滤条件不同
        # print(lists)
        for list in lists:
            list_href=list.get('href').split('?')[0]
            linklists.insert_one({'list_href':list_href})
            print(list_href)
    elif soup.find('a', 'next') and url.split('/')[-1][1] == '2':#满足两个条件1、当前页不是最后一页2、当前页属于商家类目
        lists = soup.select('a.ft-tit')#与个人列木过滤条件不同
        # print(lists)
        for list in lists:
            list_href = list.get('href')
            linklists.insert_one({'list_href': list_href})
            print(list_href)
    else:
        print('列表地址错误')
#获取每个页面的具体信息
def get_detail_info(url):
    web_data=requests.get(url,headers=headers)
    soup=BeautifulSoup(web_data.text,'lxml')
    if url[-5]=='x':
        info={
        'title':soup.select('h1.title-name')[0].text,
        'date':soup.select('i.pr-5')[0].text.strip(),
        'types':soup.select('ul > li > span > a')[5].text,
        'price':soup.select('i.f22.fc-orange.f-type')[0].text,
        'area':list(map(lambda x:x.text,soup.select('div > div > div > div > ul > li > a')[-3:-1])),
        'url':url
        }
        detailinfo.insert_one(info)
        print(info)
    elif url[-7]=='z':
        info={
        'title':soup.select('h1.info_titile')[0].text,
        'price':soup.select('span.price_now i')[0].text,
        'area':soup.select('div.palce_li span i')[0].text,
        'url':url
        }
        detailinfo.insert_one(info)
        print(info)
    else:
        print('地址错误')
