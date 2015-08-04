#!/usr/bin/env python
#coding=utf-8

#Todo: 页面链接有效性检查
#Author: 归根落叶
#Blog: http://this.ispenn.com

import os,sys
try:
    import httplib2  
except ImportError as e:
    os.system('pip install -U httplib2')
    import httplib2
try:
    from bs4 import BeautifulSoup
except ImportError as e:
    os.system('pip install -U beautifulsoup4')
    from bs4 import BeautifulSoup
from urllib.parse import urlencode  
import re
import logging
import smtplib  
from email.mime.text import MIMEText  
 
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
    resLinks = []
    linkTypes = {'a':'href','iframe':'src','img':'src','script':'src','link':'href'}
    urlParse = url.split('/')
    rootURL = urlParse[0] + '//' + urlParse[2]
    if session is None:
        headers = {'contentType':'text/html;charset=UTF-8',
                   'Cache-Control':'no-cache',
                   'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.4 Safari/537.36'}
    else:
        headers = {'contentType':'text/html;charset=UTF-8',
                   'Cache-Control':'no-cache',
                   'Cookie':'session=' + session,
                   'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.4 Safari/537.36'}
    http = httplib2.Http()
    try:
        response, content = http.request(url, 'GET', headers=headers)
    except Exception as e:
        logging.error(str(e) + ', ' + url)
        return 5001,url       
    if response.status == 200:
        try:
            soup = BeautifulSoup(str(content),'html.parser',from_encoding='utf-8')
            #获取所有页面链接
            for linkType in linkTypes:
                for links in soup.find_all(linkType):
                    if links is not None:
                        link = links.get(linkTypes[linkType])
                        if link is not None and link != '' and link != '/' and not link.find('t_=') > 0:
                            if re.search(r'^(\\\'|\\")',link):
                                link = link[2:-2]
                            if re.search(r'/$',link):
                                link = link[:-1]
                            if re.search(r'^(http://.|https://.)',link):
                                if linkType in ['a','iframe']:
                                    urlLinks.append((link,url))
                                else:
                                    resLinks.append((link,url))
                            elif re.search(r'^(//)',link):
                                link = urlParse[0] + link
                                if linkType in ['a','iframe']:
                                    urlLinks.append((link,url))
                                else:
                                    resLinks.append((link,url))
                            elif re.search(r'^/',link):
                                link = rootURL + link
                                if linkType in ['a','iframe']:
                                    urlLinks.append((link,url))
                                else:
                                    resLinks.append((link,url))
                            elif re.search(r'^(../)',link):
                                step = link.count('../')
                                link = link.replace('../','')
                                upStep = step - (len(urlParse)-4)
                                if upStep >= 0:
                                    link = rootURL  + '/' + link
                                else:
                                    upStep = (len(urlParse)-4) - step
                                    linkTemp = ''
                                    for linkTmp in urlParse[3:-(upStep+1)]:
                                        linkTemp = linkTemp + '/' + linkTmp
                                    link = rootURL + linkTemp + '/' + link
                                if linkType in ['a','iframe']:
                                    urlLinks.append((link,url))
                                else:
                                    resLinks.append((link,url))
                            elif not re.search(r'(:|#)',link):
                                link = url + '/' + link
                                if linkType in ['a','iframe']:
                                    urlLinks.append((link,url))
                                else:
                                    resLinks.append((link,url))
                            print(link)
            return response.status,{'urlLinks':urlLinks,'resLinks':resLinks}
        except Exception as e:
            logging.error(str(e) + ', ' + url)
            return 5001,url 
    return response.status,url

#检查链接
def checkLink(url,session=None):
    if session is None:
        headers = {'contentType':'text/html;charset=UTF-8',
                   'Cache-Control':'no-cache',
                   'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.4 Safari/537.36'}
    else:
        headers = {'contentType':'text/html;charset=UTF-8',
                   'Cache-Control':'no-cache',
                   'Cookie':'session=' + session,
                   'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.4 Safari/537.36'}
    http = httplib2.Http()
    try:
        response, content = http.request(url[0], 'GET', headers=headers)
    except Exception as e:
        logging.error(str(e) + ', ' + url[0] + ', ' + url[1])
        return 5001,url
    if response.status == 200:
        logging.info(str(response.status) + ', ' + url[0] + ', ' + url[1])
    else:
        logging.error(str(response.status) + ', ' + url[0] + ', ' + url[1])
    return response.status,url

#链接分类 过滤掉站外链接
def classifyLinks(urlList,baseURL,checkList,checkedList,checkNext):
    for linkType in urlList:
        if len(urlList[linkType]) > 0:
            for link in urlList[linkType]:
                if link[0].split('/')[2].find(baseURL) > 0 and link not in checkList and link[0] not in checkedList:
                    checkList.append(link)
                    if linkType == 'urlLinks':
                        checkNext.append(link)
    return checkList,checkNext

#获取登录Session
def getSession(url, postData):
    headers = {'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
               'X-Requested-With':'XMLHttpRequest',
               'Cache-Control':'no-cache',
               'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.4 Safari/537.36'}
    http = httplib2.Http()
    response, content = http.request(url, 'POST', urlencode(postData), headers=headers)
    if response.status == 200:
        match = re.search(r'true,"message":"(\w*)"',str(content))
        if match is not None:
            session = match.group(1)
            return response.status,session
        else:
            return 0,str(content)
    else:
        return response.status,str(content)

#发送通知邮件
def sendMail(text):
    sender = 'no-reply@example.com'  
    receiver = ['penn@example.com']
    mailToCc = ['penn@example.cn']
    subject = '[AutomantionTest]站点链接有效性扫描结果通知'  
    smtpserver = 'smtp.exmail.qq.com'  
    username = 'no-reply@example.com'  
    password = 'password'  
    
    msg = MIMEText(text,'html','utf-8')      
    msg['Subject'] = subject  
    msg['From'] = sender
    msg['To'] = ';'.join(receiver)
    msg['Cc'] = ';'.join(mailToCc)
    smtp = smtplib.SMTP()  
    smtp.connect(smtpserver)  
    smtp.login(username, password)  
    smtp.sendmail(sender, receiver + mailToCc, msg.as_string())  
    smtp.quit()  

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
        loginUrl = homePage + '/admin/user/login'
        postData = {'username':'username@example.com',
                    'password':'password',
                    'remeber':'0'}
        status,session = getSession(loginUrl,postData)
        if status != 200:
            logging.error(session)
            session = None
    status,urlList = getURL(homePage,session)
    if status == 200:
        checkList,checkNext = classifyLinks(urlList,baseURL,checkList,checkedList,checkNext)
        while True:
            if len(checkList) > 0:
                pageNum += 1
                logging.info('开始检查第 ' + str(pageNum) + ' 层链接')
                if ifLogin:
                    status,session = getSession(loginUrl,postData)
                    if status != 200:
                        logging.error(session)
                        session = None
                for link in checkList:
                    status,url = checkLink(link,session)
                    if status != 200:
                        errorLinks.append((status,url))
                    checkedList.append(link[0])
                del checkList[:]
            if len(checkNext) > 0:
                checkNextN = []
                if ifLogin:
                    status,session = getSession(loginUrl,postData)
                    if status != 200:
                        logging.error(session)
                        session = None
                for link in checkNext:
                    status,urlList = getURL(link[0],session)
                    if status == 200:
                        checkList,checkNextN = classifyLinks(urlList,baseURL,checkList,checkedList,checkNextN)
                    else:
                        logging.error('[ ' + str(status) + ' ] ' + urlList)
                checkNext = checkNextN
            else:
                logging.info('链接检查完毕，共检查 ' + str(len(checkedList)) + ' 个链接，其中有 ' + str(len(errorLinks)) + ' 个异常链接')
                break
        if len(errorLinks) > 0:
            text = '<html><body><p>共检查 ' + str(len(checkedList)) + ' 个链接，其中有 ' + str(len(errorLinks)) + ' 个异常链接，列表如下：' + '</p><table><tr><th>Http Code</th><th>Url</th><th>Referer Url</th></tr>'
            for link in errorLinks:
                text = text + '<tr><td>' + str(link[0]) + '</td><td>' + link[1][0] + '</td><td>' + link[1][1] + '</td></tr>'
            text = text + '</table></body></html>'
            sendMail(text)
    else:
        logging.error('[ ' + str(status) + ' ] ' + urlList)
    
if __name__ == '__main__':
    main()
