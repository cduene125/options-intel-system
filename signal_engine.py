from dataclasses import dataclass
from typing import List
import pandas as pd
@dataclass
class SignalResult:
    symbol:str; bias:str; confidence:int; suggested_trade:str; reasons:List[str]; warnings:List[str]; latest_price:float; vwap:float; atr:float|None; opening_range_high:float|None; opening_range_low:float|None; entry_trigger:float|None; invalidation_level:float|None; underlying_target_1:float|None; underlying_target_2:float|None
def generate_signal(df, symbol='SPY'):
    l=df.iloc[-1]; price=float(l['close']); vwap=float(l['session_vwap']); ema9=float(l['ema_9']); ema21=float(l['ema_21']); atr=None if pd.isna(l.get('atr')) else float(l.get('atr'))
    oh=l.get('opening_range_high'); ol=l.get('opening_range_low'); rvol=l.get('relative_volume')
    bull=bear=0; reasons=[]; warnings=[]
    if price>vwap: bull+=20; reasons.append('Price is above VWAP')
    elif price<vwap: bear+=20; reasons.append('Price is below VWAP')
    if ema9>ema21: bull+=20; reasons.append('9 EMA is above 21 EMA')
    elif ema9<ema21: bear+=20; reasons.append('9 EMA is below 21 EMA')
    if pd.notna(oh) and price>float(oh): bull+=25; reasons.append('Price is above opening range high')
    elif pd.notna(ol) and price<float(ol): bear+=25; reasons.append('Price is below opening range low')
    else: warnings.append('Price has not clearly broken the opening range')
    if pd.notna(rvol):
        r=float(rvol)
        if r>=1.5: bull+=10; bear+=10; reasons.append(f'Relative volume is strong at {r:.2f}x')
        elif r<0.8: warnings.append(f'Relative volume is weak at {r:.2f}x')
    rng=float(l['high']-l['low'])
    if rng>0:
        pos=float((l['close']-l['low'])/rng)
        if pos>=.7: bull+=10; reasons.append('Latest candle closed near its high')
        elif pos<=.3: bear+=10; reasons.append('Latest candle closed near its low')
    if abs(price-vwap)/price<.001: warnings.append('Price is very close to VWAP, possible chop zone')
    if bull>=bear+15 and bull>=50:
        bias='CALL'; conf=min(100,bull); trig=float(oh) if pd.notna(oh) else price; inv=max(vwap,float(ol)) if pd.notna(ol) else vwap; t1=price+(atr*.5 if atr else price*.002); t2=price+(atr if atr else price*.004); sug='CALL watch: enter only if market intelligence confirms.'
    elif bear>=bull+15 and bear>=50:
        bias='PUT'; conf=min(100,bear); trig=float(ol) if pd.notna(ol) else price; inv=min(vwap,float(oh)) if pd.notna(oh) else vwap; t1=price-(atr*.5 if atr else price*.002); t2=price-(atr if atr else price*.004); sug='PUT watch: enter only if market intelligence confirms.'
    else:
        bias='NO TRADE'; conf=max(bull,bear); trig=inv=t1=t2=None; sug='Wait. Conditions are mixed or not strong enough.'
    return SignalResult(symbol,bias,int(conf),sug,reasons,warnings,price,vwap,atr,None if pd.isna(oh) else float(oh),None if pd.isna(ol) else float(ol),trig,inv,t1,t2)
