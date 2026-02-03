import time
import random
import os
import requests
from pytrends.request import TrendReq

def get_trends(geo='US', count=2):
    """
    Fetches real-time trends. Returns None on 429/404/Block.
    """
    print("Fetching trends...")
    results = []
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25))
        df = pytrends.realtime_trending_searches(pn=geo)
        
        if df is None or df.empty:
            print("No trends returned.")
            return None
            
        print(f"Found {len(df)} trends. Taking top {count}.")
        
        for i in range(min(count, len(df))):
            row = df.iloc[i]
            title = row['title']
            # Safely get article URL
            article_urls = row.get('article_urls', [])
            url = article_urls[0] if isinstance(article_urls, list) and article_urls else '#'
            
            results.append({
                'title': title,
                'url': url
            })
            
        return results

    except Exception as e:
        msg = str(e)
        print(f"Trends error: {msg}")

    # Fallback to NewsAPI
    print("[INFO] Switch to NewsAPI Fallback...")
    news_key = os.getenv("NEWSAPI_API_KEY")
    if not news_key:
        print("No NewsAPI Key found.")
        return None
        
    try:
        # Fetch Top Headlines for US
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={news_key}&pageSize={count}"
        data = requests.get(url).json()
        
        articles = data.get('articles', [])
        if not articles:
            return None
            
        print(f"Recovered {len(articles)} trends from NewsAPI.")
        for art in articles:
            results.append({
                'title': art['title'],
                'url': art['url']
            })
        return results
        
    except Exception as ne:
        print(f"NewsAPI error: {ne}")
        return None
