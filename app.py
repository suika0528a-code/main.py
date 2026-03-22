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
# SQLite 初始化
# =========================
conn = sqlite3.connect("alerts.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS alerts (
    user_id TEXT,
    ticker TEXT,
    price REAL
)
""")
conn.commit()

# =========================
# Home
# =========================
@app.route("/")
def home():
    return "AI STOCK BOT RUNNING"

# =========================
# LINE webhook
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
# 到價檢查（給 UptimeRobot 用）
# =========================
@app.route("/check_alert")
def check_alert():

    cursor.execute("SELECT rowid, * FROM alerts")
    rows = cursor.fetchall()

    for row in rows:
        row_id, user_id, ticker, target = row

        try:
            price = yf.Ticker(ticker).fast_info["last_price"]

            if price >= target:
                line_bot_api.push_message(
                    user_id,
                    TextSendMessage(
                        text=f"{ticker} 已達 ${target}\n目前價格 ${round(price,2)}"
                    )
                )

                cursor.execute("DELETE FROM alerts WHERE rowid=?", (row_id,))
                conn.commit()

        except Exception as e:
            print(e)

    return "OK"

# =========================
# LINE訊息處理
# =========================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.strip().upper()
    user_id = event.source.user_id

    try:

        # 設定提醒
        if text.startswith("ALERT"):
            parts = text.split(" ")

            ticker = parts[1]
            price = float(parts[2])

            cursor.execute(
                "INSERT INTO alerts VALUES (?, ?, ?)",
                (user_id, ticker, price)
            )
            conn.commit()

            msg = f"已設定提醒 {ticker} ${price}"

        # 查股價
        else:
            ticker = text
            price = yf.Ticker(ticker).fast_info["last_price"]
            msg = f"{ticker} 目前價格 ${round(price,2)}"

    except:
        msg = "請輸入正確格式，例如：ALERT NVDA 150"

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
