import requests
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os
import sys
from datetime import datetime

# ========== 获取金融新闻 ==========
def fetch_news():
    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "category": "business",
            "language": "zh",
            "apiKey": "demo"  # 需要你自己去 newsapi.org 注册一个免费 key
        }
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        articles = data.get("articles", [])
        news_list = []
        for a in articles[:10]:  # 取前10条
            news_list.append({
                "title": a["title"],
                "source": a["source"]["name"],
                "url": a["url"]
            })
        return news_list
    except Exception as e:
        return [{"title": f"获取新闻失败: {e}", "source": "", "url": ""}]

# ========== 生成解读 ==========
def interpret_news(news_list):
    interpretations = []
    for n in news_list:
        if "美联储" in n["title"]:
            impact = "可能影响全球资金流向，利好新兴市场（包括中国股市）。"
        elif "油价" in n["title"]:
            impact = "油价波动会影响能源板块（中石油、中海油等）。"
        elif "科技" in n["title"]:
            impact = "科技政策或新闻可能影响半导体、人工智能板块。"
        else:
            impact = "整体影响中性，需要结合市场情绪。"
        interpretations.append((n["title"], impact))
    return interpretations

# ========== 生成PDF ==========
def generate_pdf(news_list, interpretations, filename):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("📊 每日金融市场报告", styles["Title"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 20))

    data = [["新闻标题", "解读及市场影响"]]
    for (title, impact) in interpretations:
        data.append([title, impact])

    table = Table(data, colWidths=[250, 250])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    story.append(table)
    doc.build(story)

# ========== 发送邮件 ==========
def send_email(pdf_file):
    sender = os.environ["EMAIL_USER"]
    password = os.environ["EMAIL_PASS"]
    receiver = os.environ["EMAIL_RECEIVER"]

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = "每日金融市场报告"

    msg.attach(MIMEText("您好，附件是今日的金融市场报告，请查收。", "plain", "utf-8"))

    with open(pdf_file, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(pdf_file)}")
    msg.attach(part)

    with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)

# ========== 主程序 ==========
def main(mode):
    news = fetch_news()
    interpretations = interpret_news(news)

    pdf_file = f"report_{mode}_{datetime.now().strftime('%Y%m%d')}.pdf"
    generate_pdf(news, interpretations, pdf_file)
    send_email(pdf_file)
    print(f"{mode} 报告已生成并发送: {pdf_file}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"
    main(mode)
