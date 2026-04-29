from dataclasses import dataclass
from data_fetcher import get_many_latest_bars
from indicators import prepare_indicators
from config import settings
@dataclass
class CorrelationResult:
    score_adjustment:int; confirmation_label:str; details:list; warnings:list
def trend_for(df):
    d=prepare_indicators(df,15); l=d.iloc[-1]; price=float(l['close']); vwap=float(l['session_vwap']); ema9=float(l['ema_9']); ema21=float(l['ema_21']); change=price/float(d.iloc[max(0,len(d)-20)]['close'])-1 if len(d)>20 else 0
    trend='BULLISH' if price>vwap and ema9>ema21 else 'BEARISH' if price<vwap and ema9<ema21 else 'MIXED'
    return trend,change
def analyze_correlations(primary_bias, symbols=None):
    if primary_bias=='NO TRADE': return CorrelationResult(0,'NO TRADE',[],['No correlation check needed because primary signal is NO TRADE.'])
    data=get_many_latest_bars(list(symbols or settings.correlation_symbols),5,2); details=[]; warnings=[]; confirms=conflicts=0
    for s,r in data.items():
        if isinstance(r,Exception): warnings.append(f'{s}: could not load data: {r}'); continue
        try:
            t,ch=trend_for(r); details.append(f'{s}: {t}, 20-bar move {ch:.2%}')
            if s in {'VXX','VIXY'}:
                if primary_bias=='CALL' and t=='BEARISH': confirms+=1
                elif primary_bias=='PUT' and t=='BULLISH': confirms+=1
                elif t!='MIXED': conflicts+=1
            elif primary_bias=='CALL' and t=='BULLISH': confirms+=1
            elif primary_bias=='PUT' and t=='BEARISH': confirms+=1
            elif t!='MIXED': conflicts+=1
        except Exception as e: warnings.append(f'{s}: correlation calculation failed: {e}')
    if confirms>=4 and conflicts<=1: return CorrelationResult(10,'STRONG CONFIRMATION',details,warnings)
    if confirms>=2 and conflicts<=2: return CorrelationResult(5,'MODERATE CONFIRMATION',details,warnings)
    if conflicts>=3: warnings.append('Several correlated assets disagree with the primary signal.'); return CorrelationResult(-10,'CONFLICTING MARKET',details,warnings)
    warnings.append('Correlation confirmation is weak.'); return CorrelationResult(0,'WEAK CONFIRMATION',details,warnings)
