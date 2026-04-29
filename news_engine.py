from dataclasses import dataclass
from datetime import datetime,timedelta,timezone
import requests
from config import settings
@dataclass
class NewsResult:
    sentiment:str; score_adjustment:int; risk_level:str; headlines:list; warnings:list; summary:str
BULL=['rally','surge','beats','cooling inflation','rate cut','strong growth','soft landing','upgrade','optimism']
BEAR=['selloff','plunge','misses','recession','hot inflation','rate hike','hawkish','downgrade','war','tariff','weak demand']
HIGH=['cpi','inflation','fomc','fed','powell','jobs report','pce','gdp','treasury yields','rate decision']
def score_text(t):
    l=t.lower(); s=sum(w in l for w in BULL)-sum(w in l for w in BEAR); h=any(w in l for w in HIGH); return s,h
def fetch_newsapi_headlines(limit=10):
    if not settings.news_api_key: return []
    try:
        r=requests.get('https://newsapi.org/v2/everything',params={'q':'SPY OR S&P 500 OR Federal Reserve OR inflation OR stock market','language':'en','sortBy':'publishedAt','pageSize':limit,'from':(datetime.now(timezone.utc)-timedelta(days=2)).date().isoformat(),'apiKey':settings.news_api_key},timeout=12); r.raise_for_status(); return [a.get('title','') for a in r.json().get('articles',[]) if a.get('title')]
    except Exception as e: return [f'NewsAPI lookup failed: {e}']
def analyze_news(limit=10):
    headlines=fetch_newsapi_headlines(limit); warnings=[]
    if not headlines: return NewsResult('NEUTRAL',0,'UNKNOWN',[],['No NewsAPI key found. News sentiment inactive. Add NEWS_API_KEY to .env.'],'News layer inactive. Using technicals and correlation only.')
    score=0; hi=0
    for h in headlines:
        s,b=score_text(h); score+=s; hi+=int(b)
    sent='BULLISH' if score>=2 else 'BEARISH' if score<=-2 else 'NEUTRAL'; adj=5 if sent=='BULLISH' else -5 if sent=='BEARISH' else 0
    risk='HIGH' if hi>=2 else 'MEDIUM' if hi==1 else 'LOW'
    if risk=='HIGH': warnings.append('Multiple high-impact macro/news keywords detected. Reduce size or wait.'); adj-=5
    elif risk=='MEDIUM': warnings.append('One high-impact macro/news keyword detected.')
    return NewsResult(sent,adj,risk,headlines,warnings,f'News sentiment: {sent}; risk level: {risk}; adjustment: {adj}.')
