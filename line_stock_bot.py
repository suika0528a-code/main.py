from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import yfinance as yf
import os

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "9M9gWuDL+9swPRQtYnGcAfXFwwy1rwlI2b9gBXBhmKv/5yXkdvAMWKCzptxJu0E9paX1nkj88rDh9HUk0mXCvKznM3sTGM9k6upXohJb/+I/civXiL3dU6dp/1Rpz2X+vPvAhMGj5PE5p0L1pCPR7gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "f7f7b714907d5efd93a29d5866c9593b"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():

    try:
        signature = request.headers.get('X-Line-Signature')
        body = request.get_data(as_text=True)

        handler.handle(body, signature)

    except Exception as e:
        print("Webhook Error:", e)

    # 一定要回傳200
    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    user_text = event.message.text.strip().upper()
    print("收到:", user_text)

    msg = ""

    try:
        stock = yf.Ticker(user_text)
        price = stock.fast_info.get("last_price")

        if price:
            msg = f"{user_text} 目前價格: ${round(price,2)}"
        else:
            msg = "查不到股票\n例如: TSLA / NVDA / AAPL"

    except Exception as e:
        print("股票錯誤:", e)
        msg = "股票查詢失敗"

    try:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=msg)
        )
    except Exception as e:
        print("LINE回覆錯誤:", e)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
