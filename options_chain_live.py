from dataclasses import dataclass
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from typing import Optional
from broker_api import get_option_contracts,get_latest_option_quotes
EASTERN=ZoneInfo('America/New_York')
@dataclass
class OptionSelection:
    source:str; underlying:str; option_type:str; dte:int; expiration:str; strike:float; symbol:str; bid:Optional[float]; ask:Optional[float]; mid:Optional[float]; spread:Optional[float]; spread_pct:Optional[float]; quality_score:int; quality_label:str; warning:str
def next_trading_expiration(dte=0):
    exp=datetime.now(tz=EASTERN).date()+timedelta(days=dte)
    if exp.weekday()==5: exp+=timedelta(days=2)
    if exp.weekday()==6: exp+=timedelta(days=1)
    return exp
def nearest_atm_strike(symbol,price):
    return float(round(price)) if symbol.upper() in {'SPY','QQQ','IWM'} or price<100 else float(round(price/5)*5 if price<500 else round(price/10)*10)
def build_occ_symbol(root,expiration,option_type,strike):
    return f"{root.upper().ljust(6)}{expiration.strftime('%y%m%d')}{'C' if option_type=='CALL' else 'P'}{int(round(strike*1000)):08d}"
def sf(v):
    try: return None if v is None else float(v)
    except Exception: return None
def extract_contracts(p):
    if isinstance(p,dict):
        for k in ['option_contracts','contracts','data']:
            if isinstance(p.get(k),list): return p[k]
    return p if isinstance(p,list) else []
def c_sym(c): return c.get('symbol') or c.get('id') or c.get('option_symbol')
def c_strike(c): return sf(c.get('strike_price') or c.get('strike'))
def q_for(p,s):
    q=p.get('quotes') or p.get('data') or p if isinstance(p,dict) else {}; return q.get(s) or q.get(s.strip()) or {} if isinstance(q,dict) else {}
def bidask(q): return sf(q.get('bid_price') or q.get('bp') or q.get('bid') or q.get('b')), sf(q.get('ask_price') or q.get('ap') or q.get('ask') or q.get('a'))
def quality(bid,ask,spct):
    if not bid or not ask or bid<=0 or ask<=0: return 30,'Needs broker check','No valid live bid/ask returned. Verify manually.'
    score=70
    if spct is not None:
        score += 30 if spct<=.05 else 20 if spct<=.1 else 10 if spct<=.15 else -15
    score=max(0,min(100,score)); label='A quality' if score>=85 else 'Acceptable' if score>=70 else 'Use caution' if score>=50 else 'Avoid'
    return score,label, 'Wide option spread.' if spct and spct>.15 else ''
def select_best_atm_option(underlying,price,bias,dte=0):
    if bias not in {'CALL','PUT'}: return None
    exp=next_trading_expiration(dte); atm=nearest_atm_strike(underlying,price); opt='call' if bias=='CALL' else 'put'; fallback=build_occ_symbol(underlying,exp,bias,atm)
    try:
        payload=get_option_contracts({'underlying_symbols':underlying.upper(),'expiration_date':exp.isoformat(),'type':opt,'status':'active','strike_price_gte':max(0,atm-5),'strike_price_lte':atm+5,'limit':100})
        cs=[c for c in extract_contracts(payload) if c_sym(c) and c_strike(c) is not None]
        if not cs: raise RuntimeError('No option contracts returned by Alpaca.')
        cs.sort(key=lambda c: abs(c_strike(c)-price)); cs=cs[:10]; quotes=get_latest_option_quotes([c_sym(c) for c in cs])
        best=None; br=-999
        for c in cs:
            sym=c_sym(c); strike=c_strike(c); bid,ask=bidask(q_for(quotes,sym)); mid=spread=spct=None
            if bid and ask and bid>0 and ask>0: mid=(bid+ask)/2; spread=ask-bid; spct=spread/mid if mid>0 else None
            qs,ql,w=quality(bid,ask,spct); rank=qs-abs(strike-price)*3
            if rank>br:
                br=rank; best=OptionSelection('Alpaca live contract + indicative quote',underlying.upper(),bias,dte,exp.isoformat(),strike,sym,bid,ask,mid,spread,spct,qs,ql,w)
        return best
    except Exception as e:
        return OptionSelection('Estimated fallback',underlying.upper(),bias,dte,exp.isoformat(),atm,fallback,None,None,None,None,None,30,'Manual verification required',f'Live option lookup failed: {e}')
