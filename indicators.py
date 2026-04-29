import pandas as pd
def add_ema(df, spans=(9,21)):
    out=df.copy()
    for span in spans: out[f'ema_{span}']=out['close'].ewm(span=span, adjust=False).mean()
    return out
def add_session_vwap(df):
    out=df.copy(); out['date']=out['timestamp'].dt.date
    tp=(out['high']+out['low']+out['close'])/3
    out['tp_x_volume']=tp*out['volume']; out['cum_tp_x_volume']=out.groupby('date')['tp_x_volume'].cumsum(); out['cum_volume']=out.groupby('date')['volume'].cumsum(); out['session_vwap']=out['cum_tp_x_volume']/out['cum_volume']
    return out
def add_relative_volume(df, window=20):
    out=df.copy(); out['avg_volume']=out['volume'].rolling(window).mean(); out['relative_volume']=out['volume']/out['avg_volume']; return out
def add_atr(df, window=14):
    out=df.copy(); pc=out['close'].shift(1); tr1=out['high']-out['low']; tr2=(out['high']-pc).abs(); tr3=(out['low']-pc).abs(); out['true_range']=pd.concat([tr1,tr2,tr3],axis=1).max(axis=1); out['atr']=out['true_range'].rolling(window).mean(); return out
def add_opening_range(df, opening_range_minutes=15):
    out=df.copy(); out['date']=out['timestamp'].dt.date; out['minute_of_day']=out['timestamp'].dt.hour*60+out['timestamp'].dt.minute
    mo=9*60+30; oe=mo+opening_range_minutes
    out['is_opening_range']=(out['minute_of_day']>=mo)&(out['minute_of_day']<oe)
    opening=out[out['is_opening_range']].groupby('date').agg(opening_range_high=('high','max'), opening_range_low=('low','min')).reset_index()
    return out.merge(opening,on='date',how='left')
def prepare_indicators(df, opening_range_minutes=15):
    return add_opening_range(add_atr(add_relative_volume(add_session_vwap(add_ema(df)))), opening_range_minutes)
