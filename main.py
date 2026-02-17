import pandas as pd
import time
import requests
from flask import Flask
from threading import Thread
import os

# --- 1. కాన్ఫిగరేషన్ ---
TELEGRAM_TOKEN = '8131878411:AAGjwDfUQZ40KAGqn60MOHQUccgBBZut-KY'
CHAT_ID = '5336787589'

app = Flask('')

@app.route('/')
def home():
    return "CoinDCX Direct API Bot is Running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
    except:
        pass

# --- 2. CoinDCX నుండి నేరుగా డేటా తీసుకోవడం (No ccxt needed) ---
def get_coindcx_data(symbol):
    try:
        # CoinDCX Public API link
        pair = symbol.replace("/", "")
        url = f"https://public.coindcx.com/market_data/candles?pair={pair}&interval=15m"
        response = requests.get(url)
        data = response.json()
        
        # డేటాను టేబుల్ లాగా మార్చడం
        df = pd.DataFrame(data)
        df['close'] = df['close'].astype(float)
        return df
    except:
        return None

# RSI ఫార్ములా
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def scan_market():
    # మనం స్కాన్ చేయాలనుకుంటున్న కాయిన్స్ (CoinDCX పేర్లు)
    # గమనిక: ఇక్కడ B-BTC_USDT అంటే Binance మార్కెట్ డేటా అని అర్థం
    coins = {"B-BTC_USDT": "BTC/USDT", "B-ETH_USDT": "ETH/USDT", "B-SOL_USDT": "SOL/USDT"}
    
    for pair_id, display_name in coins.items():
        df = get_coindcx_data(pair_id)
        if df is not None:
            df['RSI'] = calculate_rsi(df['close'])
            last_rsi = round(df.iloc[0]['RSI'], 2) # ఇక్కడ 0 అంటే లేటెస్ట్ డేటా
            price = df.iloc[0]['close']
            
            if last_rsi < 30:
                send_telegram_msg(f"🚀 *BUY ALERT* 🚀\n\n*Coin:* {display_name}\n*Price:* {price}\n*RSI:* {last_rsi}")
            elif last_rsi > 70:
                send_telegram_msg(f"⚠️ *SELL ALERT* ⚠️\n\n*Coin:* {display_name}\n*Price:* {price}\n*RSI:* {last_rsi}")
        time.sleep(2)

# --- 3. మెయిన్ లూప్ ---
def main_loop():
    send_telegram_msg("✅ *Bot Started Successfully!* \nDirect API mode active. Scanning now...")
    while True:
        scan_market()
        time.sleep(300) # 5 నిమిషాల విరామం

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    main_loop()
