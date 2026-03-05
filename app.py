"""
📊 Forex Analysis Pro - Versione Stabile con Rate Limit Handling
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
import feedparser
from textblob import TextBlob
import time

# ==================== CONFIG ====================

st.set_page_config(
    page_title="Forex Analysis Pro",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
    .signal-box {
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .bullish-signal { background: linear-gradient(135deg, #00C853, #00E676); color: white; }
    .bearish-signal { background: linear-gradient(135deg, #FF1744, #FF5252); color: white; }
    .neutral-signal { background: linear-gradient(135deg, #FFB300, #FFC107); color: black; }
</style>
""", unsafe_allow_html=True)

# ==================== COPPIE ====================

PAIRS = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "USDCHF=X": "USD/CHF",
    "AUDUSD=X": "AUD/USD",
    "USDCAD=X": "USD/CAD",
    "NZDUSD=X": "NZD/USD",
    "EURGBP=X": "EUR/GBP",
    "EURJPY=X": "EUR/JPY",
    "GBPJPY=X": "GBP/JPY",
    "GC=F": "🥇 XAU/USD (Gold)",
}

# ==================== FUNZIONI DATI ====================

@st.cache_data(ttl=900)  # Cache 15 minuti per evitare rate limit
def get_price_data(symbol, period="3mo", interval="1d"):
    """Scarica dati con gestione rate limit"""
    import yfinance as yf
    
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                # Prova simbolo alternativo per l'oro
                if symbol == "GC=F":
                    ticker = yf.Ticker("XAUUSD=X")
                    df = ticker.history(period=period, interval=interval)
            
            if not df.empty:
                return df
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "rate" in error_msg or "too many" in error_msg:
                wait_time = (attempt + 1) * 10  # 10, 20, 30 secondi
                time.sleep(wait_time)
                continue
            else:
                return None
    
    return None


def calculate_indicators(df):
    """Calcola indicatori tecnici manualmente (senza libreria ta per evitare problemi)"""
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    
    # RSI (14)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # EMA
    df['EMA_9'] = close.ewm(span=9, adjust=False).mean()
    df['EMA_21'] = close.ewm(span=21, adjust=False).mean()
    df['EMA_50'] = close.ewm(span=50, adjust=False).mean()
    
    # MACD
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    df['MACD'] = ema_12 - ema_26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    # Bollinger Bands
    df['BB_Middle'] = close.rolling(window=20).mean()
    bb_std = close.rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # ATR
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(window=14).mean()
    
    # Stochastic
    low_14 = low.rolling(window=14).min()
    high_14 = high.rolling(window=14).max()
    df['Stoch_K'] = ((close - low_14) / (high_14 - low_14)) * 100
    df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
    
    # ADX (semplificato)
    plus_dm = high.diff()
    minus_dm = low.diff().abs()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    atr_14 = df['ATR']
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr_14)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr_14)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df['ADX'] = dx.rolling(14).mean()
    df['ADX_pos'] = plus_di
    df['ADX_neg'] = minus_di
    
    return df


def get_technical_score(df):
    """Calcola score tecnico"""
    current = df.iloc[-1]
    score = 0
    
    # RSI
    rsi = current['RSI']
    if pd.isna(rsi):
        rsi = 50
    
    if rsi < 30:
        score += 1
        rsi_status = "OVERSOLD"
    elif rsi > 70:
        score -= 1
        rsi_status = "OVERBOUGHT"
    elif rsi < 45:
        score += 0.3
        rsi_status = "Slightly Oversold"
    elif rsi > 55:
        score -= 0.3
        rsi_status = "Slightly Overbought"
    else:
        rsi_status = "Neutral"
    
    # MACD
    macd = current['MACD']
    macd_signal = current['MACD_Signal']
    
    if not pd.isna(macd) and not pd.isna(macd_signal):
        if macd > macd_signal:
            score += 0.5
        else:
            score -= 0.5
    
    # EMA Trend
    if not pd.isna(current['EMA_9']) and not pd.isna(current['EMA_21']):
        if current['Close'] > current['EMA_21'] > current['EMA_50']:
            score += 0.5
        elif current['Close'] < current['EMA_21'] < current['EMA_50']:
            score -= 0.5
    
    # Bollinger
    if not pd.isna(current['BB_Lower']) and not pd.isna(current['BB_Upper']):
        if current['Close'] < current['BB_Lower']:
            score += 0.5
        elif current['Close'] > current['BB_Upper']:
            score -= 0.5
    
    # Stochastic
    stoch_k = current['Stoch_K']
    if not pd.isna(stoch_k):
        if stoch_k < 20:
            score += 0.3
        elif stoch_k > 80:
            score -= 0.3
    
    # Normalizza score tra -1 e 1
    score = max(-1, min(1, score / 2.5))
    
    return {
        'score': round(score, 3),
        'probability_bull': round(((score + 1) / 2) * 100, 1),
        'direction': 'BULLISH' if score > 0.15 else ('BEARISH' if score < -0.15 else 'NEUTRAL'),
        'rsi': round(rsi, 1),
        'rsi_status': rsi_status,
        'macd': round(macd, 6) if not pd.isna(macd) else 0,
        'adx': round(current['ADX'], 1) if not pd.isna(current['ADX']) else 0
    }


def get_fundamental_score(pair):
    """Score fondamentale basato su tassi di interesse"""
    
    # Tassi banche centrali aggiornati (Gennaio 2025)
    rates = {
        'USD': 5.50,
        'EUR': 4.50,
        'GBP': 5.25,
        'JPY': 0.25,
        'CHF': 1.00,
        'AUD': 4.35,
        'CAD': 3.75,
        'NZD': 4.75,
        'XAU': 0  # Oro
    }
    
    pair_clean = pair.replace("=X", "").replace("GC=F", "XAUUSD")
    
    if "XAU" in pair_clean or "GOLD" in pair_clean.upper():
        # Per l'oro: tassi USD alti = bearish per oro
        usd_rate = rates['USD']
        if usd_rate > 5:
            score = -0.3
        elif usd_rate < 3:
            score = 0.4
        else:
            score = 0
        
        return {
            'score': round(score, 3),
            'direction': 'BULLISH' if score > 0.1 else ('BEARISH' if score < -0.1 else 'NEUTRAL'),
            'info': f"USD Rate: {usd_rate}% (Alto = negativo per oro)"
        }
    else:
        base = pair_clean[:3]
        quote = pair_clean[3:6]
        
        base_rate = rates.get(base, 0)
        quote_rate = rates.get(quote, 0)
        diff = base_rate - quote_rate
        
        score = min(1, max(-1, diff / 5))
        
        return {
            'score': round(score, 3),
            'direction': 'BULLISH' if score > 0.1 else ('BEARISH' if score < -0.1 else 'NEUTRAL'),
            'info': f"{base}: {base_rate}% | {quote}: {quote_rate}% | Diff: {diff:+.2f}%"
        }


@st.cache_data(ttl=1800)  # Cache 30 minuti per news
def get_news_sentiment(pair):
    """Analizza sentiment news"""
    try:
        feeds = [
            "https://www.forexlive.com/feed/",
        ]
        
        pair_clean = pair.replace("=X", "").replace("GC=F", "GOLD")
        
        if "GC=F" in pair or "GOLD" in pair.upper() or "XAU" in pair.upper():
            terms = ["GOLD", "XAU", "PRECIOUS", "METAL", "BULLION"]
        else:
            base = pair_clean[:3]
            quote = pair_clean[3:6] if len(pair_clean) > 3 else ""
            terms = [pair_clean, base, quote, f"{base}/{quote}"]
        
        all_news = []
        polarities = []
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:20]:
                    title = entry.get('title', '')
                    summary = entry.get('summary', '')[:200]
                    text = title + ' ' + summary
                    
                    # Filtra per termini rilevanti
                    if any(t.upper() in text.upper() for t in terms if t):
                        blob = TextBlob(text)
                        pol = blob.sentiment.polarity
                        polarities.append(pol)
                        
                        sentiment = 'BULLISH' if pol > 0.1 else ('BEARISH' if pol < -0.1 else 'NEUTRAL')
                        
                        all_news.append({
                            'title': title[:70],
                            'polarity': round(pol, 2),
                            'sentiment': sentiment
                        })
            except:
                continue
        
        if not polarities:
            return {
                'score': 0,
                'direction': 'NEUTRAL',
                'news': [],
                'count': 0
            }
        
        avg = sum(polarities) / len(polarities)
        
        return {
            'score': round(avg, 3),
            'direction': 'BULLISH' if avg > 0.05 else ('BEARISH' if avg < -0.05 else 'NEUTRAL'),
            'news': all_news[:5],
            'count': len(all_news)
        }
        
    except Exception as e:
        return {
            'score': 0,
            'direction': 'NEUTRAL',
            'news': [],
            'error': str(e)
        }


def calculate_entry_points(df, direction):
    """Calcola entry, SL, TP"""
    current = df['Close'].iloc[-1]
    atr = df['ATR'].iloc[-1]
    
    if pd.isna(atr):
        atr = current * 0.01  # Fallback: 1% del prezzo
    
    if 'BULLISH' in direction or 'BUY' in direction:
        entry = current
        sl = current - (atr * 2)
        tp1 = current + (atr * 2)
        tp2 = current + (atr * 3.5)
        tp3 = current + (atr * 5)
    elif 'BEARISH' in direction or 'SELL' in direction:
        entry = current
        sl = current + (atr * 2)
        tp1 = current - (atr * 2)
        tp2 = current - (atr * 3.5)
        tp3 = current - (atr * 5)
    else:
        entry = current
        sl = current - (atr * 2)
        tp1 = current + (atr * 2)
        tp2 = current + (atr * 3)
        tp3 = current + (atr * 4)
    
    risk = abs(entry - sl)
    rr = abs(tp1 - entry) / risk if risk > 0 else 0
    
    return {
        'entry': entry,
        'stop_loss': sl,
        'tp1': tp1,
        'tp2': tp2,
        'tp3': tp3,
        'risk_reward': round(rr, 2),
        'atr': atr
    }


def calculate_lots(balance, risk_pct, entry, sl, pair):
    """Calcola lotti ottimali"""
    risk_amount = balance * (risk_pct / 100)
    
    pip_distance = abs(entry - sl)
    
    # Calcola pip value
    if "JPY" in pair:
        pip_distance = pip_distance * 100  # JPY pairs
        pip_value = 1000 / entry  # Circa $9.25 per USD/JPY
    elif "XAU" in pair or "GC=F" in pair:
        # Oro: 1 lotto = 100 oz
        dollar_risk_per_lot = pip_distance * 100
        lots = risk_amount / dollar_risk_per_lot if dollar_risk_per_lot > 0 else 0
        return {
            'lots': round(lots, 2),
            'mini_lots': round(lots * 10, 2),
            'micro_lots': round(lots * 100, 2),
            'risk_amount': round(risk_amount, 2),
            'units': round(lots * 100, 1)  # Oz di oro
        }
    else:
        pip_distance = pip_distance * 10000  # Standard pairs
        pip_value = 10  # $10 per pip per lotto standard
    
    if pip_distance <= 0:
        return {
            'lots': 0,
            'mini_lots': 0,
            'micro_lots': 0,
            'risk_amount': round(risk_amount, 2)
        }
    
    lots = risk_amount / (pip_distance * pip_value)
    
    return {
        'lots': round(lots, 2),
        'mini_lots': round(lots * 10, 2),
        'micro_lots': round(lots * 100, 2),
        'risk_amount': round(risk_amount, 2),
        'pips': round(pip_distance, 1)
    }


def send_telegram(signal, bot_token, chat_id):
    """Invia notifica Telegram"""
    if not bot_token or not chat_id:
        return False, "Token o Chat ID mancante"
    
    try:
        emoji = "🟢" if signal['action'] == 'LONG' else ("🔴" if signal['action'] == 'SHORT' else "🟡")
        
        message = f"""
{emoji} <b>SEGNALE FOREX</b> {emoji}

📊 <b>{signal['pair']}</b>
━━━━━━━━━━━━━━━━━━━━

🎯 <b>Azione:</b> {signal['action']}
💯 <b>Probabilità:</b> {signal['probability']:.1f}%
📈 <b>Confidenza:</b> {signal['confidence']}

━━━━━━━━━━━━━━━━━━━━
💰 <b>LIVELLI OPERATIVI</b>
━━━━━━━━━━━━━━━━━━━━

💵 Entry: <code>{signal['entry']:.5f}</code>
🛑 Stop Loss: <code>{signal['sl']:.5f}</code>
✅ TP1: <code>{signal['tp1']:.5f}</code>
✅ TP2: <code>{signal['tp2']:.5f}</code>
✅ TP3: <code>{signal['tp3']:.5f}</code>

━━━━━━━━━━━━━━━━━━━━
📐 <b>POSITION SIZING</b>
━━━━━━━━━━━━━━━━━━━━

📏 Lotti: <b>{signal['lots']}</b>
💵 Rischio: ${signal['risk_amount']}
📊 R/R: {signal['rr']}

━━━━━━━━━━━━━━━━━━━━
📊 <b>ANALISI</b>
━━━━━━━━━━━━━━━━━━━━

📈 Tecnica: {signal['tech_dir']}
💰 Fondamentale: {signal['fund_dir']}
💭 Sentiment: {signal['sent_dir']}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>⚠️ Non è un consiglio finanziario</i>
"""
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=10)
        
        if response.status_code == 200:
            return True, "OK"
        else:
            return False, response.text
            
    except Exception as e:
        return False, str(e)


# ==================== INTERFACCIA PRINCIPALE ====================

def main():
    st.title("📊 Forex Analysis Pro")
    st.caption("Analisi Tecnica, Fondamentale e Sentiment | Dati in tempo reale")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Impostazioni")
        
        pair = st.selectbox(
            "📈 Coppia", 
            options=list(PAIRS.keys()), 
            format_func=lambda x: PAIRS[x]
        )
        
        timeframe = st.selectbox(
            "⏱️ Timeframe", 
            ["1d", "1wk", "1mo"],
            index=0
        )
        
        period = st.selectbox(
            "📅 Periodo", 
            ["1mo", "3mo", "6mo", "1y"],
            index=1
        )
        
        st.divider()
        
        st.subheader("💰 Money Management")
        balance = st.number_input("Saldo Conto ($)", value=10000, step=1000, min_value=100)
        risk_pct = st.slider("Rischio per Trade (%)", 0.5, 5.0, 1.0, 0.5)
        
        st.divider()
        
        st.subheader("📱 Telegram")
        
        # Leggi da secrets o input manuale
        try:
            default_token = st.secrets.get("telegram", {}).get("bot_token", "")
            default_chat = st.secrets.get("telegram", {}).get("chat_id", "")
        except:
            default_token = ""
            default_chat = ""
        
        bot_token = st.text_input("Bot Token", value=default_token, type="password")
        chat_id = st.text_input("Chat ID", value=default_chat)
        
        telegram_enabled = bool(bot_token and chat_id)
        
        if telegram_enabled:
            st.success("✅ Telegram configurato")
        else:
            st.info("💡 Configura per ricevere notifiche")
        
        st.divider()
        
        analyze_btn = st.button("🔍 ANALIZZA", type="primary", use_container_width=True)
        
        st.divider()
        st.caption("📡 Dati: Yahoo Finance")
        st.caption("📰 News: ForexLive")
        st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")
    
    # Main content
    if analyze_btn:
        
        # Loading
        with st.spinner("📊 Caricamento dati in corso..."):
            df = get_price_data(pair, period, timeframe)
        
        if df is None or df.empty:
            st.error("❌ Impossibile caricare i dati. Riprova tra qualche minuto (rate limit).")
            st.info("💡 Yahoo Finance limita le richieste. Attendi 1-2 minuti e riprova.")
            return
        
        # Calcola indicatori
        with st.spinner("📈 Calcolo indicatori..."):
            df = calculate_indicators(df)
        
        # Analisi
        tech = get_technical_score(df)
        fund = get_fundamental_score(pair)
        sent = get_news_sentiment(pair)
        
        # Score combinato (pesi: Tech 45%, Fund 30%, Sent 25%)
        combined_score = (tech['score'] * 0.45) + (fund['score'] * 0.30) + (sent['score'] * 0.25)
        prob_bull = ((combined_score + 1) / 2) * 100
        
        # Direzione finale
        if combined_score > 0.25:
            direction = "STRONG BUY"
            action = "LONG"
            confidence = "ALTA"
        elif combined_score > 0.10:
            direction = "BUY"
            action = "LONG"
            confidence = "MEDIA"
        elif combined_score < -0.25:
            direction = "STRONG SELL"
            action = "SHORT"
            confidence = "ALTA"
        elif combined_score < -0.10:
            direction = "SELL"
            action = "SHORT"
            confidence = "MEDIA"
        else:
            direction = "NEUTRAL"
            action = "WAIT"
            confidence = "BASSA"
        
        # Entry points
        entry_data = calculate_entry_points(df, direction)
        
        # Lotti
        lot_data = calculate_lots(balance, risk_pct, entry_data['entry'], entry_data['stop_loss'], pair)
        
        # ==================== DISPLAY ====================
        
        # Header metriche
        st.subheader(f"📊 {PAIRS[pair]}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        change_pct = ((current_price / prev_price) - 1) * 100
        
        with col1:
            decimals = 2 if "JPY" in pair or "GC" in pair else 5
            st.metric("💵 Prezzo", f"{current_price:.{decimals}f}", f"{change_pct:+.2f}%")
        
        with col2:
            st.metric("📈 Prob. Bull", f"{prob_bull:.1f}%")
        
        with col3:
            st.metric("📉 Prob. Bear", f"{100-prob_bull:.1f}%")
        
        with col4:
            st.metric("🎯 Confidenza", confidence)
        
        st.divider()
        
        # Signal Box
        if action == "LONG":
            st.markdown(f'''
            <div class="signal-box bullish-signal">
                🟢 {action}<br>
                <small>{direction} | {prob_bull:.0f}% Bull</small>
            </div>
            ''', unsafe_allow_html=True)
        elif action == "SHORT":
            st.markdown(f'''
            <div class="signal-box bearish-signal">
                🔴 {action}<br>
                <small>{direction} | {100-prob_bull:.0f}% Bear</small>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.markdown(f'''
            <div class="signal-box neutral-signal">
                🟡 {action}<br>
                <small>{direction} | Attendere conferme</small>
            </div>
            ''', unsafe_allow_html=True)
        
        st.divider()
        
        # Livelli e Position Sizing
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🎯 Livelli Operativi")
            
            decimals = 2 if "JPY" in pair or "GC" in pair else 5
            
            levels_df = pd.DataFrame({
                "Livello": ["📍 Entry", "🛑 Stop Loss", "✅ Take Profit 1", "✅ Take Profit 2", "✅ Take Profit 3"],
                "Prezzo": [
                    f"{entry_data['entry']:.{decimals}f}",
                    f"{entry_data['stop_loss']:.{decimals}f}",
                    f"{entry_data['tp1']:.{decimals}f}",
                    f"{entry_data['tp2']:.{decimals}f}",
                    f"{entry_data['tp3']:.{decimals}f}"
                ]
            })
            
            st.dataframe(levels_df, hide_index=True, use_container_width=True)
            
            rr_color = "green" if entry_data['risk_reward'] >= 2 else ("orange" if entry_data['risk_reward'] >= 1.5 else "red")
            st.markdown(f"**📊 Risk/Reward:** :{rr_color}[{entry_data['risk_reward']}]")
        
        with col2:
            st.subheader("📏 Position Sizing")
            
            col2a, col2b = st.columns(2)
            with col2a:
                st.metric("📦 Lotti", lot_data['lots'])
                st.metric("📦 Mini Lotti", lot_data['mini_lots'])
            with col2b:
                st.metric("📦 Micro Lotti", lot_data['micro_lots'])
                st.metric("💵 Rischio", f"${lot_data['risk_amount']}")
            
            # Pulsante Telegram
            if telegram_enabled and action in ['LONG', 'SHORT']:
                st.divider()
                if st.button("📱 INVIA SU TELEGRAM", use_container_width=True, type="primary"):
                    signal_data = {
                        'pair': PAIRS[pair],
                        'action': action,
                        'probability': prob_bull if action == 'LONG' else 100 - prob_bull,
                        'confidence': confidence,
                        'entry': entry_data['entry'],
                        'sl': entry_data['stop_loss'],
                        'tp1': entry_data['tp1'],
                        'tp2': entry_data['tp2'],
                        'tp3': entry_data['tp3'],
                        'lots': lot_data['lots'],
                        'risk_amount': lot_data['risk_amount'],
                        'rr': entry_data['risk_reward'],
                        'tech_dir': tech['direction'],
                        'fund_dir': fund['direction'],
                        'sent_dir': sent['direction']
                    }
                    
                    success, msg = send_telegram(signal_data, bot_token, chat_id)
                    
                    if success:
                        st.success("✅ Notifica inviata su Telegram!")
                    else:
                        st.error(f"❌ Errore: {msg}")
        
        st.divider()
        
        # Breakdown Analisi
        st.subheader("📊 Breakdown Analisi")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**📈 Tecnica** (45%)")
            tech_color = "green" if 'BULLISH' in tech['direction'] else ("red" if 'BEARISH' in tech['direction'] else "gray")
            st.markdown(f"Direzione: :{tech_color}[**{tech['direction']}**]")
            st.write(f"Score: {tech['score']}")
            st.write(f"RSI: {tech['rsi']} ({tech['rsi_status']})")
            st.write(f"ADX: {tech['adx']}")
        
        with col2:
            st.markdown("**💰 Fondamentale** (30%)")
            fund_color = "green" if 'BULLISH' in fund['direction'] else ("red" if 'BEARISH' in fund['direction'] else "gray")
            st.markdown(f"Direzione: :{fund_color}[**{fund['direction']}**]")
            st.write(f"Score: {fund['score']}")
            st.write(f"{fund['info']}")
        
        with col3:
            st.markdown("**💭 Sentiment** (25%)")
            sent_color = "green" if 'BULLISH' in sent['direction'] else ("red" if 'BEARISH' in sent['direction'] else "gray")
            st.markdown(f"Direzione: :{sent_color}[**{sent['direction']}**]")
            st.write(f"Score: {sent['score']}")
            st.write(f"News analizzate: {sent.get('count', 0)}")
            
            if sent.get('news'):
                st.markdown("**Ultime news:**")
                for n in sent['news'][:3]:
                    emoji = "🟢" if n['sentiment'] == 'BULLISH' else ("🔴" if n['sentiment'] == 'BEARISH' else "⚪")
                    st.caption(f"{emoji} {n['title']}")
        
        st.divider()
        
        # Grafico
        st.subheader("📈 Grafico Tecnico")
        
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=('Prezzo + Indicatori', 'RSI', 'MACD')
        )
        
        # Candlestick
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Prezzo',
                increasing_line_color='#00C853',
                decreasing_line_color='#FF1744'
            ),
            row=1, col=1
        )
        
        # EMA
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], name='EMA 21', line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], name='EMA 50', line=dict(color='blue', width=1)), row=1, col=1)
        
        # Bollinger
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='BB Upper', line=dict(color='rgba(128,128,128,0.5)', width=1, dash='dot')), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], name='BB Lower', line=dict(color='rgba(128,128,128,0.5)', width=1, dash='dot'), fill='tonexty', fillcolor='rgba(128,128,128,0.1)'), row=1, col=1)
        
        # Livelli Entry/SL/TP
        if action != 'WAIT':
            fig.add_hline(y=entry_data['entry'], line_dash="solid", line_color="blue", annotation_text="Entry", row=1, col=1)
            fig.add_hline(y=entry_data['stop_loss'], line_dash="dash", line_color="red", annotation_text="SL", row=1, col=1)
            fig.add_hline(y=entry_data['tp1'], line_dash="dash", line_color="green", annotation_text="TP1", row=1, col=1)
            fig.add_hline(y=entry_data['tp2'], line_dash="dot", line_color="green", annotation_text="TP2", row=1, col=1)
        
        # RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple', width=2)), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)
        
        # MACD
        colors = ['green' if val >= 0 else 'red' for val in df['MACD_Hist'].fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='MACD Hist', marker_color=colors), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='blue', width=1)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal', line=dict(color='orange', width=1)), row=3, col=1)
        
        fig.update_layout(
            height=700,
            xaxis_rangeslider_visible=False,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Footer
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption("📡 Dati: Yahoo Finance (15 min delay)")
        with col2:
            st.caption("📰 News: ForexLive RSS")
        with col3:
            st.caption(f"🕐 Ultimo aggiornamento: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
