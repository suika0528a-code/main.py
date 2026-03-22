from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import yfinance as yf
import sqlite3
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "9M9gWuDL+9swPRQtYnGcAfXFwwy1rwlI2b9gBXBhmKv/5yXkdvAMWKCzptxJu0E9paX1nkj88rDh9HUk0mXCvKznM3sTGM9k6upXohJb/+I/civXiL3dU6dp/1Rpz2X+vPvAhMGj5PE5p0L1pCPR7gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "f7f7b714907d5efd93a29d5866c9593b"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# =========================
# DB 初始化
# =========================
conn = sqlite3.connect("alerts.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    user_id TEXT,
    ticker TEXT,
    price REAL,
    direction TEXT
)
""")
conn.commit()

# =========================
# Home
# =========================
@app.route("/")
def home():
    return "AI QUANT BOT V7 RUNNING"

# =========================
# Webhook
# =========================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(e)

    return "OK"

# =========================
# 技術指標
# =========================
def indicators(ticker):
    data = yf.Ticker(ticker).history(period="3mo")
    close = data["Close"]

    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    rsi = 100 - (100/(1+rs))

    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()
    macd = ema12 - ema26

    return close.iloc[-1], ma20, ma50, rsi.iloc[-1], macd.iloc[-1]

# =========================
# alert 檢查（給 UptimeRobot）
# =========================
@app.route("/check_alert")
def check_alert():

    cursor.execute("SELECT rowid, * FROM alerts")
    rows = cursor.fetchall()

    for row in rows:
        row_id, user_id, ticker, target, direction = row

        try:
            price = yf.Ticker(ticker).fast_info["last_price"]

            trigger = False

            if direction == "up" and price >= target:
                trigger = True
            elif direction == "down" and price <= target:
                trigger = True

            if trigger:
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(
                        text=f"{ticker} 觸發提醒\n目標 {target}\n目前 {round(price,2)}"
                    )
                )

                cursor.execute("DELETE FROM alerts WHERE rowid=?", (row_id,))
                conn.commit()

        except Exception as e:
            print(e)

    return "OK"

# =========================
# LINE 訊息
# =========================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.strip().upper()
    user_id = event.source.user_id

    try:

        # ALERT
        if text.startswith("ALERT"):
            _, ticker, price, direction = text.split(" ")

            cursor.execute(
                "INSERT INTO alerts VALUES (?, ?, ?, ?)",
                (user_id, ticker, float(price), direction)
            )
            conn.commit()

            msg = f"已設定 {ticker} {price} {direction}"

        # 技術分析
        elif text.startswith("ANALYSIS"):
            ticker = text.split(" ")[1]
            p, ma20, ma50, rsi, macd = indicators(ticker)

            msg = f"""{ticker}
價格: {round(p,2)}
MA20: {round(ma20,2)}
MA50: {round(ma50,2)}
RSI: {round(rsi,2)}
MACD: {round(macd,2)}"""

        # AI分析
        elif text.startswith("AI"):
            ticker = text.split(" ")[1]
            data = yf.Ticker(ticker).history(period="5d")

            start = data["Close"].iloc[0]
            end = data["Close"].iloc[-1]
            change = ((end-start)/start)*100

            trend = "多頭" if change > 0 else "空頭"

            msg = f"{ticker}\n5日變化: {round(change,2)}%\n趨勢: {trend}"

        # K線圖
        elif text.startswith("CHART"):
            ticker = text.split(" ")[1]
            msg = f"https://finance.yahoo.com/quote/{ticker}/chart"

        # 查價格
        else:
            ticker = text
            price = yf.Ticker(ticker).fast_info["last_price"]
            msg = f"{ticker} ${round(price,2)}"

    except:
        msg = "格式錯誤"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )

# =========================
# 啟動
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
