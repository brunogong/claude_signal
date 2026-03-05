"""
Utility functions
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config.settings import PAIR_NAMES

def get_forex_data(symbol: str, period: str = "3mo", interval: str = "1h") -> pd.DataFrame:
    """
    Scarica dati forex da Yahoo Finance
    """
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            return None
            
        df.index = pd.to_datetime(df.index)
        return df
        
    except Exception as e:
        print(f"Errore download dati: {e}")
        return None

def get_pair_name(symbol: str) -> str:
    """Restituisce il nome leggibile della coppia"""
    return PAIR_NAMES.get(symbol, symbol.replace("=X", ""))

def calculate_pip_value(symbol: str, price: float) -> float:
    """Calcola il valore del pip"""
    if "JPY" in symbol:
        return 0.01
    return 0.0001

def format_price(symbol: str, price: float) -> str:
    """Formatta il prezzo in base alla coppia"""
    if "JPY" in symbol:
        return f"{price:.3f}"
    return f"{price:.5f}"

def get_session_info() -> dict:
    """Restituisce info sulla sessione di trading attuale"""
    now = datetime.utcnow()
    hour = now.hour
    
    sessions = {
        "sydney": (22, 7),
        "tokyo": (0, 9),
        "london": (8, 17),
        "new_york": (13, 22)
    }
    
    active = []
    for session, (start, end) in sessions.items():
        if start <= hour < end or (start > end and (hour >= start or hour < end)):
            active.append(session)
    
    return {
        "active_sessions": active,
        "utc_time": now.strftime("%H:%M UTC"),
        "volatility": "Alta" if len(active) > 1 else "Normale"
    }
