"""
Provider Dati - 100% Gratuito
Fonti: Yahoo Finance, RSS Feeds, CFTC, MyFxBook
"""

import requests
import feedparser
import yfinance as yf
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time


class FreeDataProvider:
    """Provider dati completamente gratuito"""
    
    @staticmethod
    def get_forex_data(symbol: str, period: str = "3mo", interval: str = "1h") -> pd.DataFrame:
        """
        Scarica dati forex da Yahoo Finance
        ✅ GRATUITO illimitato
        """
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                return None
            
            df.index = pd.to_datetime(df.index)
            return df
            
        except Exception as e:
            print(f"Errore Yahoo Finance: {e}")
            return None
    
    @staticmethod
    def get_multiple_timeframes(symbol: str) -> dict:
        """Scarica dati su più timeframe"""
        timeframes = {
            '1h': ('5d', '1h'),
            '4h': ('1mo', '1h'),  # Yahoo non ha 4h, useremo 1h e resample
            '1d': ('6mo', '1d'),
            '1wk': ('2y', '1wk')
        }
        
        data = {}
        for tf, (period, interval) in timeframes.items():
            df = FreeDataProvider.get_forex_data(symbol, period, interval)
            if df is not None:
                if tf == '4h' and interval == '1h':
                    # Resample a 4h
                    df = df.resample('4H').agg({
                        'Open': 'first',
                        'High': 'max',
                        'Low': 'min',
                        'Close': 'last',
                        'Volume': 'sum'
                    }).dropna()
                data[tf] = df
        
        return data
    
    @staticmethod
    def get_central_bank_rates() -> dict:
        """
        Tassi banche centrali aggiornati
        Fonte: Dati ufficiali banche centrali
        Ultimo aggiornamento: Gennaio 2025
        """
        return {
            'USD': {
                'rate': 5.50,
                'bank': 'Federal Reserve',
                'last_change': '2023-07-26',
                'next_meeting': '2025-01-29',
                'trend': 'stable'
            },
            'EUR': {
                'rate': 4.50,
                'bank': 'European Central Bank',
                'last_change': '2023-09-14',
                'next_meeting': '2025-01-25',
                'trend': 'cutting'
            },
            'GBP': {
                'rate': 5.25,
                'bank': 'Bank of England',
                'last_change': '2023-08-03',
                'next_meeting': '2025-02-06',
                'trend': 'stable'
            },
            'JPY': {
                'rate': 0.25,
                'bank': 'Bank of Japan',
                'last_change': '2024-07-31',
                'next_meeting': '2025-01-24',
                'trend': 'hiking'
            },
            'CHF': {
                'rate': 1.00,
                'bank': 'Swiss National Bank',
                'last_change': '2024-09-26',
                'next_meeting': '2025-03-20',
                'trend': 'cutting'
            },
            'AUD': {
                'rate': 4.35,
                'bank': 'Reserve Bank of Australia',
                'last_change': '2023-11-07',
                'next_meeting': '2025-02-18',
                'trend': 'stable'
            },
            'CAD': {
                'rate': 3.75,
                'bank': 'Bank of Canada',
                'last_change': '2024-10-23',
                'next_meeting': '2025-01-29',
                'trend': 'cutting'
            },
            'NZD': {
                'rate': 4.75,
                'bank': 'Reserve Bank of New Zealand',
                'last_change': '2024-10-09',
                'next_meeting': '2025-02-19',
                'trend': 'cutting'
            }
        }
    
    @staticmethod
    def fetch_forex_news(pair: str = None, limit: int = 25) -> list:
        """
        Recupera news forex da RSS feeds gratuiti
        ✅ GRATUITO illimitato
        """
        feeds = [
            {
                'name': 'ForexLive',
                'url': 'https://www.forexlive.com/feed/',
                'priority': 1
            },
            {
                'name': 'FXStreet',
                'url': 'https://www.fxstreet.com/rss/news',
                'priority': 2
            },
            {
                'name': 'DailyFX',
                'url': 'https://www.dailyfx.com/feeds/all',
                'priority': 2
            },
            {
                'name': 'Investing.com',
                'url': 'https://www.investing.com/rss/news_301.rss',
                'priority': 3
            }
        ]
        
        all_news = []
        
        for feed in feeds:
            try:
                parsed = feedparser.parse(feed['url'])
                
                for entry in parsed.entries[:15]:
                    # Pulisci HTML
                    summary = entry.get('summary', '')
                    if summary:
                        soup = BeautifulSoup(summary, 'html.parser')
                        summary = soup.get_text()[:400]
                    
                    title = entry.get('title', '')
                    
                    all_news.append({
                        'title': title,
                        'summary': summary,
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'source': feed['name'],
                        'priority': feed['priority']
                    })
                    
            except Exception as e:
                print(f"Errore feed {feed['name']}: {e}")
                continue
        
        # Ordina per priorità
        all_news.sort(key=lambda x: x['priority'])
        
        # Filtra per coppia se specificata
        if pair:
            pair_clean = pair.replace("=X", "").replace("/", "")
            base = pair_clean[:3]
            quote = pair_clean[3:6]
            
            search_terms = [
                pair_clean, 
                f"{base}/{quote}",
                f"{base}/{quote}".lower(),
                base, 
                quote,
                base.lower(),
                quote.lower()
            ]
            
            filtered = []
            for news in all_news:
                text = (news['title'] + ' ' + news['summary']).upper()
                if any(term.upper() in text for term in search_terms):
                    filtered.append(news)
            
            if filtered:
                return filtered[:limit]
        
        return all_news[:limit]
    
    @staticmethod
    def get_economic_calendar() -> list:
        """
        Calendario economico da fonti gratuite
        """
        events = []
        
        try:
            # Prova API gratuita di nfsfaireconomy (mirror di ForexFactory)
            url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for event in data[:50]:
                    impact = event.get('impact', 'Low')
                    
                    events.append({
                        'date': event.get('date', ''),
                        'time': event.get('time', ''),
                        'currency': event.get('country', ''),
                        'event': event.get('title', ''),
                        'impact': impact,
                        'forecast': event.get('forecast', ''),
                        'previous': event.get('previous', ''),
                        'actual': event.get('actual', '')
                    })
            
        except Exception as e:
            print(f"Errore calendario: {e}")
            # Fallback con eventi importanti standard
            events = FreeDataProvider._get_standard_events()
        
        return events
    
    @staticmethod
    def _get_standard_events() -> list:
        """Eventi economici standard come fallback"""
        today = datetime.now()
        
        return [
            {'date': today.strftime('%Y-%m-%d'), 'currency': 'USD', 'event': 'Controlla ForexFactory per eventi', 'impact': 'High'},
            {'date': today.strftime('%Y-%m-%d'), 'currency': 'EUR', 'event': 'Controlla ForexFactory per eventi', 'impact': 'High'},
        ]
    
    @staticmethod
    def get_retail_sentiment(pair: str) -> dict:
        """
        Sentiment retail da MyFxBook
        ✅ GRATUITO
        """
        pair_clean = pair.replace("=X", "").replace("/", "").upper()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            url = "https://www.myfxbook.com/community/outlook"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Cerca tabella outlook
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    
                    for row in rows:
                        cells = row.find_all('td')
                        
                        if len(cells) >= 4:
                            try:
                                cell_text = cells[0].get_text().strip()
                                row_pair = cell_text.replace('/', '').replace(' ', '').upper()
                                
                                # Match flessibile
                                if (pair_clean in row_pair or 
                                    row_pair in pair_clean or
                                    pair_clean[:6] == row_pair[:6]):
                                    
                                    # Estrai percentuali
                                    long_text = cells[1].get_text().strip()
                                    short_text = cells[2].get_text().strip()
                                    
                                    # Rimuovi % e converti
                                    long_match = re.search(r'(\d+\.?\d*)', long_text)
                                    short_match = re.search(r'(\d+\.?\d*)', short_text)
                                    
                                    if long_match and short_match:
                                        long_pct = float(long_match.group(1))
                                        short_pct = float(short_match.group(1))
                                        
                                        # Segnale contrarian
                                        if long_pct > 65:
                                            contrarian = 'BEARISH'
                                        elif long_pct < 35:
                                            contrarian = 'BULLISH'
                                        else:
                                            contrarian = 'NEUTRAL'
                                        
                                        return {
                                            'pair': pair_clean,
                                            'long_percent': long_pct,
                                            'short_percent': short_pct,
                                            'source': 'MyFxBook',
                                            'retail_sentiment': 'BULLISH' if long_pct > 55 else ('BEARISH' if long_pct < 45 else 'NEUTRAL'),
                                            'contrarian_signal': contrarian,
                                            'real_data': True
                                        }
                            except:
                                continue
        
        except Exception as e:
            print(f"Errore MyFxBook: {e}")
        
        # Fallback stimato
        return {
            'pair': pair_clean,
            'long_percent': 50,
            'short_percent': 50,
            'source': 'Estimated',
            'retail_sentiment': 'NEUTRAL',
            'contrarian_signal': 'NEUTRAL',
            'real_data': False
        }
    
    @staticmethod
    def get_cot_data() -> dict:
        """
        COT Data dalla CFTC
        ✅ GRATUITO - Dati ufficiali US Government
        Aggiornato ogni martedì
        """
        cot_data = {}
        
        try:
            # URL report COT futures
            url = "https://www.cftc.gov/dea/newcot/deafut.txt"
            
            response = requests.get(url, timeout=20)
            
            if response.status_code == 200:
                lines = response.text.split('\n')
                
                # Mapping futures forex su CME
                forex_futures = {
                    'EURO FX': 'EUR',
                    'BRITISH POUND': 'GBP',
                    'JAPANESE YEN': 'JPY',
                    'SWISS FRANC': 'CHF',
                    'AUSTRALIAN DOLLAR': 'AUD',
                    'CANADIAN DOLLAR': 'CAD',
                    'NZ DOLLAR': 'NZD',
                    'MEXICAN PESO': 'MXN'
                }
                
                for line in lines:
                    line_upper = line.upper()
                    
                    for futures_name, currency in forex_futures.items():
                        if futures_name in line_upper and 'CHICAGO' in line_upper:
                            parts = line.split(',')
                            
                            if len(parts) > 12:
                                try:
                                    # Non-commercial (speculatori/hedge funds)
                                    nc_long = int(parts[4].strip() or 0)
                                    nc_short = int(parts[5].strip() or 0)
                                    
                                    # Commercial (hedgers)
                                    c_long = int(parts[8].strip() or 0)
                                    c_short = int(parts[9].strip() or 0)
                                    
                                    # Net positions
                                    net_speculative = nc_long - nc_short
                                    net_commercial = c_long - c_short
                                    
                                    # Determina bias
                                    if net_speculative > 10000:
                                        bias = 'BULLISH'
                                    elif net_speculative < -10000:
                                        bias = 'BEARISH'
                                    else:
                                        bias = 'NEUTRAL'
                                    
                                    cot_data[currency] = {
                                        'non_commercial_long': nc_long,
                                        'non_commercial_short': nc_short,
                                        'commercial_long': c_long,
                                        'commercial_short': c_short,
                                        'net_speculative': net_speculative,
                                        'net_commercial': net_commercial,
                                        'bias': bias,
                                        'source': 'CFTC'
                                    }
                                    
                                except ValueError:
                                    continue
                            break
                
        except Exception as e:
            print(f"Errore COT CFTC: {e}")
        
        return cot_data
    
    @staticmethod
    def get_currency_strength() -> dict:
        """
        Calcola forza relativa delle valute
        Basato su performance vs USD
        """
        pairs_vs_usd = {
            'EUR': 'EURUSD=X',
            'GBP': 'GBPUSD=X',
            'AUD': 'AUDUSD=X',
            'NZD': 'NZDUSD=X',
            'USD': None,
            'JPY': 'USDJPY=X',
            'CHF': 'USDCHF=X',
            'CAD': 'USDCAD=X'
        }
        
        strength = {}
        
        for currency, pair in pairs_vs_usd.items():
            if pair is None:
                strength[currency] = {'change_1d': 0, 'change_1w': 0, 'score': 50}
                continue
                
            try:
                df = FreeDataProvider.get_forex_data(pair, period='7d', interval='1d')
                
                if df is not None and len(df) >= 2:
                    # Cambio 1 giorno
                    change_1d = ((df['Close'].iloc[-1] / df['Close'].iloc[-2]) - 1) * 100
                    
                    # Cambio 1 settimana
                    change_1w = ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100
                    
                    # Per JPY, CHF, CAD il pair è invertito
                    if currency in ['JPY', 'CHF', 'CAD']:
                        change_1d = -change_1d
                        change_1w = -change_1w
                    
                    # Score 0-100
                    score = 50 + (change_1w * 10)
                    score = max(0, min(100, score))
                    
                    strength[currency] = {
                        'change_1d': round(change_1d, 2),
                        'change_1w': round(change_1w, 2),
                        'score': round(score, 1)
                    }
                    
            except Exception as e:
                strength[currency] = {'change_1d': 0, 'change_1w': 0, 'score': 50}
        
        return strength
