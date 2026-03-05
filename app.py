"""
📊 Forex Analysis Pro - Auto Scanner con Notifiche
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
import hashlib

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
    .scan-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #1E88E5;
    }
    .scan-bullish { border-left-color: #00C853; }
    .scan-bearish { border-left-color: #FF1744; }
    .auto-scan-active {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

# ==================== COPPIE E TIMEFRAME ====================

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
    "EURCHF=X": "EUR/CHF",
    "AUDJPY=X": "AUD/JPY",
    "GC=F": "🥇 XAU/USD (Gold)",
}

TIMEFRAMES = {
    "15m": {"interval": "15m", "period": "5d", "name": "15 Minuti"},
    "30m": {"interval": "30m", "period": "10d", "name": "30 Minuti"},
    "1h": {"interval": "1h", "period": "1mo", "name": "1 Ora"},
    "4h": {"interval": "1h", "period": "3mo", "name": "4 Ore"},  # Resample
    "1d": {"interval": "1d", "period": "6mo", "name": "Giornaliero"},
    "1wk": {"interval": "1wk", "period": "2y", "name": "Settimanale"},
}

# ==================== TELEGRAM ====================

def get_telegram_config():
    """Legge configurazione Telegram"""
    try:
        bot_token = st.secrets.get("telegram", {}).get("bot_token", "")
        chat_id = st.secrets.get("telegram", {}).get("chat_id", "")
        return bot_token, chat_id
    except:
        return "", ""


def is_telegram_configured():
    """Verifica se Telegram è configurato"""
    bot_token, chat_id = get_telegram_config()
    return bool(bot_token and chat_id)


def send_telegram_notification(signal, is_auto_scan=False):
    """Invia notifica Telegram"""
    bot_token, chat_id = get_telegram_config()
    
    if not bot_token or not chat_id:
        return False, "Non configurato"
    
    try:
        emoji = "🟢" if signal['action'] == 'LONG' else "🔴"
        scan_badge = "🤖 AUTO-SCAN" if is_auto_scan else "📊 MANUALE"
        
        message = f"""
{emoji} <b>SEGNALE FOREX</b> {emoji}
{scan_badge}

📊 <b>{signal['pair']}</b> | ⏱️ {signal.get('timeframe', 'N/A')}
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
        
        return response.status_code == 200, "OK" if response.status_code == 200 else response.text
            
    except Exception as e:
        return False, str(e)


def get_signal_hash(pair, action, timeframe):
    """Hash unico per evitare duplicati"""
    unique_str = f"{pair}_{action}_{timeframe}_{datetime.now().strftime('%Y-%m-%d-%H')}"
    return hashlib.md5(unique_str.encode()).hexdigest()


def was_signal_sent(signal_hash):
    """Controlla se già inviato"""
    if 'sent_signals' not in st.session_state:
        st.session_state.sent_signals = set()
    return signal_hash in st.session_state.sent_signals


def mark_signal_sent(signal_hash):
    """Marca come inviato"""
    if 'sent_signals' not in st.session_state:
        st.session_state.sent_signals = set()
    st.session_state.sent_signals.add(signal_hash)
    
    # Pulisci vecchi segnali (max 100)
    if len(st.session_state.sent_signals) > 100:
        st.session_state.sent_signals = set(list(st.session_state.sent_signals)[-50:])


# ==================== DATA FUNCTIONS ====================

@st.cache_data(ttl=300)  # Cache 5 minuti
def get_price_data(symbol, period="3mo", interval="1d"):
    """Scarica dati prezzo"""
    import yfinance as yf
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty and symbol == "GC=F":
            ticker = yf.Ticker("XAUUSD=X")
            df = ticker.history(period=period, interval=interval)
        
        return df if not df.empty else None
        
    except Exception as e:
        return None


def resample_to_4h(df):
    """Resample dati 1h a 4h"""
    if df is None or df.empty:
        return None
    
    df_4h = df.resample('4H').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    
    return df_4h


def calculate_indicators(df):
    """Calcola indicatori tecnici"""
    if df is None or len(df) < 20:
        return None
    
    close = df['Close']
    high = df['High']
    low = df['Low']
    
    # RSI
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
    
    return df


def get_technical_score(df):
    """Score tecnico"""
    if df is None or df.empty:
        return {'score': 0, 'direction': 'NEUTRAL', 'rsi': 50, 'rsi_status': 'N/A'}
    
    current = df.iloc[-1]
    score = 0
    
    rsi = current.get('RSI', 50)
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
    
    macd = current.get('MACD', 0)
    macd_signal = current.get('MACD_Signal', 0)
    
    if not pd.isna(macd) and not pd.isna(macd_signal):
        if macd > macd_signal:
            score += 0.5
        else:
            score -= 0.5
    
    ema_9 = current.get('EMA_9')
    ema_21 = current.get('EMA_21')
    ema_50 = current.get('EMA_50')
    close = current.get('Close')
    
    if all(not pd.isna(x) for x in [ema_9, ema_21, ema_50, close]):
        if close > ema_21 > ema_50:
            score += 0.5
        elif close < ema_21 < ema_50:
            score -= 0.5
    
    bb_lower = current.get('BB_Lower')
    bb_upper = current.get('BB_Upper')
    
    if not pd.isna(bb_lower) and not pd.isna(bb_upper) and not pd.isna(close):
        if close < bb_lower:
            score += 0.5
        elif close > bb_upper:
            score -= 0.5
    
    stoch_k = current.get('Stoch_K')
    if not pd.isna(stoch_k):
        if stoch_k < 20:
            score += 0.3
        elif stoch_k > 80:
            score -= 0.3
    
    score = max(-1, min(1, score / 2.5))
    
    return {
        'score': round(score, 3),
        'probability_bull': round(((score + 1) / 2) * 100, 1),
        'direction': 'BULLISH' if score > 0.15 else ('BEARISH' if score < -0.15 else 'NEUTRAL'),
        'rsi': round(rsi, 1),
        'rsi_status': rsi_status
    }


def get_fundamental_score(pair):
    """Score fondamentale"""
    rates = {
        'USD': 5.50, 'EUR': 4.50, 'GBP': 5.25, 'JPY': 0.25,
        'CHF': 1.00, 'AUD': 4.35, 'CAD': 3.75, 'NZD': 4.75, 'XAU': 0
    }
    
    pair_clean = pair.replace("=X", "").replace("GC=F", "XAUUSD")
    
    if "XAU" in pair_clean or "GOLD" in pair_clean.upper():
        usd_rate = rates['USD']
        score = -0.3 if usd_rate > 5 else (0.4 if usd_rate < 3 else 0)
        return {
            'score': round(score, 3),
            'direction': 'BULLISH' if score > 0.1 else ('BEARISH' if score < -0.1 else 'NEUTRAL'),
            'info': f"USD: {usd_rate}%"
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
            'info': f"{base}: {base_rate}% | {quote}: {quote_rate}%"
        }


@st.cache_data(ttl=1800)
def get_news_sentiment(pair):
    """Sentiment news"""
    try:
        feed = feedparser.parse("https://www.forexlive.com/feed/")
        
        pair_clean = pair.replace("=X", "").replace("GC=F", "GOLD")
        
        if "GC=F" in pair or "XAU" in pair.upper():
            terms = ["GOLD", "XAU", "PRECIOUS", "METAL"]
        else:
            base = pair_clean[:3]
            quote = pair_clean[3:6] if len(pair_clean) > 3 else ""
            terms = [pair_clean, base, quote]
        
        polarities = []
        
        for entry in feed.entries[:20]:
            text = entry.get('title', '') + ' ' + entry.get('summary', '')[:200]
            
            if any(t.upper() in text.upper() for t in terms if t):
                blob = TextBlob(text)
                polarities.append(blob.sentiment.polarity)
        
        if not polarities:
            return {'score': 0, 'direction': 'NEUTRAL'}
        
        avg = sum(polarities) / len(polarities)
        
        return {
            'score': round(avg, 3),
            'direction': 'BULLISH' if avg > 0.05 else ('BEARISH' if avg < -0.05 else 'NEUTRAL')
        }
        
    except:
        return {'score': 0, 'direction': 'NEUTRAL'}


def calculate_entry_points(df, direction):
    """Calcola entry, SL, TP"""
    if df is None or df.empty:
        return None
    
    current = df['Close'].iloc[-1]
    atr = df['ATR'].iloc[-1] if 'ATR' in df.columns else current * 0.01
    
    if pd.isna(atr):
        atr = current * 0.01
    
    if 'BULLISH' in direction:
        entry, sl = current, current - (atr * 2)
        tp1, tp2, tp3 = current + (atr * 2), current + (atr * 3.5), current + (atr * 5)
    elif 'BEARISH' in direction:
        entry, sl = current, current + (atr * 2)
        tp1, tp2, tp3 = current - (atr * 2), current - (atr * 3.5), current - (atr * 5)
    else:
        entry, sl = current, current - (atr * 2)
        tp1, tp2, tp3 = current + (atr * 2), current + (atr * 3), current + (atr * 4)
    
    risk = abs(entry - sl)
    rr = abs(tp1 - entry) / risk if risk > 0 else 0
    
    return {'entry': entry, 'stop_loss': sl, 'tp1': tp1, 'tp2': tp2, 'tp3': tp3, 'risk_reward': round(rr, 2)}


def calculate_lots(balance, risk_pct, entry, sl, pair):
    """Calcola lotti"""
    risk_amount = balance * (risk_pct / 100)
    pip_distance = abs(entry - sl)
    
    if "JPY" in pair:
        pip_distance *= 100
        pip_value = 1000 / entry
    elif "XAU" in pair or "GC=F" in pair:
        dollar_risk_per_lot = pip_distance * 100
        lots = risk_amount / dollar_risk_per_lot if dollar_risk_per_lot > 0 else 0
        return {'lots': round(lots, 2), 'risk_amount': round(risk_amount, 2)}
    else:
        pip_distance *= 10000
        pip_value = 10
    
    lots = risk_amount / (pip_distance * pip_value) if pip_distance > 0 else 0
    
    return {'lots': round(lots, 2), 'risk_amount': round(risk_amount, 2)}


def analyze_pair(pair, timeframe_key, balance, risk_pct):
    """Analizza una coppia su un timeframe"""
    tf = TIMEFRAMES[timeframe_key]
    
    # Scarica dati
    df = get_price_data(pair, tf['period'], tf['interval'])
    
    # Resample per 4h
    if timeframe_key == "4h" and df is not None:
        df = resample_to_4h(df)
    
    if df is None or len(df) < 20:
        return None
    
    # Calcola indicatori
    df = calculate_indicators(df)
    
    if df is None:
        return None
    
    # Analisi
    tech = get_technical_score(df)
    fund = get_fundamental_score(pair)
    sent = get_news_sentiment(pair)
    
    # Score combinato
    combined = (tech['score'] * 0.45) + (fund['score'] * 0.30) + (sent['score'] * 0.25)
    prob_bull = ((combined + 1) / 2) * 100
    
    # Direzione
    if combined > 0.25:
        direction, action, confidence = "STRONG BUY", "LONG", "ALTA"
    elif combined > 0.10:
        direction, action, confidence = "BUY", "LONG", "MEDIA"
    elif combined < -0.25:
        direction, action, confidence = "STRONG SELL", "SHORT", "ALTA"
    elif combined < -0.10:
        direction, action, confidence = "SELL", "SHORT", "MEDIA"
    else:
        direction, action, confidence = "NEUTRAL", "WAIT", "BASSA"
    
    # Entry points
    entry_data = calculate_entry_points(df, direction)
    
    if entry_data is None:
        return None
    
    # Lotti
    lot_data = calculate_lots(balance, risk_pct, entry_data['entry'], entry_data['stop_loss'], pair)
    
    return {
        'pair': pair,
        'pair_name': PAIRS[pair],
        'timeframe': tf['name'],
        'timeframe_key': timeframe_key,
        'price': df['Close'].iloc[-1],
        'action': action,
        'direction': direction,
        'confidence': confidence,
        'probability': prob_bull if action == 'LONG' else (100 - prob_bull if action == 'SHORT' else 50),
        'score': combined,
        'tech': tech,
        'fund': fund,
        'sent': sent,
        'entry': entry_data['entry'],
        'sl': entry_data['stop_loss'],
        'tp1': entry_data['tp1'],
        'tp2': entry_data['tp2'],
        'tp3': entry_data['tp3'],
        'rr': entry_data['risk_reward'],
        'lots': lot_data['lots'],
        'risk_amount': lot_data['risk_amount'],
        'df': df  # Per il grafico
    }


# ==================== MAIN APP ====================

def main():
    st.title("📊 Forex Analysis Pro")
    st.caption("Analisi Multi-Timeframe | Auto-Scan | Notifiche Telegram Automatiche")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Analisi Singola", "🔄 Auto-Scan", "⚙️ Impostazioni"])
    
    # ==================== TAB 1: ANALISI SINGOLA ====================
    
    with tab1:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.subheader("⚙️ Parametri")
            
            pair = st.selectbox("📈 Coppia", options=list(PAIRS.keys()), format_func=lambda x: PAIRS[x], key="single_pair")
            timeframe = st.selectbox("⏱️ Timeframe", options=list(TIMEFRAMES.keys()), format_func=lambda x: TIMEFRAMES[x]['name'], index=4, key="single_tf")
            
            st.divider()
            
            balance = st.number_input("💰 Saldo ($)", value=10000, step=1000, min_value=100, key="single_balance")
            risk_pct = st.slider("⚠️ Rischio (%)", 0.5, 5.0, 1.0, 0.5, key="single_risk")
            
            st.divider()
            
            # Telegram status
            if is_telegram_configured():
                st.success("📱 Telegram: ✅ Attivo")
            else:
                st.warning("📱 Telegram: ⚠️ Non configurato")
            
            analyze_btn = st.button("🔍 ANALIZZA", type="primary", use_container_width=True, key="single_analyze")
        
        with col2:
            if analyze_btn:
                with st.spinner("📊 Analisi in corso..."):
                    result = analyze_pair(pair, timeframe, balance, risk_pct)
                
                if result is None:
                    st.error("❌ Impossibile analizzare. Riprova.")
                else:
                    # Signal
                    if result['action'] == 'LONG':
                        st.markdown(f'<div class="signal-box bullish-signal">🟢 {result["action"]} | {result["direction"]}</div>', unsafe_allow_html=True)
                    elif result['action'] == 'SHORT':
                        st.markdown(f'<div class="signal-box bearish-signal">🔴 {result["action"]} | {result["direction"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="signal-box neutral-signal">🟡 {result["action"]} | {result["direction"]}</div>', unsafe_allow_html=True)
                    
                    # Metriche
                    m1, m2, m3, m4 = st.columns(4)
                    decimals = 2 if "JPY" in pair or "GC" in pair else 5
                    
                    m1.metric("💵 Prezzo", f"{result['price']:.{decimals}f}")
                    m2.metric("📈 Probabilità", f"{result['probability']:.1f}%")
                    m3.metric("🎯 Confidenza", result['confidence'])
                    m4.metric("📊 R/R", result['rr'])
                    
                    st.divider()
                    
                    # Livelli e Lotti
                    c1, c2 = st.columns(2)
                    
                    with c1:
                        st.markdown("**🎯 Livelli Operativi**")
                        st.code(f"""
Entry:      {result['entry']:.{decimals}f}
Stop Loss:  {result['sl']:.{decimals}f}
TP1:        {result['tp1']:.{decimals}f}
TP2:        {result['tp2']:.{decimals}f}
TP3:        {result['tp3']:.{decimals}f}
                        """)
                    
                    with c2:
                        st.markdown("**📏 Position Sizing**")
                        st.metric("Lotti", result['lots'])
                        st.metric("Rischio", f"${result['risk_amount']}")
                        
                        # Telegram
                        if result['action'] in ['LONG', 'SHORT'] and is_telegram_configured():
                            if st.button("📱 Invia Telegram", use_container_width=True):
                                signal_data = {
                                    'pair': result['pair_name'],
                                    'timeframe': result['timeframe'],
                                    'action': result['action'],
                                    'probability': result['probability'],
                                    'confidence': result['confidence'],
                                    'entry': result['entry'],
                                    'sl': result['sl'],
                                    'tp1': result['tp1'],
                                    'tp2': result['tp2'],
                                    'tp3': result['tp3'],
                                    'lots': result['lots'],
                                    'risk_amount': result['risk_amount'],
                                    'rr': result['rr'],
                                    'tech_dir': result['tech']['direction'],
                                    'fund_dir': result['fund']['direction'],
                                    'sent_dir': result['sent']['direction']
                                }
                                success, msg = send_telegram_notification(signal_data)
                                if success:
                                    st.success("✅ Inviato!")
                                else:
                                    st.error(f"❌ {msg}")
                    
                    st.divider()
                    
                    # Grafico
                    st.markdown("**📈 Grafico**")
                    
                    df = result['df']
                    
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
                    
                    fig.add_trace(go.Candlestick(
                        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                        name='Prezzo', increasing_line_color='#00C853', decreasing_line_color='#FF1744'
                    ), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(x=df.index, y=df['EMA_21'], name='EMA 21', line=dict(color='orange', width=1)), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], name='BB', line=dict(color='gray', width=1, dash='dot')), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], showlegend=False, line=dict(color='gray', width=1, dash='dot')), row=1, col=1)
                    
                    if result['action'] != 'WAIT':
                        fig.add_hline(y=result['sl'], line_dash="dash", line_color="red", annotation_text="SL", row=1, col=1)
                        fig.add_hline(y=result['tp1'], line_dash="dash", line_color="green", annotation_text="TP1", row=1, col=1)
                    
                    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='purple')), row=2, col=1)
                    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
                    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
                    
                    fig.update_layout(height=500, xaxis_rangeslider_visible=False, showlegend=True)
                    st.plotly_chart(fig, use_container_width=True)
    
    # ==================== TAB 2: AUTO-SCAN ====================
    
    with tab2:
        st.subheader("🔄 Auto-Scan Multi-Coppia")
        st.caption("Scansiona tutte le coppie e ricevi notifiche automatiche per i segnali forti")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**⚙️ Parametri Scan**")
            
            scan_timeframes = st.multiselect(
                "Timeframe da scansionare",
                options=list(TIMEFRAMES.keys()),
                default=["1h", "4h", "1d"],
                format_func=lambda x: TIMEFRAMES[x]['name']
            )
            
            scan_balance = st.number_input("💰 Saldo ($)", value=10000, step=1000, key="scan_balance")
            scan_risk = st.slider("⚠️ Rischio (%)", 0.5, 5.0, 1.0, 0.5, key="scan_risk")
            
            min_confidence = st.selectbox("📊 Confidenza minima", ["BASSA", "MEDIA", "ALTA"], index=1)
            
            auto_telegram = st.checkbox("📱 Invia automaticamente su Telegram", value=True)
            
            st.divider()
            
            scan_btn = st.button("🚀 AVVIA SCAN", type="primary", use_container_width=True)
            
            # Auto-refresh
            st.divider()
            st.markdown("**🔄 Auto-Refresh**")
            auto_refresh = st.checkbox("Attiva auto-refresh", value=False)
            
            if auto_refresh:
                refresh_interval = st.selectbox("Intervallo", [1, 5, 15, 30, 60], index=2, format_func=lambda x: f"{x} minuti")
                st.markdown(f'<div class="auto-scan-active">🔄 Auto-scan attivo ogni {refresh_interval} min</div>', unsafe_allow_html=True)
                
                # Countdown e refresh automatico
                time.sleep(0.1)  # Piccolo delay
                st.rerun() if st.session_state.get('auto_scan_trigger') else None
        
        with col2:
            if scan_btn or auto_refresh:
                st.markdown("**📊 Risultati Scan**")
                
                signals_found = []
                progress = st.progress(0)
                status = st.empty()
                
                total_scans = len(PAIRS) * len(scan_timeframes)
                current = 0
                
                for pair in PAIRS:
                    for tf in scan_timeframes:
                        current += 1
                        progress.progress(current / total_scans)
                        status.text(f"Analisi {PAIRS[pair]} - {TIMEFRAMES[tf]['name']}...")
                        
                        try:
                            result = analyze_pair(pair, tf, scan_balance, scan_risk)
                            
                            if result and result['action'] in ['LONG', 'SHORT']:
                                # Filtra per confidenza
                                conf_order = {"BASSA": 0, "MEDIA": 1, "ALTA": 2}
                                if conf_order[result['confidence']] >= conf_order[min_confidence]:
                                    signals_found.append(result)
                                    
                                    # Auto Telegram
                                    if auto_telegram and is_telegram_configured():
                                        signal_hash = get_signal_hash(pair, result['action'], tf)
                                        
                                        if not was_signal_sent(signal_hash):
                                            signal_data = {
                                                'pair': result['pair_name'],
                                                'timeframe': result['timeframe'],
                                                'action': result['action'],
                                                'probability': result['probability'],
                                                'confidence': result['confidence'],
                                                'entry': result['entry'],
                                                'sl': result['sl'],
                                                'tp1': result['tp1'],
                                                'tp2': result['tp2'],
                                                'tp3': result['tp3'],
                                                'lots': result['lots'],
                                                'risk_amount': result['risk_amount'],
                                                'rr': result['rr'],
                                                'tech_dir': result['tech']['direction'],
                                                'fund_dir': result['fund']['direction'],
                                                'sent_dir': result['sent']['direction']
                                            }
                                            
                                            success, _ = send_telegram_notification(signal_data, is_auto_scan=True)
                                            if success:
                                                mark_signal_sent(signal_hash)
                        except:
                            continue
                
                progress.empty()
                status.empty()
                
                # Mostra risultati
                if signals_found:
                    st.success(f"✅ Trovati {len(signals_found)} segnali!")
                    
                    for sig in sorted(signals_found, key=lambda x: abs(x['score']), reverse=True):
                        card_class = "scan-bullish" if sig['action'] == 'LONG' else "scan-bearish"
                        emoji = "🟢" if sig['action'] == 'LONG' else "🔴"
                        
                        decimals = 2 if "JPY" in sig['pair'] or "GC" in sig['pair'] else 5
                        
                        st.markdown(f'''
                        <div class="scan-card {card_class}">
                            <b>{emoji} {sig['pair_name']}</b> | {sig['timeframe']}<br>
                            <small>
                            {sig['action']} | Prob: {sig['probability']:.1f}% | Conf: {sig['confidence']}<br>
                            Entry: {sig['entry']:.{decimals}f} | SL: {sig['sl']:.{decimals}f} | TP1: {sig['tp1']:.{decimals}f}<br>
                            Lotti: {sig['lots']} | R/R: {sig['rr']}
                            </small>
                        </div>
                        ''', unsafe_allow_html=True)
                else:
                    st.info("ℹ️ Nessun segnale trovato con i criteri selezionati.")
    
    # ==================== TAB 3: IMPOSTAZIONI ====================
    
    with tab3:
        st.subheader("⚙️ Impostazioni")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📱 Telegram**")
            
            if is_telegram_configured():
                st.success("✅ Telegram configurato correttamente")
                
                if st.button("🧪 Test Notifica"):
                    test_signal = {
                        'pair': 'TEST',
                        'timeframe': 'Test',
                        'action': 'LONG',
                        'probability': 75.5,
                        'confidence': 'ALTA',
                        'entry': 1.12345,
                        'sl': 1.12000,
                        'tp1': 1.12700,
                        'tp2': 1.13000,
                        'tp3': 1.13500,
                        'lots': 0.10,
                        'risk_amount': 100,
                        'rr': 2.0,
                        'tech_dir': 'BULLISH',
                        'fund_dir': 'BULLISH',
                        'sent_dir': 'NEUTRAL'
                    }
                    success, msg = send_telegram_notification(test_signal)
                    if success:
                        st.success("✅ Test inviato!")
                    else:
                        st.error(f"❌ Errore: {msg}")
            else:
                st.warning("⚠️ Telegram non configurato")
                st.markdown("""
                **Come configurare:**
                1. Vai su Streamlit Cloud → Settings → Secrets
                2. Aggiungi:
                ```toml
                [telegram]
                bot_token = "IL_TUO_TOKEN"
                chat_id = "IL_TUO_CHAT_ID"
                ```
                """)
        
        with col2:
            st.markdown("**📊 Info Sistema**")
            st.write(f"🕐 Ora server: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"📈 Coppie disponibili: {len(PAIRS)}")
            st.write(f"⏱️ Timeframe disponibili: {len(TIMEFRAMES)}")
            
            if 'sent_signals' in st.session_state:
                st.write(f"📱 Segnali inviati (sessione): {len(st.session_state.sent_signals)}")


if __name__ == "__main__":
    main()
