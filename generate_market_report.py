import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import logging
from openai import OpenAI
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import os

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

model = "chatgpt-4o-latest"
api_key = "WKRcLfITficWm"

# 腾讯云 COS 配置
secret_id = 'AKID6HGE4v49KW5jJvlWCuXEnIhxEZsIpKnH'  # 替换为您的 secret_id
secret_key = 'YzRvGPQEyeSEsQC82hTCtZE47IRXhp1A'  # 替换为您的 secret_key
region = 'ap-chongqing'  # 替换为您的地域
bucket = 'rodrick-1258087398'  # 替换为您的存储桶名称

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key)
client = CosS3Client(config)

class MarketReport:
    def __init__(self):
        self.sp500 = "^GSPC"
        self.nasdaq = "^NDX"
    
    def get_market_data(self, symbol, period="30d"):
        """获取市场数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            
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
        """生成走势图并保存为图片文件"""
        try:
            data['MA5'] = data['Close'].rolling(window=5).mean()
            data['MA10'] = data['Close'].rolling(window=10).mean()
            
            data = data[data['Volume'] > 0].copy()
            data = data.tail(7)
            
            if len(data) == 0:
                raise ValueError(f"No trading data available for {symbol}")
            
            fig = go.Figure()
            
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
            
            ma5_data = data[data['MA5'].notna()]
            fig.add_trace(go.Scatter(
                x=ma5_data.index,
                y=ma5_data['MA5'],
                name='MA5',
                line=dict(color='purple', width=1),
                showlegend=True
            ))
            
            ma10_data = data[data['MA10'].notna()]
            fig.add_trace(go.Scatter(
                x=ma10_data.index,
                y=ma10_data['MA10'],
                name='MA10',
                line=dict(color='orange', width=1),
                showlegend=True
            ))
            
            fig.update_layout(
                title=f"{symbol} 7日K线图",
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
            
            fig.update_xaxes(
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),
                    dict(values=data.index[data['Volume'] == 0])
                ]
            )

            # 创建 market_report 目录（如果不存在）
            os.makedirs('market_report', exist_ok=True)
            
            filename = f"market_report/{symbol.lower()}_chart_{datetime.now().strftime('%Y%m%d')}.png"
            filepath = Path(filename)
            fig.write_image(filepath, scale=0.8, engine='kaleido')
            
            with filepath.open('rb') as f:
                client.put_object(
                    Bucket=bucket,
                    Body=f,
                    Key=filename,
                    EnableMD5=False
                )
            
            url = client.get_object_url(
                Bucket=bucket,
                Key=filename
            )
            
            # 删除本地图片文件
            os.remove(filepath)
            logger.info(f"Local file {filepath} has been deleted after uploading to COS.")
            
            return url
        
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

    def generate_markdown(self, sp500_data, nasdaq_data, sp500_chart_url, nasdaq_chart_url):
        """生成带有市场分析的Markdown报告"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            sp500_analysis = self.get_market_analysis_from_gpt(sp500_data, "标普500指数")
            nasdaq_analysis = self.get_market_analysis_from_gpt(nasdaq_data, "纳斯达克100指数")
            
            markdown = f"""# 市场简报

## 标普500指数分析
![SP500走势图]({sp500_chart_url})

**当前价格：** {sp500_data['current']} ({'+' if sp500_data['change'] > 0 else ''}{sp500_data['change']}%)
**日内区间：** {sp500_data['low']} - {sp500_data['high']}
**近期区间：** {sp500_data['week_low']} - {sp500_data['week_high']}

{sp500_analysis}

## 纳斯达克100指数分析
![NASDAQ走势图]({nasdaq_chart_url})

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
            # 创建 market_report 目录（如果不存在）
            os.makedirs('market_report', exist_ok=True)
            filename = f"market_report/market_report_{datetime.now().strftime('%Y%m%d')}.md"
            filepath = Path(filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            return str(filepath)
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            raise

def generate_market_report():
    """生成报告的主函数"""
    try:
        report = MarketReport()
        
        sp500_hist = report.get_market_data(report.sp500)
        nasdaq_hist = report.get_market_data(report.nasdaq)
        
        sp500_metrics = report.calculate_metrics(sp500_hist)
        nasdaq_metrics = report.calculate_metrics(nasdaq_hist)
        
        sp500_chart_url = report.generate_chart(sp500_hist, "SP500")
        nasdaq_chart_url = report.generate_chart(nasdaq_hist, "NASDAQ")
        
        markdown_content = report.generate_markdown(
            sp500_metrics, 
            nasdaq_metrics,
            sp500_chart_url,
            nasdaq_chart_url
        )
        
        filepath = report.save_report(markdown_content)
        
        logger.info(f"Report generated successfully: {filepath}")
        
    except Exception as e:
        logger.error(f"Error in generate_market_report: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    generate_market_report()
