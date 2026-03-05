"""
Analisi Sentiment con Dati Reali
"""
from datetime import datetime
from textblob import TextBlob
from collections import Counter
from .data_providers import (
    NewsProvider,
    SentimentDataProvider
)

class SentimentAnalyzer:
    """Classe per l'analisi del sentiment con dati reali"""
    
    def __init__(self, pair: str):
        self.pair = pair.replace("=X", "")
        self.news = []
        self._sentiment_cache = None
        
    def fetch_news(self) -> list:
        """Recupera news reali dai feed RSS"""
        self.news = NewsProvider.fetch_all_news(self.pair, limit=20)
        return self.news
    
    def analyze_news_sentiment(self) -> dict:
        """Analizza sentiment delle news reali"""
        if not self.news:
            self.fetch_news()
        
        sentiments = []
        analyzed_news = []
        
        for news in self.news:
            text = news['title'] + ' ' + news.get('summary', '')
            
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                
                if polarity > 0.1:
                    sentiment = 'BULLISH'
                elif polarity < -0.1:
                    sentiment = 'BEARISH'
                else:
                    sentiment = 'NEUTRAL'
                
                sentiments.append(polarity)
                analyzed_news.append({
                    'title': news['title'][:100],
                    'source': news['source'],
                    'polarity': round(polarity, 3),
                    'sentiment': sentiment,
                    'link': news.get('link', '')
                })
            except Exception as e:
                continue
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        sentiment_counts = Counter([n['sentiment'] for n in analyzed_news])
        
        return {
            'average_polarity': round(avg_sentiment, 3),
            'news_count': len(analyzed_news),
            'sentiment_distribution': dict(sentiment_counts),
            'analyzed_news': analyzed_news[:10],
            'overall_sentiment': 'BULLISH' if avg_sentiment > 0.05 else ('BEARISH' if avg_sentiment < -0.05 else 'NEUTRAL'),
            'data_source': 'Real-time RSS Feeds'
        }
    
    def get_market_positioning(self) -> dict:
        """Recupera positioning reale da fonti pubbliche"""
        # Prova MyFxBook
        myfxbook_data = SentimentDataProvider.get_myfxbook_sentiment()
        
        pair_key = self.pair.replace('/', '')
        
        if pair_key in myfxbook_data:
            data = myfxbook_data[pair_key]
            long_pct = data['long_percent']
            short_pct = data['short_percent']
            source = 'MyFxBook'
        else:
            # Prova DailyFX
            dailyfx_data = SentimentDataProvider.get_retail_sentiment_dailyfx()
            
            if pair_key in dailyfx_data:
                data = dailyfx_data[pair_key]
                long_pct = data['long']
                short_pct = data['short']
                source = 'DailyFX (IG Sentiment)'
            else:
                # Fallback: stima basata su analisi news
                news_sent = self.analyze_news_sentiment()
                polarity = news_sent['average_polarity']
                long_pct = 50 + (polarity * 30)  # Stima
                short_pct = 100 - long_pct
                source = 'Estimated from News Sentiment'
        
        # Sentiment contrarian (retail di solito sbaglia)
        if long_pct > 60:
            contrarian = 'BEARISH'
        elif long_pct < 40:
            contrarian = 'BULLISH'
        else:
            contrarian = 'NEUTRAL'
        
        return {
            'retail': {
                'long_percent': round(long_pct, 1),
                'short_percent': round(short_pct, 1),
                'sentiment': 'BULLISH' if long_pct > 55 else ('BEARISH' if long_pct < 45 else 'NEUTRAL'),
                'contrarian_signal': contrarian
            },
            'data_source': source
        }
    
    def get_cot_positioning(self) -> dict:
        """Recupera dati COT reali dalla CFTC"""
        cot_data = SentimentDataProvider.get_cot_data()
        
        # Analizza per la valuta base
        base = self.pair[:3]
        
        if base in cot_data:
            data = cot_data[base]
            
            # Calcola net positioning
            commercial_net = data['commercial_long'] - data['commercial_short']
            speculative_net = data['non_commercial_long'] - data['non_commercial_short']
            
            # I commerciali (hedgers) fanno spesso il contrario del trend
            # Gli speculatori (hedge funds) seguono il trend
            
            if speculative_net > 0:
                institutional_bias = 'BULLISH'
            elif speculative_net < 0:
                institutional_bias = 'BEARISH'
            else:
                institutional_bias = 'NEUTRAL'
            
            return {
                'available': True,
                'currency': base,
                'commercial_net': commercial_net,
                'speculative_net': speculative_net,
                'institutional_bias': institutional_bias,
                'data_source': 'CFTC COT Report (Weekly)'
            }
        
        return {
            'available': False,
            'note': 'COT data not available for this currency'
        }
    
    def get_sentiment_score(self) -> dict:
        """Calcola punteggio sentiment complessivo con dati reali"""
        news_sentiment = self.analyze_news_sentiment()
        positioning = self.get_market_positioning()
        cot = self.get_cot_positioning()
        
        scores = []
        
        # News sentiment (40%)
        news_score = news_sentiment['average_polarity']
        scores.append(('news', news_score, 0.40))
        
        # Retail positioning - contrarian (35%)
        contrarian = positioning['retail']['contrarian_signal']
        if contrarian == 'BULLISH':
            pos_score = 0.5
        elif contrarian == 'BEARISH':
            pos_score = -0.5
        else:
            pos_score = 0
        scores.append(('retail_contrarian', pos_score, 0.35))
        
        # COT institutional (25%)
        if cot.get('available'):
            if cot['institutional_bias'] == 'BULLISH':
                cot_score = 0.5
            elif cot['institutional_bias'] == 'BEARISH':
                cot_score = -0.5
            else:
                cot_score = 0
        else:
            cot_score = 0
        scores.append(('cot_institutional', cot_score, 0.25))
        
        # Score finale
        final_score = sum(score * weight for _, score, weight in scores)
        probability_bull = ((final_score + 1) / 2) * 100
        
        return {
            'score': round(final_score, 3),
            'probability_bull': round(probability_bull, 1),
            'probability_bear': round(100 - probability_bull, 1),
            'direction': 'BULLISH' if final_score > 0.1 else ('BEARISH' if final_score < -0.1 else 'NEUTRAL'),
            'news_sentiment': news_sentiment,
            'market_positioning': positioning,
            'cot_data': cot,
            'breakdown': {name: round(score, 3) for name, score, _ in scores},
            'data_sources': [
                'RSS Feeds (ForexLive, DailyFX, FXStreet)',
                positioning.get('data_source', 'N/A'),
                'CFTC COT Reports' if cot.get('available') else 'N/A'
            ]
        }
