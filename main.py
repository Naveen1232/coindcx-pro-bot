import pandas as pd
import time
import requests
from flask import Flask
from threading import Thread
import os

# --- కాన్ఫిగరేషన్ ---
TELEGRAM_TOKEN = '8531878411:AAGjmDFuQZ40KAGqn68MQh9UccgBBZUt-KY'
CHAT_ID = '5356787589' # మీ కరెక్ట్ ఐడి

app = Flask('')
@app.route('/')
def home(): return "Trading Bot is Active!"

def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
    except: pass

def get_coindcx_data(pair_id):
    try:
        url = f"https://public.coindcx.com/market_data/candles?pair={pair_id}&interval=15m"
        response = requests.get(url, timeout=15)
        df = pd.DataFrame(response.json())
        df['close'] = df['close'].astype(float)
        return df
    except: return None

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def scan_market():
    # ఎక్కువ సిగ్నల్స్ కోసం కాయిన్స్ లిస్ట్
    coins = {
        "B-BTC_USDT": "BTC", "B-ETH_USDT": "ETH", "B-SOL_USDT": "SOL",
        "B-MATIC_USDT": "MATIC", "B-DOGE_USDT": "DOGE", "B-ADA_USDT": "ADA"
    }
    
    for pair_id, name in coins.items():
        df = get_coindcx_data(pair_id)
        if df is not None and not df.empty:
            df['RSI'] = calculate_rsi(df['close'])
            last_rsi = round(df.iloc[0]['RSI'], 2)
            price = df.iloc[0]['close']
            
            # అసలైన సిగ్నల్ కండిషన్స్
            if last_rsi < 35: # Buy Alert (కొంచెం పెంచాను ఎక్కువ సిగ్నల్స్ కోసం)
                send_telegram_msg(f"🚀 *BUY SIGNAL* 🚀\n\n*Coin:* {name}/USDT\n*Price:* {price}\n*RSI:* {last_rsi}\n*Action:* Strong Oversold")
            elif last_rsi > 65: # Sell Alert
                send_telegram_msg(f"⚠️ *SELL SIGNAL* ⚠️\n\n*Coin:* {name}/USDT\n*Price:* {price}\n*RSI:* {last_rsi}\n*Action:* Overbought")
        time.sleep(2)

def main_loop():
    send_telegram_msg("✅ *Trading Bot Started Successfully!* \nMonitoring BTC, ETH, SOL, MATIC, DOGE, ADA...")
    while True:
        scan_market()
        time.sleep(300) # 5 నిమిషాల విరామం

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))).start()
    main_loop()
