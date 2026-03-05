"""
Analisi Sentiment
"""

from datetime import datetime
from textblob import TextBlob
from collections import Counter
from .data_providers import FreeDataProvider


class SentimentAnalyzer:
    """Analizzatore sentiment"""
    
    def __init__(self, pair: str):
        self.pair = pair.replace("=X", "")
        self.news = []
        
    def analyze_news_sentiment(self) -> dict:
        """Analizza sentiment delle news"""
        news = FreeDataProvider.fetch_forex_news(self.pair, limit=20)
        self.news = news
        
        if not news:
            return {
                'score': 0,
                'news_count': 0,
                'sentiment_distribution': {},
                'analyzed_news': [],
                'overall_sentiment': 'NEUTRAL'
            }
        
        analyzed = []
        polarities = []
        
        for article in news:
            text = article['title'] + ' ' + article.get('summary', '')
            
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                subjectivity = blob.sentiment.subjectivity
                
                if polarity > 0.15:
                    sentiment = 'BULLISH'
                elif polarity < -0.15:
                    sentiment = 'BEARISH'
                else:
                    sentiment = 'NEUTRAL'
                
                polarities.append(polarity)
                
                analyzed.append({
                    'title': article['title'][:100],
                    'source': article['source'],
                    'polarity': round(polarity, 3),
                    'subjectivity': round(subjectivity, 3),
                    'sentiment': sentiment,
                    'link': article.get('link', '')
                })
                
            except Exception as e:
                continue
        
        if not polarities:
            avg_polarity = 0
        else:
            avg_polarity = sum(polarities) / len(polarities)
        
        sentiment_counts = Counter([a['sentiment'] for a in analyzed])
        
        # Overall
        if avg_polarity > 0.1:
            overall = 'BULLISH'
        elif avg_polarity < -0.1:
            overall = 'BEARISH'
        else:
            overall = 'NEUTRAL'
        
        return {
            'score': round(avg_polarity, 3),
            'news_count': len(analyzed),
            'sentiment_distribution': dict(sentiment_counts),
            'analyzed_news': analyzed[:10],
            'overall_sentiment': overall
        }
    
    def get_retail_sentiment(self) -> dict:
        """Recupera sentiment retail"""
        data = FreeDataProvider.get_retail_sentiment(self.pair)
        return data
    
    def get_cot_analysis(self) -> dict:
        """Analisi COT data"""
        cot_data = FreeDataProvider.get_cot_data()
        
        base = self.pair[:3]
        
        if base in cot_data:
            data = cot_data[base]
            
            return {
                'available': True,
                'currency': base,
                'non_commercial_long': data['non_commercial_long'],
                'non_commercial_short': data['non_commercial_short'],
                'net_speculative': data['net_speculative'],
                'bias': data['bias'],
                'source': 'CFTC Weekly Report'
            }
        
        return {
            'available': False,
            'currency': base,
            'note': 'COT data not available for this currency'
        }
    
    def get_sentiment_score(self) -> dict:
        """Calcola punteggio sentiment complessivo"""
        
        # 1. News sentiment
        news_analysis = self.analyze_news_sentiment()
        news_score = news_analysis['score']
        
        # 2. Retail sentiment (contrarian)
        retail = self.get_retail_sentiment()
        
        retail_score = 0
        if retail.get('real_data'):
            if retail['contrarian_signal'] == 'BULLISH':
                retail_score = 0.5
            elif retail['contrarian_signal'] == 'BEARISH':
                retail_score = -0.5
        
        # 3. COT sentiment (institutional)
        cot = self.get_cot_analysis()
        
        cot_score = 0
        if cot.get('available'):
            if cot['bias'] == 'BULLISH':
                cot_score = 0.6
            elif cot['bias'] == 'BEARISH':
                cot_score = -0.6
        
        # Combina con pesi
        # News: 35%, Retail Contrarian: 30%, COT: 35%
        final_score = (news_score * 0.35) + (retail_score * 0.30) + (cot_score * 0.35)
        final_score = max(-1, min(1, final_score))
        
        # Probabilità
        probability_bull = ((final_score + 1) / 2) * 100
        
        # Direzione
        if final_score > 0.2:
            direction = 'BULLISH'
        elif final_score > 0.05:
            direction = 'SLIGHTLY BULLISH'
        elif final_score < -0.2:
            direction = 'BEARISH'
        elif final_score < -0.05:
            direction = 'SLIGHTLY BEARISH'
        else:
            direction = 'NEUTRAL'
        
        return {
            'score': round(final_score, 3),
            'probability_bull': round(probability_bull, 1),
            'probability_bear': round(100 - probability_bull, 1),
            'direction': direction,
            'news_analysis': news_analysis,
            'retail_sentiment': retail,
            'cot_analysis': cot,
            'breakdown': {
                'news': round(news_score, 3),
                'retail_contrarian': round(retail_score, 3),
                'cot_institutional': round(cot_score, 3)
            },
            'data_sources': ['RSS News Feeds', 'MyFxBook', 'CFTC COT']
        }
