"""
Analisi Fondamentale - Include supporto XAU/USD
"""

from datetime import datetime
from .data_providers import FreeDataProvider


class FundamentalAnalyzer:
    """Analizzatore fondamentale con supporto oro"""
    
    def __init__(self, pair: str):
        self.pair = pair.replace("=X", "").replace("/", "").replace("GC=F", "XAUUSD")
        self.is_gold = "XAU" in self.pair.upper() or "GOLD" in self.pair.upper()
        
        if self.is_gold:
            self.base_currency = "XAU"
            self.quote_currency = "USD"
        else:
            self.base_currency = self.pair[:3]
            self.quote_currency = self.pair[3:6]
    
    def get_interest_rate_analysis(self) -> dict:
        """Analisi tassi di interesse"""
        rates = FreeDataProvider.get_central_bank_rates()
        
        if self.is_gold:
            # Per l'oro, analizza solo USD e l'impatto dei tassi
            usd_data = rates.get('USD', {'rate': 0, 'bank': 'Unknown', 'trend': 'unknown'})
            
            # Tassi alti = bearish per oro, tassi bassi = bullish
            rate_impact = 'BEARISH' if usd_data['rate'] > 4 else ('BULLISH' if usd_data['rate'] < 2 else 'NEUTRAL')
            trend_impact = 'BEARISH' if usd_data.get('trend') == 'hiking' else ('BULLISH' if usd_data.get('trend') == 'cutting' else 'NEUTRAL')
            
            return {
                'is_gold': True,
                'usd_rate': {
                    'rate': usd_data['rate'],
                    'bank': usd_data['bank'],
                    'trend': usd_data.get('trend', 'unknown'),
                    'next_meeting': usd_data.get('next_meeting', 'N/A')
                },
                'rate_impact_on_gold': rate_impact,
                'trend_impact_on_gold': trend_impact,
                'analysis': 'Higher interest rates typically negative for gold as it increases opportunity cost of holding non-yielding assets'
            }
        else:
            # Analisi standard forex
            base_data = rates.get(self.base_currency, {'rate': 0, 'bank': 'Unknown', 'trend': 'unknown'})
            quote_data = rates.get(self.quote_currency, {'rate': 0, 'bank': 'Unknown', 'trend': 'unknown'})
            
            differential = base_data['rate'] - quote_data['rate']
            
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
                'is_gold': False,
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
    
    def get_gold_factors(self) -> dict:
        """Fattori specifici per l'oro"""
        if not self.is_gold:
            return None
        
        gold_data = FreeDataProvider.get_gold_specific_data()
        
        factors = {
            'dxy': gold_data.get('dxy'),
            'treasury_10y': gold_data.get('treasury_10y'),
            'overall_impact': 'NEUTRAL'
        }
        
        # Calcola impatto complessivo
        bullish_factors = 0
        bearish_factors = 0
        
        if factors['dxy'] and factors['dxy'].get('gold_impact') == 'BULLISH':
            bullish_factors += 1
        elif factors['dxy'] and factors['dxy'].get('gold_impact') == 'BEARISH':
            bearish_factors += 1
        
        if factors['treasury_10y'] and factors['treasury_10y'].get('gold_impact') == 'BULLISH':
            bullish_factors += 1
        elif factors['treasury_10y'] and factors['treasury_10y'].get('gold_impact') == 'BEARISH':
            bearish_factors += 1
        
        if bullish_factors > bearish_factors:
            factors['overall_impact'] = 'BULLISH'
        elif bearish_factors > bullish_factors:
            factors['overall_impact'] = 'BEARISH'
        
        return factors
    
    def get_economic_calendar_analysis(self) -> dict:
        """Analisi calendario economico"""
        calendar = FreeDataProvider.get_economic_calendar()
        
        if self.is_gold:
            # Per l'oro, filtra eventi rilevanti (USD e inflazione)
            relevant = [
                e for e in calendar
                if ('USD' in e.get('currency', '').upper() or 
                    e.get('gold_relevant', False))
            ]
        else:
            relevant = [
                e for e in calendar
                if self.base_currency in e.get('currency', '').upper() or 
                   self.quote_currency in e.get('currency', '').upper()
            ]
        
        high_impact = [e for e in relevant if e.get('impact') == 'High']
        medium_impact = [e for e in relevant if e.get('impact') == 'Medium']
        
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
        gold_factors = self.get_gold_factors() if self.is_gold else None
        
        if self.is_gold:
            # Logica specifica per l'oro
            rate_score = 0
            
            # Impatto tassi USD
            if rate_analysis['rate_impact_on_gold'] == 'BULLISH':
                rate_score += 0.3
            elif rate_analysis['rate_impact_on_gold'] == 'BEARISH':
                rate_score -= 0.3
            
            # Impatto trend tassi
            if rate_analysis['trend_impact_on_gold'] == 'BULLISH':
                rate_score += 0.3
            elif rate_analysis['trend_impact_on_gold'] == 'BEARISH':
                rate_score -= 0.3
            
            # Fattori oro specifici
            if gold_factors:
                if gold_factors['overall_impact'] == 'BULLISH':
                    rate_score += 0.4
                elif gold_factors['overall_impact'] == 'BEARISH':
                    rate_score -= 0.4
            
        else:
            # Logica forex standard
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
            
            rate_score += rate_analysis.get('trend_score', 0) * 0.3
        
        # Applica risk da eventi
        final_score = rate_score + calendar_analysis['risk_score']
        final_score = max(-1, min(1, final_score))
        
        probability_bull = ((final_score + 1) / 2) * 100
        
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
            'gold_factors': gold_factors,
            'is_gold': self.is_gold,
            'data_source': 'Central Banks & Economic Calendar'
        }
