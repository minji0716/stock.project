"""삼성 집중분석 페이지"""
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils import (
    SHARED_CSS, PLOTLY_LAYOUT,
    fetch_quote, fetch_history, fetch_financials,
    calc_return, fmt_pct, color_pct, arrow,
)

st.set_page_config(
    page_title="삼성 집중분석",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(SHARED_CSS, unsafe_allow_html=True)

# ── Samsung universe ──────────────────────────────────────────────────────────
SAMSUNG_GROUP = {
    "삼성전자":          {"ticker": "005930.KS", "sector": "반도체·가전",    "desc": "메모리·시스템 반도체, 스마트폰, 가전"},
    "삼성전자 우":       {"ticker": "005935.KS", "sector": "반도체·가전",    "desc": "삼성전자 우선주"},
    "삼성SDI":           {"ticker": "006400.KS", "sector": "배터리",         "desc": "2차전지·에너지저장시스템"},
    "삼성바이오로직스":  {"ticker": "207940.KS", "sector": "바이오",         "desc": "바이오의약품 CMO 세계 1위"},
    "삼성물산":          {"ticker": "028260.KS", "sector": "건설·패션·리조트","desc": "건설·패션·리조트·급식"},
    "삼성생명":          {"ticker": "032830.KS", "sector": "금융·보험",      "desc": "생명보험 국내 1위"},
    "삼성화재":          {"ticker": "000810.KS", "sector": "금융·보험",      "desc": "손해보험 국내 1위"},
    "삼성전기":          {"ticker": "009150.KS", "sector": "전자부품",       "desc": "MLCC·카메라모듈·기판"},
    "삼성SDS":           {"ticker": "018260.KS", "sector": "IT서비스",       "desc": "IT서비스·클라우드·물류"},
    "호텔신라":          {"ticker": "008770.KS", "sector": "호텔·면세",      "desc": "면세점·호텔·레저"},
    "제일기획":          {"ticker": "030000.KS", "sector": "광고·마케팅",    "desc": "글로벌 광고·마케팅"},
}

PEERS = {
    "삼성전자":  {"ticker": "005930.KS", "market": "KR"},
    "SK하이닉스":{"ticker": "000660.KS", "market": "KR"},
    "NVIDIA":    {"ticker": "NVDA",      "market": "US"},
    "TSMC":      {"ticker": "TSM",       "market": "US"},
    "Intel":     {"ticker": "INTC",      "market": "US"},
    "Micron":    {"ticker": "MU",        "market": "US"},
    "Qualcomm":  {"ticker": "QCOM",      "market": "US"},
}

PERIOD_MAP = {
    "1개월": "1mo", "3개월": "3mo", "6개월": "6mo",
    "1년":   "1y",  "3년":   "3y",  "5년":   "5y",
}

BLUE_PALETTE = ["#1428A0","#1a5fba","#00adef","#00c2e0","#00d4ff",
                "#38bdf8","#7dd3fc","#bae6fd","#e0f2fe"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;
         color:#4a5568;letter-spacing:0.12em;text-transform:uppercase;
         margin-bottom:8px;">NAVIGATION</div>
    """, unsafe_allow_html=True)
    st.page_link("app.py", label="📈 글로벌 비교 대시보드", use_container_width=True)

    st.markdown("""
    <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;
         color:#4a5568;letter-spacing:0.12em;text-transform:uppercase;
         margin:12px 0 8px;">DEEP DIVE</div>
    <div class="nav-menu">
      <div class="nav-item active"><span class="nav-icon">🔬</span>삼성 집중분석</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:#1e2535;margin:16px 0'>", unsafe_allow_html=True)
    st.markdown("**📅 조회 기간**")
    period_label = st.selectbox("기간", list(PERIOD_MAP.keys()), index=3, label_visibility="collapsed")
    period = PERIOD_MAP[period_label]

    st.markdown("**🏢 분석 종목**")
    selected_names = st.multiselect("삼성 계열사",
        list(SAMSUNG_GROUP.keys()),
        default=["삼성전자","삼성SDI","삼성바이오로직스","삼성전기","삼성물산"],
        label_visibility="collapsed")

    st.markdown("**⚙️ 옵션**")
    show_peer     = st.checkbox("반도체 글로벌 경쟁사 비교", value=True)
    show_fin      = st.checkbox("재무 분석 (삼성전자)", value=True)
    show_vol      = st.checkbox("거래량 히트맵", value=True)
    show_rsi      = st.checkbox("RSI 기술적 지표", value=True)

    st.caption(f"업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ── Page Header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:16px;margin-bottom:4px;">
  <div style="font-size:2.8rem;">🔬</div>
  <div>
    <div class="page-title-samsung">삼성 집중분석</div>
    <div class="main-subtitle">SAMSUNG GROUP DEEP DIVE · 계열사 통합 분석</div>
  </div>
</div>
""", unsafe_allow_html=True)
st.markdown(f'<div class="timestamp">Data via Yahoo Finance · {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>', unsafe_allow_html=True)

if not selected_names:
    st.warning("사이드바에서 분석할 계열사를 선택하세요.")
    st.stop()

# ── 1. 계열사 카드 ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">🏢 삼성 계열사 현황 <div class="section-line"></div></div>', unsafe_allow_html=True)

n_cols   = min(len(selected_names), 4)
card_rows = [selected_names[i:i+n_cols] for i in range(0, len(selected_names), n_cols)]
returns_ssm = {}

for row in card_rows:
    cols = st.columns(len(row))
    for col, name in zip(cols, row):
        info   = SAMSUNG_GROUP[name]
        ticker = info["ticker"]
        q      = fetch_quote(ticker)
        hist   = fetch_history(ticker, period)
        ret    = calc_return(hist)
        returns_ssm[name] = ret
        with col:
            if q:
                st.markdown(f"""
                <div class="metric-card metric-card-samsung">
                  <span class="market-badge badge-ssm">🇰🇷 {info['sector']}</span>
                  <div class="metric-ticker">{ticker}</div>
                  <div class="metric-name">{name}</div>
                  <div class="metric-price">₩{q['price']:,.0f}</div>
                  <div class="{color_pct(q['pct'])}">당일 {arrow(q['pct'])} {fmt_pct(q['pct'])}</div>
                  <div class="{color_pct(ret)}" style="font-size:0.78rem;margin-top:4px;font-family:'JetBrains Mono',monospace;">
                    {period_label} {arrow(ret)} {fmt_pct(ret)}
                  </div>
                  <div style="font-size:0.72rem;color:#4a5568;margin-top:6px;">{info['desc']}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="metric-card metric-card-samsung"><span class="market-badge badge-ssm">🇰🇷 {info["sector"]}</span><div class="metric-ticker">{ticker}</div><div class="metric-name">{name}</div><div class="metric-price">—</div></div>', unsafe_allow_html=True)

# ── 2. 계열사 수익률 비교 라인 차트 ──────────────────────────────────────────
st.markdown(f'<div class="section-title">📈 계열사 누적 수익률 비교 ({period_label}) <div class="section-line"></div></div>', unsafe_allow_html=True)

fig_line = go.Figure()
for i, name in enumerate(selected_names):
    hist = fetch_history(SAMSUNG_GROUP[name]["ticker"], period)
    if hist.empty: continue
    normed = (hist["Close"] / hist["Close"].iloc[0] - 1) * 100
    color  = BLUE_PALETTE[i % len(BLUE_PALETTE)]
    fig_line.add_trace(go.Scatter(
        x=normed.index, y=normed.values, name=name,
        line=dict(color=color, width=2),
        hovertemplate=f"%{{y:.2f}}%<extra>{name}</extra>",
    ))
fig_line.add_hline(y=0, line=dict(color="#374151", width=1, dash="dash"))
fig_line.update_layout(**PLOTLY_LAYOUT,
    title=dict(text="삼성 계열사 누적 수익률", font=dict(size=13, color="#9ca3af"), x=0.01),
    yaxis_title="수익률 (%)", height=420)
st.plotly_chart(fig_line, use_container_width=True)

# ── 3. 수익률 바 차트 + 랭킹 ─────────────────────────────────────────────────
col_b, col_r = st.columns([3, 2])
with col_b:
    sorted_ssm = sorted(returns_ssm.items(), key=lambda x: x[1], reverse=True)
    fig_bar = go.Figure(go.Bar(
        x=[v for _,v in sorted_ssm],
        y=[n for n,_ in sorted_ssm],
        orientation="h",
        marker=dict(
            color=[v for _,v in sorted_ssm],
            colorscale=[[0,"#f43f5e"],[0.5,"#1e2535"],[1,"#00adef"]],
            cmid=0, showscale=True,
            colorbar=dict(tickfont=dict(family="JetBrains Mono",size=9,color="#6b7280"),
                bgcolor="#0f1320", bordercolor="#1e2535", title="수익률%"),
        ),
        text=[fmt_pct(v) for _,v in sorted_ssm],
        textposition="outside",
        textfont=dict(family="JetBrains Mono, monospace", size=10, color="#9ca3af"),
        hovertemplate="%{y}: %{x:.2f}%<extra></extra>",
    ))
    fig_bar.add_vline(x=0, line=dict(color="#374151", width=1))
    fig_bar.update_layout(**PLOTLY_LAYOUT,
        height=max(280, 32*len(sorted_ssm)),
        xaxis_title="수익률 (%)",
        yaxis=dict(autorange="reversed", gridcolor="#1e2535"),
        title=dict(text=f"계열사 수익률 순위 ({period_label})", font=dict(size=12,color="#9ca3af"), x=0.01))
    st.plotly_chart(fig_bar, use_container_width=True)

with col_r:
    st.markdown(f'<div class="section-title" style="margin-top:0">🏆 랭킹 <div class="section-line"></div></div>', unsafe_allow_html=True)
    for i, (name, ret) in enumerate(sorted_ssm, 1):
        cls = color_pct(ret)
        medal = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"].get(i-1, f"{i}")
        st.markdown(f"""
        <div class="rank-row">
          <span class="rank-num">{medal}</span>
          <span class="rank-name" style="flex:1">{name}</span>
          <span class="rank-ret {cls}">{fmt_pct(ret)}</span>
        </div>""", unsafe_allow_html=True)

# ── 4. 글로벌 경쟁사 비교 ─────────────────────────────────────────────────────
if show_peer:
    st.markdown(f'<div class="section-title">🌐 반도체 글로벌 경쟁사 비교 ({period_label}) <div class="section-line"></div></div>', unsafe_allow_html=True)

    peer_cols = st.columns(len(PEERS))
    for col, (pname, pinfo) in zip(peer_cols, PEERS.items()):
        q = fetch_quote(pinfo["ticker"])
        with col:
            if q:
                price_str = f"₩{q['price']:,.0f}" if pinfo["market"]=="KR" else f"${q['price']:,.2f}"
                badge = "badge-kr" if pinfo["market"]=="KR" else "badge-us"
                flag  = "🇰🇷" if pinfo["market"]=="KR" else "🇺🇸"
                st.markdown(f"""
                <div class="metric-card">
                  <span class="market-badge {badge}">{flag}</span>
                  <div class="metric-ticker">{pinfo['ticker']}</div>
                  <div class="metric-name">{pname}</div>
                  <div class="metric-price">{price_str}</div>
                  <div class="{color_pct(q['pct'])}">{arrow(q['pct'])} {fmt_pct(q['pct'])}</div>
                </div>""", unsafe_allow_html=True)

    fig_peer = go.Figure()
    peer_colors = ["#1428A0","#00adef","#a78bfa","#7b61ff","#f472b6","#fb923c","#34d399"]
    for i, (pname, pinfo) in enumerate(PEERS.items()):
        hist = fetch_history(pinfo["ticker"], period)
        if hist.empty: continue
        normed = (hist["Close"] / hist["Close"].iloc[0] - 1) * 100
        width  = 2.5 if pname == "삼성전자" else 1.5
        dash   = "solid" if pinfo["market"]=="KR" else "dot"
        fig_peer.add_trace(go.Scatter(
            x=normed.index, y=normed.values, name=pname,
            line=dict(color=peer_colors[i % len(peer_colors)], width=width, dash=dash),
            hovertemplate=f"%{{y:.2f}}%<extra>{pname}</extra>",
        ))
    fig_peer.add_hline(y=0, line=dict(color="#374151", width=1, dash="dash"))
    fig_peer.update_layout(**PLOTLY_LAYOUT,
        title=dict(text="글로벌 반도체 누적 수익률 비교 (삼성전자 vs 경쟁사)", font=dict(size=13,color="#9ca3af"), x=0.01),
        yaxis_title="수익률 (%)", height=420)
    st.plotly_chart(fig_peer, use_container_width=True)

# ── 5. 삼성전자 상세 캔들 + RSI ───────────────────────────────────────────────
st.markdown(f'<div class="section-title">📊 삼성전자 기술적 분석 ({period_label}) <div class="section-line"></div></div>', unsafe_allow_html=True)

df_sec = yf.Ticker("005930.KS").history(period=period)
if not df_sec.empty:
    # RSI 계산
    delta = df_sec["Close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, np.nan)
    rsi   = 100 - (100 / (1 + rs))

    rows_n = 3 if show_rsi else 2
    row_h  = [0.6, 0.2, 0.2] if show_rsi else [0.75, 0.25]
    specs  = [[{"secondary_y": False}]] * rows_n

    fig_tech = make_subplots(
        rows=rows_n, cols=1, shared_xaxes=True,
        vertical_spacing=0.03, row_heights=row_h,
        subplot_titles=["캔들스틱 + 이동평균", "거래량", "RSI (14)"] if show_rsi else ["캔들스틱 + 이동평균", "거래량"],
    )

    # Candlestick
    fig_tech.add_trace(go.Candlestick(
        x=df_sec.index, open=df_sec["Open"], high=df_sec["High"],
        low=df_sec["Low"], close=df_sec["Close"], name="삼성전자",
        increasing=dict(line=dict(color="#00adef"), fillcolor="#00adef"),
        decreasing=dict(line=dict(color="#f43f5e"), fillcolor="#f43f5e"),
    ), row=1, col=1)

    # MAs
    for days, color in [(20,"#f59e0b"),(60,"#a78bfa"),(120,"#f472b6")]:
        if len(df_sec) >= days:
            fig_tech.add_trace(go.Scatter(
                x=df_sec.index, y=df_sec["Close"].rolling(days).mean(),
                line=dict(color=color, width=1.2, dash="dash"),
                name=f"MA{days}", hovertemplate=f"%{{y:,.0f}}<extra>MA{days}</extra>",
            ), row=1, col=1)

    # Bollinger Bands
    if len(df_sec) >= 20:
        ma20 = df_sec["Close"].rolling(20).mean()
        std20= df_sec["Close"].rolling(20).std()
        upper= ma20 + 2*std20
        lower= ma20 - 2*std20
        fig_tech.add_trace(go.Scatter(
            x=df_sec.index, y=upper, line=dict(color="rgba(0,173,239,0.3)", width=1),
            name="BB Upper", showlegend=True,
            hovertemplate="%{y:,.0f}<extra>BB Upper</extra>"), row=1, col=1)
        fig_tech.add_trace(go.Scatter(
            x=df_sec.index, y=lower, line=dict(color="rgba(0,173,239,0.3)", width=1),
            fill="tonexty", fillcolor="rgba(0,173,239,0.04)",
            name="BB Lower", showlegend=True,
            hovertemplate="%{y:,.0f}<extra>BB Lower</extra>"), row=1, col=1)

    # Volume
    vol_colors = ["#00adef" if df_sec["Close"].iloc[i] >= df_sec["Open"].iloc[i]
                  else "#f43f5e" for i in range(len(df_sec))]
    fig_tech.add_trace(go.Bar(
        x=df_sec.index, y=df_sec["Volume"],
        marker_color=vol_colors, opacity=0.7,
        name="거래량", hovertemplate="%{y:,}<extra>거래량</extra>",
    ), row=2, col=1)

    # RSI
    if show_rsi:
        fig_tech.add_trace(go.Scatter(
            x=rsi.index, y=rsi.values,
            line=dict(color="#a78bfa", width=1.5),
            name="RSI(14)", hovertemplate="%{y:.1f}<extra>RSI</extra>",
        ), row=3, col=1)
        fig_tech.add_hline(y=70, line=dict(color="#f43f5e", width=0.8, dash="dash"), row=3, col=1)
        fig_tech.add_hline(y=30, line=dict(color="#10b981", width=0.8, dash="dash"), row=3, col=1)
        fig_tech.add_hrect(y0=70, y1=100, fillcolor="rgba(244,63,94,0.05)",
            line_width=0, row=3, col=1)
        fig_tech.add_hrect(y0=0, y1=30, fillcolor="rgba(16,185,129,0.05)",
            line_width=0, row=3, col=1)

    fig_tech.update_layout(
        **PLOTLY_LAYOUT, height=650,
        title=dict(text="삼성전자 (005930.KS) — 캔들 + 볼린저밴드 + 이동평균 + RSI",
                   font=dict(size=13, color="#9ca3af"), x=0.01),
        xaxis_rangeslider_visible=False,
    )
    fig_tech.update_annotations(font=dict(color="#9ca3af", size=10))
    st.plotly_chart(fig_tech, use_container_width=True)

# ── 6. 재무 분석 (삼성전자) ───────────────────────────────────────────────────
if show_fin:
    st.markdown('<div class="section-title">💰 삼성전자 재무 분석 <div class="section-line"></div></div>', unsafe_allow_html=True)

    fin = fetch_financials("005930.KS")
    if fin and fin["income"] is not None and not fin["income"].empty:
        income  = fin["income"]
        balance = fin["balance"]

        tab1, tab2, tab3 = st.tabs(["📊 손익계산서", "🏦 재무상태표", "ℹ️ 기업 개요"])

        with tab1:
            try:
                rev_row  = next((r for r in ["Total Revenue","Revenue"] if r in income.index), None)
                op_row   = next((r for r in ["Operating Income","EBIT"] if r in income.index), None)
                net_row  = next((r for r in ["Net Income","Net Income Common Stockholders"] if r in income.index), None)

                plot_data = {}
                if rev_row: plot_data["매출액"] = income.loc[rev_row] / 1e12
                if op_row:  plot_data["영업이익"] = income.loc[op_row] / 1e12
                if net_row: plot_data["당기순이익"] = income.loc[net_row] / 1e12

                if plot_data:
                    cols_fin = st.columns(len(plot_data))
                    colors_fin = ["#00adef","#00d4ff","#7dd3fc"]
                    fig_inc = go.Figure()
                    for (label, series), color in zip(plot_data.items(), colors_fin):
                        dates = [str(d.year) for d in series.index]
                        fig_inc.add_trace(go.Bar(
                            x=dates, y=series.values, name=label,
                            marker_color=color, opacity=0.85,
                            hovertemplate=f"%{{x}}: %{{y:.1f}}조<extra>{label}</extra>",
                        ))
                    if op_row and rev_row:
                        op_margin = (income.loc[op_row] / income.loc[rev_row] * 100).dropna()
                        fig_inc.add_trace(go.Scatter(
                            x=[str(d.year) for d in op_margin.index],
                            y=op_margin.values, name="영업이익률(%)",
                            line=dict(color="#f59e0b", width=2),
                            yaxis="y2",
                            hovertemplate="%{y:.1f}%<extra>영업이익률</extra>",
                        ))
                    fig_inc.update_layout(
                        **PLOTLY_LAYOUT, height=380,
                        title=dict(text="매출액·영업이익·순이익 (단위: 조원)", font=dict(size=12,color="#9ca3af"), x=0.01),
                        barmode="group",
                        yaxis=dict(title="금액 (조원)", gridcolor="#1e2535"),
                        yaxis2=dict(title="영업이익률(%)", overlaying="y", side="right",
                                    gridcolor="rgba(0,0,0,0)", tickfont=dict(color="#f59e0b")),
                    )
                    st.plotly_chart(fig_inc, use_container_width=True)
                else:
                    st.info("손익 데이터를 파싱할 수 없습니다.")
            except Exception as e:
                st.info(f"손익 데이터 처리 오류: {e}")

        with tab2:
            try:
                asset_row = next((r for r in ["Total Assets"] if r in balance.index), None)
                liab_row  = next((r for r in ["Total Liabilities Net Minority Interest","Total Liabilities"] if r in balance.index), None)
                eq_row    = next((r for r in ["Stockholders Equity","Total Equity Gross Minority Interest"] if r in balance.index), None)

                if asset_row:
                    dates_b = [str(d.year) for d in balance.columns]
                    fig_bal = go.Figure()
                    if liab_row:
                        fig_bal.add_trace(go.Bar(x=dates_b, y=balance.loc[liab_row]/1e12,
                            name="부채", marker_color="#f43f5e", opacity=0.8,
                            hovertemplate="%{x}: %{y:.1f}조<extra>부채</extra>"))
                    if eq_row:
                        fig_bal.add_trace(go.Bar(x=dates_b, y=balance.loc[eq_row]/1e12,
                            name="자본", marker_color="#00adef", opacity=0.8,
                            hovertemplate="%{x}: %{y:.1f}조<extra>자본</extra>"))
                    fig_bal.update_layout(**PLOTLY_LAYOUT, height=360, barmode="stack",
                        title=dict(text="부채·자본 구조 (단위: 조원)", font=dict(size=12,color="#9ca3af"), x=0.01),
                        yaxis=dict(title="금액 (조원)", gridcolor="#1e2535"))
                    st.plotly_chart(fig_bal, use_container_width=True)
                else:
                    st.info("재무상태표 데이터를 파싱할 수 없습니다.")
            except Exception as e:
                st.info(f"재무상태표 처리 오류: {e}")

        with tab3:
            info = fin.get("info", {}) or {}
            meta_items = [
                ("업종",        info.get("sector","—")),
                ("산업",        info.get("industry","—")),
                ("직원수",      f"{info.get('fullTimeEmployees',0):,}명" if info.get("fullTimeEmployees") else "—"),
                ("시가총액",    f"₩{info.get('marketCap',0)/1e12:.1f}조" if info.get("marketCap") else "—"),
                ("PER",         f"{info.get('trailingPE','—'):.2f}x" if isinstance(info.get('trailingPE'), float) else "—"),
                ("PBR",         f"{info.get('priceToBook','—'):.2f}x" if isinstance(info.get('priceToBook'), float) else "—"),
                ("배당수익률",  f"{info.get('dividendYield',0)*100:.2f}%" if info.get('dividendYield') else "—"),
                ("52주 최고",   f"₩{info.get('fiftyTwoWeekHigh',0):,.0f}" if info.get('fiftyTwoWeekHigh') else "—"),
                ("52주 최저",   f"₩{info.get('fiftyTwoWeekLow',0):,.0f}" if info.get('fiftyTwoWeekLow') else "—"),
                ("베타",        f"{info.get('beta','—'):.2f}" if isinstance(info.get('beta'), float) else "—"),
            ]
            m_cols = st.columns(2)
            for i, (label, val) in enumerate(meta_items):
                with m_cols[i % 2]:
                    st.markdown(f"""
                    <div class="rank-row" style="margin-bottom:6px;">
                      <span style="font-size:0.8rem;color:#6b7280;flex:1">{label}</span>
                      <span style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;color:#e2e8f0">{val}</span>
                    </div>""", unsafe_allow_html=True)
            if info.get("longBusinessSummary"):
                st.markdown(f"""
                <div class="insight-box" style="margin-top:12px;">
                  <div class="insight-label">기업 소개</div>
                  {info['longBusinessSummary'][:600]}…
                </div>""", unsafe_allow_html=True)
    else:
        st.info("재무 데이터를 불러올 수 없습니다. (야후 파이낸스 제한)")

# ── 7. 거래량 히트맵 ──────────────────────────────────────────────────────────
if show_vol:
    st.markdown('<div class="section-title">🌡️ 삼성전자 월별 수익률 히트맵 <div class="section-line"></div></div>', unsafe_allow_html=True)
    df_5y = fetch_history("005930.KS", "5y")
    if not df_5y.empty:
        df_5y["year"]  = df_5y.index.year
        df_5y["month"] = df_5y.index.month
        monthly = df_5y.groupby(["year","month"])["Close"].agg(["first","last"])
        monthly["ret"] = (monthly["last"] / monthly["first"] - 1) * 100
        pivot = monthly["ret"].unstack(level="month")
        pivot.columns = ["1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]

        fig_hm = go.Figure(go.Heatmap(
            z=pivot.values, x=pivot.columns.tolist(),
            y=[str(y) for y in pivot.index.tolist()],
            colorscale=[[0,"#f43f5e"],[0.5,"#111827"],[1,"#00adef"]],
            zmid=0,
            text=np.round(pivot.values, 1),
            texttemplate="%{text}%",
            textfont=dict(size=9, family="JetBrains Mono, monospace"),
            hovertemplate="%{y} %{x}: %{z:.2f}%<extra></extra>",
            colorbar=dict(tickfont=dict(family="JetBrains Mono",size=9,color="#6b7280"),
                bgcolor="#0f1320", bordercolor="#1e2535", title="%"),
        ))
        fig_hm.update_layout(**PLOTLY_LAYOUT, height=380,
            title=dict(text="삼성전자 월별 수익률 히트맵 (최근 5년)", font=dict(size=12,color="#9ca3af"), x=0.01),
            xaxis=dict(tickfont=dict(size=10), gridcolor="#0a0d14"),
            yaxis=dict(tickfont=dict(size=10), gridcolor="#0a0d14", autorange="reversed"))
        st.plotly_chart(fig_hm, use_container_width=True)

        # 월별 평균 수익률 바 차트
        monthly_avg = pivot.mean()
        fig_mavg = go.Figure(go.Bar(
            x=monthly_avg.index, y=monthly_avg.values,
            marker_color=["#00adef" if v>=0 else "#f43f5e" for v in monthly_avg.values],
            text=[f"{v:.1f}%" for v in monthly_avg.values],
            textposition="outside",
            textfont=dict(family="JetBrains Mono", size=9, color="#9ca3af"),
            hovertemplate="%{x}: %{y:.2f}%<extra>월평균</extra>",
        ))
        fig_mavg.add_hline(y=0, line=dict(color="#374151", width=1))
        fig_mavg.update_layout(**PLOTLY_LAYOUT, height=280,
            title=dict(text="삼성전자 월별 평균 수익률 (최근 5년)", font=dict(size=12,color="#9ca3af"), x=0.01),
            yaxis_title="평균 수익률 (%)")
        st.plotly_chart(fig_mavg, use_container_width=True)

# ── 8. 계열사 상관관계 ────────────────────────────────────────────────────────
if len(selected_names) >= 3:
    st.markdown('<div class="section-title">🔗 계열사 수익률 상관관계 <div class="section-line"></div></div>', unsafe_allow_html=True)
    closes = {}
    for name in selected_names:
        hist = fetch_history(SAMSUNG_GROUP[name]["ticker"], period)
        if not hist.empty:
            closes[name] = hist["Close"]
    if len(closes) >= 2:
        df_c = pd.DataFrame(closes).dropna()
        corr = df_c.pct_change().dropna().corr()
        fig_corr = go.Figure(go.Heatmap(
            z=corr.values, x=corr.columns.tolist(), y=corr.index.tolist(),
            colorscale=[[0,"#f43f5e"],[0.5,"#0f1320"],[1,"#00adef"]],
            zmid=0, zmin=-1, zmax=1,
            text=np.round(corr.values, 2), texttemplate="%{text}",
            textfont=dict(size=10, family="JetBrains Mono"),
            hovertemplate="%{y} × %{x}: %{z:.2f}<extra></extra>",
            colorbar=dict(tickfont=dict(family="JetBrains Mono",size=9,color="#6b7280"),
                bgcolor="#0f1320", bordercolor="#1e2535"),
        ))
        fig_corr.update_layout(**PLOTLY_LAYOUT, height=400,
            title=dict(text="계열사 간 일간 수익률 상관계수", font=dict(size=12,color="#9ca3af"), x=0.01),
            xaxis=dict(tickfont=dict(size=10), gridcolor="#0a0d14"),
            yaxis=dict(tickfont=dict(size=10), gridcolor="#0a0d14", autorange="reversed"))
        st.plotly_chart(fig_corr, use_container_width=True)

# ── 9. 인사이트 박스 ──────────────────────────────────────────────────────────
st.markdown('<div class="section-title">💡 분석 인사이트 <div class="section-line"></div></div>', unsafe_allow_html=True)

best  = max(returns_ssm, key=returns_ssm.get)  if returns_ssm else "—"
worst = min(returns_ssm, key=returns_ssm.get)  if returns_ssm else "—"
avg   = np.mean(list(returns_ssm.values()))    if returns_ssm else 0

insights = [
    ("📌 기간 요약",
     f"선택 기간 <b>{period_label}</b> 기준 삼성 계열사 평균 수익률은 <b>{fmt_pct(avg)}</b>입니다."),
    ("🏆 최고 성과",
     f"<b>{best}</b>이(가) <b>{fmt_pct(returns_ssm.get(best,0))}</b>로 계열사 중 가장 높은 수익률을 기록했습니다."),
    ("⚠️ 최저 성과",
     f"<b>{worst}</b>이(가) <b>{fmt_pct(returns_ssm.get(worst,0))}</b>로 계열사 중 가장 낮은 수익률을 보였습니다."),
    ("📊 분산투자 힌트",
     "삼성 계열사 간 상관관계가 높을수록 분산 효과가 줄어듭니다. 히트맵에서 상관계수가 낮은 계열사 조합을 활용하세요."),
]
ic1, ic2 = st.columns(2)
for i, (label, text) in enumerate(insights):
    with (ic1 if i%2==0 else ic2):
        st.markdown(f"""
        <div class="insight-box">
          <div class="insight-label">{label}</div>
          {text}
        </div>""", unsafe_allow_html=True)

st.markdown('<hr class="styled-divider"><div style="text-align:center;font-family:\'JetBrains Mono\',monospace;font-size:0.7rem;color:#374151;padding:12px 0;">삼성 집중분석 · Powered by yfinance + Streamlit + Plotly · 본 정보는 투자 조언이 아닙니다.</div>', unsafe_allow_html=True)
