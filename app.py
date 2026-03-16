from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import yfinance as yf
import pandas as pd
import threading
import time

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "9M9gWuDL+9swPRQtYnGcAfXFwwy1rwlI2b9gBXBhmKv/5yXkdvAMWKCzptxJu0E9paX1nkj88rDh9HUk0mXCvKznM3sTGM9k6upXohJb/+I/civXiL3dU6dp/1Rpz2X+vPvAhMGj5PE5p0L1pCPR7gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "f7f7b714907d5efd93a29d5866c9593b"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

alerts = {}

@app.route("/")
def home():
    return "AI QUANT BOT V6 RUNNING"


@app.route("/callback", methods=['POST'])
def callback():

    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        if signature:
            handler.handle(body, signature)
    except:
        pass

    return "OK"


# -------------------------
# 到價提醒
# -------------------------
def alert_worker():

    while True:

        for user_id, data in list(alerts.items()):

            ticker = data["ticker"]
            target = data["price"]

            try:

                price = yf.Ticker(ticker).fast_info["last_price"]

                if price >= target:

                    line_bot_api.push_message(
                        user_id,
                        TextSendMessage(
                            text=f"{ticker} 已達 ${target}\n目前價格 ${round(price,2)}"
                        )
                    )

                    del alerts[user_id]

            except:
                pass

        time.sleep(60)

threading.Thread(target=alert_worker, daemon=True).start()


# -------------------------
# 技術指標
# -------------------------
def indicators(ticker):

    data = yf.Ticker(ticker).history(period="3mo")

    close = data["Close"]

    ma20 = close.rolling(20).mean().iloc[-1]
    ma50 = close.rolling(50).mean().iloc[-1]

    # RSI
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100/(1+rs))

    # MACD
    ema12 = close.ewm(span=12).mean()
    ema26 = close.ewm(span=26).mean()

    macd = ema12 - ema26

    # Bollinger
    sma = close.rolling(20).mean()
    std = close.rolling(20).std()

    upper = sma + (2 * std)
    lower = sma - (2 * std)

    price = close.iloc[-1]

    return price, ma20, ma50, rsi.iloc[-1], macd.iloc[-1], upper.iloc[-1], lower.iloc[-1]


# -------------------------
# RSI掃描
# -------------------------
def rsi_scan():

    watch = ["NVDA","TSLA","AAPL","AMD","META","AMZN","MSFT","GOOGL"]

    result = []

    for ticker in watch:

        try:

            _, _, _, rsi, _, _, _ = indicators(ticker)

            if rsi < 30:

                result.append(f"{ticker} RSI {round(rsi,2)}")

        except:
            pass

    return result


# -------------------------
# 突破掃描
# -------------------------
def breakout_scan():

    watch = ["NVDA","TSLA","AAPL","AMD","META","AMZN"]

    result = []

    for ticker in watch:

        try:

            data = yf.Ticker(ticker).history(period="1mo")

            high = data["High"].max()

            price = yf.Ticker(ticker).fast_info["last_price"]

            if price >= high:

                result.append(ticker)

        except:
            pass

    return result


# -------------------------
# LINE訊息
# -------------------------
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.strip().upper()
    user_id = event.source.user_id

    try:

        if text == "HELP":

            msg = """AI量化交易助手 v6

查股價
NVDA

技術分析
analysis NVDA

RSI
rsi NVDA

AI分析
ai NVDA

到價提醒
alert NVDA 150

RSI掃描
scan

突破掃描
breakout

K線圖
chart NVDA
"""

        elif text == "SCAN":

            result = rsi_scan()

            msg = "RSI <30 股票\n\n" + "\n".join(result) if result else "沒有 RSI <30 股票"

        elif text == "BREAKOUT":

            result = breakout_scan()

            msg = "突破股票\n\n" + "\n".join(result) if result else "沒有突破股票"

        elif text.startswith("ALERT"):

            parts = text.split(" ")

            ticker = parts[1]
            price = float(parts[2])

            alerts[user_id] = {
                "ticker": ticker,
                "price": price
            }

            msg = f"已設定提醒 {ticker} ${price}"

        elif text.startswith("ANALYSIS"):

            ticker = text.split(" ")[1]

            price, ma20, ma50, rsi, macd, upper, lower = indicators(ticker)

            msg = f"""{ticker} 技術分析

價格: ${round(price,2)}

MA20: {round(ma20,2)}
MA50: {round(ma50,2)}

RSI: {round(rsi,2)}
MACD: {round(macd,2)}

布林上軌: {round(upper,2)}
布林下軌: {round(lower,2)}
"""

        elif text.startswith("AI"):

            ticker = text.split(" ")[1]

            data = yf.Ticker(ticker).history(period="5d")

            start = data["Close"].iloc[0]
            end = data["Close"].iloc[-1]

            change = ((end-start)/start)*100

            trend = "多頭" if change > 0 else "空頭"

            msg = f"""{ticker} AI市場分析

5日變化: {round(change,2)}%

市場趨勢: {trend}
"""

        elif text.startswith("CHART"):

            ticker = text.split(" ")[1]

            msg = f"{ticker} K線圖\nhttps://finance.yahoo.com/quote/{ticker}/chart"

        else:

            ticker = text

            price = yf.Ticker(ticker).fast_info["last_price"]

            msg = f"{ticker} 目前價格 ${round(price,2)}"

    except Exception as e:

        print(e)

        msg = "請輸入有效美股代碼，例如 NVDA"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
