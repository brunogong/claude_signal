"""
Analisi Tecnica Completa
"""
import pandas as pd
import numpy as np
from ta.trend import MACD, EMAIndicator, SMAIndicator, ADXIndicator, IchimokuIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from ta.volume import OnBalanceVolumeIndicator, VolumeWeightedAveragePrice
from config.settings import TECHNICAL_PARAMS
from scipy import stats

class TechnicalAnalyzer:
    """Classe per l'analisi tecnica avanzata"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.params = TECHNICAL_PARAMS
        self.indicators = {}
        self.signals = {}
        self.levels = {}
        
    def calculate_all_indicators(self):
        """Calcola tutti gli indicatori tecnici"""
        self._calculate_moving_averages()
        self._calculate_momentum_indicators()
        self._calculate_volatility_indicators()
        self._calculate_trend_indicators()
        self._calculate_support_resistance()
        self._calculate_fibonacci_levels()
        self._calculate_pivot_points()
        
        return self.indicators
    
    def _calculate_moving_averages(self):
        """Calcola medie mobili"""
        close = self.df['Close']
        
        # EMA
        self.df['EMA_9'] = EMAIndicator(close, window=9).ema_indicator()
        self.df['EMA_21'] = EMAIndicator(close, window=21).ema_indicator()
        self.df['EMA_50'] = EMAIndicator(close, window=50).ema_indicator()
        self.df['EMA_200'] = EMAIndicator(close, window=200).ema_indicator()
        
        # SMA
        self.df['SMA_20'] = SMAIndicator(close, window=20).sma_indicator()
        self.df['SMA_50'] = SMAIndicator(close, window=50).sma_indicator()
        self.df['SMA_200'] = SMAIndicator(close, window=200).sma_indicator()
        
        # Segnali EMA
        current = self.df.iloc[-1]
        
        ema_signal = 0
        if current['EMA_9'] > current['EMA_21'] > current['EMA_50']:
            ema_signal = 1  # Bullish
        elif current['EMA_9'] < current['EMA_21'] < current['EMA_50']:
            ema_signal = -1  # Bearish
            
        # Golden/Death Cross
        cross_signal = 0
        if len(self.df) > 2:
            if (self.df['SMA_50'].iloc[-1] > self.df['SMA_200'].iloc[-1] and 
                self.df['SMA_50'].iloc[-2] <= self.df['SMA_200'].iloc[-2]):
                cross_signal = 1  # Golden Cross
            elif (self.df['SMA_50'].iloc[-1] < self.df['SMA_200'].iloc[-1] and 
                  self.df['SMA_50'].iloc[-2] >= self.df['SMA_200'].iloc[-2]):
                cross_signal = -1  # Death Cross
        
        self.indicators['moving_averages'] = {
            'EMA_9': current['EMA_9'],
            'EMA_21': current['EMA_21'],
            'EMA_50': current['EMA_50'],
            'EMA_200': current['EMA_200'],
            'SMA_20': current['SMA_20'],
            'SMA_50': current['SMA_50'],
            'SMA_200': current['SMA_200'],
            'ema_signal': ema_signal,
            'cross_signal': cross_signal,
            'trend': 'BULLISH' if ema_signal > 0 else ('BEARISH' if ema_signal < 0 else 'NEUTRAL')
        }
        
    def _calculate_momentum_indicators(self):
        """Calcola indicatori di momentum"""
        close = self.df['Close']
        high = self.df['High']
        low = self.df['Low']
        
        # RSI
        rsi = RSIIndicator(close, window=14)
        self.df['RSI'] = rsi.rsi()
        
        # MACD
        macd = MACD(close)
        self.df['MACD'] = macd.macd()
        self.df['MACD_Signal'] = macd.macd_signal()
        self.df['MACD_Hist'] = macd.macd_diff()
        
        # Stochastic
        stoch = StochasticOscillator(high, low, close)
        self.df['Stoch_K'] = stoch.stoch()
        self.df['Stoch_D'] = stoch.stoch_signal()
        
        # Williams %R
        williams = WilliamsRIndicator(high, low, close)
        self.df['Williams_R'] = williams.williams_r()
        
        current = self.df.iloc[-1]
        
        # Segnali RSI
        rsi_value = current['RSI']
        rsi_signal = 0
        if rsi_value < 30:
            rsi_signal = 1  # Oversold - Bullish
        elif rsi_value > 70:
            rsi_signal = -1  # Overbought - Bearish
        elif rsi_value < 45:
            rsi_signal = 0.5
        elif rsi_value > 55:
            rsi_signal = -0.5
            
        # Segnali MACD
        macd_signal = 0
        if current['MACD'] > current['MACD_Signal']:
            macd_signal = 1
        else:
            macd_signal = -1
            
        # Divergenze MACD
        macd_hist = self.df['MACD_Hist'].tail(5)
        macd_divergence = 0
        if macd_hist.iloc[-1] > macd_hist.iloc[-2] > macd_hist.iloc[-3]:
            macd_divergence = 1  # Momentum crescente
        elif macd_hist.iloc[-1] < macd_hist.iloc[-2] < macd_hist.iloc[-3]:
            macd_divergence = -1  # Momentum decrescente
        
        # Segnali Stochastic
        stoch_signal = 0
        if current['Stoch_K'] < 20 and current['Stoch_K'] > current['Stoch_D']:
            stoch_signal = 1
        elif current['Stoch_K'] > 80 and current['Stoch_K'] < current['Stoch_D']:
            stoch_signal = -1
        
        self.indicators['momentum'] = {
            'RSI': rsi_value,
            'RSI_signal': rsi_signal,
            'RSI_condition': 'Oversold' if rsi_value < 30 else ('Overbought' if rsi_value > 70 else 'Neutral'),
            'MACD': current['MACD'],
            'MACD_Signal_Line': current['MACD_Signal'],
            'MACD_Histogram': current['MACD_Hist'],
            'MACD_signal': macd_signal,
            'MACD_divergence': macd_divergence,
            'Stochastic_K': current['Stoch_K'],
            'Stochastic_D': current['Stoch_D'],
            'Stochastic_signal': stoch_signal,
            'Williams_R': current['Williams_R']
        }
        
    def _calculate_volatility_indicators(self):
        """Calcola indicatori di volatilità"""
        close = self.df['Close']
        high = self.df['High']
        low = self.df['Low']
        
        # Bollinger Bands
        bb = BollingerBands(close, window=20, window_dev=2)
        self.df['BB_Upper'] = bb.bollinger_hband()
        self.df['BB_Middle'] = bb.bollinger_mavg()
        self.df['BB_Lower'] = bb.bollinger_lband()
        self.df['BB_Width'] = bb.bollinger_wband()
        
        # ATR
        atr = AverageTrueRange(high, low, close, window=14)
        self.df['ATR'] = atr.average_true_range()
        
        current = self.df.iloc[-1]
        
        # Segnali BB
        bb_signal = 0
        bb_position = ""
        if current['Close'] <= current['BB_Lower']:
            bb_signal = 1
            bb_position = "Below Lower Band"
        elif current['Close'] >= current['BB_Upper']:
            bb_signal = -1
            bb_position = "Above Upper Band"
        elif current['Close'] < current['BB_Middle']:
            bb_signal = 0.3
            bb_position = "Lower Half"
        else:
            bb_signal = -0.3
            bb_position = "Upper Half"
        
        # Volatilità
        atr_percent = (current['ATR'] / current['Close']) * 100
        volatility = "Alta" if atr_percent > 1 else ("Bassa" if atr_percent < 0.3 else "Normale")
        
        self.indicators['volatility'] = {
            'BB_Upper': current['BB_Upper'],
            'BB_Middle': current['BB_Middle'],
            'BB_Lower': current['BB_Lower'],
            'BB_Width': current['BB_Width'],
            'BB_signal': bb_signal,
            'BB_position': bb_position,
            'ATR': current['ATR'],
            'ATR_percent': atr_percent,
            'Volatility': volatility
        }
        
    def _calculate_trend_indicators(self):
        """Calcola indicatori di trend"""
        close = self.df['Close']
        high = self.df['High']
        low = self.df['Low']
        
        # ADX
        adx = ADXIndicator(high, low, close, window=14)
        self.df['ADX'] = adx.adx()
        self.df['ADX_pos'] = adx.adx_pos()
        self.df['ADX_neg'] = adx.adx_neg()
        
        # Ichimoku
        ichimoku = IchimokuIndicator(high, low, window1=9, window2=26, window3=52)
        self.df['Ichimoku_A'] = ichimoku.ichimoku_a()
        self.df['Ichimoku_B'] = ichimoku.ichimoku_b()
        self.df['Ichimoku_Base'] = ichimoku.ichimoku_base_line()
        self.df['Ichimoku_Conv'] = ichimoku.ichimoku_conversion_line()
        
        current = self.df.iloc[-1]
        
        # ADX Signal
        adx_value = current['ADX']
        trend_strength = "Forte" if adx_value > 25 else ("Debole" if adx_value < 20 else "Moderato")
        
        adx_signal = 0
        if current['ADX_pos'] > current['ADX_neg']:
            adx_signal = 1 if adx_value > 25 else 0.5
        else:
            adx_signal = -1 if adx_value > 25 else -0.5
            
        # Ichimoku Signal
        ichimoku_signal = 0
        if current['Close'] > current['Ichimoku_A'] and current['Close'] > current['Ichimoku_B']:
            ichimoku_signal = 1
        elif current['Close'] < current['Ichimoku_A'] and current['Close'] < current['Ichimoku_B']:
            ichimoku_signal = -1
        
        self.indicators['trend'] = {
            'ADX': adx_value,
            'ADX_Positive': current['ADX_pos'],
            'ADX_Negative': current['ADX_neg'],
            'ADX_signal': adx_signal,
            'Trend_Strength': trend_strength,
            'Ichimoku_A': current['Ichimoku_A'],
            'Ichimoku_B': current['Ichimoku_B'],
            'Ichimoku_signal': ichimoku_signal
        }
        
    def _calculate_support_resistance(self):
        """Calcola livelli di supporto e resistenza"""
        high = self.df['High'].values
        low = self.df['Low'].values
        close = self.df['Close'].values
        
        # Pivot Points classici
        pivot = (high[-1] + low[-1] + close[-1]) / 3
        
        # Trova massimi e minimi locali
        window = 10
        local_max = []
        local_min = []
        
        for i in range(window, len(high) - window):
            if high[i] == max(high[i-window:i+window+1]):
                local_max.append(high[i])
            if low[i] == min(low[i-window:i+window+1]):
                local_min.append(low[i])
        
        # Cluster levels
        current_price = close[-1]
        
        resistances = sorted([r for r in local_max if r > current_price])[:3]
        supports = sorted([s for s in local_min if s < current_price], reverse=True)[:3]
        
        self.levels['support_resistance'] = {
            'pivot': pivot,
            'resistances': resistances if resistances else [current_price * 1.005, current_price * 1.01, current_price * 1.02],
            'supports': supports if supports else [current_price * 0.995, current_price * 0.99, current_price * 0.98]
        }
        
    def _calculate_fibonacci_levels(self):
        """Calcola livelli di Fibonacci"""
        high = self.df['High'].max()
        low = self.df['Low'].min()
        diff = high - low
        
        fib_levels = {
            '0.0': high,
            '0.236': high - (diff * 0.236),
            '0.382': high - (diff * 0.382),
            '0.5': high - (diff * 0.5),
            '0.618': high - (diff * 0.618),
            '0.786': high - (diff * 0.786),
            '1.0': low
        }
        
        # Extension levels
        fib_extensions = {
            '1.272': low - (diff * 0.272),
            '1.618': low - (diff * 0.618),
            '-0.272': high + (diff * 0.272),
            '-0.618': high + (diff * 0.618)
        }
        
        self.levels['fibonacci'] = {
            'retracement': fib_levels,
            'extension': fib_extensions
        }
        
    def _calculate_pivot_points(self):
        """Calcola Pivot Points"""
        high = self.df['High'].iloc[-1]
        low = self.df['Low'].iloc[-1]
        close = self.df['Close'].iloc[-1]
        
        pivot = (high + low + close) / 3
        
        # Standard Pivot Points
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        
        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        self.levels['pivot_points'] = {
            'Pivot': pivot,
            'R1': r1,
            'R2': r2,
            'R3': r3,
            'S1': s1,
            'S2': s2,
            'S3': s3
        }
        
    def get_technical_score(self) -> dict:
        """Calcola il punteggio tecnico complessivo"""
        if not self.indicators:
            self.calculate_all_indicators()
            
        scores = []
        weights = []
        
        # Moving Averages Score (peso 25%)
        ma_score = self.indicators['moving_averages']['ema_signal']
        ma_score += self.indicators['moving_averages']['cross_signal'] * 0.5
        scores.append(ma_score)
        weights.append(0.25)
        
        # Momentum Score (peso 30%)
        mom = self.indicators['momentum']
        mom_score = (mom['RSI_signal'] + mom['MACD_signal'] + 
                    mom['Stochastic_signal'] + mom['MACD_divergence']) / 4
        scores.append(mom_score)
        weights.append(0.30)
        
        # Volatility Score (peso 15%)
        vol_score = self.indicators['volatility']['BB_signal']
        scores.append(vol_score)
        weights.append(0.15)
        
        # Trend Score (peso 30%)
        trend = self.indicators['trend']
        trend_score = (trend['ADX_signal'] + trend['Ichimoku_signal']) / 2
        scores.append(trend_score)
        weights.append(0.30)
        
        # Calcolo punteggio finale
        final_score = sum(s * w for s, w in zip(scores, weights))
        
        # Normalizza a probabilità
        probability = (final_score + 1) / 2 * 100  # Converti da [-1,1] a [0,100]
        
        direction = "BULLISH" if final_score > 0.1 else ("BEARISH" if final_score < -0.1 else "NEUTRAL")
        strength = abs(final_score)
        
        confidence = "Alta" if strength > 0.6 else ("Media" if strength > 0.3 else "Bassa")
        
        return {
            'score': final_score,
            'probability_bull': probability,
            'probability_bear': 100 - probability,
            'direction': direction,
            'strength': strength,
            'confidence': confidence,
            'breakdown': {
                'moving_averages': scores[0],
                'momentum': scores[1],
                'volatility': scores[2],
                'trend': scores[3]
            }
        }
    
    def get_entry_points(self) -> dict:
        """Calcola entry points ottimali"""
        if not self.levels:
            self.calculate_all_indicators()
            
        current_price = self.df['Close'].iloc[-1]
        atr = self.indicators['volatility']['ATR']
        
        tech_score = self.get_technical_score()
        direction = tech_score['direction']
        
        if direction == "BULLISH":
            # Entry su pullback
            entry = current_price - (atr * 0.5)
            stop_loss = current_price - (atr * 2)
            take_profit_1 = current_price + (atr * 1.5)
            take_profit_2 = current_price + (atr * 3)
            take_profit_3 = current_price + (atr * 5)
        elif direction == "BEARISH":
            # Entry su pullback
            entry = current_price + (atr * 0.5)
            stop_loss = current_price + (atr * 2)
            take_profit_1 = current_price - (atr * 1.5)
            take_profit_2 = current_price - (atr * 3)
            take_profit_3 = current_price - (atr * 5)
        else:
            entry = current_price
            stop_loss = current_price - (atr * 1.5)
            take_profit_1 = current_price + (atr * 1.5)
            take_profit_2 = current_price + (atr * 2)
            take_profit_3 = current_price + (atr * 3)
        
        risk_reward_1 = abs(take_profit_1 - entry) / abs(entry - stop_loss) if abs(entry - stop_loss) > 0 else 0
        risk_reward_2 = abs(take_profit_2 - entry) / abs(entry - stop_loss) if abs(entry - stop_loss) > 0 else 0
        
        return {
            'direction': direction,
            'current_price': current_price,
            'entry_price': entry,
            'stop_loss': stop_loss,
            'take_profit_1': take_profit_1,
            'take_profit_2': take_profit_2,
            'take_profit_3': take_profit_3,
            'risk_reward_1': risk_reward_1,
            'risk_reward_2': risk_reward_2,
            'atr': atr,
            'key_levels': self.levels
        }
