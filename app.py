"""
app.py
======
Interface Streamlit do Horizon.
Deploy: streamlit run app.py  |  Streamlit Cloud (gratuito)
"""

import os
import streamlit as st

st.set_page_config(
    page_title="Horizon",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Secrets: injeta do Streamlit Cloud para os.getenv funcionar normalmente ───
# Localmente: lê do .env via python-dotenv (em ai_analysis.py)
# Na nuvem:   lê do painel Secrets do Streamlit Cloud
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0f;
    color: #e2e8f0;
}
.stApp { background-color: #0a0a0f; }

[data-testid="stSidebar"] {
    background-color: #0f0f1a;
    border-right: 1px solid #1e1e2e;
}
.horizon-card {
    background: #0f0f1a;
    border: 1px solid #1e1e2e;
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.horizon-card-accent {
    background: #0f0f1a;
    border: 1px solid #2a2a4a;
    border-left: 3px solid #6366f1;
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.horizon-card-action {
    background: #0f0f1a;
    border: 1px solid #2a2a4a;
    border-left: 3px solid #22c55e;
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.horizon-card-wait {
    background: #0f0f1a;
    border: 1px solid #2a2a4a;
    border-left: 3px solid #eab308;
    border-radius: 8px;
    padding: 20px 24px;
    margin-bottom: 16px;
}
.score-block {
    font-family: 'Space Mono', monospace;
    font-size: 64px;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -2px;
}
.score-label {
    font-size: 13px;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 4px;
}
.badge-long {
    display: inline-block;
    background: rgba(34,197,94,0.15);
    color: #22c55e;
    border: 1px solid rgba(34,197,94,0.3);
    border-radius: 4px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
    font-family: 'Space Mono', monospace;
}
.badge-short {
    display: inline-block;
    background: rgba(239,68,68,0.15);
    color: #ef4444;
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 4px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
    font-family: 'Space Mono', monospace;
}
.badge-neutral {
    display: inline-block;
    background: rgba(234,179,8,0.15);
    color: #eab308;
    border: 1px solid rgba(234,179,8,0.3);
    border-radius: 4px;
    padding: 4px 14px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 1px;
    font-family: 'Space Mono', monospace;
}
.action-enter {
    font-family: 'Space Mono', monospace;
    font-size: 20px;
    font-weight: 700;
    color: #22c55e;
    letter-spacing: 1px;
}
.action-wait {
    font-family: 'Space Mono', monospace;
    font-size: 20px;
    font-weight: 700;
    color: #eab308;
    letter-spacing: 1px;
}
.rr-ratio {
    font-family: 'Space Mono', monospace;
    font-size: 32px;
    font-weight: 700;
}
.section-title {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 3px;
    color: #475569;
    margin-bottom: 12px;
    font-weight: 600;
}
.reason-item {
    font-size: 13px;
    color: #94a3b8;
    padding: 4px 0;
    border-bottom: 1px solid #1e1e2e;
    font-family: 'Space Mono', monospace;
}
.ai-advice {
    font-size: 14px;
    line-height: 1.7;
    color: #cbd5e1;
    font-style: italic;
    border-left: 2px solid #6366f1;
    padding-left: 16px;
}
.metric-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #1e1e2e;
    font-size: 13px;
}
.metric-label  { color: #64748b; }
.metric-value  { color: #e2e8f0; font-family: 'Space Mono', monospace; font-weight: 700; }
.metric-value-green  { color: #22c55e; font-family: 'Space Mono', monospace; font-weight: 700; }
.metric-value-red    { color: #ef4444; font-family: 'Space Mono', monospace; font-weight: 700; }
.metric-value-yellow { color: #eab308; font-family: 'Space Mono', monospace; font-weight: 700; }
.logo     { font-family: 'Space Mono', monospace; font-size: 22px; font-weight: 700; color: #6366f1; letter-spacing: -1px; }
.logo-sub { font-size: 11px; color: #475569; letter-spacing: 2px; text-transform: uppercase; }
.fomo-warning  { background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.25); border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #ef4444; font-family: 'Space Mono', monospace; }
.optimal-zone  { background: rgba(34,197,94,0.08);  border: 1px solid rgba(34,197,94,0.25);  border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #22c55e; font-family: 'Space Mono', monospace; }
.neutral-zone  { background: rgba(234,179,8,0.08);  border: 1px solid rgba(234,179,8,0.25);  border-radius: 6px; padding: 12px 16px; font-size: 13px; color: #eab308; font-family: 'Space Mono', monospace; }
.confidence-bar-wrap { background: #1e1e2e; border-radius: 4px; height: 6px; margin-top: 6px; }
.confidence-bar { height: 6px; border-radius: 4px; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── Imports do sistema ────────────────────────────────────────────────────────
from market_data import fetch_hierarchical_timeframes
from indicators  import calculate_all
from scoring     import process_hierarchical_data
from ai_analysis import get_ai_analysis

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="logo">HORIZON</div>', unsafe_allow_html=True)
    st.markdown('<div class="logo-sub">Trading Copilot</div>', unsafe_allow_html=True)
    st.markdown("---")

    symbol = st.text_input("Símbolo", value="BTC/USDT", placeholder="BTC/USDT, ETH/USDT...").strip().upper()

    tf_options = {
        "1m  — Scalp":        "1m",
        "15m — Intraday":     "15m",
        "1H  — Short-Swing":  "1h",
        "4H  — Swing":        "4h",
        "1D  — Position":     "1d",
        "1W  — Macro":        "1w",
        "1M  — Deep Macro":   "1M",
    }
    tf_label   = st.selectbox("Timeframe Primário", list(tf_options.keys()), index=4)
    primary_tf = tf_options[tf_label]

    use_ai = st.toggle("Análise IA (Groq)", value=True)

    st.markdown("---")
    run = st.button("▶  ANALISAR", use_container_width=True, type="primary")
    st.markdown("")
    st.markdown('<div style="font-size:11px;color:#334155;">Dados: Binance via CCXT<br>IA: Groq llama-3.1-8b</div>', unsafe_allow_html=True)

# ── Estado ────────────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = {}

# ── Análise ───────────────────────────────────────────────────────────────────
if run:
    with st.spinner(f"Analisando {symbol} em {primary_tf}..."):
        try:
            raw = fetch_hierarchical_timeframes(symbol, primary_tf)
            hierarchical = {
                "inds_primary":   calculate_all(raw["primary"]),
                "inds_secondary": calculate_all(raw["secondary"]) if not raw["secondary"].empty else {},
                "inds_tertiary":  calculate_all(raw["tertiary"])  if not raw["tertiary"].empty  else {},
                "symbol":         symbol,
                "mode":           raw["mode"],
                "tf_labels":      raw["tf_labels"],
            }
            score_data = process_hierarchical_data(hierarchical, symbol)
            ai_data    = get_ai_analysis(symbol, score_data, hierarchical) if use_ai else {"analysis": "IA desativada."}
            st.session_state.results = {
                "symbol": symbol, "primary_tf": primary_tf,
                "score_data": score_data, "ai_data": ai_data,
                "hierarchical": hierarchical,
            }
        except Exception as e:
            st.error(f"Erro ao analisar {symbol}: {e}")

# ── Render ────────────────────────────────────────────────────────────────────
r = st.session_state.results

if not r:
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:60vh;gap:16px;">
        <div style="font-family:'Space Mono',monospace;font-size:48px;color:#1e1e2e;font-weight:700;">HORIZON</div>
        <div style="font-size:14px;color:#334155;letter-spacing:2px;text-transform:uppercase;">Configure e clique em Analisar</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

sd  = r["score_data"]
ai  = r["ai_data"]
sym = r["symbol"]
tf  = r["primary_tf"]

score        = sd["score"]
direction    = sd.get("direction", "N/A")
exec_plan    = sd["exec_plan"]
rr           = sd["rr_data"]
reasons      = sd.get("reasons", [])
mode         = sd["mode"]
tfs          = sd["tf_labels"]
profile_name = sd.get("profile_name", "—")
market_order = sd.get("market_order", {})

# Cores
if score >= 80:   score_color = "#22c55e"
elif score >= 60: score_color = "#84cc16"
elif score >= 40: score_color = "#eab308"
else:             score_color = "#ef4444"

if "LONG"  in direction: badge = f'<span class="badge-long">{direction}</span>'
elif "SHORT" in direction: badge = f'<span class="badge-short">{direction}</span>'
else:                      badge = f'<span class="badge-neutral">{direction}</span>'

if "FOMO"    in exec_plan["status"]: status_html = f'<div class="fomo-warning">⚠ {exec_plan["status"]}</div>'
elif "Optimal" in exec_plan["status"]: status_html = f'<div class="optimal-zone">✓ {exec_plan["status"]}</div>'
else:                                   status_html = f'<div class="neutral-zone">◎ {exec_plan["status"]}</div>'

if rr["rr_class"] == "Strong":       rr_color = "#22c55e"
elif rr["rr_class"] == "Acceptable": rr_color = "#84cc16"
elif rr["rr_class"] == "Weak":       rr_color = "#eab308"
else:                                 rr_color = "#ef4444"

# ── Header ────────────────────────────────────────────────────────────────────
col_sym, col_mode = st.columns([2, 3])
with col_sym:
    st.markdown(f"""
    <div class="horizon-card" style="padding:16px 24px;">
        <div style="font-size:11px;color:#475569;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;">Ativo / Timeframe</div>
        <div style="font-family:'Space Mono',monospace;font-size:26px;font-weight:700;color:#e2e8f0;">{sym}</div>
        <div style="font-size:13px;color:#64748b;margin-top:2px;">{tfs[0]} → {tfs[1]} → {tfs[2] or '—'}</div>
    </div>
    """, unsafe_allow_html=True)
with col_mode:
    st.markdown(f"""
    <div class="horizon-card" style="padding:16px 24px;">
        <div style="font-size:11px;color:#475569;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">Market Mode</div>
        <div style="font-size:15px;font-weight:500;color:#a5b4fc;margin-bottom:6px;">{mode}</div>
        <div style="font-size:11px;color:#334155;margin-bottom:6px;">{profile_name}</div>
        <div>{badge}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Operação a Mercado ────────────────────────────────────────────────────────
if market_order:
    enter_now  = market_order.get("enter_now", False)
    action     = market_order.get("action", "AGUARDAR")
    confidence = market_order.get("confidence", 0)
    urgency    = market_order.get("urgency", "Baixa")
    mo_entry   = market_order.get("entry_price", 0)
    mo_tp      = market_order.get("tp_price", 0)
    mo_sl      = market_order.get("sl_price", 0)
    mo_rr      = market_order.get("rr_ratio", 0)
    mo_rew     = market_order.get("reward_pct", 0)
    mo_risk    = market_order.get("risk_pct", 0)
    mo_reason  = market_order.get("reason", "—")

    card_class   = "horizon-card-action" if enter_now else "horizon-card-wait"
    action_class = "action-enter"        if enter_now else "action-wait"
    conf_color   = "#22c55e" if confidence >= 70 else "#eab308" if confidence >= 40 else "#ef4444"
    conf_pct     = confidence

    st.markdown(f"""
    <div class="{card_class}">
        <div class="section-title">Operação a Mercado</div>
        <div style="display:flex;align-items:center;gap:20px;margin-bottom:16px;">
            <div class="{action_class}">{action}</div>
            <div style="font-size:12px;color:#64748b;">Urgência: <span style="color:#e2e8f0;font-family:'Space Mono',monospace;">{urgency}</span></div>
        </div>
        <div style="margin-bottom:14px;">
            <div style="font-size:11px;color:#475569;letter-spacing:1px;margin-bottom:4px;">CONFIANÇA</div>
            <div style="display:flex;align-items:center;gap:10px;">
                <div class="confidence-bar-wrap" style="flex:1;">
                    <div class="confidence-bar" style="width:{conf_pct}%;background:{conf_color};"></div>
                </div>
                <div style="font-family:'Space Mono',monospace;font-size:13px;color:{conf_color};">{conf_pct}/100</div>
            </div>
        </div>
        <div class="metric-row">
            <span class="metric-label">Entrada</span>
            <span class="metric-value">${mo_entry}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Take Profit</span>
            <span class="metric-value-green">${mo_tp} &nbsp;+{mo_rew}%</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Stop Loss</span>
            <span class="metric-value-red">${mo_sl} &nbsp;-{mo_risk}%</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">R/R</span>
            <span class="metric-value">{mo_rr}</span>
        </div>
        <div style="margin-top:12px;font-size:12px;color:#475569;font-style:italic;">{mo_reason}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Score + Fatores | Execution Plan ─────────────────────────────────────────
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown(f"""
    <div class="horizon-card">
        <div class="section-title">Sistema Score</div>
        <div class="score-block" style="color:{score_color};">{score}</div>
        <div style="font-size:12px;color:{score_color};margin-top:6px;font-family:'Space Mono',monospace;">{sd['classification']}</div>
    </div>
    """, unsafe_allow_html=True)

    reasons_html = "".join(f'<div class="reason-item">{r}</div>' for r in reasons)
    st.markdown(f"""
    <div class="horizon-card">
        <div class="section-title">Fatores do Score</div>
        {reasons_html if reasons_html else '<div style="color:#334155;font-size:13px;">N/A</div>'}
    </div>
    """, unsafe_allow_html=True)

with col_right:
    st.markdown(f"""
    <div class="horizon-card">
        <div class="section-title">Tactical Execution Plan</div>
        {status_html}
        <div style="height:12px;"></div>
        <div class="metric-row">
            <span class="metric-label">Entry Zone</span>
            <span class="metric-value">{exec_plan['entry_lower']} — {exec_plan['entry_upper']}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Ideal Entry</span>
            <span class="metric-value">{exec_plan['ideal_entry']}</span>
        </div>
        <div style="height:8px;"></div>
        <div style="font-size:12px;color:#475569;margin-bottom:4px;">Confirmação</div>
        <div style="font-size:13px;color:#94a3b8;margin-bottom:12px;">{exec_plan['confirmation']}</div>
        <div style="font-size:12px;color:#475569;margin-bottom:4px;">Invalidação</div>
        <div style="font-size:13px;color:#94a3b8;">{exec_plan['invalidation']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="horizon-card">
        <div class="section-title">Projected Risk / Reward</div>
        <div style="display:flex;align-items:baseline;gap:10px;margin-bottom:16px;">
            <div class="rr-ratio" style="color:{rr_color};">{rr['rr_ratio']}</div>
            <div style="font-size:13px;color:{rr_color};font-family:'Space Mono',monospace;">{rr['rr_class']}</div>
        </div>
        <div class="metric-row">
            <span class="metric-label">Take Profit</span>
            <span class="metric-value-green">${rr['tp_price']} &nbsp;+{rr['reward_pct']}%</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Stop Loss</span>
            <span class="metric-value-red">${rr['sl_price']} &nbsp;-{rr['risk_pct']}%</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">Entrada simulada</span>
            <span class="metric-value">${exec_plan['ideal_entry']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── AI Copilot ────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="horizon-card-accent">
    <div class="section-title">Horizon Copilot</div>
    <div class="ai-advice">{ai.get('analysis', 'Sem análise.')}</div>
</div>
""", unsafe_allow_html=True)
