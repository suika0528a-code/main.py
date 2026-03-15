from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import yfinance as yf

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "BPQ/+EOBTi0a5fWsab/05yvB8J8v4jsh3zqjk2TqnSoMJ5CsJxU2+RTGKlQx0FndpaX1nkj88rDh9HUk0mXCvKznM3sTGM9k6upXohJb/+JtLYzFboHjcT41gIldo8TNka3g0m8jfe/dgZuU8ll8tAdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "23cd049315c1c76fc3c115445fe1f650"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():

    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    if signature:
        handler.handle(body, signature)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    text = event.message.text.strip().upper()

    print("收到訊息:", text)

    try:
        stock = yf.Ticker(text)
        price = stock.fast_info["last_price"]

        msg = f"{text} 目前價格: ${round(price,2)}"

    except:
        msg = f"查不到股票: {text}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )

    text = event.message.text.upper()

    try:
        stock = yf.Ticker(text)
        price = stock.fast_info["last_price"]

        msg = f"{text} 目前價格: ${round(price,2)}"

    except:
        msg = "查不到此股票，請輸入例如 NVDA / TSLA / AAPL"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=msg)
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
