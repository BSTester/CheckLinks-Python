#!/usr/bin/env python
#coding=utf-8

#Todo: 页面链接有效性检查
#Author: 归根落叶
#Blog: http://this.ispenn.com

import httplib2  
from bs4 import BeautifulSoup
import re
import os,sys
import logging

reload(sys)  
sys.setdefaultencoding('utf8')   
log_file = os.path.join(os.getcwd(),'result/checkLinks.csv')
log_format = '[%(asctime)s] [%(levelname)s] %(message)s'
logging.basicConfig(format=log_format,filename=log_file,filemode='w',level=logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter(log_format)
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

#获取页面链接列表
def getURL(url,session=None):
    urlLinks = []
    imgLinks = []
    jsLinks = []
    cssLinks = []
    urlParse = url.split('/')
    rootURL = urlParse[0] + '//' + urlParse[2]
    if session is None:
        headers = {'contentType':'text/html;charset=UTF-8',
                   'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.4 Safari/537.36'}
    else:
        headers = {'contentType':'text/html;charset=UTF-8',
                   'Cookie':'session=' + session,
                   'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.4 Safari/537.36'}
    http = httplib2.Http('.cache')
    response, content = http.request(url, 'GET', headers=headers)
    if response.status == 200:
        soup = BeautifulSoup(str(content),from_encoding='utf-8')
        #获取所有页面链接
        for links in soup.find_all('a'):
            if links is not None:
                link = links.get('href')
                if link is not None and link != '/' and not link.find('?t_=') > 0:
                    if re.search(r'/$',link):
                        link = link[:-1]
                    if re.search(r'^(http|https)://',link):
                        urlLinks.append(link)
                    elif re.search(r'^//',link):
                        link = urlParse[0] + link
                        urlLinks.append(link)
                    elif re.search(r'^/',link):
                        link = rootURL + link
                        urlLinks.append(link)
                    elif re.search(r'^[^(javascript|#|\\|\'|")]',link):
                        link = url + '/' + link
                        urlLinks.append(link)
        #获取所有图片链接
        for links in soup.find_all('img'):
            if links is not None:
                link = links.get('src')
                if link is not None and link != '/':
                    if re.search(r'/$',link):
                        link = link[:-1]
                    if re.search(r'^(http|https)://',link):
                        imgLinks.append(link)
                    elif re.search(r'^//',link):
                        link = urlParse[0] + link
                        imgLinks.append(link)
                    elif re.search(r'^/',link):
                        link = rootURL + link
                        imgLinks.append(link)
                    else:
                        link = url + '/' + link
                        imgLinks.append(link) 
        #获取所有js链接
        for links in soup.find_all('script'):
            if links is not None:
                link = links.get('src')
                if link is not None and link != '/':
                    if re.search(r'/$',link):
                        link = link[:-1]
                    if re.search(r'^(http|https)://',link):
                        jsLinks.append(link)
                    elif re.search(r'^//',link):
                        link = urlParse[0] + link
                        jsLinks.append(link)
                    elif re.search(r'^/',link):
                        link = rootURL + link
                        jsLinks.append(link)
                    else:
                        link = url + '/' + link
                        jsLinks.append(link) 
        #获取所有css链接
        for links in soup.find_all('link'):
            if links is not None:
                link = links.get('href')
                if link is not None and link != '/':
                    if re.search(r'/$',link):
                        link = link[:-1]
                    if re.search(r'^(http|https)://',link):
                        cssLinks.append(link)
                    elif re.search(r'^//',link):
                        link = urlParse[0] + link
                        cssLinks.append(link)
                    elif re.search(r'^/',link):
                        link = rootURL + link
                        cssLinks.append(link)
                    else:
                        link = url + '/' + link
                        cssLinks.append(link) 
        return response.status,(urlLinks,imgLinks,jsLinks,cssLinks)
    return response.status,url

#检查链接
def checkLink(url):
    headers = {'contentType':'text/html;charset=UTF-8',
               'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.4 Safari/537.36'}
    http = httplib2.Http('.cache')
    response, content = http.request(url, 'GET', headers=headers)
    if response.status == 200:
        logging.info(str(response.status) + ', ' + url)
    else:
        logging.error(str(response.status) + ', ' + url)
    return response.status,url

#链接分类 过滤掉站外链接
def classifyLinks(urlList,baseURL,checkList,checkedList,checkNext):
    for i in range(len(urlList)):
        if len(urlList[i]) > 0:
            for link in urlList[i]:
                if link.find(baseURL) > 0 and link not in checkList and link not in checkedList:
                    checkList.append(link)
                    if i == 0:
                        checkNext.append(link)
                    print(link)
    return checkList,checkedList,checkNext

#获取登录Session
def getSession(url, postData):
    if sys.version_info[0] == 3:
        from urllib.parse import urlencode  
        postData = urlencode(postData)
    else:
        import urllib
        postData = urllib.urlencode(postData)
    headers = {'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
               'X-Requested-With':'XMLHttpRequest',
               'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.4 Safari/537.36'}
    http = httplib2.Http('.cache')
    response, content = http.request(url, 'POST', postData, headers=headers)
    if response.status == 200:
        match = re.search(r'true,"message":"(\w*)"',str(content))
        if match is not None:
            session = match.group(1)
            return response.status,session
        else:
            return 0,str(content)
    else:
        return response.status,str(content)

def main():
    homePage = 'http://www.example.com' #首页链接
    urlParse = homePage.split('/')
    baseURL = urlParse[2][len(urlParse[2].split('.')[0])+1:] #获取根域名
    checkList = []
    checkedList = []
    checkNext = []
    errorLinks = []
    pageNum = 0
    ifLogin = 1 #是否登录开关
    session = None
    if ifLogin:
        url = homePage + '/admin/user/login'
        postData = {'username':'username@yunlai.cn',
                    'password':'password',
                    'remeber':'0'}
        status,session = getSession(url,postData)
        if status != 200:
            logging.error(session)
            session = None
        else:
            session = session
    status,urlList = getURL(homePage,session)
    if status == 200:
        checkList,checkedList,checkNext = classifyLinks(urlList,baseURL,checkList,checkedList,checkNext)
        while True:
            if len(checkList) > 0:
                pageNum += 1
                logging.info('开始检查第 ' + str(pageNum) + ' 层链接')
                for link in checkList:
                    status,url = checkLink(link)
                    if status != 200:
                        errorLinks.append((status,url))
                    checkedList.append(link)
                del checkList[:]
            if len(checkNext) > 0:
                checkNextN = []
                for link in checkNext:
                    status,urlList = getURL(link,session)
                    if status == 200:
                        checkList,checkedList,checkNextN = classifyLinks(urlList,baseURL,checkList,checkedList,checkNextN)
                checkNext = checkNextN
            else:
                logging.info('链接检查完毕')
                break
        for link in errorLinks:
            print(link)
    else:
        logging.error('[ ' + str(status) + ' ] ' + urlList)
    
if __name__ == '__main__':
    main()
