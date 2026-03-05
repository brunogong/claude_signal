"""
Analisi del Sentiment - Versione Lite
"""
import requests
from bs4 import BeautifulSoup
import feedparser
from textblob import TextBlob
from datetime import datetime, timedelta
from collections import Counter

class SentimentAnalyzer:
    """Classe per l'analisi del sentiment (versione lite per Streamlit Cloud)"""
    
    def __init__(self, pair: str):
        self.pair = pair.replace("=X", "")
        self.news = []
        
    def fetch_news(self) -> list:
        """Recupera news dai feed RSS"""
        feeds = [
            "https://www.forexlive.com/feed/",
            "https://www.dailyfx.com/feeds/all"
        ]
        
        all_news = []
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:15]:  # Limita per performance
                    all_news.append({
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'source': feed_url
                    })
            except Exception as e:
                print(f"Errore feed: {e}")
                continue
                
        # Filtra news rilevanti
        relevant_news = []
        pair_terms = [self.pair, self.pair[:3], self.pair[3:6]]
        
        for news in all_news:
            text = (news['title'] + ' ' + news.get('summary', '')).upper()
            if any(term.upper() in text for term in pair_terms):
                relevant_news.append(news)
                
        self.news = relevant_news[:10] if relevant_news else all_news[:5]
        return self.news
    
    def analyze_news_sentiment(self) -> dict:
        """Analizza il sentiment con TextBlob"""
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
                    **news,
                    'polarity': polarity,
                    'sentiment': sentiment
                })
            except:
                continue
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        sentiment_counts = Counter([n['sentiment'] for n in analyzed_news])
        
        return {
            'average_polarity': avg_sentiment,
            'news_count': len(analyzed_news),
            'sentiment_distribution': dict(sentiment_counts),
            'overall_sentiment': 'BULLISH' if avg_sentiment > 0.05 else ('BEARISH' if avg_sentiment < -0.05 else 'NEUTRAL')
        }
    
    def get_market_positioning(self) -> dict:
        """Simula dati di positioning"""
        import random
        random.seed(hash(self.pair + datetime.now().strftime('%Y-%m-%d')))
        
        long_percent = random.uniform(30, 70)
        
        return {
            'retail': {
                'long_percent': long_percent,
                'short_percent': 100 - long_percent,
                'sentiment': 'BULLISH' if long_percent > 55 else 'BEARISH',
                'contrarian_signal': 'BEARISH' if long_percent > 60 else ('BULLISH' if long_percent < 40 else 'NEUTRAL')
            }
        }
    
    def get_sentiment_score(self) -> dict:
        """Calcola punteggio sentiment"""
        news_sentiment = self.analyze_news_sentiment()
        positioning = self.get_market_positioning()
        
        # Score semplificato
        news_score = news_sentiment['average_polarity']
        pos_score = 0.3 if positioning['retail']['contrarian_signal'] == 'BULLISH' else -0.3
        
        final_score = news_score * 0.7 + pos_score * 0.3
        
        return {
            'score': final_score,
            'probability_bull': ((final_score + 1) / 2) * 100,
            'direction': 'BULLISH' if final_score > 0.1 else ('BEARISH' if final_score < -0.1 else 'NEUTRAL'),
            'news_sentiment': news_sentiment,
            'market_positioning': positioning
        }
