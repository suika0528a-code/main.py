from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import yfinance as yf

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN ="9M9gWuDL+9swPRQtYnGcAfXFwwy1rwlI2b9gBXBhmKv/5yXkdvAMWKCzptxJu0E9paX1nkj88rDh9HUk0mXCvK znM3sTGM9k6upXohJb/+I/civXiL3dU6dp/1Rpz2X+vPvAhMGj5PE5p0L1pCPR7gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "23cd049315c1c76fc3c115445fe1f650"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():

    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.upper()

    try:
        stock = yf.Ticker(text)
        price = stock.info["regularMarketPrice"]

        msg = f"{text} 目前價格: ${price}"

    except:
        msg = "請輸入股票代碼，例如 NVDA"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
