import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="글로벌 주식 비교 대시보드",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}
.stApp {
    background: #0a0d14;
    color: #e8eaf0;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f1320 !important;
    border-right: 1px solid #1e2535;
}
[data-testid="stSidebar"] * {
    font-family: 'Syne', sans-serif !important;
}

/* Header */
.main-header {
    display: flex;
    align-items: baseline;
    gap: 16px;
    margin-bottom: 8px;
}
.main-title {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    background: linear-gradient(135deg, #00d4ff 0%, #7b61ff 50%, #ff6b9d 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
}
.main-subtitle {
    font-size: 0.85rem;
    color: #4a5568;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Metric Cards */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
}
.metric-card {
    background: #111827;
    border: 1px solid #1e2535;
    border-radius: 12px;
    padding: 16px 20px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s, border-color 0.2s;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00d4ff, #7b61ff);
    opacity: 0;
    transition: opacity 0.2s;
}
.metric-card:hover {
    transform: translateY(-2px);
    border-color: #2d3748;
}
.metric-card:hover::before { opacity: 1; }
.metric-ticker {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #4a5568;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.metric-name {
    font-size: 0.82rem;
    color: #6b7280;
    margin-bottom: 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.metric-price {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.25rem;
    font-weight: 600;
    color: #f1f5f9;
    margin-bottom: 4px;
}
.metric-change-pos {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #10b981;
    font-weight: 500;
}
.metric-change-neg {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: #f43f5e;
    font-weight: 500;
}
.market-badge {
    display: inline-block;
    font-size: 0.65rem;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}
.badge-kr {
    background: rgba(0, 212, 255, 0.12);
    color: #00d4ff;
    border: 1px solid rgba(0, 212, 255, 0.25);
}
.badge-us {
    background: rgba(123, 97, 255, 0.12);
    color: #a78bfa;
    border: 1px solid rgba(123, 97, 255, 0.25);
}

/* Section Headers */
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e2e8f0;
    letter-spacing: -0.01em;
    margin: 24px 0 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, #1e2535, transparent);
}

/* Divider */
.styled-divider {
    border: none;
    border-top: 1px solid #1e2535;
    margin: 20px 0;
}

/* Rank table */
.rank-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 6px;
    background: #111827;
    border: 1px solid #1e2535;
}
.rank-num {
    font-family: 'JetBrains Mono', monospace;
    color: #4a5568;
    font-size: 0.75rem;
    width: 20px;
}
.rank-ticker {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 600;
    color: #e2e8f0;
    width: 80px;
}
.rank-name {
    font-size: 0.8rem;
    color: #6b7280;
    flex: 1;
}
.rank-ret {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.9rem;
    font-weight: 600;
}

/* Timestamp */
.timestamp {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: #374151;
    text-align: right;
    margin-top: -4px;
    margin-bottom: 12px;
}

/* Plotly container */
.stPlotlyChart > div {
    border-radius: 12px;
    overflow: hidden;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0a0d14; }
::-webkit-scrollbar-thumb { background: #1e2535; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #2d3748; }
</style>
""", unsafe_allow_html=True)

# ── Stock Universe ────────────────────────────────────────────────────────────
KR_STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "현대차": "005380.KS",
    "POSCO홀딩스": "005490.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "셀트리온": "068270.KS",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
    "LG화학": "051910.KS",
    "기아": "000270.KS",
    "삼성SDI": "006400.KS",
    "하이브": "352820.KS",
}

US_STOCKS = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Tesla": "TSLA",
    "Berkshire": "BRK-B",
    "JPMorgan": "JPM",
    "Visa": "V",
    "Walmart": "WMT",
    "ExxonMobil": "XOM",
    "UnitedHealth": "UNH",
    "Johnson&Johnson": "JNJ",
    "Netflix": "NFLX",
}

INDICES = {
    "KOSPI": "^KS11",
    "KOSDAQ": "^KQ11",
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "DOW": "^DJI",
}

PERIOD_MAP = {
    "1주": "5d",
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "3년": "3y",
    "5년": "5y",
}

# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_quote(ticker: str):
    try:
        t = yf.Ticker(ticker)
        info = t.fast_info
        hist = t.history(period="2d")
        if hist.empty:
            return None
        price = hist["Close"].iloc[-1]
        prev  = hist["Close"].iloc[-2] if len(hist) > 1 else price
        chg   = price - prev
        pct   = (chg / prev) * 100 if prev else 0
        return {"price": price, "change": chg, "pct": pct}
    except Exception:
        return None

@st.cache_data(ttl=300)
def fetch_history(ticker: str, period: str) -> pd.DataFrame:
    try:
        t = yf.Ticker(ticker)
        df = t.history(period=period)
        return df[["Close", "Volume"]] if not df.empty else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def calc_return(df: pd.DataFrame) -> float:
    if df.empty or len(df) < 2:
        return 0.0
    return ((df["Close"].iloc[-1] / df["Close"].iloc[0]) - 1) * 100

def fmt_pct(v: float) -> str:
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.2f}%"

def color_pct(v: float) -> str:
    return "metric-change-pos" if v >= 0 else "metric-change-neg"

def arrow(v: float) -> str:
    return "▲" if v >= 0 else "▼"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    st.markdown("---")

    period_label = st.selectbox("📅 조회 기간", list(PERIOD_MAP.keys()), index=3)
    period = PERIOD_MAP[period_label]

    st.markdown("---")
    st.markdown("**🇰🇷 한국 주식 선택**")
    kr_selected = st.multiselect(
        "종목 선택",
        list(KR_STOCKS.keys()),
        default=["삼성전자", "SK하이닉스", "현대차", "NAVER", "카카오"],
        label_visibility="collapsed",
    )

    st.markdown("**🇺🇸 미국 주식 선택**")
    us_selected = st.multiselect(
        "종목 선택",
        list(US_STOCKS.keys()),
        default=["Apple", "NVIDIA", "Tesla", "Amazon", "Meta"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**📊 차트 옵션**")
    chart_type = st.radio(
        "차트 종류",
        ["수익률 비교", "가격 차트", "캔들스틱"],
        label_visibility="collapsed",
    )
    show_volume = st.checkbox("거래량 표시", value=True)
    show_ma = st.checkbox("이동평균선 (20/60일)", value=True)

    st.markdown("---")
    st.caption(f"마지막 업데이트\n{datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ── Main Content ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <div class="main-title">GLOBAL STOCK DASHBOARD</div>
</div>
<div class="main-subtitle">KR &nbsp;×&nbsp; US &nbsp;·&nbsp; REAL-TIME COMPARISON</div>
<div class="timestamp">Data via Yahoo Finance · 최대 5분 캐시</div>
""", unsafe_allow_html=True)

all_selected = (
    [(n, KR_STOCKS[n], "KR") for n in kr_selected] +
    [(n, US_STOCKS[n], "US") for n in us_selected]
)

if not all_selected:
    st.warning("사이드바에서 종목을 1개 이상 선택하세요.")
    st.stop()

# ── Index Bar ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🌐 주요 지수 <div class="section-line"></div></div>', unsafe_allow_html=True)

idx_cols = st.columns(len(INDICES))
for col, (name, ticker) in zip(idx_cols, INDICES.items()):
    q = fetch_quote(ticker)
    with col:
        if q:
            cls = color_pct(q["pct"])
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-ticker">{name}</div>
              <div class="metric-price">{q['price']:,.2f}</div>
              <div class="{cls}">{arrow(q['pct'])} {fmt_pct(q['pct'])}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-ticker">{name}</div>
              <div class="metric-price">—</div>
            </div>
            """, unsafe_allow_html=True)

# ── Stock Cards ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📋 선택 종목 현황 <div class="section-line"></div></div>', unsafe_allow_html=True)

n_cols = min(len(all_selected), 5)
rows = [all_selected[i:i+n_cols] for i in range(0, len(all_selected), n_cols)]

returns_data = {}

for row in rows:
    cols = st.columns(len(row))
    for col, (name, ticker, market) in zip(cols, row):
        q = fetch_quote(ticker)
        hist = fetch_history(ticker, period)
        ret = calc_return(hist)
        returns_data[(name, ticker, market)] = ret

        badge_cls = "badge-kr" if market == "KR" else "badge-us"
        flag = "🇰🇷" if market == "KR" else "🇺🇸"
        with col:
            if q:
                cls = color_pct(q["pct"])
                ret_cls = color_pct(ret)
                price_str = f"₩{q['price']:,.0f}" if market == "KR" else f"${q['price']:,.2f}"
                st.markdown(f"""
                <div class="metric-card">
                  <div><span class="market-badge {badge_cls}">{flag} {market}</span></div>
                  <div class="metric-ticker">{ticker}</div>
                  <div class="metric-name">{name}</div>
                  <div class="metric-price">{price_str}</div>
                  <div class="{cls}">당일 {arrow(q['pct'])} {fmt_pct(q['pct'])}</div>
                  <div class="{ret_cls}" style="font-size:0.78rem;margin-top:4px;font-family:'JetBrains Mono',monospace;">
                    {period_label} {arrow(ret)} {fmt_pct(ret)}
                  </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="metric-card">
                  <div><span class="market-badge {badge_cls}">{flag} {market}</span></div>
                  <div class="metric-ticker">{ticker}</div>
                  <div class="metric-name">{name}</div>
                  <div class="metric-price">데이터 없음</div>
                </div>
                """, unsafe_allow_html=True)

# ── Chart Section ─────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">📈 {period_label} 수익률 비교 차트 <div class="section-line"></div></div>', unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0a0d14",
    plot_bgcolor="#0f1320",
    font=dict(family="JetBrains Mono, monospace", color="#6b7280", size=11),
    xaxis=dict(gridcolor="#1e2535", zerolinecolor="#1e2535", showgrid=True),
    yaxis=dict(gridcolor="#1e2535", zerolinecolor="#1e2535", showgrid=True),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(
        bgcolor="rgba(15,19,32,0.8)",
        bordercolor="#1e2535",
        borderwidth=1,
        font=dict(size=10),
    ),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="#111827",
        bordercolor="#1e2535",
        font=dict(family="JetBrains Mono, monospace", size=11),
    ),
)

COLORS_KR = ["#00d4ff", "#00b8d9", "#0ea5e9", "#38bdf8", "#7dd3fc", "#bae6fd", "#e0f2fe"]
COLORS_US = ["#a78bfa", "#7b61ff", "#8b5cf6", "#c084fc", "#e879f9", "#f472b6", "#fb7185"]

# ── Chart 1: Normalised Return Lines ─────────────────────────────────────────
if chart_type == "수익률 비교":
    fig = go.Figure()
    ki, ui = 0, 0
    for name, ticker, market in all_selected:
        hist = fetch_history(ticker, period)
        if hist.empty:
            continue
        normed = (hist["Close"] / hist["Close"].iloc[0] - 1) * 100
        color = COLORS_KR[ki % len(COLORS_KR)] if market == "KR" else COLORS_US[ui % len(COLORS_US)]
        if market == "KR":
            ki += 1
        else:
            ui += 1
        dash = "solid" if market == "KR" else "dot"
        fig.add_trace(go.Scatter(
            x=normed.index,
            y=normed.values,
            name=f"{'🇰🇷' if market=='KR' else '🇺🇸'} {name}",
            line=dict(color=color, width=1.8, dash=dash),
            hovertemplate="%{y:.2f}%<extra>" + name + "</extra>",
        ))

    fig.add_hline(y=0, line=dict(color="#374151", width=1, dash="dash"))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text=f"누적 수익률 비교 ({period_label})", font=dict(size=13, color="#9ca3af"), x=0.01),
        yaxis_title="수익률 (%)",
        height=480,
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Chart 2: Individual Price + MA ───────────────────────────────────────────
elif chart_type == "가격 차트":
    n = len(all_selected)
    ncols = 2
    nrows = (n + 1) // 2

    fig = make_subplots(
        rows=nrows, cols=ncols,
        subplot_titles=[f"{'🇰🇷' if m=='KR' else '🇺🇸'} {nm}" for nm, _, m in all_selected],
        vertical_spacing=0.08,
        horizontal_spacing=0.06,
    )

    ki, ui = 0, 0
    for idx, (name, ticker, market) in enumerate(all_selected):
        hist = fetch_history(ticker, period)
        if hist.empty:
            continue
        r = idx // ncols + 1
        c = idx % ncols + 1
        color = COLORS_KR[ki % len(COLORS_KR)] if market == "KR" else COLORS_US[ui % len(COLORS_US)]
        if market == "KR": ki += 1
        else: ui += 1

        fig.add_trace(go.Scatter(
            x=hist.index, y=hist["Close"],
            name=name, line=dict(color=color, width=1.5),
            showlegend=False,
            hovertemplate="%{y:,.2f}<extra>" + name + "</extra>",
        ), row=r, col=c)

        if show_ma and len(hist) >= 20:
            ma20 = hist["Close"].rolling(20).mean()
            fig.add_trace(go.Scatter(
                x=hist.index, y=ma20,
                name="MA20", line=dict(color="#f59e0b", width=1, dash="dash"),
                showlegend=False, hovertemplate="%{y:,.2f}<extra>MA20</extra>",
            ), row=r, col=c)
        if show_ma and len(hist) >= 60:
            ma60 = hist["Close"].rolling(60).mean()
            fig.add_trace(go.Scatter(
                x=hist.index, y=ma60,
                name="MA60", line=dict(color="#ef4444", width=1, dash="dash"),
                showlegend=False, hovertemplate="%{y:,.2f}<extra>MA60</extra>",
            ), row=r, col=c)

        if show_volume:
            fig.add_trace(go.Bar(
                x=hist.index, y=hist["Volume"],
                marker_color=color, opacity=0.25,
                showlegend=False, yaxis=f"y{idx*2+2}",
                hovertemplate="%{y:,}<extra>거래량</extra>",
            ), row=r, col=c)

    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=max(300 * nrows, 400),
        title=dict(text="개별 가격 차트", font=dict(size=13, color="#9ca3af"), x=0.01),
    )
    fig.update_annotations(font=dict(color="#9ca3af", size=11))
    st.plotly_chart(fig, use_container_width=True)

# ── Chart 3: Candlestick ─────────────────────────────────────────────────────
elif chart_type == "캔들스틱":
    selected_for_candle = st.selectbox(
        "종목 선택",
        [f"{'🇰🇷' if m=='KR' else '🇺🇸'} {n}" for n, _, m in all_selected],
        label_visibility="visible",
    )
    idx_c = [f"{'🇰🇷' if m=='KR' else '🇺🇸'} {n}" for n, _, m in all_selected].index(selected_for_candle)
    name_c, ticker_c, market_c = all_selected[idx_c]

    t_obj = yf.Ticker(ticker_c)
    df_c = t_obj.history(period=period)

    if not df_c.empty:
        rows_c = 2 if show_volume else 1
        row_h = [0.75, 0.25] if show_volume else [1]
        fig = make_subplots(rows=rows_c, cols=1, shared_xaxes=True,
                            vertical_spacing=0.03, row_heights=row_h)

        color_up = "#10b981"
        color_dn = "#f43f5e"
        fig.add_trace(go.Candlestick(
            x=df_c.index,
            open=df_c["Open"], high=df_c["High"],
            low=df_c["Low"], close=df_c["Close"],
            name=name_c,
            increasing=dict(line=dict(color=color_up), fillcolor=color_up),
            decreasing=dict(line=dict(color=color_dn), fillcolor=color_dn),
        ), row=1, col=1)

        if show_ma and len(df_c) >= 20:
            fig.add_trace(go.Scatter(
                x=df_c.index, y=df_c["Close"].rolling(20).mean(),
                line=dict(color="#f59e0b", width=1.2, dash="dash"),
                name="MA20", hovertemplate="%{y:,.2f}<extra>MA20</extra>",
            ), row=1, col=1)
        if show_ma and len(df_c) >= 60:
            fig.add_trace(go.Scatter(
                x=df_c.index, y=df_c["Close"].rolling(60).mean(),
                line=dict(color="#60a5fa", width=1.2, dash="dash"),
                name="MA60", hovertemplate="%{y:,.2f}<extra>MA60</extra>",
            ), row=1, col=1)

        if show_volume:
            vol_colors = [color_up if df_c["Close"].iloc[i] >= df_c["Open"].iloc[i]
                          else color_dn for i in range(len(df_c))]
            fig.add_trace(go.Bar(
                x=df_c.index, y=df_c["Volume"],
                marker_color=vol_colors, opacity=0.6,
                name="거래량", hovertemplate="%{y:,}<extra>거래량</extra>",
            ), row=2, col=1)

        fig.update_layout(
            **PLOTLY_LAYOUT,
            title=dict(text=f"{name_c} 캔들스틱 ({period_label})", font=dict(size=13, color="#9ca3af"), x=0.01),
            height=520,
            xaxis_rangeslider_visible=False,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("데이터를 불러오지 못했습니다.")

# ── Bar Chart: Return Ranking ─────────────────────────────────────────────────
st.markdown(f'<div class="section-title">🏆 수익률 랭킹 ({period_label}) <div class="section-line"></div></div>', unsafe_allow_html=True)

sorted_returns = sorted(returns_data.items(), key=lambda x: x[1], reverse=True)

col_bar, col_rank = st.columns([3, 2])

with col_bar:
    names_bar   = [f"{'🇰🇷' if m=='KR' else '🇺🇸'} {n}" for (n, t, m), _ in sorted_returns]
    values_bar  = [v for _, v in sorted_returns]
    colors_bar  = ["#10b981" if v >= 0 else "#f43f5e" for v in values_bar]

    fig_bar = go.Figure(go.Bar(
        x=values_bar,
        y=names_bar,
        orientation="h",
        marker_color=colors_bar,
        text=[fmt_pct(v) for v in values_bar],
        textposition="outside",
        textfont=dict(family="JetBrains Mono, monospace", size=10, color="#9ca3af"),
        hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
    ))
    fig_bar.add_vline(x=0, line=dict(color="#374151", width=1))
    fig_bar.update_layout(
        **PLOTLY_LAYOUT,
        height=max(320, 28 * len(sorted_returns)),
        xaxis_title="수익률 (%)",
        yaxis=dict(autorange="reversed", gridcolor="#1e2535"),
        title=dict(text="수익률 순위", font=dict(size=12, color="#9ca3af"), x=0.01),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_rank:
    st.markdown("**📊 상위 / 하위 종목**")
    top5    = sorted_returns[:5]
    bottom5 = sorted_returns[-5:][::-1]

    st.markdown("<div style='font-size:0.75rem;color:#4a5568;margin-bottom:6px;font-family:JetBrains Mono,monospace;'>▲ TOP 5</div>", unsafe_allow_html=True)
    for i, ((name, ticker, market), ret) in enumerate(top5, 1):
        flag = "🇰🇷" if market == "KR" else "🇺🇸"
        cls  = "metric-change-pos"
        st.markdown(f"""
        <div class="rank-row">
          <span class="rank-num">{i}</span>
          <span class="rank-ticker">{ticker[:8]}</span>
          <span class="rank-name">{flag} {name}</span>
          <span class="rank-ret {cls}">{fmt_pct(ret)}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='font-size:0.75rem;color:#4a5568;margin:12px 0 6px;font-family:JetBrains Mono,monospace;'>▼ BOTTOM 5</div>", unsafe_allow_html=True)
    for i, ((name, ticker, market), ret) in enumerate(bottom5, 1):
        flag = "🇰🇷" if market == "KR" else "🇺🇸"
        cls  = "metric-change-neg"
        st.markdown(f"""
        <div class="rank-row">
          <span class="rank-num">{i}</span>
          <span class="rank-ticker">{ticker[:8]}</span>
          <span class="rank-name">{flag} {name}</span>
          <span class="rank-ret {cls}">{fmt_pct(ret)}</span>
        </div>
        """, unsafe_allow_html=True)

# ── Correlation Heatmap ───────────────────────────────────────────────────────
if len(all_selected) >= 3:
    st.markdown(f'<div class="section-title">🔗 수익률 상관관계 히트맵 <div class="section-line"></div></div>', unsafe_allow_html=True)

    closes = {}
    for name, ticker, market in all_selected:
        hist = fetch_history(ticker, period)
        if not hist.empty:
            closes[f"{'🇰🇷' if market=='KR' else '🇺🇸'} {name}"] = hist["Close"]

    if len(closes) >= 2:
        df_close = pd.DataFrame(closes).dropna()
        corr = df_close.pct_change().dropna().corr()

        fig_heat = go.Figure(go.Heatmap(
            z=corr.values,
            x=corr.columns.tolist(),
            y=corr.index.tolist(),
            colorscale=[
                [0.0,  "#f43f5e"],
                [0.5,  "#0f1320"],
                [1.0,  "#10b981"],
            ],
            zmid=0,
            zmin=-1, zmax=1,
            text=np.round(corr.values, 2),
            texttemplate="%{text}",
            textfont=dict(size=9, family="JetBrains Mono, monospace"),
            hovertemplate="%{y} × %{x}: %{z:.2f}<extra></extra>",
            colorbar=dict(
                tickfont=dict(family="JetBrains Mono, monospace", size=10, color="#6b7280"),
                bgcolor="#0f1320",
                bordercolor="#1e2535",
                borderwidth=1,
            ),
        ))
        fig_heat.update_layout(
            **PLOTLY_LAYOUT,
            height=420,
            title=dict(text="일간 수익률 상관계수", font=dict(size=12, color="#9ca3af"), x=0.01),
            xaxis=dict(tickfont=dict(size=9), gridcolor="#0a0d14"),
            yaxis=dict(tickfont=dict(size=9), gridcolor="#0a0d14", autorange="reversed"),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

# ── Stats Table ───────────────────────────────────────────────────────────────
st.markdown(f'<div class="section-title">📑 통계 요약 테이블 <div class="section-line"></div></div>', unsafe_allow_html=True)

rows_stat = []
for name, ticker, market in all_selected:
    hist = fetch_history(ticker, period)
    if hist.empty:
        continue
    ret_arr = hist["Close"].pct_change().dropna() * 100
    rows_stat.append({
        "시장":      "🇰🇷 KR" if market == "KR" else "🇺🇸 US",
        "종목":      name,
        "티커":      ticker,
        f"{period_label} 수익률": f"{fmt_pct(calc_return(hist))}",
        "변동성(일간std)": f"{ret_arr.std():.2f}%",
        "최대 낙폭":  f"{((hist['Close'] / hist['Close'].cummax()) - 1).min() * 100:.2f}%",
        "최고가":    f"{hist['Close'].max():,.2f}",
        "최저가":    f"{hist['Close'].min():,.2f}",
        "평균 거래량": f"{hist['Volume'].mean():,.0f}",
    })

if rows_stat:
    df_stat = pd.DataFrame(rows_stat)
    st.dataframe(
        df_stat,
        use_container_width=True,
        hide_index=True,
        column_config={
            "시장":       st.column_config.TextColumn(width="small"),
            "종목":       st.column_config.TextColumn(width="medium"),
            "티커":       st.column_config.TextColumn(width="small"),
        }
    )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr class="styled-divider">
<div style="text-align:center;font-family:'JetBrains Mono',monospace;font-size:0.7rem;color:#374151;padding:16px 0;">
  GLOBAL STOCK DASHBOARD &nbsp;·&nbsp; Powered by yfinance + Streamlit + Plotly
  &nbsp;·&nbsp; 본 정보는 투자 조언이 아닙니다.
</div>
""", unsafe_allow_html=True)
