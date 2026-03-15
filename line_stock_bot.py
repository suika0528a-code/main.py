from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import yfinance as yf

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "9M9gWuDL+9swPRQtYnGcAfXFwwy1rwlI2b9gBXBhmKv/5yXkdvAMWKCzptxJu0E9paX1nkj88rDh9HUk0mXCvKznM3sTGM9k6upXohJb/+I/civXiL3dU6dp/1Rpz2X+vPvAhMGj5PE5p0L1pCPR7gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "f7f7b714907d5efd93a29d5866c9593b"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/")
def home():
    return "LINE BOT RUNNING"


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


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.strip().upper()

    try:

        stock = yf.Ticker(text)
        price = stock.fast_info["last_price"]

        msg = f"{text} 目前價格 ${round(price,2)}"

    except:

        msg = "請輸入股票代碼，例如 NVDA"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
