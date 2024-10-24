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
import time
import random
from urllib.parse import quote
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import base64
from io import BytesIO
import logging
import os

app = Flask(__name__)

model = "chatgpt-4o-latest"
api_key = "WKRcLfITficWm"

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('market_report.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@app.route('/openai/romantic')
def openai():
    client = OpenAI(
        api_key=api_key,  # this is also the default, it can be omitted
        base_url='https://ai.liaobots.work/v1'
    )

    response = client.chat.completions.create(
        model=model,
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


@app.route('/cjzzd')
def get_cjzzd_link():
    target_title = "财经早知道"
    base_url = "https://mappsv5.caixin.com/index_page_v5/index_page_{}.json"
    page = 1

    try:
        while page <= 10:  # 限制最多查找10页
            url = base_url.format(page)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            items = data.get('data', {}).get('list', [])
            for item in items:
                if target_title in item.get('audio_title', ''):
                    id = item.get('id', '')
                    if id:
                        type_param = quote("普通文章页")
                        url = f"https://datayi.cn/1lnZaaido8xd?id={id}&article_type=1&isHttp=0&type={type_param}&open_type=6"
                        return url
            
            page += 1
            time.sleep(random.uniform(1, 3))  # 添加随机时,避免请求过于频繁

        return jsonify({"error": "未找到目标标题"}), 404

    except requests.RequestException as e:
        return jsonify({"error": f"请求失败: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"处理失败: {str(e)}"}), 500


@app.route('/get_market_report')
def get_market_report():
    """获取当天的市场报告"""
    try:
        today = datetime.now().strftime("%Y%m%d")
        filename = f"market_report/market_report_{today}.md"
        
        if not os.path.exists(filename):
            return jsonify({
                "status": "error",
                "message": "Today's report is not available yet.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 404
        
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            "status": "success",
            "markdown_content": content,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    except Exception as e:
        logger.error(f"Error in get_market_report endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18000)
