"""
Provider Dati - 100% Gratuito
Fonti: Yahoo Finance, RSS Feeds, CFTC, MyFxBook
Include XAU/USD (Oro)
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
    
    # Coppie supportate incluso XAU/USD
    SUPPORTED_PAIRS = {
        "EURUSD=X": {"name": "EUR/USD", "type": "forex", "pip": 0.0001},
        "GBPUSD=X": {"name": "GBP/USD", "type": "forex", "pip": 0.0001},
        "USDJPY=X": {"name": "USD/JPY", "type": "forex", "pip": 0.01},
        "USDCHF=X": {"name": "USD/CHF", "type": "forex", "pip": 0.0001},
        "AUDUSD=X": {"name": "AUD/USD", "type": "forex", "pip": 0.0001},
        "USDCAD=X": {"name": "USD/CAD", "type": "forex", "pip": 0.0001},
        "NZDUSD=X": {"name": "NZD/USD", "type": "forex", "pip": 0.0001},
        "EURGBP=X": {"name": "EUR/GBP", "type": "forex", "pip": 0.0001},
        "EURJPY=X": {"name": "EUR/JPY", "type": "forex", "pip": 0.01},
        "GBPJPY=X": {"name": "GBP/JPY", "type": "forex", "pip": 0.01},
        "EURCHF=X": {"name": "EUR/CHF", "type": "forex", "pip": 0.0001},
        "AUDJPY=X": {"name": "AUD/JPY", "type": "forex", "pip": 0.01},
        "GC=F": {"name": "XAU/USD (Gold)", "type": "commodity", "pip": 0.01},
        "XAUUSD=X": {"name": "XAU/USD", "type": "commodity", "pip": 0.01},
    }
    
    @staticmethod
    def get_forex_data(symbol: str, period: str = "3mo", interval: str = "1h") -> pd.DataFrame:
        """
        Scarica dati forex/commodity da Yahoo Finance
        ✅ GRATUITO illimitato
        """
        # Mappa simboli alternativi per l'oro
        symbol_map = {
            "XAUUSD=X": "GC=F",  # Gold Futures
            "XAUUSD": "GC=F",
        }
        
        actual_symbol = symbol_map.get(symbol, symbol)
        
        try:
            ticker = yf.Ticker(actual_symbol)
            df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                # Prova simbolo alternativo per l'oro
                if "XAU" in symbol.upper() or "GOLD" in symbol.upper():
                    ticker = yf.Ticker("GC=F")
                    df = ticker.history(period=period, interval=interval)
            
            if df.empty:
                return None
            
            df.index = pd.to_datetime(df.index)
            return df
            
        except Exception as e:
            print(f"Errore Yahoo Finance: {e}")
            return None
    
    @staticmethod
    def get_gold_data(period: str = "3mo", interval: str = "1h") -> pd.DataFrame:
        """
        Scarica specificamente dati oro
        Prova più simboli per maggiore affidabilità
        """
        symbols = ["GC=F", "XAUUSD=X", "^XAUUSD"]
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)
                
                if not df.empty:
                    df.index = pd.to_datetime(df.index)
                    return df
            except:
                continue
        
        return None
    
    @staticmethod
    def get_central_bank_rates() -> dict:
        """
        Tassi banche centrali aggiornati
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
            },
            'XAU': {
                'rate': 0,
                'bank': 'N/A - Commodity',
                'last_change': 'N/A',
                'next_meeting': 'N/A',
                'trend': 'N/A',
                'note': 'Gold - influenced by USD rates and inflation'
            }
        }
    
    @staticmethod
    def fetch_forex_news(pair: str = None, limit: int = 25) -> list:
        """
        Recupera news forex/gold da RSS feeds gratuiti
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
            },
            {
                'name': 'Kitco Gold',
                'url': 'https://www.kitco.com/rss/gold.rss',
                'priority': 1  # Priorità alta per notizie sull'oro
            }
        ]
        
        all_news = []
        
        for feed in feeds:
            try:
                parsed = feedparser.parse(feed['url'])
                
                for entry in parsed.entries[:15]:
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
        
        all_news.sort(key=lambda x: x['priority'])
        
        # Filtra per coppia se specificata
        if pair:
            pair_clean = pair.replace("=X", "").replace("/", "").replace("GC=F", "XAUUSD")
            
            # Termini di ricerca specifici per tipo
            if "XAU" in pair_clean.upper() or pair == "GC=F":
                search_terms = ['GOLD', 'XAU', 'ORO', 'PRECIOUS', 'METAL', 'BULLION', 'GOLD PRICE']
            else:
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
        Include eventi rilevanti per l'oro
        """
        events = []
        
        try:
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
            events = FreeDataProvider._get_standard_events()
        
        # Aggiungi eventi specifici per l'oro
        gold_events = [
            e for e in events 
            if any(term in e.get('event', '').upper() 
                   for term in ['CPI', 'INFLATION', 'FED', 'FOMC', 'INTEREST RATE', 'NFP', 'NON-FARM'])
        ]
        
        # Marca gli eventi rilevanti per l'oro
        for e in events:
            e['gold_relevant'] = any(
                term in e.get('event', '').upper() 
                for term in ['CPI', 'INFLATION', 'FED', 'FOMC', 'INTEREST RATE', 'NFP', 'GDP']
            )
        
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
        pair_clean = pair.replace("=X", "").replace("/", "").replace("GC=F", "XAUUSD").upper()
        
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
                
                tables = soup.find_all('table')
                
                for table in tables:
                    rows = table.find_all('tr')
                    
                    for row in rows:
                        cells = row.find_all('td')
                        
                        if len(cells) >= 4:
                            try:
                                cell_text = cells[0].get_text().strip()
                                row_pair = cell_text.replace('/', '').replace(' ', '').upper()
                                
                                # Match per forex e oro
                                if (pair_clean in row_pair or 
                                    row_pair in pair_clean or
                                    pair_clean[:6] == row_pair[:6] or
                                    ('XAU' in pair_clean and 'GOLD' in row_pair.upper())):
                                    
                                    long_text = cells[1].get_text().strip()
                                    short_text = cells[2].get_text().strip()
                                    
                                    long_match = re.search(r'(\d+\.?\d*)', long_text)
                                    short_match = re.search(r'(\d+\.?\d*)', short_text)
                                    
                                    if long_match and short_match:
                                        long_pct = float(long_match.group(1))
                                        short_pct = float(short_match.group(1))
                                        
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
        ✅ GRATUITO - Include Gold futures
        """
        cot_data = {}
        
        try:
            url = "https://www.cftc.gov/dea/newcot/deafut.txt"
            
            response = requests.get(url, timeout=20)
            
            if response.status_code == 200:
                lines = response.text.split('\n')
                
                # Mapping futures incluso oro
                futures_map = {
                    'EURO FX': 'EUR',
                    'BRITISH POUND': 'GBP',
                    'JAPANESE YEN': 'JPY',
                    'SWISS FRANC': 'CHF',
                    'AUSTRALIAN DOLLAR': 'AUD',
                    'CANADIAN DOLLAR': 'CAD',
                    'NZ DOLLAR': 'NZD',
                    'GOLD': 'XAU',  # Oro!
                    'SILVER': 'XAG',
                    'MEXICAN PESO': 'MXN'
                }
                
                for line in lines:
                    line_upper = line.upper()
                    
                    for futures_name, currency in futures_map.items():
                        if futures_name in line_upper:
                            # Per forex cerca CHICAGO, per metalli cerca COMEX
                            if ('CHICAGO' in line_upper or 
                                'COMEX' in line_upper or 
                                futures_name in ['GOLD', 'SILVER']):
                                
                                parts = line.split(',')
                                
                                if len(parts) > 12:
                                    try:
                                        nc_long = int(parts[4].strip() or 0)
                                        nc_short = int(parts[5].strip() or 0)
                                        c_long = int(parts[8].strip() or 0)
                                        c_short = int(parts[9].strip() or 0)
                                        
                                        net_speculative = nc_long - nc_short
                                        net_commercial = c_long - c_short
                                        
                                        # Soglie diverse per oro vs forex
                                        if currency == 'XAU':
                                            threshold = 50000
                                        else:
                                            threshold = 10000
                                        
                                        if net_speculative > threshold:
                                            bias = 'BULLISH'
                                        elif net_speculative < -threshold:
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
    def get_gold_specific_data() -> dict:
        """
        Dati specifici per l'analisi dell'oro
        """
        data = {
            'dxy_correlation': None,  # Correlazione inversa con USD Index
            'inflation_data': None,
            'treasury_yields': None
        }
        
        try:
            # DXY (US Dollar Index) - correlazione inversa con oro
            dxy = yf.Ticker("DX-Y.NYB")
            dxy_hist = dxy.history(period="5d")
            
            if not dxy_hist.empty:
                dxy_current = dxy_hist['Close'].iloc[-1]
                dxy_change = ((dxy_hist['Close'].iloc[-1] / dxy_hist['Close'].iloc[0]) - 1) * 100
                
                data['dxy'] = {
                    'current': round(dxy_current, 2),
                    'change_5d': round(dxy_change, 2),
                    'gold_impact': 'BULLISH' if dxy_change < 0 else 'BEARISH'  # Correlazione inversa
                }
            
            # Treasury Yields (10Y) - correlazione inversa con oro
            tny = yf.Ticker("^TNX")
            tny_hist = tny.history(period="5d")
            
            if not tny_hist.empty:
                yield_current = tny_hist['Close'].iloc[-1]
                yield_change = tny_hist['Close'].iloc[-1] - tny_hist['Close'].iloc[0]
                
                data['treasury_10y'] = {
                    'current': round(yield_current, 2),
                    'change_5d': round(yield_change, 2),
                    'gold_impact': 'BULLISH' if yield_change < 0 else 'BEARISH'
                }
                
        except Exception as e:
            print(f"Errore dati oro specifici: {e}")
        
        return data
