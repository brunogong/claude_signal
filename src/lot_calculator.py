"""
Calcolatore Lotti e Gestione Rischio
"""

import streamlit as st


class LotCalculator:
    """Calcola i lotti ottimali per il trading"""
    
    # Valori standard lotti forex
    STANDARD_LOT = 100000  # 1 lotto standard = 100,000 unità
    MINI_LOT = 10000       # 1 mini lotto = 10,000 unità
    MICRO_LOT = 1000       # 1 micro lotto = 1,000 unità
    
    # Pip values per diversi tipi di coppie
    PIP_VALUES = {
        'standard': 0.0001,  # EUR/USD, GBP/USD, etc.
        'jpy': 0.01,         # USD/JPY, EUR/JPY, etc.
        'xau': 0.01          # XAU/USD (oro)
    }
    
    def __init__(self, account_balance: float, risk_percent: float = 1.0):
        """
        Inizializza il calcolatore
        
        Args:
            account_balance: Saldo del conto in USD
            risk_percent: Percentuale di rischio per trade (default 1%)
        """
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        self.risk_amount = account_balance * (risk_percent / 100)
    
    def get_pip_type(self, pair: str) -> str:
        """Determina il tipo di pip per la coppia"""
        pair = pair.upper().replace("=X", "")
        
        if "XAU" in pair or "GOLD" in pair:
            return 'xau'
        elif "JPY" in pair:
            return 'jpy'
        else:
            return 'standard'
    
    def get_pip_value(self, pair: str) -> float:
        """Ottieni valore pip per la coppia"""
        pip_type = self.get_pip_type(pair)
        return self.PIP_VALUES[pip_type]
    
    def calculate_pips(self, pair: str, entry: float, stop_loss: float) -> float:
        """Calcola pips tra entry e stop loss"""
        pip_value = self.get_pip_value(pair)
        pips = abs(entry - stop_loss) / pip_value
        return round(pips, 1)
    
    def calculate_pip_value_per_lot(self, pair: str, current_price: float) -> float:
        """
        Calcola il valore di 1 pip per 1 lotto standard
        
        Per la maggior parte delle coppie con USD come quote currency:
        1 pip = $10 per lotto standard
        
        Per coppie con USD come base currency (USD/JPY, USD/CHF):
        1 pip = 1000 / prezzo corrente * $10
        
        Per XAU/USD:
        1 pip ($0.01) = $1 per lotto (100 oz)
        """
        pair_clean = pair.upper().replace("=X", "")
        
        if "XAU" in pair_clean:
            # Oro: 1 lotto = 100 oz, movimento di $0.01 = $1
            return 1.0  # $1 per 0.01 movimento per lotto
        
        elif pair_clean.endswith("USD"):
            # Quote currency USD (EUR/USD, GBP/USD, etc.)
            return 10.0  # $10 per pip per lotto standard
        
        elif pair_clean.startswith("USD"):
            # Base currency USD (USD/JPY, USD/CHF)
            if "JPY" in pair_clean:
                return (1 / current_price) * 1000  # Circa $9.26 per USD/JPY a 108
            else:
                return (1 / current_price) * 10
        
        else:
            # Cross pairs (EUR/GBP, etc.) - approssimazione
            return 10.0
    
    def calculate_lots(self, pair: str, entry: float, stop_loss: float, 
                      current_price: float = None) -> dict:
        """
        Calcola i lotti ottimali basati sul rischio
        
        Formula:
        Lotti = Rischio in $ / (Pips di SL * Valore Pip per Lotto)
        """
        if current_price is None:
            current_price = entry
        
        # Calcola pips
        pips = self.calculate_pips(pair, entry, stop_loss)
        
        if pips == 0:
            return {
                'lots': 0,
                'mini_lots': 0,
                'micro_lots': 0,
                'units': 0,
                'risk_pips': 0,
                'risk_amount': 0,
                'risk_percent': self.risk_percent,
                'position_value': 0,
                'error': 'Stop loss uguale a entry'
            }
        
        # Valore pip per lotto
        pip_value_per_lot = self.calculate_pip_value_per_lot(pair, current_price)
        
        # Per XAU/USD, il calcolo è diverso
        pair_clean = pair.upper().replace("=X", "")
        
        if "XAU" in pair_clean:
            # Per l'oro: rischio per pip * numero pips
            # 1 lotto oro = 100 oz, movimento di $1 = $100
            dollar_move = abs(entry - stop_loss)
            risk_per_lot = dollar_move * 100  # 100 oz per lotto
            
            if risk_per_lot > 0:
                lots = self.risk_amount / risk_per_lot
            else:
                lots = 0
        else:
            # Per forex standard
            risk_per_lot = pips * pip_value_per_lot
            
            if risk_per_lot > 0:
                lots = self.risk_amount / risk_per_lot
            else:
                lots = 0
        
        # Arrotonda a 2 decimali
        lots = round(lots, 2)
        
        # Converti in altri formati
        units = int(lots * self.STANDARD_LOT)
        mini_lots = round(lots * 10, 2)
        micro_lots = round(lots * 100, 2)
        
        # Valore posizione
        if "XAU" in pair_clean:
            position_value = lots * 100 * current_price  # 100 oz * prezzo oro
        else:
            position_value = units * current_price
        
        return {
            'lots': lots,
            'mini_lots': mini_lots,
            'micro_lots': micro_lots,
            'units': units,
            'risk_pips': pips,
            'risk_amount': round(self.risk_amount, 2),
            'risk_percent': self.risk_percent,
            'pip_value_per_lot': round(pip_value_per_lot, 4),
            'position_value': round(position_value, 2),
            'account_balance': self.account_balance,
            'pair': pair,
            'entry': entry,
            'stop_loss': stop_loss
        }
    
    def calculate_position_size_fixed_lots(self, pair: str, lots: float, 
                                           entry: float, stop_loss: float) -> dict:
        """
        Calcola il rischio per un numero fisso di lotti
        """
        pips = self.calculate_pips(pair, entry, stop_loss)
        pip_value_per_lot = self.calculate_pip_value_per_lot(pair, entry)
        
        risk_amount = lots * pips * pip_value_per_lot
        risk_percent = (risk_amount / self.account_balance) * 100
        
        return {
            'lots': lots,
            'risk_pips': pips,
            'risk_amount': round(risk_amount, 2),
            'risk_percent': round(risk_percent, 2),
            'pip_value_per_lot': pip_value_per_lot
        }
    
    def get_risk_assessment(self, risk_percent: float) -> dict:
        """Valuta il livello di rischio"""
        if risk_percent <= 0.5:
            level = 'VERY LOW'
            color = 'green'
            recommendation = 'Conservativo - Ottimo per preservare capitale'
        elif risk_percent <= 1:
            level = 'LOW'
            color = 'lightgreen'
            recommendation = 'Basso rischio - Raccomandato per la maggior parte dei trader'
        elif risk_percent <= 2:
            level = 'MODERATE'
            color = 'yellow'
            recommendation = 'Rischio moderato - Accettabile per trader esperti'
        elif risk_percent <= 3:
            level = 'HIGH'
            color = 'orange'
            recommendation = 'Alto rischio - Solo per trade ad alta probabilità'
        else:
            level = 'VERY HIGH'
            color = 'red'
            recommendation = 'Rischio eccessivo - Non raccomandato'
        
        return {
            'level': level,
            'color': color,
            'recommendation': recommendation
        }


def get_lot_calculator() -> LotCalculator:
    """Factory per ottenere calcolatore con impostazioni da secrets"""
    try:
        balance = st.secrets.get("trading", {}).get("account_balance", 10000)
        risk = st.secrets.get("trading", {}).get("risk_percent", 1)
        return LotCalculator(float(balance), float(risk))
    except:
        return LotCalculator(10000, 1)
