"""
Notifiche Telegram per segnali di trading
"""

import requests
from datetime import datetime
import streamlit as st


class TelegramNotifier:
    """Gestisce le notifiche Telegram"""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        """
        Inizializza il notifier
        
        Per ottenere bot_token:
        1. Cerca @BotFather su Telegram
        2. Invia /newbot
        3. Segui le istruzioni e copia il token
        
        Per ottenere chat_id:
        1. Cerca @userinfobot su Telegram
        2. Invia /start
        3. Copia il tuo ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        
    def is_configured(self) -> bool:
        """Verifica se il bot è configurato"""
        return bool(self.bot_token and self.chat_id)
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Invia messaggio Telegram"""
        if not self.is_configured():
            print("Telegram non configurato")
            return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                print(f"Errore Telegram: {response.text}")
                return False
                
        except Exception as e:
            print(f"Errore invio Telegram: {e}")
            return False
    
    def send_trading_signal(self, signal_data: dict) -> bool:
        """
        Invia segnale di trading formattato
        """
        rec = signal_data.get('recommendation', {})
        combined = signal_data.get('combined_signal', {})
        entry = signal_data.get('entry_points', {})
        lot_info = signal_data.get('lot_calculation', {})
        
        # Emoji basata sulla direzione
        if rec['action'] == 'LONG':
            emoji = "🟢"
            direction_emoji = "📈"
        elif rec['action'] == 'SHORT':
            emoji = "🔴"
            direction_emoji = "📉"
        else:
            emoji = "🟡"
            direction_emoji = "⏸️"
        
        # Confidence emoji
        conf_emoji = "🔥" if rec['confidence'] == 'HIGH' else ("✅" if rec['confidence'] == 'MEDIUM' else "⚠️")
        
        # Formatta messaggio
        message = f"""
{emoji} <b>SEGNALE FOREX</b> {emoji}

{direction_emoji} <b>{signal_data['pair']}</b>
━━━━━━━━━━━━━━━━━━━━

📊 <b>AZIONE:</b> {rec['action']}
💯 <b>Probabilità:</b> {rec['probability']:.1f}%
{conf_emoji} <b>Confidenza:</b> {rec['confidence']}

━━━━━━━━━━━━━━━━━━━━
💰 <b>LIVELLI OPERATIVI</b>
━━━━━━━━━━━━━━━━━━━━

💵 <b>Prezzo Attuale:</b> {signal_data['current_price']:.5f}
🎯 <b>Entry:</b> {entry['entry_price']:.5f}
🛑 <b>Stop Loss:</b> {entry['stop_loss']:.5f}
✅ <b>Take Profit 1:</b> {entry['take_profit_1']:.5f}
✅ <b>Take Profit 2:</b> {entry['take_profit_2']:.5f}
✅ <b>Take Profit 3:</b> {entry['take_profit_3']:.5f}

━━━━━━━━━━━━━━━━━━━━
📐 <b>GESTIONE POSIZIONE</b>
━━━━━━━━━━━━━━━━━━━━

📏 <b>Lotti:</b> {lot_info.get('lots', 'N/A')}
💵 <b>Valore Posizione:</b> ${lot_info.get('position_value', 0):,.2f}
⚠️ <b>Rischio:</b> ${lot_info.get('risk_amount', 0):,.2f} ({lot_info.get('risk_percent', 0)}%)
📊 <b>Risk/Reward:</b> {entry['risk_reward_1']:.2f}

━━━━━━━━━━━━━━━━━━━━
📈 <b>ANALISI</b>
━━━━━━━━━━━━━━━━━━━━

📊 Tecnica: {combined['individual_directions']['technical']}
💰 Fondamentale: {combined['individual_directions']['fundamental']}
💭 Sentiment: {combined['individual_directions']['sentiment']}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<i>⚠️ Questo non è un consiglio finanziario</i>
"""
        
        return self.send_message(message)
    
    def send_alert(self, title: str, message: str, alert_type: str = "info") -> bool:
        """Invia alert generico"""
        
        if alert_type == "success":
            emoji = "✅"
        elif alert_type == "warning":
            emoji = "⚠️"
        elif alert_type == "error":
            emoji = "❌"
        else:
            emoji = "ℹ️"
        
        formatted = f"""
{emoji} <b>{title}</b>

{message}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(formatted)
    
    def send_daily_summary(self, signals: list) -> bool:
        """Invia riepilogo giornaliero"""
        
        if not signals:
            message = """
📊 <b>RIEPILOGO GIORNALIERO</b>

Nessun segnale generato oggi.

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        else:
            signal_lines = []
            for s in signals[:10]:  # Max 10 segnali
                emoji = "🟢" if s.get('action') == 'LONG' else ("🔴" if s.get('action') == 'SHORT' else "🟡")
                signal_lines.append(f"{emoji} {s.get('pair', 'N/A')}: {s.get('action', 'N/A')} ({s.get('probability', 0):.0f}%)")
            
            signals_text = "\n".join(signal_lines)
            
            message = f"""
📊 <b>RIEPILOGO GIORNALIERO</b>

<b>Segnali generati: {len(signals)}</b>

{signals_text}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        return self.send_message(message)


def get_telegram_notifier() -> TelegramNotifier:
    """Factory per ottenere notifier configurato"""
    try:
        bot_token = st.secrets.get("telegram", {}).get("bot_token", "")
        chat_id = st.secrets.get("telegram", {}).get("chat_id", "")
        return TelegramNotifier(bot_token, chat_id)
    except:
        return TelegramNotifier()
