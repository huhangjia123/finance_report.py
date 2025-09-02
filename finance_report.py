import os
import requests
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========== 邮箱配置 ==========
import os

SENDER_EMAIL = os.getenv("EMAIL_USER")
SENDER_PASSWORD = os.getenv("EMAIL_PASS")
RECEIVER_EMAIL = os.getenv("EMAIL_RECEIVER")


# ========== 获取数据 ==========
def get_data():
    # 免费API示例（可根据需要换更权威数据源）
    try:
        # 美元指数（示例接口）
        dxy = requests.get("https://www.alphavantage.co/query?function=DOLLAR_INDEX&apikey=demo").json().get("value", 104.3)
        # 人民币汇率
        usd_cny = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=CNY").json()["rates"]["CNY"]
        # 股指示例（你可以换成真实数据API）
        shanghai = 3150
        hang_seng = 18500
        sp500 = 5200
        # 大宗商品示例
        wti = 78.5
        gold = 1940
        # 债券收益率
        cn10y = "2.55%"
        us10y = "4.25%"
        # PMI示例（固定数据，宏观数据每月更新）
        manufacturing_pmi = 50.5
        services_pmi = 52.1
        M1 = "3.2%"
        M2 = "8.5%"
        
        return {
            "美元指数": round(dxy,2),
            "人民币汇率": round(usd_cny,4),
            "上证综指": shanghai,
            "恒生指数": hang_seng,
            "标普500": sp500,
            "WTI原油": wti,
            "黄金": gold,
            "中国10年期国债": cn10y,
            "美国10年期国债": us10y,
            "制造业PMI": manufacturing_pmi,
            "服务业PMI": services_pmi,
            "M1": M1,
            "M2": M2
        }
    except Exception as e:
        print("⚠️ 获取数据失败:", e)
        return {}

# ========== 生成日报 ==========
def generate_report(data):
    today = datetime.date.today().strftime("%Y/%m/%d")
    report = f"""📊 每日金融数据简报（{today}）

1. 外汇 & 美元指数
- 美元指数 DXY：{data.get('美元指数')}
  🔎 美元走强，可能对人民币贬值造成压力
- 人民币汇率 USD/CNY：{data.get('人民币汇率')}
  🔎 人民币小幅波动，受美元走势影响

2. 货币供应（最新月度）
- M1 同比：{data.get('M1')}
  🔎 企业短期资金活跃度一般
- M2 同比：{data.get('M2')}
  🔎 流动性宽松，政策偏稳健

3. 宏观景气
- 制造业 PMI：{data.get('制造业PMI')}
  🔎 高于荣枯线，制造业保持扩张
- 服务业 PMI：{data.get('服务业PMI')}
  🔎 消费和服务业回暖

4. 股指表现
- 上证综指：{data.get('上证综指')}
  🔎 政策推动下市场情绪改善
- 恒生指数：{data.get('恒生指数')}
  🔎 港股反弹，科技股带动
- 标普500：{data.get('标普500')}
  🔎 美股高位震荡，受利率预期影响

5. 大宗商品
- WTI 原油：{data.get('WTI原油')} 美元/桶
  🔎 地缘风险推升油价
- 黄金：{data.get('黄金')} 美元/盎司
  🔎 避险需求上升

6. 债券收益率
- 中国10年期国债：{data.get('中国10年期国债')}
  🔎 资金流入债市，避险情绪增强
- 美国10年期国债：{data.get('美国10年期国债')}
  🔎 利率预期分歧，美债波动
"""
    return report

# ========== 发送邮件 ==========
def send_email(report):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "每日金融数据简报"
    msg.attach(MIMEText(report, 'plain', 'utf-8'))
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("✅ 邮件已发送")
    except Exception as e:
        print("⚠️ 邮件发送失败:", e)

# ========== 主程序 ==========
if __name__ == "__main__":
    data = get_data()
    if data:
        report = generate_report(data)
        send_email(report)
    else:
        print("⚠️ 无数据生成日报")

