"""
Analisi del Sentiment
"""
import requests
from bs4 import BeautifulSoup
import feedparser
from textblob import TextBlob
from datetime import datetime, timedelta
import re
from collections import Counter

class SentimentAnalyzer:
    """Classe per l'analisi del sentiment"""
    
    def __init__(self, pair: str):
        self.pair = pair.replace("=X", "")
        self.news = []
        self.social_sentiment = {}
        
    def fetch_news(self) -> list:
        """Recupera news dai feed RSS"""
        feeds = [
            "https://www.forexlive.com/feed/",
            "https://www.fxstreet.com/rss/news"
        ]
        
        all_news = []
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:20]:
                    all_news.append({
                        'title': entry.get('title', ''),
                        'summary': entry.get('summary', ''),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'source': feed_url
                    })
            except Exception as e:
                print(f"Errore fetch feed {feed_url}: {e}")
                
        # Filtra news rilevanti per la coppia
        relevant_news = []
        pair_terms = [self.pair, self.pair[:3], self.pair[3:6]]
        
        for news in all_news:
            text = (news['title'] + ' ' + news['summary']).upper()
            if any(term.upper() in text for term in pair_terms):
                relevant_news.append(news)
                
        self.news = relevant_news[:10] if relevant_news else all_news[:5]
        return self.news
    
    def analyze_news_sentiment(self) -> dict:
        """Analizza il sentiment delle news"""
        if not self.news:
            self.fetch_news()
            
        sentiments = []
        analyzed_news = []
        
        for news in self.news:
            text = news['title'] + ' ' + news.get('summary', '')
            blob = TextBlob(text)
            
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            
            # Determina sentiment
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
                'subjectivity': subjectivity,
                'sentiment': sentiment
            })
        
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        
        sentiment_counts = Counter([n['sentiment'] for n in analyzed_news])
        
        return {
            'average_polarity': avg_sentiment,
            'news_count': len(analyzed_news),
            'sentiment_distribution': dict(sentiment_counts),
            'analyzed_news': analyzed_news,
            'overall_sentiment': 'BULLISH' if avg_sentiment > 0.05 else ('BEARISH' if avg_sentiment < -0.05 else 'NEUTRAL')
        }
    
    def get_market_positioning(self) -> dict:
        """Simula dati di positioning del mercato"""
        # In produzione, recuperare da API COT, IG Sentiment, etc.
        import random
        random.seed(hash(self.pair + datetime.now().strftime('%Y-%m-%d')))
        
        long_percent = random.uniform(25, 75)
        short_percent = 100 - long_percent
        
        # Sentiment retail (contrarian indicator)
        retail_sentiment = 'BULLISH' if long_percent > 55 else ('BEARISH' if long_percent < 45 else 'NEUTRAL')
        
        # Institutional positioning
        inst_long = random.uniform(40, 60)
        inst_bias = 'BULLISH' if inst_long > 52 else ('BEARISH' if inst_long < 48 else 'NEUTRAL')
        
        return {
            'retail': {
                'long_percent': long_percent,
                'short_percent': short_percent,
                'sentiment': retail_sentiment,
                'contrarian_signal': 'BEARISH' if retail_sentiment == 'BULLISH' else ('BULLISH' if retail_sentiment == 'BEARISH' else 'NEUTRAL')
            },
            'institutional': {
                'long_percent': inst_long,
                'short_percent': 100 - inst_long,
                'bias': inst_bias
            }
        }
    
    def get_social_sentiment(self) -> dict:
        """Analizza sentiment social media (simulato)"""
        import random
        random.seed(hash(self.pair + datetime.now().strftime('%Y-%m-%d-%H')))
        
        # Simula dati Twitter/X
        twitter_sentiment = random.uniform(-0.5, 0.5)
        tweet_volume = random.randint(100, 1000)
        
        # Trend topics
        trending = random.choice([True, False])
        
        return {
            'twitter': {
                'sentiment_score': twitter_sentiment,
                'sentiment': 'BULLISH' if twitter_sentiment > 0.1 else ('BEARISH' if twitter_sentiment < -0.1 else 'NEUTRAL'),
                'volume': tweet_volume,
                'trending': trending
            },
            'reddit': {
                'sentiment_score': random.uniform(-0.3, 0.3),
                'mentions': random.randint(10, 100)
            }
        }
    
    def get_fear_greed_index(self) -> dict:
        """Calcola indice Fear & Greed per forex"""
        import random
        random.seed(hash(datetime.now().strftime('%Y-%m-%d')))
        
        # Componenti dell'indice
        volatility = random.uniform(0, 100)
        momentum = random.uniform(0, 100)
        volume = random.uniform(0, 100)
        safe_haven = random.uniform(0, 100)
        
        index = (volatility * 0.25 + momentum * 0.25 + volume * 0.25 + safe_haven * 0.25)
        
        if index < 25:
            status = "Extreme Fear"
            color = "red"
        elif index < 45:
            status = "Fear"
            color = "orange"
        elif index < 55:
            status = "Neutral"
            color = "gray"
        elif index < 75:
            status = "Greed"
            color = "lightgreen"
        else:
            status = "Extreme Greed"
            color = "green"
            
        return {
            'index': index,
            'status': status,
            'color': color,
            'components': {
                'volatility': volatility,
                'momentum': momentum,
                'volume': volume,
                'safe_haven_demand': safe_haven
            }
        }
    
    def get_sentiment_score(self) -> dict:
        """Calcola punteggio sentiment complessivo"""
        news_sentiment = self.analyze_news_sentiment()
        positioning = self.get_market_positioning()
        social = self.get_social_sentiment()
        fear_greed = self.get_fear_greed_index()
        
        # Calcola score composito
        scores = []
        
        # News sentiment (25%)
        news_score = news_sentiment['average_polarity']
        scores.append(('news', news_score, 0.25))
        
        # Positioning contrarian (30%)
        pos_score = 0
        if positioning['retail']['contrarian_signal'] == 'BULLISH':
            pos_score = 0.5
        elif positioning['retail']['contrarian_signal'] == 'BEARISH':
            pos_score = -0.5
            
        if positioning['institutional']['bias'] == 'BULLISH':
            pos_score += 0.5
        elif positioning['institutional']['bias'] == 'BEARISH':
            pos_score -= 0.5
        scores.append(('positioning', pos_score, 0.30))
        
        # Social sentiment (25%)
        social_score = social['twitter']['sentiment_score']
        scores.append(('social', social_score, 0.25))
        
        # Fear & Greed (20%)
        fg_score = (fear_greed['index'] - 50) / 50  # Normalizza a [-1, 1]
        scores.append(('fear_greed', fg_score, 0.20))
        
        # Score finale
        final_score = sum(score * weight for _, score, weight in scores)
        probability_bull = ((final_score + 1) / 2) * 100
        
        return {
            'score': final_score,
            'probability_bull': probability_bull,
            'probability_bear': 100 - probability_bull,
            'direction': 'BULLISH' if final_score > 0.1 else ('BEARISH' if final_score < -0.1 else 'NEUTRAL'),
            'news_sentiment': news_sentiment,
            'market_positioning': positioning,
            'social_sentiment': social,
            'fear_greed': fear_greed,
            'breakdown': {name: score for name, score, _ in scores}
        }
