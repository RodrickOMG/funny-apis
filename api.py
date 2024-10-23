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
            time.sleep(random.uniform(1, 3))  # 添加随机���时,避免请求过于频繁

        return jsonify({"error": "未找到目标标题"}), 404

    except requests.RequestException as e:
        return jsonify({"error": f"请求失败: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"处理失败: {str(e)}"}), 500


class MarketReport:
    def __init__(self):
        self.sp500 = "^GSPC"
        self.nasdaq = "^NDX"
        self.report_path = Path("reports")
        self.report_path.mkdir(exist_ok=True)
    
    def get_market_data(self, symbol, period="30d"):  # 保持30天数据以确保有足够数据计算均线
        """获取市场数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)  # 获取30天的数据
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                raise ValueError(f"No data retrieved for {symbol}")
            return hist
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            raise
    
    def calculate_metrics(self, data):
        """计算关键指标"""
        try:
            latest = data.iloc[-1]
            previous = data.iloc[-2]
            change = ((latest['Close'] - previous['Close']) / previous['Close']) * 100
            
            week_high = data['High'].max()
            week_low = data['Low'].min()
            
            return {
                'current': round(latest['Close'], 2),
                'change': round(change, 2),
                'volume': int(latest['Volume']),
                'high': round(latest['High'], 2),
                'low': round(latest['Low'], 2),
                'week_high': round(week_high, 2),
                'week_low': round(week_low, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            raise
    
    def generate_chart(self, data, symbol):
        """生成走势图"""
        try:
            # 计算均线（使用完整数据）
            data['MA5'] = data['Close'].rolling(window=5).mean()
            data['MA10'] = data['Close'].rolling(window=10).mean()
            
            # 只保留最近7个交易日的数据用于显示
            data = data[data['Volume'] > 0].copy()
            data = data.tail(7)  # 改为获取最后7个交易日的数据
            
            if len(data) == 0:
                raise ValueError(f"No trading data available for {symbol}")
            
            fig = go.Figure()
            
            # K线图
            fig.add_trace(go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name=symbol,
                increasing_line_color='red',
                decreasing_line_color='green'
            ))
            
            # 添加5日均线
            ma5_data = data[data['MA5'].notna()]
            fig.add_trace(go.Scatter(
                x=ma5_data.index,
                y=ma5_data['MA5'],
                name='MA5',
                line=dict(color='purple', width=1),
                showlegend=True
            ))
            
            # 添加10日均线
            ma10_data = data[data['MA10'].notna()]
            fig.add_trace(go.Scatter(
                x=ma10_data.index,
                y=ma10_data['MA10'],
                name='MA10',
                line=dict(color='orange', width=1),
                showlegend=True
            ))
            
            # 更新布局
            fig.update_layout(
                title=f"{symbol} 7日K线图",  # 更新标题
                yaxis_title='价格',
                xaxis_title='日期',
                height=500,
                width=800,
                template='plotly_white',
                showlegend=True,
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01
                ),
                xaxis_rangeslider_visible=False
            )
            
            # 更新X轴以只显示交易日
            fig.update_xaxes(
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),
                    dict(values=data.index[data['Volume'] == 0])
                ]
            )
            
            buffer = BytesIO()
            fig.write_image(
                buffer, 
                format="png",
                scale=0.8,  # 适当调整分辨率
                engine='kaleido'
            )
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode()
        
        except Exception as e:
            logger.error(f"Error generating chart for {symbol}: {str(e)}")
            raise
    
    def get_market_analysis_from_gpt(self, market_data, market_name):
        """使用GPT生成市场分析"""
        try:
            client = OpenAI(
                api_key=api_key,
                base_url='https://ai.liaobots.work/v1'
            )
            
            # 构建提示信息
            prompt = f"""作为一位专业的金融分析师，请对{market_name}近期走势进行专业分析，结合最新相关新闻及市场动态。以下是关键数据：
- 最新收盘价：{market_data['current']}
- 日涨跌幅：{market_data['change']}%
- 成交量：{market_data['volume']:,}
- 日内最高：{market_data['high']}
- 日内最低：{market_data['low']}
- 近期最高：{market_data['week_high']}
- 近期最低：{market_data['week_low']}

请用专业但易懂的语言进行分析，控制在300字以内。"""

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位专业的金融市场分析师，擅长技术分析和市场研判。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            logger.error(f"Error getting GPT analysis: {str(e)}")
            return "无法获取AI分析"

    def generate_markdown(self, sp500_data, nasdaq_data, sp500_chart, nasdaq_chart):
        """生成带有市场分析的Markdown报告"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 获取GPT分析
            sp500_analysis = self.get_market_analysis_from_gpt(sp500_data, "标普500指数")
            nasdaq_analysis = self.get_market_analysis_from_gpt(nasdaq_data, "纳斯达克100指数")
            
            markdown = f"""# 市场简报 {today}

## 标普500指数分析
![SP500走势图](data:image/png;base64,{sp500_chart})

**当前价格：** {sp500_data['current']} ({'+' if sp500_data['change'] > 0 else ''}{sp500_data['change']}%)
**日内区间：** {sp500_data['low']} - {sp500_data['high']}
**近期区间：** {sp500_data['week_low']} - {sp500_data['week_high']}

{sp500_analysis}

## 纳斯达克100指数分析
![NASDAQ走势图](data:image/png;base64,{nasdaq_chart})

**当前价格：** {nasdaq_data['current']} ({'+' if nasdaq_data['change'] > 0 else ''}{nasdaq_data['change']}%)
**日内区间：** {nasdaq_data['low']} - {nasdaq_data['high']}
**近期区间：** {nasdaq_data['week_low']} - {nasdaq_data['week_high']}

{nasdaq_analysis}

---
*本报告由AI助手生成，仅供参考，不构成投资建议。*
更新时间: {datetime.now().strftime("%H:%M:%S")}
"""
            return markdown
        except Exception as e:
            logger.error(f"Error generating markdown: {str(e)}")
            raise

    def save_report(self, markdown_content):
        """保存报告到文件"""
        try:
            filename = f"market_report_{datetime.now().strftime('%Y%m%d')}.md"
            filepath = self.report_path / filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            raise


@app.route('/generate_market_report')
def generate_market_report():
    """生成报告的API端点"""
    try:
        report = MarketReport()
        
        # 获取数据
        sp500_hist = report.get_market_data(report.sp500)
        nasdaq_hist = report.get_market_data(report.nasdaq)
        
        # 计算指标
        sp500_metrics = report.calculate_metrics(sp500_hist)
        nasdaq_metrics = report.calculate_metrics(nasdaq_hist)
        
        # 生成图表
        sp500_chart = report.generate_chart(sp500_hist, "SP500")
        nasdaq_chart = report.generate_chart(nasdaq_hist, "NASDAQ")
        
        # 生成markdown
        markdown_content = report.generate_markdown(
            sp500_metrics, 
            nasdaq_metrics,
            sp500_chart,
            nasdaq_chart
        )
        
        # 保存报告
        # filepath = report.save_report(markdown_content)
        
        return jsonify({
            "status": "success",
            "markdown_content": markdown_content,
            "sp500": sp500_metrics,
            "nasdaq": nasdaq_metrics,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    
    except Exception as e:
        logger.error(f"Error in generate_report endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=18000)
