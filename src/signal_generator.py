"""
Generatore di Segnali Combinato
"""
from .technical_analysis import TechnicalAnalyzer
from .fundamental_analysis import FundamentalAnalyzer
from .sentiment_analysis import SentimentAnalyzer
from config.settings import SIGNAL_WEIGHTS
import pandas as pd
from datetime import datetime

class SignalGenerator:
    """Classe per generare segnali di trading combinati"""
    
    def __init__(self, df: pd.DataFrame, pair: str):
        self.df = df
        self.pair = pair
        self.technical = TechnicalAnalyzer(df)
        self.fundamental = FundamentalAnalyzer(pair.replace("=X", ""))
        self.sentiment = SentimentAnalyzer(pair)
        
    def generate_complete_analysis(self) -> dict:
        """Genera analisi completa"""
        # Calcola tutti gli indicatori
        self.technical.calculate_all_indicators()
        
        # Ottieni scores
        tech_score = self.technical.get_technical_score()
        fund_score = self.fundamental.get_fundamental_score()
        sent_score = self.sentiment.get_sentiment_score()
        
        # Combina scores
        combined = self._combine_scores(tech_score, fund_score, sent_score)
        
        # Entry points
        entry_points = self.technical.get_entry_points()
        
        # Aggiungi livelli chiave
        key_levels = self._get_all_key_levels()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'pair': self.pair,
            'current_price': self.df['Close'].iloc[-1],
            'combined_signal': combined,
            'technical_analysis': {
                'score': tech_score,
                'indicators': self.technical.indicators
            },
            'fundamental_analysis': fund_score,
            'sentiment_analysis': sent_score,
            'entry_points': entry_points,
            'key_levels': key_levels,
            'recommendation': self._generate_recommendation(combined, entry_points)
        }
    
    def _combine_scores(self, tech: dict, fund: dict, sent: dict) -> dict:
        """Combina i punteggi delle tre analisi"""
        weights = SIGNAL_WEIGHTS
        
        # Punteggi normalizzati [-1, 1]
        tech_normalized = tech['score']
        fund_normalized = fund['score']
        sent_normalized = sent['score']
        
        # Score combinato
        combined_score = (
            tech_normalized * weights['technical'] +
            fund_normalized * weights['fundamental'] +
            sent_normalized * weights['sentiment']
        )
        
        # Probabilità
        probability_bull = ((combined_score + 1) / 2) * 100
        
        # Confidence basata sulla concordanza
        directions = [tech['direction'], fund['direction'], sent['direction']]
        agreement = directions.count(directions[0]) / 3
        
        if all(d == directions[0] for d in directions):
            confidence = "ALTA"
            confidence_score = 0.9
        elif directions.count('NEUTRAL') >= 2:
            confidence = "BASSA"
            confidence_score = 0.4
        else:
            confidence = "MEDIA"
            confidence_score = 0.6
        
        # Direzione finale
        if combined_score > 0.15:
            direction = "STRONG BUY"
        elif combined_score > 0.05:
            direction = "BUY"
        elif combined_score < -0.15:
            direction = "STRONG SELL"
        elif combined_score < -0.05:
            direction = "SELL"
        else:
            direction = "NEUTRAL"
        
        return {
            'combined_score': combined_score,
            'probability_bull': probability_bull,
            'probability_bear': 100 - probability_bull,
            'direction': direction,
            'confidence': confidence,
            'confidence_score': confidence_score,
            'agreement': {
                'technical': tech['direction'],
                'fundamental': fund['direction'],
                'sentiment': sent['direction'],
                'aligned': all(d == directions[0] for d in directions if d != 'NEUTRAL')
            },
            'weights_used': weights,
            'individual_scores': {
                'technical': tech_normalized,
                'fundamental': fund_normalized,
                'sentiment': sent_normalized
            }
        }
    
    def _get_all_key_levels(self) -> dict:
        """Raccoglie tutti i livelli chiave"""
        return {
            'support_resistance': self.technical.levels.get('support_resistance', {}),
            'fibonacci': self.technical.levels.get('fibonacci', {}),
            'pivot_points': self.technical.levels.get('pivot_points', {}),
            'moving_averages': {
                'EMA_50': self.technical.indicators['moving_averages']['EMA_50'],
                'EMA_200': self.technical.indicators['moving_averages']['EMA_200'],
                'SMA_200': self.technical.indicators['moving_averages']['SMA_200']
            }
        }
    
    def _generate_recommendation(self, combined: dict, entry: dict) -> dict:
        """Genera raccomandazione finale"""
        direction = combined['direction']
        confidence = combined['confidence']
        prob_bull = combined['probability_bull']
        
        # Action
        if direction in ['STRONG BUY', 'BUY']:
            action = "LONG"
            action_color = "green"
        elif direction in ['STRONG SELL', 'SELL']:
            action = "SHORT"
            action_color = "red"
        else:
            action = "WAIT"
            action_color = "gray"
        
        # Risk level
        if confidence == "ALTA" and abs(combined['combined_score']) > 0.3:
            risk_level = "Basso"
            position_size = "1-2% del capitale"
        elif confidence == "MEDIA":
            risk_level = "Medio"
            position_size = "0.5-1% del capitale"
        else:
            risk_level = "Alto"
            position_size = "0.25-0.5% del capitale"
        
        return {
            'action': action,
            'action_color': action_color,
            'confidence': confidence,
            'probability': prob_bull if action == "LONG" else (100 - prob_bull if action == "SHORT" else 50),
            'risk_level': risk_level,
            'suggested_position_size': position_size,
            'entry': entry['entry_price'],
            'stop_loss': entry['stop_loss'],
            'take_profit_1': entry['take_profit_1'],
            'take_profit_2': entry['take_profit_2'],
            'take_profit_3': entry['take_profit_3'],
            'risk_reward': entry['risk_reward_1'],
            'notes': self._generate_notes(combined, entry)
        }
    
    def _generate_notes(self, combined: dict, entry: dict) -> list:
        """Genera note operative"""
        notes = []
        
        # Allineamento analisi
        if combined['agreement']['aligned']:
            notes.append("✅ Tutte le analisi concordano - Segnale forte")
        else:
            notes.append("⚠️ Analisi discordanti - Procedere con cautela")
        
        # Technical
        tech_dir = combined['agreement']['technical']
        if tech_dir != 'NEUTRAL':
            notes.append(f"📊 Tecnica: {tech_dir}")
        
        # Fundamental
        fund_dir = combined['agreement']['fundamental']
        if fund_dir != 'NEUTRAL':
            notes.append(f"📈 Fondamentale: {fund_dir}")
        
        # Sentiment
        sent_dir = combined['agreement']['sentiment']
        if sent_dir != 'NEUTRAL':
            notes.append(f"💭 Sentiment: {sent_dir}")
        
        # Risk/Reward
        if entry['risk_reward_1'] >= 2:
            notes.append(f"✅ Risk/Reward favorevole: {entry['risk_reward_1']:.2f}")
        else:
            notes.append(f"⚠️ Risk/Reward limitato: {entry['risk_reward_1']:.2f}")
        
        return notes
