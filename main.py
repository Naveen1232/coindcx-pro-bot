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

# --- 2. CoinDCX నుండి డేటా తీసుకోవడం ---
def get_coindcx_data(pair_id):
    try:
        url = f"https://public.coindcx.com/market_data/candles?pair={pair_id}&interval=15m"
        response = requests.get(url, timeout=10)
        data = response.json()
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)
            df['close'] = df['close'].astype(float)
            return df
        return None
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
    # మరిన్ని కాయిన్స్ యాడ్ చేయబడ్డాయి
    coins = {
        "B-BTC_USDT": "BTC/USDT",
        "B-ETH_USDT": "ETH/USDT",
        "B-SOL_USDT": "SOL/USDT",
        "B-MATIC_USDT": "MATIC/USDT",
        "B-DOGE_USDT": "DOGE/USDT",
        "B-ADA_USDT": "ADA/USDT",
        "B-XRP_USDT": "XRP/USDT",
        "B-LINK_USDT": "LINK/USDT",
        "B-DOT_USDT": "DOT/USDT"
    }
    
    for pair_id, display_name in coins.items():
        df = get_coindcx_data(pair_id)
        if df is not None:
            df['RSI'] = calculate_rsi(df['close'])
            last_rsi = round(df.iloc[0]['RSI'], 2)
            price = df.iloc[0]['close']
            
            # --- టెస్టింగ్ కండిషన్ (ఇక్కడ RSI < 100 పెట్టాము, కాబట్టి ప్రతి కాయిన్ కి మెసేజ్ వస్తుంది) ---
            if last_rsi < 100:
                msg = f"✅ *Test Alert (Live)*\n\n*Coin:* {display_name}\n*Price:* {price}\n*RSI:* {last_rsi}\n*Status:* Bot is working!"
                send_telegram_msg(msg)
            
            # అసలైన సిగ్నల్స్ కోసం కింద ఉన్నవి భవిష్యత్తులో వాడుకోవచ్చు:
            # if last_rsi < 30: (Buy Alert)
            # elif last_rsi > 70: (Sell Alert)
            
        time.sleep(2) # API రేట్ లిమిట్ కోసం చిన్న గ్యాప్

# --- 3. మెయిన్ లూప్ ---
def main_loop():
    send_telegram_msg("🚀 *Bot Updated!* \nTesting mode active. Checking all coins now...")
    while True:
        scan_market()
        print("Scan complete. Waiting 5 minutes...")
        time.sleep(300)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    main_loop()
