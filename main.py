import ccxt
import pandas as pd
import time
import requests
from flask import Flask
from threading import Thread
import os

# --- కాన్ఫిగరేషన్ (మీ వివరాలు) ---
TELEGRAM_TOKEN = '8131878411:AAGjwDfUQZ40KAGqn60MOHQUccgBBZut-KY'
CHAT_ID = '5336787589'

# CoinDCX కనెక్షన్ (కరెక్ట్ స్పెల్లింగ్ ఇక్కడ ఉంది)
try:
    EXCHANGE = ccxt.coindcx() 
except AttributeError:
    # ఒకవేళ పైది పనిచేయకపోతే ఇది పనిచేస్తుంది
    EXCHANGE = getattr(ccxt, 'coindcx')()

app = Flask('')

@app.route('/')
def home():
    return "CoinDCX Bot is Live and Scanning!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- కస్టమ్ ఇండికేటర్స్ (ఎర్రర్స్ రాకుండా ఉండటానికి) ---
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
        
        # RSI మరియు EMA లెక్కించడం
        df['RSI'] = calculate_rsi(df['close'])
        df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['EMA_50'] = df['close'].ewm(span=50, adjust=False).mean()
        
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        msg = ""
        # బై సిగ్నల్ (RSI Oversold)
        if last['RSI'] < 30:
            msg = f"🚀 *BUY ALERT (RSI)* 🚀\n\n*Coin:* {symbol}\n*Price:* {last['close']}\n*RSI:* {round(last['RSI'], 2)}"
        
        # గోల్డెన్ క్రాస్ సిగ్నల్
        elif prev['EMA_20'] < prev['EMA_50'] and last['EMA_20'] > last['EMA_50']:
            msg = f"📈 *GOLDEN CROSS (BUY)* 📈\n\n*Coin:* {symbol}\n*Price:* {last['close']}\n*Trend:* Bullish"

        if msg:
            send_telegram_msg(msg)
    except Exception as e:
        print(f"Error scanning {symbol}: {e}")

def main_loop():
    print("Bot Started...")
    send_telegram_msg("🤖 *CoinDCX Pro Bot is now Online!* \nScanning coins every 5 minutes...")
    
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'MATIC/USDT', 'DOGE/USDT']
    
    while True:
        for s in symbols:
            get_signals(s)
            time.sleep(2)
        print("Scan complete. Waiting...")
        time.sleep(300)

if __name__ == "__main__":
    # Flask సర్వర్‌ని విడిగా స్టార్ట్ చేయాలి
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # మెయిన్ బాట్ స్టార్ట్
    main_loop()
