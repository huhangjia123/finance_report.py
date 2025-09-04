# -*- coding: utf-8 -*-
import os, io, csv, math, requests, smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TZ = timezone(timedelta(hours=8))  # 北京时间

# ---------- 工具 ----------
def _fmt(x, digits=2):
    try:
        if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
            return "暂无"
        if isinstance(x, (int, float)):
            return f"{x:.{digits}f}"
        return str(x)
    except:
        return "暂无"

def _get_json(url, timeout=15):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()

def _get_text(url, timeout=15):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text

# ---------- 数据获取（稳 + 兜底） ----------
def get_fx_and_gold():
    """
    返回：
    - USD/CNY
    - DXY(近似复刻公式)
    - XAU/USD（黄金美元价）
    """
    data = {"USD/CNY": None, "DXY(近似)": None, "XAU/USD": None}
    try:
        # 1) 汇率基础盘：用 exchangerate.host（免 Key、稳定）
        url = "https://api.exchangerate.host/latest?base=USD&symbols=EUR,JPY,GBP,CAD,SEK,CHF,CNY"
        js = _get_json(url)
        rates = js.get("rates", {})
        # USD/CNY
        data["USD/CNY"] = rates.get("CNY")

        # 2) 近似 DXY（标准权重）
        # DXY = 50.14348112 × (EURUSD^-0.576) × (USDJPY^0.136) × (GBPUSD^-0.119) × (USDCAD^0.091) × (USDSEK^0.042) × (USDCHF^0.036)
        if all(k in rates for k in ["EUR", "JPY", "GBP", "CAD", "SEK", "CHF"]):
            EURUSD = 1.0 / rates["EUR"]   # 我们拿到的是 USD/EUR → 取倒数得 EURUSD
            GBPUSD = 1.0 / rates["GBP"]
            USDJPY = rates["JPY"]
            USDCAD = rates["CAD"]
            USDSEK = rates["SEK"]
            USDCHF = rates["CHF"]
            dxy = 50.14348112 * (EURUSD ** -0.576) * (USDJPY ** 0.136) * (GBPUSD ** -0.119) * \
                  (USDCAD ** 0.091) * (USDSEK ** 0.042) * (USDCHF ** 0.036)
            data["DXY(近似)"] = dxy
    except Exception as e:
        print("FX/DXY 获取失败：", e)

    # 3) 黄金：exchangerate.host 支持贵金属货币符号 XAU
    try:
        js = _get_json("https://api.exchangerate.host/convert?from=XAU&to=USD")
        data["XAU/USD"] = js.get("result")
    except Exception as e:
        print("黄金获取失败：", e)

    return data

def get_stooq_close(symbol):
    """
    从 Stooq 拉取收盘价（连续合约/指数）。返回 float 或 None
    """
    try:
        url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
        txt = _get_text(url)
        reader = csv.DictReader(io.StringIO(txt))
        row = next(reader)
        val = row.get("Close") or row.get("close")
        if val and val != "N/A":
            return float(val)
    except Exception as e:
        print(f"Stooq 获取 {symbol} 失败：", e)
    return None

def get_yahoo_price(symbol):
    """
    从 Yahoo 兜底获取当前价。返回 float 或 None
    """
    try:
        js = _get_json(f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}")
        res = js.get("quoteResponse", {}).get("result", [])
        if res:
            return float(res[0]["regularMarketPrice"])
    except Exception as e:
        print(f"Yahoo 获取 {symbol} 失败：", e)
    return None

def get_index_and_commodities():
    """
    返回：
    - 上证指数（000001.SS 优先 Yahoo；Sina 兜底）
    - 恒生指数（hsi 优先 Stooq；Yahoo 兜底 ^HSI）
    - 原油（CL 连续：先 Stooq cl，后 Yahoo CL=F）
    """
    data = {"上证指数": None, "恒生指数": None, "WTI原油(近月)": None}

    # 上证：Yahoo → Sina 兜底
    sh = get_yahoo_price("000001.SS")
    if sh is None:
        try:
            # 新浪短行情：var hq_str_s_sh000001="上证指数,价,涨跌额,涨跌幅,成交额";
            txt = _get_text("http://hq.sinajs.cn/list=s_sh000001")
            # 解析
            if "=" in txt and "," in txt:
                price = txt.split('="')[1].split('",')[0].split(",")[1]
                sh = float(price)
        except Exception as e:
            print("Sina 上证兜底失败：", e)
    data["上证指数"] = sh

    # 恒生：Stooq → Yahoo
    hsi = get_stooq_close("hsi")
    if hsi is None:
        hsi = get_yahoo_price("^HSI")
    data["恒生指数"] = hsi

    # 原油：Stooq → Yahoo
    wti = get_stooq_close("cl")
    if wti is None:
        wti = get_yahoo_price("CL=F")
    data["WTI原油(近月)"] = wti

    return data

# ---------- 解读 ----------
def build_insights(fx_gold, idx_cmd):
    tips = []

    dxy = fx_gold.get("DXY(近似)")
    usdcny = fx_gold.get("USD/CNY")
    xau = fx_gold.get("XAU/USD")
    sh = idx_cmd.get("上证指数")
    hsi = idx_cmd.get("恒生指数")
    wti = idx_cmd.get("WTI原油(近月)")

    # 美元 & 人民币
    if dxy:
        if dxy >= 105:
            tips.append("美元指数偏强 → 新兴市场资金承压，A股/港股偏谨慎。")
        elif dxy <= 101:
            tips.append("美元走弱 → 有利于资金回流新兴市场，利好A股与商品资产。")
        else:
            tips.append("美元中性区间 → 汇率扰动有限，关注基本面与政策预期。")
    if usdcny:
        if usdcny >= 7.25:
            tips.append("USD/CNY 偏高 → 人民币走弱，外资风险偏好受抑。")
        elif usdcny <= 7.10:
            tips.append("USD/CNY 回落 → 人民币偏稳，利好内需与高股息资产。")

    # 黄金（避险）
    if xau:
        if xau >= 2200:
            tips.append("金价高企 → 避险情绪上升，股市风偏或承压。")
        elif xau <= 1950:
            tips.append("金价回落 → 风险偏好改善，成长板块弹性更大。")

    # 指数位置（简单阈值提示）
    if sh:
        if sh < 3000:
            tips.append("上证处于相对低位 → 价值/红利具备配置性价比。")
        else:
            tips.append("上证企稳于3000上方 → 风险偏好改善，关注景气赛道。")
    if hsi:
        if hsi < 18000:
            tips.append("恒生指数偏低位运行 → 关注南下资金与盈利修复。")
        else:
            tips.append("恒生指数企稳 → 科技/互联网可能继续受益。")

    # 原油（通胀预期/成本）
    if wti:
        if wti >= 85:
            tips.append("油价走强 → 通胀回升压力，利空高成本行业；上游能源受益。")
        elif wti <= 70:
            tips.append("油价偏弱 → 成本端压力缓解，利好制造/消费。")

    # 综合结论
    if not tips:
        tips.append("数据来源部分受限，建议以趋势为纲：关注政策节奏、社融/PMI拐点与北向资金。")

    return tips

# ---------- 报告 HTML ----------
def generate_html(report_type, fx_gold, idx_cmd, insights):
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    def row(k, v): return f"<tr><td>{k}</td><td>{_fmt(v)}</td></tr>"

    css = """
    <style>
      body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, PingFang SC, Hiragino Sans GB, "Microsoft YaHei", Helvetica, Arial; line-height:1.6; color:#1f2937; }
      h2 { margin: 0 0 8px; }
      .sec { margin:18px 0; }
      table { border-collapse: collapse; width:100%; }
      th, td { border:1px solid #e5e7eb; padding:8px 10px; font-size:14px; }
      th { background:#f3f4f6; text-align:left; }
      .tips li { margin:6px 0; }
      .tag { display:inline-block; padding:2px 8px; border-radius:12px; background:#eef2ff; color:#3730a3; font-size:12px; margin-left:6px; }
    </style>
    """

    html = f"""
    <html><head>{css}</head><body>
      <h2>{report_type.capitalize()} 投资报告 <span class="tag">{ts}</span></h2>

      <div class="sec">
        <h3>📊 宏观与外汇/贵金属</h3>
        <table>
          <tr><th>指标</th><th>数值</th></tr>
          {row("USD/CNY", fx_gold.get("USD/CNY"))}
          {row("DXY(近似)", fx_gold.get("DXY(近似)"))}
          {row("黄金 XAU/USD", fx_gold.get("XAU/USD"))}
        </table>
      </div>

      <div class="sec">
        <h3>📈 指数与大宗</h3>
        <table>
          <tr><th>指标</th><th>数值</th></tr>
          {row("上证指数", idx_cmd.get("上证指数"))}
          {row("恒生指数", idx_cmd.get("恒生指数"))}
          {row("WTI原油(近月)", idx_cmd.get("WTI原油(近月)"))}
        </table>
      </div>

      <div class="sec">
        <h3>🧭 解读与对市场影响</h3>
        <ul class="tips">
          {''.join(f'<li>{x}</li>' for x in insights)}
        </ul>
      </div>

      <div class="sec">
        <h3>📌 关注线索（适合新手的每日 Checklist）</h3>
        <ul>
          <li>流动性：观察社融、M2、DR007/SHIBOR 是否放松。</li>
          <li>景气度：留意制造业 PMI 是否重返 50 上方。</li>
          <li>资金面：北向资金净流入/流出方向与行业偏好。</li>
          <li>主题与产业：半导体/面板/存储是否出现“去库存+涨价”。</li>
        </ul>
      </div>
    </body></html>
    """
    return html

# ---------- 发送邮件 ----------
def send_email(report_type, html, sender, password, receiver):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📈 {report_type.capitalize()} 投资报告"
    msg["From"] = sender
    msg["To"] = receiver
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.qq.com", 465) as server:
        server.login(sender.strip(), password.strip())
        server.sendmail(sender, receiver, msg.as_string())

# ---------- 主流程 ----------
def main(report_type="daily"):
    fx_gold = get_fx_and_gold()
    idx_cmd = get_index_and_commodities()
    insights = build_insights(fx_gold, idx_cmd)
    html = generate_html(report_type, fx_gold, idx_cmd, insights)
    return html

if __name__ == "__main__":
    import sys
    report_type = sys.argv[1] if len(sys.argv) > 1 else "daily"

    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER")

    if not all([EMAIL_USER, EMAIL_PASS, EMAIL_RECEIVER]):
        raise SystemExit("❌ 环境变量缺失：EMAIL_USER / EMAIL_PASS / EMAIL_RECEIVER")

    html = main(report_type)
    send_email(report_type, html, EMAIL_USER, EMAIL_PASS, EMAIL_RECEIVER)
    print("✅ 邮件已发送")
