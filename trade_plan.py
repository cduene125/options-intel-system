from dataclasses import dataclass
from typing import Optional
@dataclass
class TradePlan:
    action:str; action_label:str; final_score:int; entry_indicator:str; exit_indicator:str; contract_entry_zone:str; contract_stop:str; contract_target_1:str; contract_target_2:str; underlying_stop:Optional[float]; underlying_target_1:Optional[float]; underlying_target_2:Optional[float]; reasons:list; warnings:list
def build_trade_plan(signal, option, news, correlation, projection, min_entry_confidence=80, stop_loss_pct=.30, profit_target_pct=.50):
    warnings=list(signal.warnings)+news.warnings+correlation.warnings+projection.warnings
    final=max(0,min(100,signal.confidence+news.score_adjustment+correlation.score_adjustment+projection.score_adjustment))
    if signal.bias=='NO TRADE' or option is None: return TradePlan('WAIT','NO TRADE',final,'Do not enter. Primary signal is not strong enough.','No position.','N/A','N/A','N/A','N/A',None,None,None,signal.reasons,warnings)
    reasons=[f'Base technical confidence: {signal.confidence}/100.', news.summary, f'Correlation: {correlation.confirmation_label} ({correlation.score_adjustment:+d}).', f'Projection: {projection.projection_label} ({projection.score_adjustment:+d}).']+signal.reasons+projection.notes
    if option.quality_score<70: warnings.append(f'Option quality weak/unverified: {option.quality_label} at {option.quality_score}/100.')
    trigger_ok=(signal.bias=='CALL' and signal.entry_trigger and signal.latest_price>=signal.entry_trigger) or (signal.bias=='PUT' and signal.entry_trigger and signal.latest_price<=signal.entry_trigger)
    if not trigger_ok: warnings.append('Underlying has not confirmed the trigger yet.')
    high_news=news.risk_level=='HIGH'; conflict=correlation.confirmation_label=='CONFLICTING MARKET'; chop=any('chop' in w.lower() for w in warnings)
    if high_news or conflict: action='AVOID'; label=f'AVOID {signal.bias}'; entry='Avoid entry: market intelligence risk is too high.'
    elif final>=min_entry_confidence and option.quality_score>=70 and trigger_ok and not chop: action='ENTER'; label=f'ENTER {signal.bias}'; entry=f'Entry indicator ON: {signal.bias} contract acceptable while underlying holds trigger.'
    elif final>=70: action='WATCH'; label=f'WATCH {signal.bias}'; entry=f'Watch only: wait for cleaner confirmation before entering {signal.bias}.'
    else: action='WAIT'; label='WAIT'; entry='Wait. Score is not strong enough.'
    if option.mid:
        entry_zone=f'${(option.bid or option.mid*.98):.2f} to ${(option.ask or option.mid*1.02):.2f}; avoid chasing above ask.'; stop=f'Premium stop near ${option.mid*(1-stop_loss_pct):.2f} or if underlying breaks invalidation.'; t1=f'First target near ${option.mid*(1+profit_target_pct):.2f}.'; t2=f'Runner target near ${option.mid*(1+profit_target_pct*2):.2f} or trail after target 1.'
    else:
        entry_zone='No live option quote. Check broker bid/ask before entry.'; stop=f'Cut if premium drops about {int(stop_loss_pct*100)}% or underlying breaks invalidation.'; t1=f'Take partial around {int(profit_target_pct*100)}% premium gain.'; t2='Trail runner after target 1 or exit if momentum fades.'
    exit_ind=('Exit CALL if SPY loses VWAP/invalidation, correlated market turns against you, or option hits stop/target.' if signal.bias=='CALL' else 'Exit PUT if SPY reclaims VWAP/invalidation, correlated market turns against you, or option hits stop/target.')
    return TradePlan(action,label,final,entry,exit_ind,entry_zone,stop,t1,t2,signal.invalidation_level,signal.underlying_target_1,signal.underlying_target_2,reasons,warnings+([option.warning] if option.warning else []))
