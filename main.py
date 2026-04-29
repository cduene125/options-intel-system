from config import settings
from data_fetcher import get_stock_bars
from indicators import prepare_indicators
from signal_engine import generate_signal
from options_chain_live import select_best_atm_option
from news_engine import analyze_news
from correlation_engine import analyze_correlations
from projection_engine import build_projection
from trade_plan import build_trade_plan


def fmt(x):
    return "N/A" if x is None else f"{x:.2f}"


def main():
    symbol = settings.default_symbol
    print(f"\nScanning {symbol} with V4 market intelligence...\n")

    # Get data + signal
    bars = get_stock_bars(symbol, settings.default_timeframe_minutes, settings.lookback_days)
    df = prepare_indicators(bars, settings.opening_range_minutes)
    signal = generate_signal(df, symbol)

    # Intelligence layers
    option = select_best_atm_option(symbol, signal.latest_price, signal.bias, settings.default_dte)
    news = analyze_news(10)
    corr = analyze_correlations(signal.bias)
    proj = build_projection(signal, df)

    # Final trade plan
    plan = build_trade_plan(
        signal,
        option,
        news,
        corr,
        proj,
        settings.min_entry_confidence,
        settings.option_stop_loss_pct,
        settings.option_profit_target_pct,
    )

    # ==============================
    print("==============================")
    print(f"Ticker: {signal.symbol}")
    print(f"Price: {signal.latest_price:.2f} | VWAP: {signal.vwap:.2f} | ATR: {fmt(signal.atr)}")
    print(f"Bias: {signal.bias} | Base Confidence: {signal.confidence}/100 | Final Score: {plan.final_score}/100")
    print(f"Action: {plan.action_label}")
    print(f"Entry Indicator: {plan.entry_indicator}")
    print(f"Exit Indicator: {plan.exit_indicator}")

    print("------------------------------")
    print("Market Intelligence:")
    print(f"News: {news.sentiment} | Risk: {news.risk_level} | Adj: {news.score_adjustment:+d}")
    print(f"Correlation: {corr.confirmation_label} | Adj: {corr.score_adjustment:+d}")
    print(f"Projection: {proj.projection_label} | Adj: {proj.score_adjustment:+d}")

    print("------------------------------")
    print("Contract:")
    if option:
        print(f"{option.symbol} | {option.option_type} | DTE {option.dte} | Exp {option.expiration} | Strike {option.strike}")
        print(f"Bid {fmt(option.bid)} | Ask {fmt(option.ask)} | Mid {fmt(option.mid)}")
        print(f"Quality {option.quality_label} ({option.quality_score}/100)")
    else:
        print("No contract selected.")

    print("------------------------------")
    print("Entry / Exit Plan:")
    print(f"Entry Zone: {plan.contract_entry_zone}")
    print(f"Stop: {plan.contract_stop}")
    print(f"Target 1: {plan.contract_target_1}")
    print(f"Target 2: {plan.contract_target_2}")
    print(f"Underlying Stop: {fmt(plan.underlying_stop)}")
    print(f"Underlying Target 1: {fmt(plan.underlying_target_1)}")
    print(f"Underlying Target 2: {fmt(plan.underlying_target_2)}")

    print("------------------------------")
    print("Correlation Details:")
    for d in corr.details:
        print(f"- {d}")

    print("------------------------------")
    print("Recent Headlines:")
    if news.headlines:
        for h in news.headlines[:5]:
            print(f"- {h}")
    else:
        print("- NewsAPI inactive or no headlines returned.")

    print("------------------------------")
    print("Reasons:")
    for r in plan.reasons:
        print(f"- {r}")

    if plan.warnings:
        print("------------------------------")
        print("Warnings:")
        for w in plan.warnings:
            print(f"- {w}")

    print("==============================\n")


if __name__ == "__main__":
    main()