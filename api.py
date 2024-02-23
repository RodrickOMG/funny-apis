#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：morningReport 
@File    ：api.py
@Author  ：Rodrick
@Date    ：2024/2/23 15:30 
'''
from flask import Flask, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/funny-apis/dress-recommend')
def dress_recommend():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
    }
    city = request.args.get('city', 'chongqing')  # 默认值为'chongqing'
    try:
        # 获取字符串格式的html_doc。由于content为bytes类型，故需要decode()
        html_doc = requests.get('https://www.tianqi.com/chuanyi-'+city+'.html', headers=headers).content.decode()
        # 使用BeautifulSoup模块对页面文件进行解析
        soup = BeautifulSoup(html_doc, 'html.parser')
        # 查找所有class为'detail_life_zhishu'的ul元素中的li元素
        li_elements = soup.find('ul', class_='detail_life_zhishu').find_all('li')
    except AttributeError:
        html_doc = requests.get('https://www.tianqi.com/chuanyi-chongqing.html', headers=headers).content.decode()
        # 使用BeautifulSoup模块对页面文件进行解析
        soup = BeautifulSoup(html_doc, 'html.parser')
        # 查找所有class为'detail_life_zhishu'的ul元素中的li元素
        li_elements = soup.find('ul', class_='detail_life_zhishu').find_all('li')
    # 遍历每个li元素，提取和打印信息
    for li in li_elements:
        # 提取指数名称和建议
        if '穿衣指数' in li.find('h2').text.strip():
            status = li.find('span').text.strip()
            suggestion = li.find('p').text.strip()
            return f"{status}，{suggestion}"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)