"""
Analisi Fondamentale
"""
import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta
import re

class FundamentalAnalyzer:
    """Classe per l'analisi fondamentale"""
    
    def __init__(self, pair: str):
        self.pair = pair
        self.base_currency = pair[:3]
        self.quote_currency = pair[3:6]
        self.events = []
        self.economic_data = {}
        
    def get_economic_calendar(self) -> list:
        """Recupera eventi economici rilevanti"""
        events = []
        
        # Simulated economic events (in produzione, usa API reali)
        high_impact_events = self._get_simulated_events()
        
        return high_impact_events
    
    def _get_simulated_events(self) -> list:
        """Genera eventi simulati per demo"""
        now = datetime.now()
        
        events = [
            {
                'date': now.strftime('%Y-%m-%d'),
                'time': '14:30',
                'currency': self.base_currency,
                'event': 'Interest Rate Decision',
                'impact': 'High',
                'forecast': '5.25%',
                'previous': '5.00%',
                'actual': None
            },
            {
                'date': now.strftime('%Y-%m-%d'),
                'time': '08:30',
                'currency': self.quote_currency,
                'event': 'Employment Change',
                'impact': 'High',
                'forecast': '180K',
                'previous': '175K',
                'actual': '185K'
            },
            {
                'date': (now + timedelta(days=1)).strftime('%Y-%m-%d'),
                'time': '10:00',
                'currency': self.base_currency,
                'event': 'CPI y/y',
                'impact': 'High',
                'forecast': '3.2%',
                'previous': '3.4%',
                'actual': None
            },
            {
                'date': (now + timedelta(days=2)).strftime('%Y-%m-%d'),
                'time': '15:00',
                'currency': self.quote_currency,
                'event': 'GDP q/q',
                'impact': 'Medium',
                'forecast': '2.1%',
                'previous': '1.9%',
                'actual': None
            }
        ]
        
        return events
    
    def get_interest_rates(self) -> dict:
        """Recupera tassi di interesse delle banche centrali"""
        # Tassi attuali (in produzione, recuperare da API)
        rates = {
            'USD': {'rate': 5.50, 'bank': 'Federal Reserve', 'trend': 'stable'},
            'EUR': {'rate': 4.50, 'bank': 'ECB', 'trend': 'stable'},
            'GBP': {'rate': 5.25, 'bank': 'Bank of England', 'trend': 'stable'},
            'JPY': {'rate': -0.10, 'bank': 'Bank of Japan', 'trend': 'rising'},
            'CHF': {'rate': 1.75, 'bank': 'SNB', 'trend': 'stable'},
            'AUD': {'rate': 4.35, 'bank': 'RBA', 'trend': 'stable'},
            'CAD': {'rate': 5.00, 'bank': 'Bank of Canada', 'trend': 'falling'},
            'NZD': {'rate': 5.50, 'bank': 'RBNZ', 'trend': 'stable'}
        }
        
        base_rate = rates.get(self.base_currency, {'rate': 0, 'trend': 'unknown'})
        quote_rate = rates.get(self.quote_currency, {'rate': 0, 'trend': 'unknown'})
        
        differential = base_rate['rate'] - quote_rate['rate']
        
        return {
            'base_currency': {
                'currency': self.base_currency,
                **base_rate
            },
            'quote_currency': {
                'currency': self.quote_currency,
                **quote_rate
            },
            'differential': differential,
            'carry_trade_direction': 'LONG' if differential > 0 else 'SHORT'
        }
    
    def analyze_economic_indicators(self) -> dict:
        """Analizza indicatori economici chiave"""
        # Simulazione dati economici
        indicators = {
            self.base_currency: {
                'gdp_growth': 2.1,
                'inflation': 3.2,
                'unemployment': 3.8,
                'pmi_manufacturing': 52.5,
                'pmi_services': 54.2,
                'consumer_confidence': 102.5,
                'trade_balance': -65.2
            },
            self.quote_currency: {
                'gdp_growth': 1.8,
                'inflation': 2.9,
                'unemployment': 4.1,
                'pmi_manufacturing': 49.8,
                'pmi_services': 51.3,
                'consumer_confidence': 98.7,
                'trade_balance': 42.1
            }
        }
        
        # Calcola score fondamentale
        base_score = self._calculate_economic_score(indicators[self.base_currency])
        quote_score = self._calculate_economic_score(indicators[self.quote_currency])
        
        return {
            'indicators': indicators,
            'base_score': base_score,
            'quote_score': quote_score,
            'fundamental_bias': 'BULLISH' if base_score > quote_score else 'BEARISH'
        }
    
    def _calculate_economic_score(self, data: dict) -> float:
        """Calcola score economico"""
        score = 0
        
        # GDP Growth (positive = good)
        if data['gdp_growth'] > 2:
            score += 1
        elif data['gdp_growth'] > 0:
            score += 0.5
        else:
            score -= 0.5
            
        # Inflation (2% target is optimal)
        if 1.5 <= data['inflation'] <= 2.5:
            score += 1
        elif data['inflation'] < 1:
            score -= 0.5
        elif data['inflation'] > 4:
            score -= 0.5
            
        # Unemployment (lower is better)
        if data['unemployment'] < 4:
            score += 1
        elif data['unemployment'] < 5:
            score += 0.5
        else:
            score -= 0.5
            
        # PMI (>50 = expansion)
        if data['pmi_manufacturing'] > 55:
            score += 1
        elif data['pmi_manufacturing'] > 50:
            score += 0.5
        else:
            score -= 0.5
            
        if data['pmi_services'] > 55:
            score += 0.5
        elif data['pmi_services'] > 50:
            score += 0.25
            
        return score
    
    def get_fundamental_score(self) -> dict:
        """Calcola punteggio fondamentale complessivo"""
        rates = self.get_interest_rates()
        economic = self.analyze_economic_indicators()
        calendar = self.get_economic_calendar()
        
        # Score basato su tassi di interesse
        rate_score = 0
        if rates['differential'] > 1:
            rate_score = 1
        elif rates['differential'] > 0:
            rate_score = 0.5
        elif rates['differential'] < -1:
            rate_score = -1
        else:
            rate_score = -0.5
            
        # Score economico
        econ_diff = economic['base_score'] - economic['quote_score']
        econ_score = econ_diff / 5  # Normalizza
        
        # Eventi ad alto impatto imminenti
        event_impact = 0
        high_impact_today = [e for e in calendar if e['impact'] == 'High' and e['date'] == datetime.now().strftime('%Y-%m-%d')]
        if high_impact_today:
            event_impact = 0.2  # Aumenta incertezza
        
        # Score finale
        final_score = (rate_score * 0.4 + econ_score * 0.6)
        
        probability_bull = ((final_score + 1) / 2) * 100
        
        return {
            'score': final_score,
            'probability_bull': probability_bull,
            'probability_bear': 100 - probability_bull,
            'direction': 'BULLISH' if final_score > 0.1 else ('BEARISH' if final_score < -0.1 else 'NEUTRAL'),
            'rate_analysis': rates,
            'economic_analysis': economic,
            'upcoming_events': calendar,
            'event_risk': 'HIGH' if high_impact_today else 'LOW',
            'breakdown': {
                'interest_rates': rate_score,
                'economic_indicators': econ_score,
                'event_risk_factor': event_impact
            }
        }
