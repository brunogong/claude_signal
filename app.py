"""
📊 Forex Analysis Pro - Con Debug
"""

import streamlit as st

# Debug mode - mostra errori
st.set_page_config(
    page_title="Forex Analysis Pro",
    page_icon="📊",
    layout="wide"
)

try:
    import pandas as pd
    import numpy as np
    st.write("✅ pandas, numpy OK")
except Exception as e:
    st.error(f"❌ Errore pandas/numpy: {e}")
    st.stop()

try:
    import yfinance as yf
    st.write("✅ yfinance OK")
except Exception as e:
    st.error(f"❌ Errore yfinance: {e}")
    st.stop()

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    st.write("✅ plotly OK")
except Exception as e:
    st.error(f"❌ Errore plotly: {e}")
    st.stop()

try:
    from ta.trend import MACD, EMAIndicator, ADXIndicator
    from ta.momentum import RSIIndicator, StochasticOscillator
    from ta.volatility import BollingerBands, AverageTrueRange
    st.write("✅ ta (technical analysis) OK")
except Exception as e:
    st.error(f"❌ Errore ta: {e}")
    st.stop()

try:
    import requests
    from bs4 import BeautifulSoup
    import feedparser
    st.write("✅ requests, beautifulsoup, feedparser OK")
except Exception as e:
    st.error(f"❌ Errore requests/bs4/feedparser: {e}")
    st.stop()

try:
    from textblob import TextBlob
    st.write("✅ textblob OK")
except Exception as e:
    st.error(f"❌ Errore textblob: {e}")
    st.stop()

try:
    from datetime import datetime
    st.write("✅ datetime OK")
except Exception as e:
    st.error(f"❌ Errore datetime: {e}")
    st.stop()

st.success("🎉 Tutte le librerie caricate correttamente!")
st.divider()

# ==================== TEST DATI ====================

st.subheader("Test caricamento dati")

try:
    ticker = yf.Ticker("EURUSD=X")
    df = ticker.history(period="5d", interval="1d")
    
    if df.empty:
        st.warning("⚠️ DataFrame vuoto per EURUSD")
    else:
        st.write(f"✅ Dati EURUSD caricati: {len(df)} righe")
        st.dataframe(df.tail())
except Exception as e:
    st.error(f"❌ Errore caricamento dati: {e}")

st.divider()

# ==================== APP COMPLETA ====================

st.title("📊 Forex Analysis Pro")
st.caption("Se vedi questo messaggio, l'app funziona!")

# Coppie
PAIRS = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "GC=F": "🥇 XAU/USD (Gold)",
}

# Sidebar
with st.sidebar:
    st.header("⚙️ Impostazioni")
    pair = st.selectbox("Coppia", options=list(PAIRS.keys()), format_func=lambda x: PAIRS[x])
    
    if st.button("🔍 Test Analisi", type="primary"):
        with st.spinner("Caricamento..."):
            try:
                ticker = yf.Ticker(pair)
                df = ticker.history(period="1mo", interval="1d")
                
                if df.empty:
                    st.error("Nessun dato disponibile")
                else:
                    st.success(f"Caricati {len(df)} dati per {PAIRS[pair]}")
                    
                    # Calcola RSI semplice
                    close = df['Close']
                    delta = close.diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    current_price = close.iloc[-1]
                    current_rsi = rsi.iloc[-1]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Prezzo", f"{current_price:.4f}")
                    with col2:
                        st.metric("RSI", f"{current_rsi:.1f}")
                    
                    # Segnale
                    if current_rsi < 30:
                        st.success("🟢 OVERSOLD - Possibile BUY")
                    elif current_rsi > 70:
                        st.error("🔴 OVERBOUGHT - Possibile SELL")
                    else:
                        st.info("🟡 NEUTRALE")
                        
            except Exception as e:
                st.error(f"Errore: {e}")
                import traceback
                st.code(traceback.format_exc())
