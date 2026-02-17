import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests
from flask import Flask
from threading import Thread
import os

# --- 1. కాన్ఫిగరేషన్ (మీ వివరాలు ఇక్కడ మార్చండి) ---
TELEGRAM_TOKEN = '8531878411:AAGjmDFuQZ40KAGqn68MQh9UccgBBZUt-KY'  # మీ టెలిగ్రామ్ బాట్ టోకెన్
CHAT_ID = '5356787589'                  # మీ చాట్ ఐడి
EXCHANGE = ccxt.coindcx()

# --- 2. Flask సెటప్ (Render లో బాట్ ఆగిపోకుండా ఉండటానికి) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive and Scanning CoinDCX!"

def run_flask():
    # Render పోర్ట్ 10000 ని వాడుకుంటుంది, లోకల్ గా 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 3. టెలిగ్రామ్ అలర్ట్ ఫంక్షన్ ---
def send_telegram_msg(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram Error: {e}")

# --- 4. మార్కెట్ అనాలసిస్ లాజిక్ ---
def get_signals(symbol):
    try:
        # CoinDCX నుండి 15 నిమిషాల చార్ట్ డేటా తీసుకోవడం
        bars = EXCHANGE.fetch_ohlcv(symbol, timeframe='15m', limit=100)
        df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
        
        # టెక్నికల్ ఇండికేటర్స్ లెక్కించడం
        df['RSI'] = ta.rsi(df['close'], length=14)
        df['EMA_20'] = ta.ema(df['close'], length=20)
        df['EMA_50'] = ta.ema(df['close'], length=50)
        
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        current_price = last_row['close']
        rsi_val = round(last_row['RSI'], 2)

        # సిగ్నల్ కండిషన్స్
        msg = ""
        
        # పాటర్న్ 1: RSI Oversold (బై సిగ్నల్)
        if rsi_val < 30:
            msg = f"🚀 *BUY SIGNAL (RSI)* 🚀\n\n*Coin:* {symbol}\n*Price:* {current_price}\n*RSI:* {rsi_val}\n*Condition:* Oversold (Strong Bounce Expected)"

        # పాటర్న్ 2: Golden Cross (ట్రెండ్ రివర్సల్)
        elif prev_row['EMA_20'] < prev_row['EMA_50'] and last_row['EMA_20'] > last_row['EMA_50']:
            msg = f"📈 *GOLDEN CROSS (BUY)* 📈\n\n*Coin:* {symbol}\n*Price:* {current_price}\n*Condition:* 20 EMA crossed above 50 EMA (Bullish Trend)"

        # పాటర్న్ 3: RSI Overbought (సెల్ సిగ్నల్)
        elif rsi_val > 70:
            msg = f"⚠️ *SELL ALERT (RSI)* ⚠️\n\n*Coin:* {symbol}\n*Price:* {current_price}\n*RSI:* {rsi_val}\n*Condition:* Overbought (Price may drop)"

        if msg:
            send_telegram_msg(msg)
            
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")

# --- 5. మెయిన్ బాట్ లూప్ ---
def main_loop():
    print("Starting Scanner...")
    send_telegram_msg("🤖 *CoinDCX Pro Bot is now Online!* \nScanning all major coins every 5 minutes...")
    
    # మీరు స్కాన్ చేయాలనుకుంటున్న కాయిన్స్ లిస్ట్ ఇక్కడ పెంచుకోవచ్చు
    symbols = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'MATIC/USDT', 'DOGE/USDT', 'ADA/USDT']
    
    while True:
        for s in symbols:
            get_signals(s)
            time.sleep(2)  # API రేట్ లిమిట్ దాటకుండా చిన్న గ్యాప్
        
        print("Scan complete. Waiting for 5 minutes...")
        time.sleep(300)  # 5 నిమిషాల విరామం

if __name__ == "__main__":
    # Flask సర్వర్‌ని విడిగా ఒక త్రెడ్‌లో రన్ చేయాలి
    t = Thread(target=run_flask)
    t.start()
    
    # బాట్ లూప్ ని స్టార్ట్ చేయాలి
    main_loop()

