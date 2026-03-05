"""
Analisi Fondamentale con Dati Reali
"""
from datetime import datetime
from .data_providers import (
    ForexDataProvider, 
    EconomicCalendarProvider
)

class FundamentalAnalyzer:
    """Classe per l'analisi fondamentale con dati reali"""
    
    def __init__(self, pair: str):
        self.pair = pair.replace("=X", "")
        self.base_currency = self.pair[:3]
        self.quote_currency = self.pair[3:6]
        self._rates_cache = None
        self._calendar_cache = None
        
    def get_interest_rates(self) -> dict:
        """Recupera tassi di interesse reali"""
        if not self._rates_cache:
            self._rates_cache = ForexDataProvider.get_central_bank_rates()
        
        rates = self._rates_cache
        
        base_rate = rates.get(self.base_currency, {'rate': 0, 'bank': 'Unknown'})
        quote_rate = rates.get(self.quote_currency, {'rate': 0, 'bank': 'Unknown'})
        
        differential = base_rate['rate'] - quote_rate['rate']
        
        return {
            'base_currency': {
                'currency': self.base_currency,
                'rate': base_rate['rate'],
                'bank': base_rate['bank']
            },
            'quote_currency': {
                'currency': self.quote_currency,
                'rate': quote_rate['rate'],
                'bank': quote_rate['bank']
            },
            'differential': differential,
            'carry_trade_direction': 'LONG' if differential > 0 else 'SHORT',
            'source': 'Central Banks Official Rates',
            'note': 'Aggiornato quotidianamente'
        }
    
    def get_economic_calendar(self) -> list:
        """Recupera calendario economico reale"""
        if not self._calendar_cache:
            # Prova prima Investing, poi Forex Factory
            self._calendar_cache = EconomicCalendarProvider.get_calendar_from_investing()
            
            if not self._calendar_cache:
                self._calendar_cache = EconomicCalendarProvider.get_calendar_from_forexfactory()
        
        # Filtra per valute rilevanti
        relevant_currencies = [self.base_currency, self.quote_currency]
        
        filtered = [
            e for e in self._calendar_cache 
            if any(c in e.get('currency', '').upper() for c in relevant_currencies)
        ]
        
        return filtered if filtered else self._calendar_cache[:5]
    
    def get_fundamental_score(self) -> dict:
        """Calcola punteggio fondamentale con dati reali"""
        rates = self.get_interest_rates()
        calendar = self.get_economic_calendar()
        
        # Score basato su tassi di interesse
        rate_score = 0
        diff = rates['differential']
        
        if diff > 2:
            rate_score = 1
        elif diff > 1:
            rate_score = 0.7
        elif diff > 0:
            rate_score = 0.3
        elif diff > -1:
            rate_score = -0.3
        elif diff > -2:
            rate_score = -0.7
        else:
            rate_score = -1
        
        # Eventi ad alto impatto
        high_impact = [e for e in calendar if e.get('impact') == 'High']
        event_risk = 'HIGH' if len(high_impact) > 0 else 'LOW'
        
        # Aumenta incertezza se ci sono eventi importanti
        uncertainty_factor = 0.2 if high_impact else 0
        
        final_score = rate_score * (1 - uncertainty_factor)
        probability_bull = ((final_score + 1) / 2) * 100
        
        return {
            'score': final_score,
            'probability_bull': probability_bull,
            'probability_bear': 100 - probability_bull,
            'direction': 'BULLISH' if final_score > 0.1 else ('BEARISH' if final_score < -0.1 else 'NEUTRAL'),
            'rate_analysis': rates,
            'upcoming_events': calendar[:10],
            'high_impact_events_today': len(high_impact),
            'event_risk': event_risk,
            'data_source': 'Real-time from Central Banks & Economic Calendars'
        }
