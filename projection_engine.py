from dataclasses import dataclass
@dataclass
class ProjectionResult:
    projection_label:str; score_adjustment:int; expected_move:float|None; projected_upside:float|None; projected_downside:float|None; notes:list; warnings:list
def build_projection(signal,df):
    notes=[]; warnings=[]
    if signal.atr is None: return ProjectionResult('UNKNOWN',0,None,None,None,[],['ATR unavailable, projection quality reduced.'])
    price=signal.latest_price; atr=signal.atr; up=price+atr; down=price-atr
    if signal.opening_range_high is not None and signal.opening_range_low is not None:
        width=signal.opening_range_high-signal.opening_range_low; notes.append(f'Opening range width: {width:.2f}')
        if width>atr*1.5: warnings.append('Opening range is wide versus ATR. Chasing may be risky.'); return ProjectionResult('WIDE RANGE / CHASE RISK',-5,atr,up,down,notes+[f'ATR expected move: {atr:.2f}'],warnings)
    label='UPSIDE ROOM' if signal.bias=='CALL' else 'DOWNSIDE ROOM' if signal.bias=='PUT' else 'NEUTRAL'; adj=5 if signal.bias in {'CALL','PUT'} else 0
    notes += [f'ATR expected move: {atr:.2f}', f'Projected upside: {up:.2f}', f'Projected downside: {down:.2f}']
    return ProjectionResult(label,adj,atr,up,down,notes,warnings)
