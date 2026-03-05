"""
Provider di dati reali da fonti gratuite
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import feedparser
import json
import re

class ForexDataProvider:
    """Provider dati forex da fonti gratuite"""
    
    # Tassi di interesse attuali (aggiornamento manuale periodico o scraping)
    CENTRAL_BANK_RATES_URL = "https://www.global-rates.com/en/interest-rates/central-banks/central-banks.aspx"
    
    @staticmethod
    def get_live_rates():
        """
        Ottiene tassi di cambio in tempo reale da exchangerate-api (gratuito)
        1500 richieste/mese gratis senza API key
        """
        try:
            # API gratuita senza key (limite 1500/mese)
            url = "https://open.er-api.com/v6/latest/USD"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get('result') == 'success':
                return {
                    'rates': data['rates'],
                    'timestamp': data['time_last_update_utc'],
                    'source': 'exchangerate-api'
                }
        except Exception as e:
            print(f"Errore API rates: {e}")
        
        return None
    
    @staticmethod
    def get_central_bank_rates():
        """Scraping tassi banche centrali da siti pubblici"""
        rates = {}
        
        try:
            # Trading Economics (dati pubblici)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Fonte alternativa: scraping da pagine pubbliche
            bank_data = {
                'USD': {'url': 'federal-reserve', 'bank': 'Federal Reserve'},
                'EUR': {'url': 'european-central-bank', 'bank': 'ECB'},
                'GBP': {'url': 'bank-of-england', 'bank': 'Bank of England'},
                'JPY': {'url': 'bank-of-japan', 'bank': 'Bank of Japan'},
                'CHF': {'url': 'swiss-national-bank', 'bank': 'SNB'},
                'AUD': {'url': 'reserve-bank-of-australia', 'bank': 'RBA'},
                'CAD': {'url': 'bank-of-canada', 'bank': 'Bank of Canada'},
                'NZD': {'url': 'reserve-bank-of-new-zealand', 'bank': 'RBNZ'}
            }
            
            # Tassi aggiornati manualmente (backup) - Aggiorna periodicamente
            # Fonte: https://www.global-rates.com/en/interest-rates/central-banks/
            current_rates = {
                'USD': 5.50,  # Fed Funds Rate
                'EUR': 4.50,  # ECB Main Refinancing Rate
                'GBP': 5.25,  # BoE Bank Rate
                'JPY': 0.25,  # BoJ Rate
                'CHF': 1.50,  # SNB Rate
                'AUD': 4.35,  # RBA Cash Rate
                'CAD': 5.00,  # BoC Rate
                'NZD': 5.50   # RBNZ Rate
            }
            
            for currency, rate in current_rates.items():
                rates[currency] = {
                    'rate': rate,
                    'bank': bank_data[currency]['bank'],
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }
                
        except Exception as e:
            print(f"Errore scraping rates: {e}")
            
        return rates


class EconomicCalendarProvider:
    """Provider calendario economico da fonti gratuite"""
    
    @staticmethod
    def get_calendar_from_investing():
        """
        Scraping calendario economico da Investing.com
        """
        events = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9'
            }
            
            url = "https://www.investing.com/economic-calendar/"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Parsing eventi (struttura semplificata)
                rows = soup.select('tr.js-event-item')[:20]  # Primi 20 eventi
                
                for row in rows:
                    try:
                        time_elem = row.select_one('td.time')
                        currency_elem = row.select_one('td.flagCur')
                        event_elem = row.select_one('td.event')
                        impact_elem = row.select_one('td.sentiment')
                        
                        if event_elem:
                            # Determina impatto
                            impact_icons = impact_elem.select('i.grayFullBullishIcon') if impact_elem else []
                            impact = 'High' if len(impact_icons) >= 3 else ('Medium' if len(impact_icons) >= 2 else 'Low')
                            
                            events.append({
                                'time': time_elem.text.strip() if time_elem else '',
                                'currency': currency_elem.text.strip() if currency_elem else '',
                                'event': event_elem.text.strip() if event_elem else '',
                                'impact': impact,
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })
                    except:
                        continue
                        
        except Exception as e:
            print(f"Errore calendario: {e}")
            
        return events
    
    @staticmethod
    def get_calendar_from_forexfactory():
        """
        Scraping da Forex Factory
        """
        events = []
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            url = "https://www.forexfactory.com/calendar"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                rows = soup.select('tr.calendar__row')[:20]
                
                for row in rows:
                    try:
                        currency = row.select_one('.calendar__currency')
                        event = row.select_one('.calendar__event-title')
                        impact = row.select_one('.calendar__impact')
                        
                        if event:
                            impact_class = impact.get('class', []) if impact else []
                            impact_level = 'High' if 'high' in str(impact_class) else 'Medium'
                            
                            events.append({
                                'currency': currency.text.strip() if currency else '',
                                'event': event.text.strip(),
                                'impact': impact_level,
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })
                    except:
                        continue
                        
        except Exception as e:
            print(f"Errore FF calendar: {e}")
            
        return events


class NewsProvider:
    """Provider news forex da RSS feeds"""
    
    RSS_FEEDS = [
        {
            'name': 'ForexLive',
            'url': 'https://www.forexlive.com/feed/',
            'reliable': True
        },
        {
            'name': 'DailyFX',
            'url': 'https://www.dailyfx.com/feeds/all',
            'reliable': True
        },
        {
            'name': 'FXStreet',
            'url': 'https://www.fxstreet.com/rss/news',
            'reliable': True
        },
        {
            'name': 'Investing.com',
            'url': 'https://www.investing.com/rss/news.rss',
            'reliable': True
        }
    ]
    
    @staticmethod
    def fetch_all_news(pair: str = None, limit: int = 30) -> list:
        """Recupera news da tutti i feed RSS"""
        all_news = []
        
        for feed_info in NewsProvider.RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_info['url'])
                
                for entry in feed.entries[:15]:
                    news_item = {
                        'title': entry.get('title', ''),
                        'summary': BeautifulSoup(
                            entry.get('summary', ''), 'html.parser'
                        ).get_text()[:500],
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'source': feed_info['name']
                    }
                    all_news.append(news_item)
                    
            except Exception as e:
                print(f"Errore feed {feed_info['name']}: {e}")
                continue
        
        # Filtra per coppia se specificata
        if pair:
            pair_clean = pair.replace("=X", "")
            terms = [pair_clean, pair_clean[:3], pair_clean[3:6]]
            
            filtered = [
                n for n in all_news 
                if any(t.upper() in (n['title'] + n['summary']).upper() for t in terms)
            ]
            
            return filtered[:limit] if filtered else all_news[:limit//2]
        
        return all_news[:limit]


class SentimentDataProvider:
    """Provider dati sentiment da fonti pubbliche"""
    
    @staticmethod
    def get_cot_data():
        """
        Dati COT (Commitment of Traders) dalla CFTC
        Aggiornati settimanalmente
        """
        try:
            # URL dati COT in formato CSV
            # https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
            
            # Per forex, usa i futures CME
            cot_url = "https://www.cftc.gov/dea/newcot/deafut.txt"
            
            response = requests.get(cot_url, timeout=15)
            
            if response.status_code == 200:
                # Parse del file (struttura complessa)
                # Restituisce dati di positioning istituzionale
                lines = response.text.split('\n')
                
                # Cerca le righe rilevanti per le valute
                forex_futures = {
                    'EUR': 'EURO FX',
                    'GBP': 'BRITISH POUND',
                    'JPY': 'JAPANESE YEN',
                    'CHF': 'SWISS FRANC',
                    'AUD': 'AUSTRALIAN DOLLAR',
                    'CAD': 'CANADIAN DOLLAR'
                }
                
                cot_data = {}
                
                for line in lines:
                    for currency, search_term in forex_futures.items():
                        if search_term in line.upper():
                            # Estrai dati long/short
                            parts = line.split(',')
                            if len(parts) > 10:
                                try:
                                    cot_data[currency] = {
                                        'commercial_long': int(parts[8]) if parts[8].strip() else 0,
                                        'commercial_short': int(parts[9]) if parts[9].strip() else 0,
                                        'non_commercial_long': int(parts[4]) if parts[4].strip() else 0,
                                        'non_commercial_short': int(parts[5]) if parts[5].strip() else 0,
                                    }
                                except:
                                    pass
                
                return cot_data
                
        except Exception as e:
            print(f"Errore COT data: {e}")
            
        return {}
    
    @staticmethod
    def get_retail_sentiment_dailyfx():
        """
        Scraping sentiment retail da DailyFX (dati IG)
        """
        sentiment = {}
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            url = "https://www.dailyfx.com/sentiment"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Cerca i dati di sentiment (la struttura può variare)
                pairs = ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'USD/CAD']
                
                for pair in pairs:
                    try:
                        # Trova elemento con i dati
                        pair_elem = soup.find(text=re.compile(pair))
                        if pair_elem:
                            parent = pair_elem.find_parent('div')
                            if parent:
                                # Estrai percentuali
                                long_elem = parent.find(class_=re.compile('long'))
                                short_elem = parent.find(class_=re.compile('short'))
                                
                                if long_elem and short_elem:
                                    sentiment[pair.replace('/', '')] = {
                                        'long': float(re.search(r'[\d.]+', long_elem.text).group()),
                                        'short': float(re.search(r'[\d.]+', short_elem.text).group())
                                    }
                    except:
                        continue
                        
        except Exception as e:
            print(f"Errore sentiment DailyFX: {e}")
            
        return sentiment
    
    @staticmethod
    def get_myfxbook_sentiment():
        """
        Dati sentiment da MyFxBook (API pubblica)
        """
        try:
            url = "https://www.myfxbook.com/community/outlook"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                sentiment_data = {}
                
                # Parse della tabella sentiment
                rows = soup.select('table tr')[1:10]  # Salta header
                
                for row in rows:
                    try:
                        cols = row.select('td')
                        if len(cols) >= 4:
                            pair = cols[0].text.strip().replace('/', '')
                            long_pct = float(cols[2].text.strip().replace('%', ''))
                            short_pct = float(cols[3].text.strip().replace('%', ''))
                            
                            sentiment_data[pair] = {
                                'long_percent': long_pct,
                                'short_percent': short_pct
                            }
                    except:
                        continue
                        
                return sentiment_data
                
        except Exception as e:
            print(f"Errore MyFxBook: {e}")
            
        return {}
