"""
Generatore Segnali con supporto Telegram e Lot Calculation
"""

from .technical_analysis import TechnicalAnalyzer
from .fundamental_analysis import FundamentalAnalyzer
from .sentiment_analysis import SentimentAnalyzer
from .lot_calculator import LotCalculator
from datetime import datetime


class SignalGenerator:
    """Genera segnali di trading combinati"""
    
    def __init__(self, df, pair: str, weights: dict = None, 
                 account_balance: float = 10000, risk_percent: float = 1.0):
        self.df = df
        self.pair = pair
        self.is_gold = "XAU" in pair.upper() or "GC=F" in pair.upper() or "GOLD" in pair.upper()
        
        self.weights = weights or {
            'technical': 0.45,
            'fundamental': 0.30,
            'sentiment': 0.25
        }
        
        self.technical = TechnicalAnalyzer(df)
        self.fundamental = FundamentalAnalyzer(pair)
        self.sentiment = SentimentAnalyzer(pair)
        self.lot_calculator = LotCalculator(account_balance, risk_percent)
    
    def generate_signal(self) -> dict:
        """Genera segnale completo"""
        
        # Calcola tutti gli indicatori tecnici
        self.technical.calculate_all_indicators()
        
        # Ottieni scores
        tech_score = self.technical.get_technical_score()
        fund_score = self.fundamental.get_fundamental_score()
        sent_score = self.sentiment.get_sentiment_score()
        
        # Entry points
        entry_points = self.technical.get_entry_points()
        
        # Calcola lotti
        lot_calculation = self.lot_calculator.calculate_lots(
            pair=self.pair,
            entry=entry_points['entry_price'],
            stop_loss=entry_points['stop_loss'],
            current_price=self.df['Close'].iloc[-1]
        )
        
        # Combina scores
        combined = self._combine_scores(tech_score, fund_score, sent_score)
        
        # Genera raccomandazione
        recommendation = self._generate_recommendation(combined, entry_points, lot_calculation)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'pair': self.pair,
            'pair_display': self._get_display_name(),
            'is_gold': self.is_gold,
            'current_price': self.df['Close'].iloc[-1],
            'combined_signal': combined,
            'technical': tech_score,
            'fundamental': fund_score,
            'sentiment': sent_score,
            'entry_points': entry_points,
            'lot_calculation': lot_calculation,
            'recommendation': recommendation,
            'levels': {
                'support_resistance': self.technical.levels.get('support_resistance', {}),
                'fibonacci': self.technical.levels.get('fibonacci', {}),
                'pivot_points': self.technical.levels.get('pivot_points', {})
            },
            '_analyzer': self.technical  # Per accesso al df con indicatori
        }
    
    def _get_display_name(self) -> str:
        """Ottieni nome display della coppia"""
        if self.is_gold:
            return "XAU/USD (Gold)"
        return self.pair.replace("=X", "").replace("/", "")[:3] + "/" + self.pair.replace("=X", "").replace("/", "")[3:6]
    
    def _combine_scores(self, tech: dict, fund: dict, sent: dict) -> dict:
        """Combina i punteggi"""
        
        combined_score = (
            tech['score'] * self.weights['technical'] +
            fund['score'] * self.weights['fundamental'] +
            sent['score'] * self.weights['sentiment']
        )
        
        prob_bull = ((combined_score + 1) / 2) * 100
        prob_bull = max(0, min(100, prob_bull))
        
        if combined_score > 0.35:
            direction = 'STRONG BUY'
        elif combined_score > 0.15:
            direction = 'BUY'
        elif combined_score > 0.05:
            direction = 'WEAK BUY'
        elif combined_score < -0.35:
            direction = 'STRONG SELL'
        elif combined_score < -0.15:
            direction = 'SELL'
        elif combined_score < -0.05:
            direction = 'WEAK SELL'
        else:
            direction = 'NEUTRAL'
        
        directions = [
            tech['direction'],
            fund['direction'],
            sent['direction']
        ]
        
        bullish_count = sum(1 for d in directions if 'BULLISH' in d or 'BUY' in d)
        bearish_count = sum(1 for d in directions if 'BEARISH' in d or 'SELL' in d)
        
        if bullish_count == 3:
            agreement = 'FULL BULLISH'
            confidence = 'HIGH'
        elif bearish_count == 3:
            agreement = 'FULL BEARISH'
            confidence = 'HIGH'
        elif bullish_count >= 2:
            agreement = 'MAJORITY BULLISH'
            confidence = 'MEDIUM'
        elif bearish_count >= 2:
            agreement = 'MAJORITY BEARISH'
            confidence = 'MEDIUM'
        else:
            agreement = 'MIXED'
            confidence = 'LOW'
        
        return {
            'score': round(combined_score, 3),
            'probability_bull': round(prob_bull, 1),
            'probability_bear': round(100 - prob_bull, 1),
            'direction': direction,
            'confidence': confidence,
            'agreement': agreement,
            'individual_directions': {
                'technical': tech['direction'],
                'fundamental': fund['direction'],
                'sentiment': sent['direction']
            },
            'individual_scores': {
                'technical': tech['score'],
                'fundamental': fund['score'],
                'sentiment': sent['score']
            },
            'weights': self.weights
        }
    
    def _generate_recommendation(self, combined: dict, entry: dict, lots: dict) -> dict:
        """Genera raccomandazione finale"""
        
        direction = combined['direction']
        confidence = combined['confidence']
        
        if direction in ['STRONG BUY', 'BUY']:
            action = 'LONG'
            color = 'green'
        elif direction in ['STRONG SELL', 'SELL']:
            action = 'SHORT'
            color = 'red'
        elif direction == 'WEAK BUY':
            action = 'CONSIDER LONG'
            color = 'lightgreen'
        elif direction == 'WEAK SELL':
            action = 'CONSIDER SHORT'
            color = 'orange'
        else:
            action = 'WAIT'
            color = 'gray'
        
        if confidence == 'HIGH':
            position_size = '1.5-2% del capitale'
            risk_level = 'ACCEPTABLE'
        elif confidence == 'MEDIUM':
            position_size = '0.75-1% del capitale'
            risk_level = 'MODERATE'
        else:
            position_size = '0.25-0.5% del capitale'
            risk_level = 'HIGH'
        
        notes = []
        
        if combined['agreement'] in ['FULL BULLISH', 'FULL BEARISH']:
            notes.append("✅ Tutte le analisi concordano - Segnale forte")
        elif 'MAJORITY' in combined['agreement']:
            notes.append("⚠️ Maggioranza concorde - Segnale moderato")
        else:
            notes.append("❌ Analisi discordanti - Attendere conferme")
        
        if entry['risk_reward_1'] >= 2:
            notes.append(f"✅ Risk/Reward ottimo: {entry['risk_reward_1']:.2f}")
        elif entry['risk_reward_1'] >= 1.5:
            notes.append(f"⚠️ Risk/Reward accettabile: {entry['risk_reward_1']:.2f}")
        else:
            notes.append(f"❌ Risk/Reward scarso: {entry['risk_reward_1']:.2f}")
        
        notes.append(f"📊 Tecnica: {combined['individual_directions']['technical']}")
        notes.append(f"💰 Fondamentale: {combined['individual_directions']['fundamental']}")
        notes.append(f"💭 Sentiment: {combined['individual_directions']['sentiment']}")
        notes.append(f"📏 Lotti suggeriti: {lots['lots']}")
        
        # Determina se inviare segnale (solo per segnali forti)
        should_notify = action in ['LONG', 'SHORT'] and confidence in ['HIGH', 'MEDIUM']
        
        return {
            'action': action,
            'color': color,
            'direction': direction,
            'confidence': confidence,
            'probability': combined['probability_bull'] if 'BUY' in direction or 'LONG' in action else combined['probability_bear'],
            'position_size': position_size,
            'risk_level': risk_level,
            'entry': entry['entry_price'],
            'stop_loss': entry['stop_loss'],
            'take_profit_1': entry['take_profit_1'],
            'take_profit_2': entry['take_profit_2'],
            'take_profit_3': entry['take_profit_3'],
            'risk_reward': entry['risk_reward_1'],
            'lots': lots['lots'],
            'notes': notes,
            'should_notify': should_notify
        }
