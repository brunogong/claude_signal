"""
Forex Analysis Pro - Applicazione Streamlit
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sys
import os

# Aggiungi path per import locali
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.technical_analysis import TechnicalAnalyzer
from src.fundamental_analysis import FundamentalAnalyzer
from src.sentiment_analysis import SentimentAnalyzer
from src.signal_generator import SignalGenerator
from src.utils import get_forex_data, get_pair_name, format_price, get_session_info
from config.settings import FOREX_PAIRS, PAIR_NAMES, TIMEFRAMES

# Configurazione pagina
st.set_page_config(
    page_title="Forex Analysis Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizzato
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .bullish {
        color: #00C853;
        font-weight: bold;
    }
    .bearish {
        color: #FF1744;
        font-weight: bold;
    }
    .neutral {
        color: #FFB300;
        font-weight: bold;
    }
    .signal-box {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .buy-signal {
        background-color: rgba(0, 200, 83, 0.2);
        border: 2px solid #00C853;
    }
    .sell-signal {
        background-color: rgba(255, 23, 68, 0.2);
        border: 2px solid #FF1744;
    }
    .wait-signal {
        background-color: rgba(255, 179, 0, 0.2);
        border: 2px solid #FFB300;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">📊 Forex Analysis Pro</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/currency-exchange.png", width=80)
        st.title("⚙️ Impostazioni")
        
        # Selezione coppia
        selected_pair = st.selectbox(
            "Seleziona Coppia",
            options=FOREX_PAIRS,
            format_func=lambda x: PAIR_NAMES.get(x, x),
            index=0
        )
        
        # Timeframe
        timeframe = st.selectbox(
            "Timeframe",
            options=list(TIMEFRAMES.keys()),
            index=2  # Default: 1d
        )
        
        # Periodo analisi
        period = st.selectbox(
            "Periodo Storico",
            options=["1mo", "3mo", "6mo", "1y"],
            index=1
        )
        
        st.markdown("---")
        
        # Info sessione
        session_info = get_session_info()
        st.subheader("🕐 Sessioni Attive")
        for session in session_info['active_sessions']:
            st.write(f"• {session.capitalize()}")
        st.caption(f"Ora: {session_info['utc_time']}")
        st.caption(f"Volatilità attesa: {session_info['volatility']}")
        
        st.markdown("---")
        
        # Pesi analisi
        st.subheader("📊 Pesi Analisi")
        tech_weight = st.slider("Tecnica", 0.0, 1.0, 0.45)
        fund_weight = st.slider("Fondamentale", 0.0, 1.0, 0.30)
        sent_weight = st.slider("Sentiment", 0.0, 1.0, 0.25)
        
        # Normalizza pesi
        total = tech_weight + fund_weight + sent_weight
        if total > 0:
            tech_weight /= total
            fund_weight /= total
            sent_weight /= total
        
        analyze_button = st.button("🔍 Analizza", type="primary", use_container_width=True)
    
    # Main content
    if analyze_button or 'analysis' not in st.session_state:
        with st.spinner("Caricamento dati..."):
            df = get_forex_data(selected_pair, period=period, interval=TIMEFRAMES[timeframe])
            
            if df is None or df.empty:
                st.error("Impossibile caricare i dati. Riprova più tardi.")
                return
            
            # Genera analisi
            signal_gen = SignalGenerator(df, selected_pair)
            analysis = signal_gen.generate_complete_analysis()
            st.session_state['analysis'] = analysis
            st.session_state['df'] = df
            st.session_state['pair'] = selected_pair
    
    analysis = st.session_state.get('analysis')
    df = st.session_state.get('df')
    
    if analysis:
        display_analysis(analysis, df)

def display_analysis(analysis: dict, df: pd.DataFrame):
    """Visualizza l'analisi completa"""
    
    pair_name = get_pair_name(analysis['pair'])
    
    # Row 1: Metriche principali
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_price = analysis['current_price']
        st.metric(
            label=f"💱 {pair_name}",
            value=format_price(analysis['pair'], current_price),
            delta=f"{((df['Close'].iloc[-1] / df['Close'].iloc[-2]) - 1) * 100:.2f}%"
        )
    
    with col2:
        direction = analysis['combined_signal']['direction']
        color = "bullish" if "BUY" in direction else ("bearish" if "SELL" in direction else "neutral")
        st.metric(
            label="📈 Direzione",
            value=direction
        )
        st.markdown(f'<p class="{color}">{analysis["combined_signal"]["confidence"]} Confidenza</p>', unsafe_allow_html=True)
    
    with col3:
        prob_bull = analysis['combined_signal']['probability_bull']
        st.metric(
            label="🐂 Prob. Rialzo",
            value=f"{prob_bull:.1f}%"
        )
    
    with col4:
        st.metric(
            label="🐻 Prob. Ribasso",
            value=f"{analysis['combined_signal']['probability_bear']:.1f}%"
        )
    
    st.markdown("---")
    
    # Row 2: Signal Box e Entry Points
    col1, col2 = st.columns([1, 1])
    
    with col1:
        rec = analysis['recommendation']
        signal_class = "buy-signal" if rec['action'] == "LONG" else ("sell-signal" if rec['action'] == "SHORT" else "wait-signal")
        
        st.markdown(f"""
        <div class="signal-box {signal_class}">
            <h2 style="text-align: center;">{'🟢' if rec['action'] == 'LONG' else ('🔴' if rec['action'] == 'SHORT' else '🟡')} {rec['action']}</h2>
            <h3 style="text-align: center;">Probabilità: {rec['probability']:.1f}%</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Entry Points
        st.subheader("🎯 Entry Points")
        entry_data = {
            "Livello": ["Entry", "Stop Loss", "Take Profit 1", "Take Profit 2", "Take Profit 3"],
            "Prezzo": [
                format_price(analysis['pair'], rec['entry']),
                format_price(analysis['pair'], rec['stop_loss']),
                format_price(analysis['pair'], rec['take_profit_1']),
                format_price(analysis['pair'], rec['take_profit_2']),
                format_price(analysis['pair'], rec['take_profit_3'])
            ],
            "Pips": [
                "-",
                f"{abs(rec['entry'] - rec['stop_loss']) * (100 if 'JPY' in analysis['pair'] else 10000):.1f}",
                f"{abs(rec['take_profit_1'] - rec['entry']) * (100 if 'JPY' in analysis['pair'] else 10000):.1f}",
                f"{abs(rec['take_profit_2'] - rec['entry']) * (100 if 'JPY' in analysis['pair'] else 10000):.1f}",
                f"{abs(rec['take_profit_3'] - rec['entry']) * (100 if 'JPY' in analysis['pair'] else 10000):.1f}"
            ]
        }
        st.table(pd.DataFrame(entry_data))
        
        st.info(f"📊 Risk/Reward: {rec['risk_reward']:.2f}")
        st.info(f"📏 Position Size Suggerito: {rec['suggested_position_size']}")
    
    with col2:
        st.subheader("📝 Note Operative")
        for note in rec['notes']:
            st.write(note)
        
        st.markdown("---")
        
        # Score breakdown
        st.subheader("📊 Breakdown Analisi")
        scores = analysis['combined_signal']['individual_scores']
        
        fig_scores = go.Figure(data=[
            go.Bar(
                x=['Tecnica', 'Fondamentale', 'Sentiment'],
                y=[scores['technical'], scores['fundamental'], scores['sentiment']],
                marker_color=['#2196F3', '#4CAF50', '#FF9800'],
                text=[f"{s:.2f}" for s in [scores['technical'], scores['fundamental'], scores['sentiment']]],
                textposition='auto'
            )
        ])
        fig_scores.update_layout(
            title="Punteggi per Categoria",
            yaxis_range=[-1, 1],
            height=300
        )
        st.plotly_chart(fig_scores, use_container_width=True)
    
    st.markdown("---")
    
    # Row 3: Charts
    st.subheader("📈 Analisi Grafica")
    
    # Candlestick con indicatori
    fig = create_advanced_chart(df, analysis)
    st.plotly_chart(fig, use_container_width=True)
    
    # Row 4: Tabs per analisi dettagliate
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Tecnica", "📈 Fondamentale", "💭 Sentiment", "📋 Livelli"])
    
    with tab1:
        display_technical_analysis(analysis['technical_analysis'])
    
    with tab2:
        display_fundamental_analysis(analysis['fundamental_analysis'])
    
    with tab3:
        display_sentiment_analysis(analysis['sentiment_analysis'])
    
    with tab4:
        display_key_levels(analysis['key_levels'], analysis['current_price'])

def create_advanced_chart(df: pd.DataFrame, analysis: dict) -> go.Figure:
    """Crea grafico avanzato con indicatori"""
    
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=('Price Action', 'RSI', 'MACD', 'Volume')
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price'
        ),
        row=1, col=1
    )
    
    # Bollinger Bands
    tech = analysis['technical_analysis']['indicators']
    
    if 'volatility' in tech:
        bb_upper = tech['volatility']['BB_Upper']
        bb_lower = tech['volatility']['BB_Lower']
        bb_middle = tech['volatility']['BB_Middle']
        
        # Aggiungi BB come lines
        last_n = 50
        x_range = df.index[-last_n:] if len(df) > last_n else df.index
    
    # EMAs
    if 'moving_averages' in tech:
        ma = tech['moving_averages']
        # Plotta EMA usando i dati dal DataFrame
        analyzer = TechnicalAnalyzer(df)
        analyzer.calculate_all_indicators()
        
        fig.add_trace(
            go.Scatter(x=df.index, y=analyzer.df['EMA_21'], name='EMA 21', line=dict(color='orange', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=analyzer.df['EMA_50'], name='EMA 50', line=dict(color='blue', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=analyzer.df['BB_Upper'], name='BB Upper', line=dict(color='gray', width=1, dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=analyzer.df['BB_Lower'], name='BB Lower', line=dict(color='gray', width=1, dash='dash')),
            row=1, col=1
        )
    
        # RSI
        fig.add_trace(
            go.Scatter(x=df.index, y=analyzer.df['RSI'], name='RSI', line=dict(color='purple')),
            row=2, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        
        # MACD
        fig.add_trace(
            go.Scatter(x=df.index, y=analyzer.df['MACD'], name='MACD', line=dict(color='blue')),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=analyzer.df['MACD_Signal'], name='Signal', line=dict(color='orange')),
            row=3, col=1
        )
        fig.add_trace(
            go.Bar(x=df.index, y=analyzer.df['MACD_Hist'], name='Histogram', marker_color='gray'),
            row=3, col=1
        )
    
    # Volume
    colors = ['green' if close >= open else 'red' for close, open in zip(df['Close'], df['Open'])]
    fig.add_trace(
        go.Bar(x=df.index, y=df['Volume'], name='Volume', marker_color=colors),
        row=4, col=1
    )
    
    # Entry points lines
    rec = analysis['recommendation']
    if rec['action'] != 'WAIT':
        fig.add_hline(y=rec['entry'], line_dash="solid", line_color="blue", annotation_text="Entry", row=1, col=1)
        fig.add_hline(y=rec['stop_loss'], line_dash="dash", line_color="red", annotation_text="SL", row=1, col=1)
        fig.add_hline(y=rec['take_profit_1'], line_dash="dash", line_color="green", annotation_text="TP1", row=1, col=1)
    
    fig.update_layout(
        title=f'{get_pair_name(analysis["pair"])} - Analisi Tecnica',
        height=800,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    return fig

def display_technical_analysis(tech: dict):
    """Visualizza analisi tecnica dettagliata"""
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📊 Momentum")
        indicators = tech['indicators']['momentum']
        
        st.metric("RSI (14)", f"{indicators['RSI']:.2f}", indicators['RSI_condition'])
        st.metric("MACD", f"{indicators['MACD']:.6f}")
        st.metric("Stochastic %K", f"{indicators['Stochastic_K']:.2f}")
        
        # RSI Gauge
        fig_rsi = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = indicators['RSI'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "RSI"},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 30], 'color': "lightgreen"},
                    {'range': [30, 70], 'color': "lightyellow"},
                    {'range': [70, 100], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': indicators['RSI']
                }
            }
        ))
        fig_rsi.update_layout(height=250)
        st.plotly_chart(fig_rsi, use_container_width=True)
    
    with col2:
        st.subheader("📈 Trend")
        trend = tech['indicators']['trend']
        
        st.metric("ADX", f"{trend['ADX']:.2f}", trend['Trend_Strength'])
        st.metric("DI+", f"{trend['ADX_Positive']:.2f}")
        st.metric("DI-", f"{trend['ADX_Negative']:.2f}")
        
        # Trend strength gauge
        fig_adx = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = trend['ADX'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Forza Trend (ADX)"},
            gauge = {
                'axis': {'range': [0, 60]},
                'bar': {'color': "purple"},
                'steps': [
                    {'range': [0, 20], 'color': "lightgray"},
                    {'range': [20, 40], 'color': "lightyellow"},
                    {'range': [40, 60], 'color': "lightgreen"}
                ]
            }
        ))
        fig_adx.update_layout(height=250)
        st.plotly_chart(fig_adx, use_container_width=True)
    
    with col3:
        st.subheader("📉 Volatilità")
        vol = tech['indicators']['volatility']
        
        st.metric("ATR", f"{vol['ATR']:.5f}")
        st.metric("ATR %", f"{vol['ATR_percent']:.2f}%", vol['Volatility'])
        st.metric("BB Position", vol['BB_position'])
        
        # Score breakdown
        st.markdown("---")
        st.subheader("Segnali")
        score = tech['score']
        
        for key, value in score['breakdown'].items():
            icon = "🟢" if value > 0.3 else ("🔴" if value < -0.3 else "🟡")
            st.write(f"{icon} {key.replace('_', ' ').title()}: {value:.2f}")

def display_fundamental_analysis(fund: dict):
    """Visualizza analisi fondamentale"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Tassi di Interesse")
        rates = fund['rate_analysis']
        
        rate_data = pd.DataFrame({
            'Valuta': [rates['base_currency']['currency'], rates['quote_currency']['currency']],
            'Tasso': [f"{rates['base_currency']['rate']:.2f}%", f"{rates['quote_currency']['rate']:.2f}%"],
            'Banca Centrale': [rates['base_currency']['bank'], rates['quote_currency']['bank']],
            'Trend': [rates
