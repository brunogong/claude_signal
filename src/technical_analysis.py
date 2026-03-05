"""
Analisi Tecnica Completa
"""

import pandas as pd
import numpy as np
from ta.trend import MACD, EMAIndicator, SMAIndicator, ADXIndicator, IchimokuIndicator
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator, ROCIndicator
from ta.volatility import BollingerBands, AverageTrueRange, KeltnerChannel
from ta.volume import OnBalanceVolumeIndicator, MFIIndicator


class TechnicalAnalyzer:
    """Analizzatore tecnico completo"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.indicators = {}
        self.signals = {}
        self.levels = {}
        
    def calculate_all_indicators(self):
        """Calcola tutti gli indicatori tecnici"""
        self._calculate_moving_averages()
        self._calculate_momentum()
        self._calculate_volatility()
        self._calculate_trend()
        self._calculate_support_resistance()
        self._calculate_fibonacci()
        self._calculate_pivot_points()
        
        return self.indicators
    
    def _calculate_moving_averages(self):
        """Medie mobili e crossover"""
        close = self.df['Close']
        
        # EMA
        self.df['EMA_9'] = EMAIndicator(close, window=9).ema_indicator()
        self.df['EMA_21'] = EMAIndicator(close, window=21).ema_indicator()
        self.df['EMA_50'] = EMAIndicator(close, window=50).ema_indicator()
        self.df['EMA_100'] = EMAIndicator(close, window=100).ema_indicator()
        self.df['EMA_200'] = EMAIndicator(close, window=200).ema_indicator()
        
        # SMA
        self.df['SMA_20'] = SMAIndicator(close, window=20).sma_indicator()
        self.df['SMA_50'] = SMAIndicator(close, window=50).sma_indicator()
        self.df['SMA_200'] = SMAIndicator(close, window=200).sma_indicator()
        
        current = self.df.iloc[-1]
        prev = self.df.iloc[-2] if len(self.df) > 1 else current
        
        # Segnale EMA
        ema_signal = 0
        if current['EMA_9'] > current['EMA_21'] > current['EMA_50']:
            ema_signal = 1
        elif current['EMA_9'] < current['EMA_21'] < current['EMA_50']:
            ema_signal = -1
        elif current['EMA_9'] > current['EMA_21']:
            ema_signal = 0.5
        elif current['EMA_9'] < current['EMA_21']:
            ema_signal = -0.5
        
        # Golden/Death Cross
        cross_signal = 0
        if len(self.df) > 2:
            if (current['SMA_50'] > current['SMA_200'] and 
                prev['SMA_50'] <= prev['SMA_200']):
                cross_signal = 1  # Golden Cross
            elif (current['SMA_50'] < current['SMA_200'] and 
                  prev['SMA_50'] >= prev['SMA_200']):
                cross_signal = -1  # Death Cross
        
        # Prezzo vs medie
        price_vs_ema = 0
        if current['Close'] > current['EMA_200']:
            price_vs_ema += 0.5
        else:
            price_vs_ema -= 0.5
            
        if current['Close'] > current['EMA_50']:
            price_vs_ema += 0.3
        else:
            price_vs_ema -= 0.3
        
        self.indicators['moving_averages'] = {
            'EMA_9': current['EMA_9'],
            'EMA_21': current['EMA_21'],
            'EMA_50': current['EMA_50'],
            'EMA_200': current['EMA_200'],
            'SMA_50': current['SMA_50'],
            'SMA_200': current['SMA_200'],
            'ema_signal': ema_signal,
            'cross_signal': cross_signal,
            'price_vs_ema': price_vs_ema,
            'trend': 'BULLISH' if ema_signal > 0 else ('BEARISH' if ema_signal < 0 else 'NEUTRAL')
        }
    
    def _calculate_momentum(self):
        """Indicatori momentum"""
        close = self.df['Close']
        high = self.df['High']
        low = self.df['Low']
        
        # RSI
        rsi = RSIIndicator(close, window=14)
        self.df['RSI'] = rsi.rsi()
        
        # MACD
        macd = MACD(close, window_slow=26, window_fast=12, window_sign=9)
        self.df['MACD'] = macd.macd()
        self.df['MACD_Signal'] = macd.macd_signal()
        self.df['MACD_Hist'] = macd.macd_diff()
        
        # Stochastic
        stoch = StochasticOscillator(high, low, close, window=14, smooth_window=3)
        self.df['Stoch_K'] = stoch.stoch()
        self.df['Stoch_D'] = stoch.stoch_signal()
        
        # Williams %R
        williams = WilliamsRIndicator(high, low, close, lbp=14)
        self.df['Williams_R'] = williams.williams_r()
        
        # ROC
        roc = ROCIndicator(close, window=12)
        self.df['ROC'] = roc.roc()
        
        current = self.df.iloc[-1]
        prev = self.df.iloc[-2] if len(self.df) > 1 else current
        
        # RSI Signal
        rsi_value = current['RSI']
        rsi_signal = 0
        
        if rsi_value < 30:
            rsi_signal = 1  # Oversold
            rsi_condition = 'OVERSOLD'
        elif rsi_value > 70:
            rsi_signal = -1  # Overbought
            rsi_condition = 'OVERBOUGHT'
        elif rsi_value < 40:
            rsi_signal = 0.5
            rsi_condition = 'SLIGHTLY OVERSOLD'
        elif rsi_value > 60:
            rsi_signal = -0.5
            rsi_condition = 'SLIGHTLY OVERBOUGHT'
        else:
            rsi_condition = 'NEUTRAL'
        
        # RSI Divergence
        rsi_divergence = 0
        if len(self.df) > 10:
            price_trend = current['Close'] - self.df['Close'].iloc[-10]
            rsi_trend = current['RSI'] - self.df['RSI'].iloc[-10]
            
            if price_trend > 0 and rsi_trend < 0:
                rsi_divergence = -1  # Bearish divergence
            elif price_trend < 0 and rsi_trend > 0:
                rsi_divergence = 1  # Bullish divergence
        
        # MACD Signal
        macd_signal = 0
        if current['MACD'] > current['MACD_Signal']:
            macd_signal = 1
        else:
            macd_signal = -1
        
        # MACD Crossover
        macd_cross = 0
        if (current['MACD'] > current['MACD_Signal'] and 
            prev['MACD'] <= prev['MACD_Signal']):
            macd_cross = 1  # Bullish cross
        elif (current['MACD'] < current['MACD_Signal'] and 
              prev['MACD'] >= prev['MACD_Signal']):
            macd_cross = -1  # Bearish cross
        
        # MACD Histogram momentum
        macd_momentum = 0
        hist = self.df['MACD_Hist'].tail(5)
        if all(hist.diff().dropna() > 0):
            macd_momentum = 1  # Increasing
        elif all(hist.diff().dropna() < 0):
            macd_momentum = -1  # Decreasing
        
        # Stochastic Signal
        stoch_signal = 0
        if current['Stoch_K'] < 20:
            stoch_signal = 1
        elif current['Stoch_K'] > 80:
            stoch_signal = -1
        
        if current['Stoch_K'] > current['Stoch_D'] and prev['Stoch_K'] <= prev['Stoch_D']:
            stoch_signal += 0.5
        elif current['Stoch_K'] < current['Stoch_D'] and prev['Stoch_K'] >= prev['Stoch_D']:
            stoch_signal -= 0.5
        
        self.indicators['momentum'] = {
            'RSI': round(rsi_value, 2),
            'RSI_signal': rsi_signal,
            'RSI_condition': rsi_condition,
            'RSI_divergence': rsi_divergence,
            'MACD': round(current['MACD'], 6),
            'MACD_Signal_Line': round(current['MACD_Signal'], 6),
            'MACD_Histogram': round(current['MACD_Hist'], 6),
            'MACD_signal': macd_signal,
            'MACD_cross': macd_cross,
            'MACD_momentum': macd_momentum,
            'Stochastic_K': round(current['Stoch_K'], 2),
            'Stochastic_D': round(current['Stoch_D'], 2),
            'Stochastic_signal': stoch_signal,
            'Williams_R': round(current['Williams_R'], 2),
            'ROC': round(current['ROC'], 2)
        }
    
    def _calculate_volatility(self):
        """Indicatori volatilità"""
        close = self.df['Close']
        high = self.df['High']
        low = self.df['Low']
        
        # Bollinger Bands
        bb = BollingerBands(close, window=20, window_dev=2)
        self.df['BB_Upper'] = bb.bollinger_hband()
        self.df['BB_Middle'] = bb.bollinger_mavg()
        self.df['BB_Lower'] = bb.bollinger_lband()
        self.df['BB_Width'] = bb.bollinger_wband()
        self.df['BB_Percent'] = bb.bollinger_pband()
        
        # ATR
        atr = AverageTrueRange(high, low, close, window=14)
        self.df['ATR'] = atr.average_true_range()
        
        # Keltner Channel
        kc = KeltnerChannel(high, low, close, window=20)
        self.df['KC_Upper'] = kc.keltner_channel_hband()
        self.df['KC_Lower'] = kc.keltner_channel_lband()
        
        current = self.df.iloc[-1]
        
        # BB Signal
        bb_signal = 0
        if current['Close'] <= current['BB_Lower']:
            bb_signal = 1
            bb_position = 'BELOW LOWER BAND'
        elif current['Close'] >= current['BB_Upper']:
            bb_signal = -1
            bb_position = 'ABOVE UPPER BAND'
        elif current['Close'] < current['BB_Middle']:
            bb_signal = 0.3
            bb_position = 'LOWER HALF'
        else:
            bb_signal = -0.3
            bb_position = 'UPPER HALF'
        
        # Squeeze (BB dentro KC = bassa volatilità, possibile breakout)
        squeeze = current['BB_Upper'] < current['KC_Upper'] and current['BB_Lower'] > current['KC_Lower']
        
        # Volatilità
        atr_percent = (current['ATR'] / current['Close']) * 100
        if atr_percent > 1.5:
            volatility = 'VERY HIGH'
        elif atr_percent > 1:
            volatility = 'HIGH'
        elif atr_percent > 0.5:
            volatility = 'NORMAL'
        else:
            volatility = 'LOW'
        
        self.indicators['volatility'] = {
            'BB_Upper': round(current['BB_Upper'], 5),
            'BB_Middle': round(current['BB_Middle'], 5),
            'BB_Lower': round(current['BB_Lower'], 5),
            'BB_Width': round(current['BB_Width'], 5),
            'BB_Percent': round(current['BB_Percent'] * 100, 2),
            'BB_signal': bb_signal,
            'BB_position': bb_position,
            'ATR': round(current['ATR'], 5),
            'ATR_percent': round(atr_percent, 2),
            'Volatility': volatility,
            'Squeeze': squeeze,
            'KC_Upper': round(current['KC_Upper'], 5),
            'KC_Lower': round(current['KC_Lower'], 5)
        }
    
    def _calculate_trend(self):
        """Indicatori trend"""
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
        
        if adx_value > 40:
            trend_strength = 'VERY STRONG'
        elif adx_value > 25:
            trend_strength = 'STRONG'
        elif adx_value > 20:
            trend_strength = 'MODERATE'
        else:
            trend_strength = 'WEAK'
        
        adx_signal = 0
        if current['ADX_pos'] > current['ADX_neg']:
            adx_signal = 1 if adx_value > 25 else 0.5
        else:
            adx_signal = -1 if adx_value > 25 else -0.5
        
        # Ichimoku Signal
        ichimoku_signal = 0
        cloud_top = max(current['Ichimoku_A'], current['Ichimoku_B'])
        cloud_bottom = min(current['Ichimoku_A'], current['Ichimoku_B'])
        
        if current['Close'] > cloud_top:
            ichimoku_signal = 1
            ichimoku_position = 'ABOVE CLOUD'
        elif current['Close'] < cloud_bottom:
            ichimoku_signal = -1
            ichimoku_position = 'BELOW CLOUD'
        else:
            ichimoku_position = 'INSIDE CLOUD'
        
        # TK Cross
        tk_cross = 0
        if current['Ichimoku_Conv'] > current['Ichimoku_Base']:
            tk_cross = 0.5
        else:
            tk_cross = -0.5
        
        self.indicators['trend'] = {
            'ADX': round(adx_value, 2),
            'ADX_Positive': round(current['ADX_pos'], 2),
            'ADX_Negative': round(current['ADX_neg'], 2),
            'ADX_signal': adx_signal,
            'Trend_Strength': trend_strength,
            'Ichimoku_A': round(current['Ichimoku_A'], 5),
            'Ichimoku_B': round(current['Ichimoku_B'], 5),
            'Ichimoku_signal': ichimoku_signal,
            'Ichimoku_position': ichimoku_position,
            'TK_cross': tk_cross,
            'Cloud_Top': round(cloud_top, 5),
            'Cloud_Bottom': round(cloud_bottom, 5)
        }
    
    def _calculate_support_resistance(self):
        """Calcola supporti e resistenze"""
        high = self.df['High'].values
        low = self.df['Low'].values
        close = self.df['Close'].values
        current_price = close[-1]
        
        # Trova pivot points locali
        window = 10
        local_highs = []
        local_lows = []
        
        for i in range(window, len(high) - window):
            if high[i] == max(high[i-window:i+window+1]):
                local_highs.append(high[i])
            if low[i] == min(low[i-window:i+window+1]):
                local_lows.append(low[i])
        
        # Cluster simili
        def cluster_levels(levels, threshold=0.001):
            if not levels:
                return []
            levels = sorted(levels)
            clusters = [[levels[0]]]
            
            for level in levels[1:]:
                if abs(level - clusters[-1][-1]) / clusters[-1][-1] < threshold:
                    clusters[-1].append(level)
                else:
                    clusters.append([level])
            
            return [sum(c) / len(c) for c in clusters]
        
        resistances = cluster_levels([h for h in local_highs if h > current_price])[:3]
        supports = cluster_levels([l for l in local_lows if l < current_price])[-3:]
        supports.reverse()
        
        # Fallback se non ci sono livelli
        atr = self.indicators.get('volatility', {}).get('ATR', current_price * 0.01)
        
        if not resistances:
            resistances = [current_price + atr, current_price + atr * 2, current_price + atr * 3]
        if not supports:
            supports = [current_price - atr, current_price - atr * 2, current_price - atr * 3]
        
        self.levels['support_resistance'] = {
            'resistances': [round(r, 5) for r in resistances],
            'supports': [round(s, 5) for s in supports],
            'nearest_resistance': round(resistances[0], 5) if resistances else None,
            'nearest_support': round(supports[0], 5) if supports else None
        }
    
    def _calculate_fibonacci(self):
        """Calcola livelli Fibonacci"""
        period = min(100, len(self.df))
        high = self.df['High'].tail(period).max()
        low = self.df['Low'].tail(period).min()
        diff = high - low
        
        # Retracement
        fib_retracement = {
            '0.0 (High)': high,
            '0.236': high - (diff * 0.236),
            '0.382': high - (diff * 0.382),
            '0.5': high - (diff * 0.5),
            '0.618': high - (diff * 0.618),
            '0.786': high - (diff * 0.786),
            '1.0 (Low)': low
        }
        
        # Extension
        fib_extension = {
            '1.272': low - (diff * 0.272),
            '1.618': low - (diff * 0.618),
            '2.0': low - diff,
            '-0.272': high + (diff * 0.272),
            '-0.618': high + (diff * 0.618)
        }
        
        self.levels['fibonacci'] = {
            'retracement': {k: round(v, 5) for k, v in fib_retracement.items()},
            'extension': {k: round(v, 5) for k, v in fib_extension.items()},
            'range_high': round(high, 5),
            'range_low': round(low, 5)
        }
    
    def _calculate_pivot_points(self):
        """Calcola Pivot Points"""
        if len(self.df) < 2:
            return
            
        # Usa i dati del giorno precedente
        prev = self.df.iloc[-2]
        high = prev['High']
        low = prev['Low']
        close = prev['Close']
        
        pivot = (high + low + close) / 3
        
        # Standard Pivot Points
        r1 = (2 * pivot) - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        
        s1 = (2 * pivot) - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        # Camarilla Pivot Points
        range_hl = high - low
        c_r1 = close + range_hl * 1.1 / 12
        c_r2 = close + range_hl * 1.1 / 6
        c_r3 = close + range_hl * 1.1 / 4
        c_s1 = close - range_hl * 1.1 / 12
        c_s2 = close - range_hl * 1.1 / 6
        c_s3 = close - range_hl * 1.1 / 4
        
        self.levels['pivot_points'] = {
            'standard': {
                'Pivot': round(pivot, 5),
                'R1': round(r1, 5),
                'R2': round(r2, 5),
                'R3': round(r3, 5),
                'S1': round(s1, 5),
                'S2': round(s2, 5),
                'S3': round(s3, 5)
            },
            'camarilla': {
                'R1': round(c_r1, 5),
                'R2': round(c_r2, 5),
                'R3': round(c_r3, 5),
                'S1': round(c_s1, 5),
                'S2': round(c_s2, 5),
                'S3': round(c_s3, 5)
            }
        }
    
    def get_technical_score(self) -> dict:
        """Calcola punteggio tecnico complessivo"""
        if not self.indicators:
            self.calculate_all_indicators()
        
        scores = []
        details = {}
        
        # 1. Moving Averages (25%)
        ma = self.indicators['moving_averages']
        ma_score = ma['ema_signal'] * 0.6 + ma['cross_signal'] * 0.2 + ma['price_vs_ema'] * 0.2
        scores.append(('Moving Averages', ma_score, 0.25))
        details['moving_averages'] = ma_score
        
        # 2. Momentum (35%)
        mom = self.indicators['momentum']
        mom_score = (
            mom['RSI_signal'] * 0.3 +
            mom['MACD_signal'] * 0.25 +
            mom['MACD_cross'] * 0.15 +
            mom['MACD_momentum'] * 0.1 +
            mom['Stochastic_signal'] * 0.15 +
            mom['RSI_divergence'] * 0.05
        )
        scores.append(('Momentum', mom_score, 0.35))
        details['momentum'] = mom_score
        
        # 3. Volatility (15%)
        vol = self.indicators['volatility']
        vol_score = vol['BB_signal']
        if vol['Squeeze']:
            vol_score *= 0.5  # Riduci confidence durante squeeze
        scores.append(('Volatility', vol_score, 0.15))
        details['volatility'] = vol_score
        
        # 4. Trend (25%)
        trend = self.indicators['trend']
        trend_score = (
            trend['ADX_signal'] * 0.5 +
            trend['Ichimoku_signal'] * 0.35 +
            trend['TK_cross'] * 0.15
        )
        scores.append(('Trend', trend_score, 0.25))
        details['trend'] = trend_score
        
        # Score finale
        final_score = sum(score * weight for _, score, weight in scores)
        
        # Normalizza a probabilità [0, 100]
        probability_bull = ((final_score + 1) / 2) * 100
        probability_bull = max(0, min(100, probability_bull))
        
        # Direzione
        if final_score > 0.3:
            direction = 'STRONG BULLISH'
        elif final_score > 0.1:
            direction = 'BULLISH'
        elif final_score < -0.3:
            direction = 'STRONG BEARISH'
        elif final_score < -0.1:
            direction = 'BEARISH'
        else:
            direction = 'NEUTRAL'
        
        # Confidence
        strength = abs(final_score)
        if strength > 0.5:
            confidence = 'HIGH'
        elif strength > 0.25:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'
        
        return {
            'score': round(final_score, 3),
            'probability_bull': round(probability_bull, 1),
            'probability_bear': round(100 - probability_bull, 1),
            'direction': direction,
            'confidence': confidence,
            'strength': round(strength, 3),
            'breakdown': details
        }
    
    def get_entry_points(self) -> dict:
        """Calcola entry points ottimali con SL e TP"""
        if not self.indicators:
            self.calculate_all_indicators()
        
        current_price = self.df['Close'].iloc[-1]
        atr = self.indicators['volatility']['ATR']
        
        score = self.get_technical_score()
        direction = score['direction']
        
        # Risk multipliers basati su confidence
        if score['confidence'] == 'HIGH':
            sl_mult = 1.5
            tp_mult = [2, 3.5, 5]
        elif score['confidence'] == 'MEDIUM':
            sl_mult = 2
            tp_mult = [1.5, 2.5, 4]
        else:
            sl_mult = 2.5
            tp_mult = [1, 2, 3]
        
        if 'BULLISH' in direction:
            # Long setup
            entry = current_price
            stop_loss = current_price - (atr * sl_mult)
            take_profit_1 = current_price + (atr * tp_mult[0])
            take_profit_2 = current_price + (atr * tp_mult[1])
            take_profit_3 = current_price + (atr * tp_mult[2])
            trade_type = 'LONG'
            
        elif 'BEARISH' in direction:
            # Short setup
            entry = current_price
            stop_loss = current_price + (atr * sl_mult)
            take_profit_1 = current_price - (atr * tp_mult[0])
            take_profit_2 = current_price - (atr * tp_mult[1])
            take_profit_3 = current_price - (atr * tp_mult[2])
            trade_type = 'SHORT'
            
        else:
            # Neutral - no trade
            entry = current_price
            stop_loss = current_price - (atr * 2)
            take_profit_1 = current_price + (atr * 1.5)
            take_profit_2 = current_price + (atr * 2.5)
            take_profit_3 = current_price + (atr * 3.5)
            trade_type = 'WAIT'
        
        # Risk/Reward
        risk = abs(entry - stop_loss)
        reward_1 = abs(take_profit_1 - entry)
        reward_2 = abs(take_profit_2 - entry)
        
        rr_1 = reward_1 / risk if risk > 0 else 0
        rr_2 = reward_2 / risk if risk > 0 else 0
        
        return {
            'trade_type': trade_type,
            'direction': direction,
            'current_price': round(current_price, 5),
            'entry_price': round(entry, 5),
            'stop_loss': round(stop_loss, 5),
            'take_profit_1': round(take_profit_1, 5),
            'take_profit_2': round(take_profit_2, 5),
            'take_profit_3': round(take_profit_3, 5),
            'risk_pips': round(risk * 10000, 1),  # Per non-JPY pairs
            'reward_1_pips': round(reward_1 * 10000, 1),
            'risk_reward_1': round(rr_1, 2),
            'risk_reward_2': round(rr_2, 2),
            'atr': round(atr, 5),
            'confidence': score['confidence']
        }
