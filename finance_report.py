import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import os

# 获取环境变量中的敏感信息
email_user = os.getenv('EMAIL_USER')  # 你的QQ邮箱
email_password = os.getenv('EMAIL_PASSWORD')  # QQ邮箱SMTP授权码
to_email = os.getenv('TO_EMAIL')  # 接收邮件的邮箱，可以和你发送邮箱一致

def fetch_exchange_rate():
    """
    获取人民币汇率中间价（示例：从公开来源获取）
    注意：实际使用时请替换为稳定可靠的数据源API
    """
    try:
        # 这里以获取人民币对美元中间价为例，使用了公开数据源
        # 由于真实API可能需要密钥或稳定性考虑，此处使用模拟数据
        today = datetime.now().strftime('%Y-%m-%d')
        # 模拟数据 - 实际应用中应替换为真实的API请求
        # 例如从中国外汇交易中心或其他财经网站获取
        usd_to_cny = 7.1986  # 假设今日汇率
        return {
            'date': today,
            'USD/CNY': usd_to_cny,
            'EUR/CNY': 7.8234,  # 模拟数据
            'JPY/CNY': 0.0482   # 模拟数据（每100日元）
        }
    except Exception as e:
        print(f"获取汇率数据时出错: {e}")
        return None

def fetch_dollar_index():
    """
    获取美元指数（DXY）
    同样使用模拟数据，实际应用中请使用金融数据API（如Investing.com, Alpha Vantage等）
    """
    try:
        # 模拟数据 - 实际应用请调用API
        return {
            'DXY': 98.10,
            'change': -0.30,
            'change_pct': '-0.30%'
        }
    except Exception as e:
        print(f"获取美元指数时出错: {e}")
        return None

def fetch_stock_indices():
    """
    获取全球主要股指（模拟数据）
    """
    # 实际应用中可调用新浪财经、东方财富、Alpha Vantage、Yahoo Finance等的API
    return {
        'SHANGHAI': 3204.56,
        'SHANGHAI_CHG': -0.45,
        'SZ_COMP': 10234.12,
        'SZ_COMP_CHG': 0.12,
        'S&P_500': 4550.43,
        'S&P_500_CHG': 0.89
    }

def create_email_html(data_dict):
    """
    创建HTML格式的邮件内容
    """
    if not data_dict:
        return "<p>今日未能获取到经济数据。</p>"

    html_content = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            h2 { color: #333366; }
            table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
            th, td { border: 1px solid #dddddd; text-align: left; padding: 8px; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .positive { color: green; }
            .negative { color: red; }
        </style>
    </head>
    <body>
        <h2>每日经济数据简报</h2>
        <p>生成时间： <b>""" + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</b></p>
    """

    # 汇率表
    if 'exchange_rate' in data_dict and data_dict['exchange_rate']:
        html_content += """
        <h3>💰 人民币汇率中间价</h3>
        <table>
            <tr><th>货币对</th><th>中间价</th></tr>
        """
        forex = data_dict['exchange_rate']
        html_content += f"<tr><td>美元/人民币</td><td>{forex.get('USD/CNY', 'N/A')}</td></tr>"
        html_content += f"<tr><td>欧元/人民币</td><td>{forex.get('EUR/CNY', 'N/A')}</td></tr>"
        html_content += f"<tr><td>日元/人民币</td><td>{forex.get('JPY/CNY', 'N/A')} (每100日元)</td></tr>"
        html_content += "</table>"

    # 美元指数
    if 'dollar_index' in data_dict and data_dict['dollar_index']:
        dxy = data_dict['dollar_index']
        change_class = "positive" if dxy.get('change', 0) >= 0 else "negative"
        html_content += f"""
        <h3>📊 美元指数 (DXY)</h3>
        <table>
            <tr><th>指数值</th><th>涨跌</th><th>涨跌幅</th></tr>
            <tr>
                <td>{dxy.get('DXY', 'N/A')}</td>
                <td class="{change_class}">{dxy.get('change', 'N/A')}</td>
                <td class="{change_class}">{dxy.get('change_pct', 'N/A')}</td>
            </tr>
        </table>
        """

    # 股票指数
    if 'stock_indices' in data_dict and data_dict['stock_indices']:
        stocks = data_dict['stock_indices']
        html_content += """
        <h3>📈 主要股票指数</h3>
        <table>
            <tr><th>指数</th><th>收盘价</th><th>涨跌</th></tr>
        """
        # 上证指数
        sh_chg_class = "positive" if stocks.get('SHANGHAI_CHG', 0) >= 0 else "negative"
        html_content += f"""
            <tr>
                <td>上证指数</td>
                <td>{stocks.get('SHANGHAI', 'N/A')}</td>
                <td class="{sh_chg_class}">{stocks.get('SHANGHAI_CHG', 'N/A')}</td>
            </tr>
        """
        # 深证成指
        sz_chg_class = "positive" if stocks.get('SZ_COMP_CHG', 0) >= 0 else "negative"
        html_content += f"""
            <tr>
                <td>深证成指</td>
                <td>{stocks.get('SZ_COMP', 'N/A')}</td>
                <td class="{sz_chg_class}">{stocks.get('SZ_COMP_CHG', 'N/A')}</td>
            </tr>
        """
        # 标普500
        sp_chg_class = "positive" if stocks.get('S&P_500_CHG', 0) >= 0 else "negative"
        html_content += f"""
            <tr>
                <td>标普500</td>
                <td>{stocks.get('S&P_500', 'N/A')}</td>
                <td class="{sp_chg_class}">{stocks.get('S&P_500_CHG', 'N/A')}</td>
            </tr>
        """
        html_content += "</table>"

    html_content += """
        <br>
        <p><i>注：本邮件由GitHub Actions自动生成并发送。数据仅供参考，请以官方发布为准。</i></p>
    </body>
    </html>
    """
    return html_content

def send_email(subject, html_content):
    """
    使用QQ邮箱SMTP发送邮件
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = email_user
        msg['To'] = to_email

        # 添加HTML内容
        part_html = MIMEText(html_content, 'html')
        msg.attach(part_html)

        # 连接QQ邮箱SMTP服务器并发送
        server = smtplib.SMTP('smtp.qq.com', 587)
        server.starttls()  # 启用安全传输模式
        server.login(email_user, email_password)
        server.sendmail(email_user, to_email, msg.as_string())
        server.quit()

        print("邮件发送成功！")
        return True
    except Exception as e:
        print(f"发送邮件时出错: {e}")
        return False

def main():
    """主函数，协调数据获取和邮件发送"""
    print("开始获取经济数据...")

    # 获取数据
    exchange_data = fetch_exchange_rate()
    dollar_data = fetch_dollar_index()
    stock_data = fetch_stock_indices()

    data_dict = {
        'exchange_rate': exchange_data,
        'dollar_index': dollar_data,
        'stock_indices': stock_data
    }

    # 生成邮件主题和内容
    today_str = datetime.now().strftime("%Y-%m-%d")
    email_subject = f"每日经济数据简报 ({today_str})"
    email_html_body = create_email_html(data_dict)

    # 发送邮件
    success = send_email(email_subject, email_html_body)
    if not success:
        # 发送失败可以抛出异常或记录日志，GitHub Actions会捕获
        raise Exception("邮件发送失败，请检查配置。")

if __name__ == '__main__':
    main()
