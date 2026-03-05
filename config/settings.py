"""
Configurazioni dell'applicazione
"""

# Coppie di valute supportate
FOREX_PAIRS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X",
    "AUDUSD=X", "USDCAD=X", "NZDUSD=X", "EURGBP=X",
    "EURJPY=X", "GBPJPY=X", "EURCHF=X", "AUDJPY=X"
]

# Mapping nomi leggibili
PAIR_NAMES = {
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
    "AUDJPY=X": "AUD/JPY"
}

# Timeframes
TIMEFRAMES = {
    "1h": "1h",
    "4h": "4h",
    "1d": "1d",
    "1wk": "1wk"
}

# Fonti per sentiment analysis
NEWS_SOURCES = [
    "https://www.forexfactory.com/calendar",
    "https://www.investing.com/currencies/",
    "https://www.dailyfx.com/forex-rates",
    "https://www.fxstreet.com/"
]

# RSS Feeds
RSS_FEEDS = [
    "https://www.forexlive.com/feed/",
    "https://www.dailyfx.com/feeds/all",
    "https://www.fxstreet.com/rss/news"
]

# Parametri analisi tecnica
TECHNICAL_PARAMS = {
    "rsi_period": 14,
    "rsi_overbought": 70,
    "rsi_oversold": 30,
    "macd_fast": 12,
    "macd_slow": 26,
    "macd_signal": 9,
    "bb_period": 20,
    "bb_std": 2,
    "ema_short": 9,
    "ema_medium": 21,
    "ema_long": 50,
    "atr_period": 14
}

# Pesi per il calcolo del segnale finale
SIGNAL_WEIGHTS = {
    "technical": 0.45,
    "fundamental": 0.30,
    "sentiment": 0.25
}
