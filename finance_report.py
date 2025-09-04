import os
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ===== 获取金融数据 =====
def fetch_data():
    data = {}
    try:
        # 美元指数
        dxy = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=DX-Y.NYB").json()
        data["美元指数"] = dxy["quoteResponse"]["result"][0]["regularMarketPrice"]

        # 黄金价格
        gold = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=GC=F").json()
        data["黄金期货"] = gold["quoteResponse"]["result"][0]["regularMarketPrice"]

        # 上证指数
        sh = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=000001.SS").json()
        data["上证指数"] = sh["quoteResponse"]["result"][0]["regularMarketPrice"]

        # 恒生指数
        hs = requests.get("https://query1.finance.yahoo.com/v7/finance/quote?symbols=^HSI").json()
        data["恒生指数"] = hs["quoteResponse"]["result"][0]["regularMarketPrice"]

    except Exception as e:
        data["error"] = str(e)
    return data

# ===== 解读逻辑 =====
def interpret(data):
    insights = []
    if "美元指数" in data and data["美元指数"] > 100:
        insights.append("美元指数偏强 → 对人民币汇率和A股资金面可能形成压力。")
    else:
        insights.append("美元指数走弱 → 有利于资金回流新兴市场，利好A股和港股。")

    if "黄金期货" in data and data["黄金期货"] > 2000:
        insights.append("黄金价格高企 → 市场避险情绪较强，短期可能不利于股市。")
    else:
        insights.append("黄金下行 → 投资者风险偏好回升，利好股市。")

    if "上证指数" in data and data["上证指数"] < 3000:
        insights.append("上证指数低位运行 → 市场信心不足，但可能存在价值机会。")
    else:
        insights.append("上证指数稳健 → A股整体市场环境偏积极。")

    if "恒生指数" in data and data["恒生指数"] < 18000:
        insights.append("恒生指数承压 → 港股流动性不足，需要关注外资动向。")
    else:
        insights.append("恒生指数企稳 → 港股有望出现结构性机会。")

    return insights

# ===== 生成 HTML 报告 =====
def generate_report(report_type):
    data = fetch_data()
    insights = interpret(data)

    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    html = f"""
    <html>
      <body>
        <h2>{report_type.capitalize()} 投资报告 ({today})</h2>
        <h3>📊 市场数据</h3>
        <table border="1" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
          <tr><th>指标</th><th>数值</th></tr>
    """

    for key, value in data.items():
        if key != "error":
            html += f"<tr><td>{key}</td><td>{value}</td></tr>"

    html += """
        </table>
        <h3>📌 解读</h3>
        <ul>
    """
    for ins in insights:
        html += f"<li>{ins}</li>"

    html += """
        </ul>
      </body>
    </html>
    """
    return html

# ===== 发送邮件 =====
def send_email(report_type, receiver, sender, password):
    report_html = generate_report(report_type)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📈 {report_type.capitalize()} 投资报告"
    msg["From"] = sender
    msg["To"] = receiver

    msg.attach(MIMEText(report_html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())

# ===== 主程序入口 =====
if __name__ == "__main__":
    import sys
    report_type = sys.argv[1] if len(sys.argv) > 1 else "daily"

    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

    send_email(report_type, EMAIL_RECEIVER, EMAIL_USER, EMAIL_PASS)
