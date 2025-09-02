import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import sys

# =============== 1. 报告数据（这里先写死，后面你可以换成爬虫/接口） ===============
def get_market_data():
    return {
        "大盘指数": [
            ["上证指数", "3,100", "+0.45%"],
            ["深证成指", "10,200", "+0.72%"],
            ["创业板指", "2,050", "+1.10%"]
        ],
        "资金流向": [
            ["北向资金", "+45亿", "连续3日净流入"],
            ["两市成交额", "9,800亿", "放量"]
        ],
        "国际市场": [
            ["美股（标普500）", "5,250", "-0.30%"],
            ["美元指数", "101.2", "-0.20%"],
            ["黄金", "2,350", "+0.50%"],
            ["原油(WTI)", "78.3", "+0.80%"]
        ],
        "行业热点": [
            ["半导体", "库存去化加速，涨价预期增强"],
            ["新能源车", "电池上游锂价回升"],
            ["军工", "中报订单增加，反内卷趋势明显"]
        ]
    }

# =============== 2. 生成PDF报告 ===============
def generate_pdf(report_type, filename="finance_report.pdf"):
    data = get_market_data()
    styles = getSampleStyleSheet()
    story = []

    title = f"📊 财经{report_type}报告 - {datetime.today().strftime('%Y-%m-%d')}"
    story.append(Paragraph(title, styles['Title']))
    story.append(Spacer(1, 20))

    # 遍历每个板块
    for section, content in data.items():
        story.append(Paragraph(f"【{section}】", styles['Heading2']))
        if isinstance(content[0], list):
            table = Table([["指标", "数值", "解读"]] + content, colWidths=[120, 120, 200])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
            ]))
            story.append(table)
        else:
            for line in content:
                story.append(Paragraph(line, styles['Normal']))
        story.append(Spacer(1, 15))

    story.append(Paragraph("📌 投资提示：", styles['Heading2']))
    story.append(Paragraph("1. 科技与半导体库存下降，价格回升 → 有望带动相关板块行情。", styles['Normal']))
    story.append(Paragraph("2. 美元指数走弱，利好人民币与大宗商品。", styles['Normal']))
    story.append(Paragraph("3. 北向资金连续流入，外资偏好科技、医药等成长股。", styles['Normal']))
    story.append(Spacer(1, 20))

    doc = SimpleDocTemplate(filename, pagesize=A4)
    doc.build(story)

# =============== 3. 发送邮件（QQ邮箱） ===============
def send_email(report_type, receiver, sender, password, smtp_server="smtp.qq.com", smtp_port=465):
    filename = f"finance_report_{datetime.today().strftime('%Y%m%d')}.pdf"
    generate_pdf(report_type, filename)

    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = f"📩 财经{report_type}报告 - {datetime.today().strftime('%Y-%m-%d')}"

    # 邮件正文
    body = f"您好，附件是今日的财经{report_type}报告，请查收。\n\n祝投资顺利！"
    msg.attach(MIMEText(body, 'plain'))

    # 添加附件
    with open(filename, "rb") as f:
        part = MIMEApplication(f.read(), Name=filename)
    part['Content-Disposition'] = f'attachment; filename="{filename}"'
    msg.attach(part)

    # 发送邮件
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
      sender = sender.strip()
password = password.strip()

        server.login(sender, password)
        server.send_message(msg)

    print(f"✅ 已发送 {report_type} 报告到 {receiver}")

# =============== 4. 主函数 ===============
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请指定报告类型：daily / weekly / monthly")
        sys.exit(1)

    report_type = sys.argv[1]
    EMAIL_USER = "你的qq邮箱@qq.com"
    EMAIL_PASS = "你的QQ邮箱授权码"  # 注意不是密码，是授权码
    EMAIL_RECEIVER = "接收邮箱@qq.com"

    send_email(report_type, EMAIL_RECEIVER, EMAIL_USER, EMAIL_PASS)

