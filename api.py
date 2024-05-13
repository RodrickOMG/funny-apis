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
    city = request.args.get('city', 'dalian')  # 默认值为'dalian'
    county_id = 101070201
    word = '大连'
    if city == 'dalian':
        county_id = 101070201
        word = '大连'
    elif city == 'chongqing':
        county_id = 101040100
        word = '重庆'
    # 获取字符串格式的html_doc。由于content为bytes类型，故需要decode()
    html_doc = requests.get('https://m.baidu.com/sf?county_id='+str(county_id)+'&dspName=iphone&ext=%7B%22bar_'
                            'sort%22%3A%22chuanyi%2Cchuyou%2Cxiche%2Chuazhuang%2Cganmao%2Cfangshai%2C%22%2C%22sf_'
                            'tab_name%22%3A%22chuanyi%22%7D&from_sf=1&fromapp=vsgo&openapi=1&pd=life_compare_weather'
                            '&resource_id=4599&title=生活气象指数&word='+word+'&fromSite=pc', headers=headers).content.decode()
    # 使用BeautifulSoup模块对页面文件进行解析
    soup = BeautifulSoup(html_doc, 'html.parser')
    # 查找所有class为'detail_life_zhishu'的ul元素中的li元素
    text = soup.find('p', class_='sfc-weather-number-today-desc c-color-gray-a c-gap-top')
    print(str(text))
    return str(text)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)