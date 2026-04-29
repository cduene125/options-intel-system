import streamlit as st
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

from config import settings
from data_fetcher import get_stock_bars
from indicators import prepare_indicators
from signal_engine import generate_signal
from options_chain_live import select_best_atm_option
from news_engine import analyze_news
from correlation_engine import analyze_correlations
from projection_engine import build_projection
from trade_plan import build_trade_plan


def fmt_money(x):
    return "N/A" if x is None else f"${x:.2f}"


st.set_page_config(page_title="Options Intel System", layout="wide")
st.title("Options Intel System")
st.caption("Technical signal + option contract + news + correlation + projection intelligence.")

with st.sidebar:
    st.header("Scanner Settings")
    symbol = st.text_input("Ticker", value=settings.default_symbol)
    timeframe = st.selectbox("Candle Timeframe", options=[1, 5, 15], index=0)
    dte = st.selectbox("DTE", options=[0, 1, 2, 3], index=0)

    st.header("Risk Settings")
    min_conf = st.slider("Min Entry Score", min_value=50, max_value=100, value=settings.min_entry_confidence)
    stop_loss_pct = st.slider("Option Stop Loss %", min_value=10, max_value=70, value=30) / 100
    profit_target_pct = st.slider("Option Profit Target %", min_value=10, max_value=200, value=50) / 100

    st.header("Auto Refresh")
    auto_refresh = st.toggle("Enable auto-refresh", value=True)
    refresh_seconds = st.selectbox("Refresh every", options=[15, 30, 60, 120, 300], index=2)

    run_scan = st.button("Run Scan Now", type="primary")

if auto_refresh:
    st_autorefresh(interval=refresh_seconds * 1000, key="market_auto_refresh")

should_run = run_scan or auto_refresh

if should_run:
    try:
        bars = get_stock_bars(symbol.upper(), timeframe, settings.lookback_days)
        df = prepare_indicators(bars, settings.opening_range_minutes)
        signal = generate_signal(df, symbol.upper())
        option = select_best_atm_option(symbol.upper(), signal.latest_price, signal.bias, dte=dte)
        news = analyze_news(10)
        corr = analyze_correlations(signal.bias)
        proj = build_projection(signal, df)

        plan = build_trade_plan(
            signal,
            option,
            news,
            corr,
            proj,
            min_conf,
            stop_loss_pct,
            profit_target_pct,
        )

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Action", plan.action_label)
        col2.metric("Bias", signal.bias)
        col3.metric("Final Score", f"{plan.final_score}/100")
        col4.metric("Price", fmt_money(signal.latest_price))
        col5.metric("VWAP", fmt_money(signal.vwap))

        if plan.action == "ENTER":
            st.success(plan.entry_indicator)
        elif plan.action == "AVOID":
            st.error(plan.entry_indicator)
        elif plan.action == "WATCH":
            st.warning(plan.entry_indicator)
        else:
            st.info(plan.entry_indicator)

        st.write(f"**Exit Indicator:** {plan.exit_indicator}")

        st.subheader("Market Intelligence")
        m1, m2, m3 = st.columns(3)
        m1.metric("News", f"{news.sentiment} / {news.risk_level}", f"{news.score_adjustment:+d}")
        m2.metric("Correlation", corr.confirmation_label, f"{corr.score_adjustment:+d}")
        m3.metric("Projection", proj.projection_label, f"{proj.score_adjustment:+d}")

        st.subheader("Contract Selection")
        if option:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Contract", option.symbol)
            c2.metric("Strike", fmt_money(option.strike))
            c3.metric("Bid", fmt_money(option.bid))
            c4.metric("Ask", fmt_money(option.ask))
            c5.metric("Quality", f"{option.quality_score}/100")
            st.write(f"**Source:** {option.source}")
            st.write(f"**Quality Label:** {option.quality_label}")
            if option.spread_pct is not None:
                st.write(f"**Spread:** {option.spread_pct:.1%}")
        else:
            st.warning("No contract selected because signal is NO TRADE.")

        st.subheader("Entry / Exit Plan")
        p1, p2, p3, p4 = st.columns(4)

        p1.write("**Entry Zone**")
        p1.write(plan.contract_entry_zone)

        p2.write("**Stop**")
        p2.write(plan.contract_stop)

        p3.write("**Target 1**")
        p3.write(plan.contract_target_1)

        p4.write("**Target 2**")
        p4.write(plan.contract_target_2)

        u1, u2, u3 = st.columns(3)
        u1.metric("Underlying Stop", fmt_money(plan.underlying_stop))
        u2.metric("Underlying Target 1", fmt_money(plan.underlying_target_1))
        u3.metric("Underlying Target 2", fmt_money(plan.underlying_target_2))

        left, right = st.columns([2, 1])

        with left:
            st.subheader("Chart")

            fig = go.Figure()
            fig.add_trace(
                go.Candlestick(
                    x=df["timestamp"],
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    name="Price",
                )
            )

            fig.add_trace(go.Scatter(x=df["timestamp"], y=df["session_vwap"], mode="lines", name="VWAP"))
            fig.add_trace(go.Scatter(x=df["timestamp"], y=df["ema_9"], mode="lines", name="EMA 9"))
            fig.add_trace(go.Scatter(x=df["timestamp"], y=df["ema_21"], mode="lines", name="EMA 21"))

            if signal.opening_range_high is not None:
                fig.add_hline(y=signal.opening_range_high, line_dash="dash", annotation_text="OR High")
            if signal.opening_range_low is not None:
                fig.add_hline(y=signal.opening_range_low, line_dash="dash", annotation_text="OR Low")
            if signal.entry_trigger is not None:
                fig.add_hline(y=signal.entry_trigger, line_dash="dot", annotation_text="Entry Trigger")
            if signal.invalidation_level is not None:
                fig.add_hline(y=signal.invalidation_level, line_dash="dot", annotation_text="Invalidation")
            if signal.underlying_target_1 is not None:
                fig.add_hline(y=signal.underlying_target_1, line_dash="dot", annotation_text="Target 1")
            if signal.underlying_target_2 is not None:
                fig.add_hline(y=signal.underlying_target_2, line_dash="dot", annotation_text="Target 2")

            fig.update_layout(height=650, xaxis_rangeslider_visible=False, title=f"{symbol.upper()} Chart")
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("Correlation Details")
            for detail in corr.details:
                st.write(f"• {detail}")

            st.subheader("Recent Headlines")
            if news.headlines:
                for h in news.headlines[:5]:
                    st.write(f"• {h}")
            else:
                st.write("NewsAPI inactive or no headlines returned.")

            st.subheader("Reasons")
            for reason in plan.reasons[:14]:
                st.write(f"• {reason}")

            st.subheader("Warnings")
            if plan.warnings:
                for warning in plan.warnings:
                    st.write(f"• {warning}")
            else:
                st.write("No major warnings.")

    except Exception as e:
        st.error(str(e))
else:
    st.info("Click Run Scan Now or enable auto-refresh.")
