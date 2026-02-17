
import ccxt
import pandas as pd
import time
import requests
from flask import Flask
from threading import Thread
import os

# --- కాన్ఫిగరేషన్ ---
TELEGRAM_TOKEN = '8131878411:AAGjwDfUQZ40KAGqn60MOHQUccgBBZut-KY'
CHAT_ID = '5336787589'
EXCHANGE = ccxt.coindcx() 

app = Flask('')

@app.route('/')
def home(): return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
    except: pass

# --- Custom Indicators (No Library Needed) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_signals(symbol):
    try:
        bars = EXCHANGE.fetch_ohlcv(symbol, timeframe='15m', limit=100)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        # టెక్నికల్ అనాలసిస్
        df['RSI'] = calculate_rsi(df['close'])
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        msg = ""
        if last['RSI'] < 30:
            msg = f"🚀 *BUY ALERT* 🚀\n{symbol}\nPrice: {last['close']}\nRSI: {round(last['RSI'], 2)}"
        elif prev['EMA_20'] < prev['EMA_50'] and last['EMA_20'] > last['EMA_50']:
            msg = f"📈 *GOLDEN CROSS* 📈\n{symbol}\nPrice: {last['close']}"
        
        if msg: send_telegram_msg(msg)
    except: pass

def main_loop():
    send_telegram_msg("🤖 CoinDCX Bot Online (No-Library Mode)!")
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'MATIC/USDT']
    while True:
        for s in symbols:
            get_signals(s)
            time.sleep(2)
        time.sleep(300)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    main_loop()
