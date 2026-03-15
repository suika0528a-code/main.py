from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import yfinance as yf
import threading
import time

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = "9M9gWuDL+9swPRQtYnGcAfXFwwy1rwlI2b9gBXBhmKv/5yXkdvAMWKCzptxJu0E9paX1nkj88rDh9HUk0mXCvKznM3sTGM9k6upXohJb/+I/civXiL3dU6dp/1Rpz2X+vPvAhMGj5PE5p0L1pCPR7gdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "f7f7b714907d5efd93a29d5866c9593b"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

alerts = {}

# ----------------
# 根
