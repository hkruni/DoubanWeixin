#encoding=utf-8

import hashlib
import re
import time

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt
import requests

import MessageTemplate
import xml.etree.ElementTree as ET


@csrf_exempt
def handleRequest(request):
    if request.method == 'GET':
        response = HttpResponse(checkSignature(request),content_type='text/plain')
        return response
    elif request.method == 'POST':
        response = HttpResponse(responseMsg(request),content_type='application/xml')
        return response
    else:
        return  None

def checkSignature(request):
    # global TOKEN
    signature = request.GET.get("signature")
    timestamp = request.GET.get("timestamp")
    nonce = request.GET.get("nonce")
    echoStr = request.GET.get("echostr")
    
    token = "cmccyjs"
    tmpList = [token,timestamp,nonce]
    tmpList.sort()
    # tmpStr = "{0}{1}{2}".format(tmpList[0],tmpList[1],tmpList[2])
    tmpStr = "%s%s%s"%tuple(tmpList)
    tmpStr = hashlib.sha1(tmpStr.encode('utf-8')).hexdigest()
    if tmpStr == signature:
        return echoStr
    else:
        return None
        

#对查询参数进行搜索，获取指定电影的ID号
def get_movie_id(m_name):
    url = 'https://movie.douban.com/subject_search?search_text='+m_name
    r = requests.get(url)
    content = r.content.decode('utf-8')
    pattern = re.compile(r'<a href="https://movie.douban.com/subject/(\d+)/"')
    m_id = re.findall(pattern,content)
    
    if m_id != []:
        m_id = str(m_id[0])
        return m_id
    else:
        return None
        
#通过电影ID号获取电影影评
def get_movie_reviews(m_name):
    # try:
        # url = 'https://movie.douban.com/subject/'+get_movie_id()+'/reviews'
    url = 'https://m.douban.com/movie/subject/'+get_movie_id(m_name)
    re_r = requests.get(url)
    try:
        r_content = re_r.content
        #匹配影评标题和链接
        pattern = re.compile(r'<a href="/movie/review/(\d+)/">\s*<h3>(.*?)</h3>')
        m_reviews = re.findall(pattern,r_content)
        #匹配电影名称
        patName = re.compile(r'<section class="subject-reviews">\s*<h2>(.*?)的影评\((\d+)\)</h2>')
        tmp_name = re.findall(patName,r_content)
        movie_name = tmp_name[0][0]
        movie_reviews = []
        for xx in m_reviews:
            r_url = 'https://m.douban.com/movie/review/'+xx[0]
            r_title = xx[1]
            r_reviews = "【"+r_title+"】"+r_url
            movie_reviews.append(r_reviews)
            
        movie_review = "电影【%s】的热门影评：\n%s\n%s\n%s"%(movie_name,movie_reviews[0],movie_reviews[1],movie_reviews[2])
        return movie_review
    except:
        movie_review = "抱歉，没有匹配到电影名，请检查输入……"
        return movie_review

def get_lj_home():
    
    url = 'http://bj.lianjia.com/ershoufang/'
    district_list = ['xicheng','dongcheng','haidian','chaoyang','fengtai']
    #district_list = ['xicheng','dongcheng','haidian','chaoyang','fengtai','shijingshan','tongzhou','changping','shunyi']
    items = []
    pattern = re.compile(r'二手房真实房源(\d+)套')
    cc = requests.get('http://bj.lianjia.com/ershoufang/').content
    num_bj =  re.search(pattern,cc).group(1)
    items.append(num_bj)
    
    for district in district_list:
        r = requests.get(url + district + '/')
        r_content = r.content
        num = re.search(pattern,r_content).group(1)
        items.append(str(num))
    print len(items)
    #item = "北京:%s,西城:%s"%(items[0],items[1])
    item = "北京:%s,西城:%s,东城:%s,海淀:%s,朝阳:%s,丰台:%s"%(items[0],items[1],items[2],items[3],items[4],items[5])
    print item
    return item
    pass
          
#响应请求
def responseMsg(request):
    requestMsg = smart_str(request.body)#获取POST数据
    #print requestMsg
    msg = ET.fromstring(requestMsg)#从字符串中读取数据
    fromUser = msg.find("ToUserName").text
    toUser = msg.find("FromUserName").text
    mtype = msg.find("MsgType").text
    times = str(int(time.time()))
    if mtype == 'text':
        
        m_name = msg.find("Content").text
        
        if m_name == u'链家':
            items = get_lj_home()
            xmlMsg = MessageTemplate.textmessage % (toUser,fromUser,times,"text",items)
        else:
            movie_revi = get_movie_reviews(m_name)
            xmlMsg = MessageTemplate.textmessage % (toUser,fromUser,times,"text",movie_revi)

        
    else:
        item1 = MessageTemplate.item % ("标题一","标题一的描述","http://1650x7y063.imwork.net/static/images/1.jpg","https://www.baidu.com")
        item2 = MessageTemplate.item % ("标题一","标题一的描述","http://1650x7y063.imwork.net/static/images/2.jpg","http://www.douban.com")
        item = item1 + item2
        xmlMsg = MessageTemplate.newsmessage %(toUser,fromUser,times,"news",2,item)
        
        
    return xmlMsg