"""
Analisi Fondamentale
"""

from datetime import datetime
from .data_providers import FreeDataProvider


class FundamentalAnalyzer:
    """Analizzatore fondamentale"""
    
    def __init__(self, pair: str):
        self.pair = pair.replace("=X", "").replace("/", "")
        self.base_currency = self.pair[:3]
        self.quote_currency = self.pair[3:6]
        
    def get_interest_rate_analysis(self) -> dict:
        """Analisi tassi di interesse"""
        rates = FreeDataProvider.get_central_bank_rates()
        
        base_data = rates.get(self.base_currency, {'rate': 0, 'bank': 'Unknown', 'trend': 'unknown'})
        quote_data = rates.get(self.quote_currency, {'rate': 0, 'bank': 'Unknown', 'trend': 'unknown'})
        
        differential = base_data['rate'] - quote_data['rate']
        
        # Trend analysis
        trend_score = 0
        if base_data.get('trend') == 'hiking' and quote_data.get('trend') != 'hiking':
            trend_score = 0.5
        elif base_data.get('trend') == 'cutting' and quote_data.get('trend') != 'cutting':
            trend_score = -0.5
        elif quote_data.get('trend') == 'hiking' and base_data.get('trend') != 'hiking':
            trend_score = -0.5
        elif quote_data.get('trend') == 'cutting' and base_data.get('trend') != 'cutting':
            trend_score = 0.5
        
        return {
            'base_currency': {
                'currency': self.base_currency,
                'rate': base_data['rate'],
                'bank': base_data['bank'],
                'trend': base_data.get('trend', 'unknown'),
                'next_meeting': base_data.get('next_meeting', 'N/A')
            },
            'quote_currency': {
                'currency': self.quote_currency,
                'rate': quote_data['rate'],
                'bank': quote_data['bank'],
                'trend': quote_data.get('trend', 'unknown'),
                'next_meeting': quote_data.get('next_meeting', 'N/A')
            },
            'differential': round(differential, 2),
            'trend_score': trend_score,
            'carry_trade': 'FAVORABLE' if differential > 1 else ('UNFAVORABLE' if differential < -1 else 'NEUTRAL')
        }
    
    def get_economic_calendar_analysis(self) -> dict:
        """Analisi calendario economico"""
        calendar = FreeDataProvider.get_economic_calendar()
        
        # Filtra per valute rilevanti
        relevant = [
            e for e in calendar
            if self.base_currency in e.get('currency', '').upper() or 
               self.quote_currency in e.get('currency', '').upper()
        ]
        
        # Conta impatti
        high_impact = [e for e in relevant if e.get('impact') == 'High']
        medium_impact = [e for e in relevant if e.get('impact') == 'Medium']
        
        # Risk assessment
        if len(high_impact) >= 3:
            event_risk = 'VERY HIGH'
            risk_score = -0.3
        elif len(high_impact) >= 1:
            event_risk = 'HIGH'
            risk_score = -0.15
        elif len(medium_impact) >= 2:
            event_risk = 'MODERATE'
            risk_score = -0.05
        else:
            event_risk = 'LOW'
            risk_score = 0
        
        return {
            'total_events': len(relevant),
            'high_impact_count': len(high_impact),
            'medium_impact_count': len(medium_impact),
            'event_risk': event_risk,
            'risk_score': risk_score,
            'upcoming_events': relevant[:10]
        }
    
    def get_fundamental_score(self) -> dict:
        """Calcola punteggio fondamentale"""
        rate_analysis = self.get_interest_rate_analysis()
        calendar_analysis = self.get_economic_calendar_analysis()
        
        # Score da differential tassi
        diff = rate_analysis['differential']
        
        if diff >= 3:
            rate_score = 0.8
        elif diff >= 2:
            rate_score = 0.6
        elif diff >= 1:
            rate_score = 0.4
        elif diff >= 0.5:
            rate_score = 0.2
        elif diff >= 0:
            rate_score = 0
        elif diff >= -0.5:
            rate_score = -0.2
        elif diff >= -1:
            rate_score = -0.4
        elif diff >= -2:
            rate_score = -0.6
        else:
            rate_score = -0.8
        
        # Aggiungi trend score
        rate_score += rate_analysis['trend_score'] * 0.3
        
        # Applica risk da eventi
        final_score = rate_score + calendar_analysis['risk_score']
        final_score = max(-1, min(1, final_score))
        
        # Probabilità
        probability_bull = ((final_score + 1) / 2) * 100
        
        # Direzione
        if final_score > 0.3:
            direction = 'BULLISH'
        elif final_score > 0.1:
            direction = 'SLIGHTLY BULLISH'
        elif final_score < -0.3:
            direction = 'BEARISH'
        elif final_score < -0.1:
            direction = 'SLIGHTLY BEARISH'
        else:
            direction = 'NEUTRAL'
        
        return {
            'score': round(final_score, 3),
            'probability_bull': round(probability_bull, 1),
            'probability_bear': round(100 - probability_bull, 1),
            'direction': direction,
            'rate_analysis': rate_analysis,
            'calendar_analysis': calendar_analysis,
            'data_source': 'Central Banks & Economic Calendar'
        }
