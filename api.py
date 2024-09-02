#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''
@Project ：morningReport 
@File    ：api.py
@Author  ：Rodrick
@Date    ：2024/2/23 15:30 
'''
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

app = Flask(__name__)


@app.route('/openai/romantic')
def openai():
    client = OpenAI(
        api_key='WKRcLfITficWm',  # this is also the default, it can be omitted
        base_url='https://ai.liaobots.work/v1'
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "你是一个浪漫的文学大师，请每天说一句想要对女朋友说的浪漫情话。"
            },
            {
                "role": "user",
                "content": "请说出今天你想说的一句话。"
            }
        ],
        stream=False,
    )

    return response.choices[0].message.content


@app.route('/dress-recommend')
def dress_recommend():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
    }
    city = request.args.get('city', 'dalian')  # 默认值为'dalian'
    if city == 'dalian':
        county_id = 101070201
        word = '大连'
    elif city == 'chongqing':
        county_id = 101040100
        word = '重庆'
    else:
        return "City not supported", 400

    try:
        response = requests.get(
            f'https://m.baidu.com/sf?county_id={county_id}&dspName=iphone&ext=%7B%22bar_sort%22%3A%22chuanyi%2Cchuyou%2Cxiche%2Chuazhuang%2Cganmao%2Cfangshai%2C%22%2C%22sf_tab_name%22%3A%22chuanyi%22%7D&from_sf=1&fromapp=vsgo&openapi=1&pd=life_compare_weather&resource_id=4599&title=生活气象指数&word={word}&fromSite=pc',
            headers=headers
        )
        response.raise_for_status()
        html_doc = response.content.decode()
        soup = BeautifulSoup(html_doc, 'html.parser')
        text = soup.find('p', class_='sfc-weather-number-today-desc c-color-gray-a c-gap-top')
        return str(text) if text else "No data available"
    except requests.RequestException as e:
        return str(e), 500


@app.route('/daily-english')
def daily_english():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
    }
    url = "https://apis.tianapi.com/everyday/index"
    params = {
        "key": "your_api_key_here"  # 使用环境变量管理API密钥
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        json_data = response.json()
        return jsonify({
            'content': json_data['result']['content'],
            'note': json_data['result']['note']
        })
    except requests.RequestException as e:
        return str(e), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18000)
