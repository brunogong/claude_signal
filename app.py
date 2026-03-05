"""
📊 Forex Analysis Pro
Analisi completa con XAU/USD, Notifiche Telegram e Calcolo Lotti
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from src.data_providers import FreeDataProvider
from src.signal_generator import SignalGenerator
from src.telegram_notifier import TelegramNotifier, get_telegram_notifier
from src.lot_calculator import LotCalculator, get_lot_calculator

# ==================== CONFIGURAZIONE ====================

st.set_page_config(
    page_title="Forex Analysis Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #1E88E5, #7C4DFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .signal-box {
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
        font-size: 1.5rem;
        font-weight: bold;
    }
    .bullish-signal {
        background: linear-gradient(135deg, #00C853, #00E676);
        color: white;
    }
    .bearish-signal {
        background: linear-gradient(135deg, #FF1744, #FF5252);
        color: white;
    }
    .neutral-signal {
        background: linear-gradient(135deg, #FFB300, #FFC107);
        color: black;
    }
    .gold-badge {
        background: linear-gradient(135deg, #FFD700, #FFA000);
        color: black;
        padding: 0.2rem 0.5rem;
        border-radius: 5px;
        font-size: 0.8rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1E88E5;
    }
    .telegram-status {
        padding: 0.5rem;
        border-radius: 5px;
        font-size: 0.8rem;
    }
    .telegram-ok { background: #c8e6c9; color: #2e7d32; }
    .telegram-error { background: #ffcdd2; color: #c62828; }
</style>
""", unsafe_allow_html=True)

# ==================== COPPIE FOREX + XAU ====================

FOREX_PAIRS = {
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

# ==================== FUNZIONI ====================

@st.cache_data(ttl=300)
def load_data(pair: str, period: str, interval: str):
    """Carica dati con cache 5 minuti"""
    if pair == "GC=F" or "XAU" in pair.upper():
        return FreeDataProvider.get_gold_data(period, interval)
    return FreeDataProvider.get_forex_data(pair, period, interval)


def send_telegram_notification(signal_data: dict, notifier: TelegramNotifier) -> bool:
    """Invia notifica Telegram"""
    if not notifier.is_configured():
        return False
    
    if not signal_data.get('recommendation', {}).get('should_notify', False):
        return False
    
    return notifier.send_trading_signal(signal_data)


def create_price_chart(df, signal_data):
    """Crea grafico prezzi"""
    
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.5, 0.17, 0.17, 0.16],
        subplot_titles=('Prezzo', 'RSI', 'MACD', 'Volume')
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#00C853',
            decreasing_line_color='#FF1744'
        ),
        row=1, col=1
    )
    
    # Indicatori dal technical analyzer
    analyzer = signal_data.get('_analyzer')
    if analyzer and hasattr(analyzer, 'df'):
        adf = analyzer.df
