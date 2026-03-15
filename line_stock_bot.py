from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import threading
import time
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "9M9gWuDL+9swPRQtYnGcAfXFwwy1rwlI2b9gBXBhmKv/5yXkdvAMWKCzptxJu0E9paX1nkj88rDh9HUk0mXCvKznM3sTGM9k6upXohJb/+I/civXiL3dU6dp/1Rpz2X+vPvAhMGj5PE5p0L1pCPR7gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "f7f7b714907d5efd93a29d5866c9593b"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

alerts = {}

# ----------------
# 基本頁面
# ----------------
@app.route("/")
def home():
    return "LINE STOCK BOT RUNNING"


# ----------------
# Webhook
# ----------------
@app.route("/callback", methods=['POST'])
def callback():

    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    if signature:
        handler.handle(body, signature)

    return 'OK'


# ----------------
# 到價提醒
# ----------------
def check_alerts():

    while True:

        for user_id, alert in list(alerts.items()):

            ticker = alert["ticker"]
            target = alert["price"]

            try:

                stock = yf.Ticker(ticker)
                data = stock.history(period="1d")

                if not data.empty:

                    price = data["Close"].iloc[-1]

                    if price >= target:

                        line_bot_api.push_message(
                            user_id,
                            TextSendMessage(
                                text=f"{ticker} 已到 ${target}\n目前價格 ${round(price,2)}"
                            )
                        )

                        del alerts[user_id]

            except:
                pass

        time.sleep(60)


threading.Thread(target=check_alerts, daemon=True).start()


# ----------------
# 產生K線圖
# ----------------
def generate_chart(ticker):

    data = yf.Ticker(ticker).history(period="3mo")

    plt.figure(figsize=(8,4))
    plt.plot(data.index, data["Close"])
    plt.title(ticker)
    plt.grid(True)

    filename = f"{ticker}.png"
    plt.savefig(filename)
    plt.close()

    return filename


# ----------------
# LINE訊息處理
# ----------------
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.strip().upper()
    user_id = event.source.user_id

    try:

        # 說明
        if text == "HELP":

            msg = """可用指令

NVDA 查股價
price NVDA

analysis NVDA
ai NVDA

rsi NVDA
support NVDA

chart NVDA

alert NVDA 150

scan
hot
"""

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return


        # 熱門股
        elif text == "HOT":

            msg = """熱門科技股

NVDA
TSLA
META
AMD
AMZN
MSFT"""

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return


        # 市場掃描
        elif text == "SCAN":

            msg = """市場觀察

AI股強勢
半導體資金流入
科技股動能偏多"""

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return


        # 查股價
        elif text.startswith("PRICE"):

            ticker = text.split(" ")[1]

            data = yf.Ticker(ticker).history(period="1d")

            price = data["Close"].iloc[-1]

            msg = f"{ticker} 目前價格 ${round(price,2)}"

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return


        # AI分析
        elif text.startswith("AI"):

            ticker = text.split(" ")[1]

            data = yf.Ticker(ticker).history(period="5d")

            start = data["Close"].iloc[0]
            end = data["Close"].iloc[-1]

            change = ((end-start)/start)*100

            trend = "多頭" if change > 0 else "空頭"

            msg = f"""{ticker} AI解讀

趨勢: {trend}
5日變化: {round(change,2)}%

市場動能: {"強" if abs(change) > 3 else "中"}
"""

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return


        # 技術分析
        elif text.startswith("ANALYSIS"):

            ticker = text.split(" ")[1]

            data = yf.Ticker(ticker).history(period="3mo")

            close = data["Close"]

            ma20 = close.rolling(20).mean().iloc[-1]
            ma50 = close.rolling(50).mean().iloc[-1]

            delta = close.diff()

            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)

            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()

            rs = avg_gain / avg_loss
            rsi = 100 - (100/(1+rs))

            price = close.iloc[-1]

            trend = "多頭" if price > ma20 else "空頭"

            msg = f"""{ticker} 技術分析

價格: ${round(price,2)}

MA20: {round(ma20,2)}
MA50: {round(ma50,2)}

RSI: {round(rsi.iloc[-1],2)}

趨勢: {trend}
"""

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return


        # RSI
        elif text.startswith("RSI"):

            ticker = text.split(" ")[1]

            data = yf.Ticker(ticker).history(period="3mo")

            close = data["Close"]

            delta = close.diff()

            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)

            avg_gain = gain.rolling(14).mean()
            avg_loss = loss.rolling(14).mean()

            rs = avg_gain / avg_loss
            rsi = 100 - (100/(1+rs))

            rsi_val = rsi.iloc[-1]

            state = "超買" if rsi_val > 70 else "超賣" if rsi_val < 30 else "中性"

            msg = f"""{ticker} RSI

RSI: {round(rsi_val,2)}

狀態: {state}
"""

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return


        # 支撐壓力
        elif text.startswith("SUPPORT"):

            ticker = text.split(" ")[1]

            data = yf.Ticker(ticker).history(period="3mo")

            support = data["Low"].min()
            resistance = data["High"].max()

            msg = f"""{ticker} 支撐壓力

支撐: {round(support,2)}
壓力: {round(resistance,2)}
"""

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return


        # K線圖
        elif text.startswith("CHART"):

            ticker = text.split(" ")[1]

            filename = generate_chart(ticker)

            url = f"https://your-render-domain/{filename}"

            line_bot_api.reply_message(
                event.reply_token,
                ImageSendMessage(original_content_url=url, preview_image_url=url)
            )

            return


        # 到價提醒
        elif text.startswith("ALERT"):

            parts = text.split(" ")

            ticker = parts[1]
            target = float(parts[2])

            alerts[user_id] = {
                "ticker": ticker,
                "price": target
            }

            msg = f"已設定 {ticker} 到 ${target} 提醒"

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
            return


        # 直接輸入股票
        else:

            ticker = text

            data = yf.Ticker(ticker).history(period="1d")

            if data.empty:

                msg = "請輸入股票代碼，例如 NVDA"

            else:

                price = data["Close"].iloc[-1]

                msg = f"{ticker} 目前價格 ${round(price,2)}"

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))


    except Exception as e:

        print(e)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="查詢錯誤")
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
