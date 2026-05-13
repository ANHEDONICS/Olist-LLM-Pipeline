"""
streamlit_app.py — Main Landing Page
Olist LLM Pipeline — Enterprise Dashboard
"""
import os, json, datetime, subprocess, time
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="Olist Pipeline", page_icon="🔮", layout="wide", initial_sidebar_state="expanded")

# ── Shared CSS ──────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*,[class*="css"]{font-family:'Inter',sans-serif!important}
.stApp{background:#0b0b14}
section[data-testid="stSidebar"]{background:#10101f!important}
h1,h2,h3{color:#e2e8f0!important}
.hero{text-align:center;padding:2rem 0 1rem}
.hero h1{font-size:2.6rem;font-weight:900;background:linear-gradient(135deg,#818cf8,#a78bfa,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0}
.hero p{color:#64748b;font-size:.9rem;margin-top:.3rem}
.kpi-row{display:flex;gap:12px;margin:1rem 0}
.kpi{flex:1;background:rgba(30,30,50,.6);border:1px solid rgba(99,102,241,.12);border-radius:14px;padding:18px 16px;text-align:center;transition:border-color .2s}
.kpi:hover{border-color:rgba(99,102,241,.35)}
.kpi .v{font-size:2rem;font-weight:800;line-height:1.1}
.kpi .l{font-size:.68rem;color:#64748b;text-transform:uppercase;letter-spacing:1.2px;margin-top:4px}
.purple{color:#a78bfa}.green{color:#34d399}.amber{color:#fbbf24}.rose{color:#fb7185}.white{color:#e2e8f0}
.sec{font-size:1.05rem;font-weight:700;color:#e2e8f0;border-left:3px solid #818cf8;padding-left:12px;margin:1.8rem 0 .8rem}
.chip{display:inline-block;padding:3px 12px;border-radius:99px;font-size:.72rem;font-weight:700}
.chip-ok{background:rgba(52,211,153,.12);color:#34d399}
.chip-fail{background:rgba(251,113,133,.12);color:#fb7185}
.live-bar{text-align:center;padding:6px;margin:0 0 1.5rem;background:rgba(99,102,241,.06);border-radius:8px;color:#818cf8;font-size:.78rem}
.card{background:rgba(30,30,50,.5);border:1px solid rgba(99,102,241,.1);border-radius:12px;padding:16px;margin-bottom:10px}
.finding{padding:8px 14px;border-radius:8px;margin:4px 0;font-size:.82rem;background:rgba(30,30,50,.5);border-left:3px solid}
.finding-high{border-color:#fb7185;color:#fda4af}
.finding-med{border-color:#fbbf24;color:#fde68a}
.finding-low{border-color:#34d399;color:#6ee7b7}
.finding-info{border-color:#818cf8;color:#a5b4fc}
</style>""", unsafe_allow_html=True)

# ── Helpers ─────────────────────────────────────────────────────
@st.cache_resource(ttl=30)
def get_sf():
    try:
        import snowflake.connector
        return snowflake.connector.connect(
            account=os.getenv("SNOWFLAKE_ACCOUNT"), user=os.getenv("SNOWFLAKE_USER"),
            password=os.getenv("SNOWFLAKE_PASSWORD"), warehouse=os.getenv("SNOWFLAKE_WAREHOUSE","COMPUTE_WH"),
            database=os.getenv("SNOWFLAKE_DATABASE","MY_DB"), schema=os.getenv("SNOWFLAKE_SCHEMA","PUBLIC"),
            role=os.getenv("SNOWFLAKE_ROLE","SYSADMIN"))
    except: return None

def qry(sql):
    conn = get_sf()
    if not conn: return pd.DataFrame()
    try:
        c=conn.cursor();c.execute(sql);cols=[d[0] for d in c.description];data=c.fetchall();c.close()
        return pd.DataFrame(data,columns=cols)
    except: return pd.DataFrame()

def load_hist():
    p=Path("metadata/batch_history.json")
    return json.load(open(p)) if p.exists() else []

# ── Data ────────────────────────────────────────────────────────
hist = load_hist()
raw_df = qry("SELECT COUNT(*) AS CNT FROM RAW_OLIST_CUSTOMERS")
silver_df = qry("SELECT COUNT(*) AS CNT FROM SILVER_CUSTOMERS_CLEAN")
masked_df = qry("SELECT COUNT(*) AS CNT FROM SILVER_CUSTOMERS_MASKED")
gold_df = qry("SELECT COUNT(*) AS CNT FROM GOLD_CUSTOMERS_KPIS")

raw_n = int(raw_df.iloc[0,0]) if not raw_df.empty else 0
silver_n = int(silver_df.iloc[0,0]) if not silver_df.empty else 0
masked_n = int(masked_df.iloc[0,0]) if not masked_df.empty else 0
gold_n = int(gold_df.iloc[0,0]) if not gold_df.empty else 0

# ── Hero ────────────────────────────────────────────────────────
st.markdown("""<div class="hero">
<h1>🔮 Olist LLM Pipeline</h1>
<p>Autonomous Self-Healing Data Pipeline &mdash; LLM on Every Agent &mdash; Snowflake</p>
</div>""", unsafe_allow_html=True)

now = datetime.datetime.now().strftime("%H:%M:%S")
bid = hist[-1].get("batch_id","—") if hist else "—"
st.markdown(f'<div class="live-bar">🟢 Live · {now} · {len(hist)} batches processed · Latest: {bid}</div>', unsafe_allow_html=True)

# ── Top KPIs ────────────────────────────────────────────────────
latest = hist[-1] if hist else {}
status = latest.get("status","—")
chip = "chip-ok" if status=="SUCCESS" else "chip-fail"

st.markdown(f"""<div class="kpi-row">
<div class="kpi"><div class="v amber">{raw_n:,}</div><div class="l">🟤 Bronze Rows</div></div>
<div class="kpi"><div class="v white">{silver_n:,}</div><div class="l">⚪ Silver Clean</div></div>
<div class="kpi"><div class="v purple">{masked_n:,}</div><div class="l">🔒 PII Masked</div></div>
<div class="kpi"><div class="v green">{gold_n}</div><div class="l">🥇 Gold KPIs</div></div>
<div class="kpi"><div class="v"><span class="chip {chip}">{status}</span></div><div class="l">Pipeline Status</div></div>
<div class="kpi"><div class="v rose">{latest.get('heals',0)}</div><div class="l">🔧 Self-Heals</div></div>
</div>""", unsafe_allow_html=True)

# ── Pipeline Flow ───────────────────────────────────────────────
st.markdown('<div class="sec">🔄 Pipeline Architecture</div>', unsafe_allow_html=True)

flow = """
```mermaid
graph LR
    GEN[Generate Data] --> P[Profile]
    P --> BI[Inspector]
    BI --> SD[Schema Drift]
    SD --> PD[PII Detect]
    PD --> RG[Rules]
    RG --> V[Validator]
    V -->|pass| T[Transform]
    V -->|fail| H[Heal Agent]
    H -->|retry| V
    T --> PM[PII Mask]
    PM --> GK[Gold KPI]
    GK --> LT[Lineage]
    LT --> AW[Audit]
    AW --> AL[Alert]
```
"""
st.markdown(flow)

# ── Batch History ───────────────────────────────────────────────
if hist:
    st.markdown('<div class="sec">📈 Batch History Overview</div>', unsafe_allow_html=True)
    hdf = pd.DataFrame(hist)
    hdf["label"] = [f"#{i+1}" for i in range(len(hdf))]

    c1, c2 = st.columns(2)
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=hdf["label"], y=hdf["raw_rows"], name="Bronze", marker_color="#d97706", opacity=.8))
        fig.add_trace(go.Bar(x=hdf["label"], y=hdf["clean_rows"], name="Silver", marker_color="#94a3b8", opacity=.8))
        fig.add_trace(go.Bar(x=hdf["label"], y=hdf["masked_rows"], name="Masked", marker_color="#818cf8", opacity=.8))
        fig.update_layout(title="Rows per Batch", barmode="group", height=300, template="plotly_dark",
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="Inter", color="#94a3b8"), legend=dict(orientation="h", y=-.15))
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        colors = ["#34d399" if s=="SUCCESS" else "#fb7185" for s in hdf["status"]]
        fig2 = go.Figure(go.Bar(x=hdf["label"], y=hdf["duration_s"], marker_color=colors,
                                 text=hdf["status"], textposition="auto", opacity=.85))
        fig2.update_layout(title="Duration & Status", height=300, template="plotly_dark",
                           paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font=dict(family="Inter", color="#94a3b8"))
        st.plotly_chart(fig2, use_container_width=True)

# ── Navigation ──────────────────────────────────────────────────
st.markdown('<div class="sec">📂 Dashboard Pages</div>', unsafe_allow_html=True)

pages = [
    ("🎛️", "Pipeline Control", "Generate data, trigger pipeline, control batch size"),
    ("📊", "Quality KPIs", "Validation pass %, null rates, healing success, quarantine rate"),
    ("🔐", "Governance & PII", "PII detection, masking audit, data classification"),
    ("🌊", "Schema Evolution", "Schema drift tracking, column changes, type modifications"),
    ("🔗", "Lineage", "Data flow tracing across Bronze → Silver → Gold"),
    ("📋", "Audit & Logs", "Run history, heal logs, error summaries"),
    ("🔍", "Data Explorer", "Browse Snowflake tables: Bronze, Silver, Masked, Gold"),
]

cols = st.columns(4)
for i, (icon, name, desc) in enumerate(pages):
    with cols[i % 4]:
        st.markdown(f"""<div class="card">
        <div style="font-size:1.5rem;margin-bottom:4px">{icon}</div>
        <div style="font-weight:700;color:#e2e8f0;font-size:.9rem">{name}</div>
        <div style="color:#64748b;font-size:.75rem;margin-top:2px">{desc}</div>
        </div>""", unsafe_allow_html=True)

st.caption("👈 Use the sidebar to navigate between pages")
st.markdown("---")
st.markdown('<div style="text-align:center;color:#475569;font-size:.7rem">GEN AI Capstone-2 · LangGraph · Groq · Snowflake</div>', unsafe_allow_html=True)
