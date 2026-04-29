from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from config import settings
EASTERN=ZoneInfo('America/New_York')
def _timeframe(minutes:int)->TimeFrame: return TimeFrame(minutes, TimeFrameUnit.Minute)
def get_stock_bars(symbol='SPY', timeframe_minutes=1, lookback_days=5):
    if not settings.alpaca_api_key or not settings.alpaca_secret_key: raise ValueError('Missing Alpaca API keys in .env')
    client=StockHistoricalDataClient(api_key=settings.alpaca_api_key, secret_key=settings.alpaca_secret_key)
    end=datetime.now(tz=EASTERN); start=end-timedelta(days=lookback_days)
    req=StockBarsRequest(symbol_or_symbols=symbol, timeframe=_timeframe(timeframe_minutes), start=start, end=end, adjustment='raw', feed='iex')
    bars=client.get_stock_bars(req).df
    if bars.empty: raise RuntimeError(f'No bars returned for {symbol}')
    bars=bars.reset_index()
    if 'symbol' not in bars.columns: bars['symbol']=symbol
    bars['timestamp']=pd.to_datetime(bars['timestamp'], utc=True).dt.tz_convert(EASTERN)
    return bars[bars['symbol']==symbol].sort_values('timestamp').reset_index(drop=True)
def get_many_latest_bars(symbols, timeframe_minutes=5, lookback_days=2):
    out={}
    for s in symbols:
        try: out[s]=get_stock_bars(s,timeframe_minutes,lookback_days)
        except Exception as e: out[s]=e
    return out
