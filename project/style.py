"""
style.py — Premium CSS theme for Company Intelligence Dashboard
Inject this at the top of app.py with: from style import inject_css; inject_css()
"""

import streamlit as st


def inject_css():
    st.markdown("""
    <style>
    /* ═══════════════════════════════════════════════════════════════
       FONTS
    ═══════════════════════════════════════════════════════════════ */
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ═══════════════════════════════════════════════════════════════
       CSS VARIABLES — change these to re-theme the whole app
    ═══════════════════════════════════════════════════════════════ */
    :root {
        --bg-base:        #09090f;
        --bg-surface:     #111118;
        --bg-card:        #16161f;
        --bg-card-hover:  #1c1c28;
        --border:         rgba(255,255,255,0.06);
        --border-accent:  rgba(212,175,55,0.35);

        --gold:           #d4af37;
        --gold-light:     #f0d060;
        --gold-glow:      rgba(212,175,55,0.15);
        --gold-glow-soft: rgba(212,175,55,0.07);

        --text-primary:   #eeeef4;
        --text-secondary: #8888aa;
        --text-muted:     #55556a;

        --success:        #2ecc71;
        --warning:        #f39c12;
        --danger:         #e74c3c;
        --info:           #3a86ff;

        --radius:         10px;
        --radius-lg:      16px;
        --font:           'Sora', sans-serif;
        --font-mono:      'JetBrains Mono', monospace;
    }

    /* ═══════════════════════════════════════════════════════════════
       BASE
    ═══════════════════════════════════════════════════════════════ */
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {
        background: var(--bg-base) !important;
        color: var(--text-primary) !important;
        font-family: var(--font) !important;
    }

    /* Subtle grid texture on the main bg */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        inset: 0;
        background-image:
            linear-gradient(rgba(212,175,55,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(212,175,55,0.03) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
        z-index: 0;
    }

    [data-testid="stMain"], .main .block-container {
        background: transparent !important;
        padding-top: 2rem !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       SIDEBAR
    ═══════════════════════════════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: var(--bg-surface) !important;
        border-right: 1px solid var(--border) !important;
    }

    [data-testid="stSidebar"] > div {
        padding-top: 1.5rem;
    }

    /* Sidebar title */
    [data-testid="stSidebar"] h1 {
        font-size: 1.1rem !important;
        color: var(--gold) !important;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    /* ═══════════════════════════════════════════════════════════════
       TYPOGRAPHY
    ═══════════════════════════════════════════════════════════════ */
    h1 {
        font-family: var(--font) !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.02em;
        line-height: 1.2 !important;
    }

    h1::after {
        content: '';
        display: block;
        width: 48px;
        height: 3px;
        background: linear-gradient(90deg, var(--gold), transparent);
        margin-top: 10px;
        border-radius: 2px;
    }

    h2 {
        font-family: var(--font) !important;
        font-weight: 600 !important;
        font-size: 1.3rem !important;
        color: var(--text-primary) !important;
        letter-spacing: -0.01em;
    }

    h3 {
        font-family: var(--font) !important;
        font-weight: 500 !important;
        color: var(--gold-light) !important;
        font-size: 1rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    p, li, .stMarkdown p {
        font-size: 0.95rem !important;
        line-height: 1.75 !important;
        color: var(--text-secondary) !important;
    }

    /* Caption */
    [data-testid="stCaptionContainer"], .stCaption {
        color: var(--text-muted) !important;
        font-size: 0.78rem !important;
        font-family: var(--font-mono) !important;
    }

    /* Subheader */
    [data-testid="stHeadingWithActionElements"] h2,
    [data-testid="stHeadingWithActionElements"] h3 {
        padding-bottom: 0.4rem;
        border-bottom: 1px solid var(--border);
    }

    /* ═══════════════════════════════════════════════════════════════
       BUTTONS
    ═══════════════════════════════════════════════════════════════ */
    .stButton > button, [data-testid="stDownloadButton"] > button {
        font-family: var(--font) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.04em !important;
        border-radius: var(--radius) !important;
        transition: all 0.22s ease !important;
        border: 1px solid var(--border) !important;
        background: var(--bg-card) !important;
        color: var(--text-secondary) !important;
        padding: 0.55rem 1.2rem !important;
    }

    .stButton > button:hover {
        background: var(--bg-card-hover) !important;
        border-color: var(--border-accent) !important;
        color: var(--gold-light) !important;
        box-shadow: 0 0 20px var(--gold-glow) !important;
        transform: translateY(-1px) !important;
    }

    /* Primary button (gold) */
    .stButton > button[kind="primary"],
    [data-testid="stDownloadButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #c9a227, #d4af37) !important;
        border: none !important;
        color: #09090f !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 24px rgba(212,175,55,0.25) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #d4af37, #f0d060) !important;
        box-shadow: 0 6px 32px rgba(212,175,55,0.40) !important;
        transform: translateY(-2px) !important;
        color: #09090f !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       INPUTS
    ═══════════════════════════════════════════════════════════════ */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--text-primary) !important;
        font-family: var(--font) !important;
        font-size: 0.9rem !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: var(--border-accent) !important;
        box-shadow: 0 0 0 3px var(--gold-glow-soft) !important;
        outline: none !important;
    }

    .stTextInput > label, .stSelectbox > label,
    .stMultiSelect > label, .stCheckbox > label {
        color: var(--text-secondary) !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.03em !important;
        text-transform: uppercase !important;
    }

    /* Checkbox */
    .stCheckbox > label > span {
        color: var(--text-secondary) !important;
        text-transform: none !important;
        letter-spacing: normal !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       TABS
    ═══════════════════════════════════════════════════════════════ */
    [data-testid="stTabs"] [role="tablist"] {
        border-bottom: 1px solid var(--border) !important;
        gap: 0 !important;
        background: transparent !important;
    }

    [data-testid="stTabs"] [role="tab"] {
        font-family: var(--font) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: var(--text-muted) !important;
        padding: 0.65rem 1.2rem !important;
        border: none !important;
        border-radius: 0 !important;
        background: transparent !important;
        transition: color 0.2s !important;
        letter-spacing: 0.02em;
    }

    [data-testid="stTabs"] [role="tab"]:hover {
        color: var(--text-secondary) !important;
    }

    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: var(--gold) !important;
        border-bottom: 2px solid var(--gold) !important;
        background: transparent !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       DATAFRAME / TABLE
    ═══════════════════════════════════════════════════════════════ */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-lg) !important;
        overflow: hidden !important;
        background: var(--bg-card) !important;
    }

    [data-testid="stDataFrame"] table {
        font-family: var(--font-mono) !important;
        font-size: 0.82rem !important;
    }

    [data-testid="stDataFrame"] thead th {
        background: var(--bg-surface) !important;
        color: var(--gold) !important;
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        border-bottom: 1px solid var(--border-accent) !important;
        padding: 0.75rem 1rem !important;
    }

    [data-testid="stDataFrame"] tbody td {
        color: var(--text-secondary) !important;
        border-bottom: 1px solid var(--border) !important;
        padding: 0.6rem 1rem !important;
    }

    [data-testid="stDataFrame"] tbody tr:hover td {
        background: var(--bg-card-hover) !important;
        color: var(--text-primary) !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       INFO / WARNING / SUCCESS / ERROR BOXES
    ═══════════════════════════════════════════════════════════════ */
    [data-testid="stAlert"] {
        border-radius: var(--radius-lg) !important;
        border-left-width: 3px !important;
        font-family: var(--font) !important;
        font-size: 0.9rem !important;
        padding: 1rem 1.2rem !important;
    }

    /* Info → executive brief */
    [data-testid="stAlert"][data-baseweb="notification"] {
        background: rgba(58,134,255,0.07) !important;
        border-left-color: var(--info) !important;
        color: var(--text-secondary) !important;
    }

    .stSuccess {
        background: rgba(46,204,113,0.07) !important;
        border-left-color: var(--success) !important;
    }

    .stWarning {
        background: rgba(243,156,18,0.07) !important;
        border-left-color: var(--warning) !important;
    }

    .stError {
        background: rgba(231,76,60,0.08) !important;
        border-left-color: var(--danger) !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       SPINNER
    ═══════════════════════════════════════════════════════════════ */
    [data-testid="stSpinner"] > div {
        border-top-color: var(--gold) !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       DIVIDER
    ═══════════════════════════════════════════════════════════════ */
    hr {
        border: none !important;
        border-top: 1px solid var(--border) !important;
        margin: 1.5rem 0 !important;
    }

    /* ═══════════════════════════════════════════════════════════════
       NEWS CARD — applied via st.markdown in render_news_card()
    ═══════════════════════════════════════════════════════════════ */
    .news-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1rem 1.2rem;
        margin-bottom: 0.75rem;
        transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
    }

    .news-card:hover {
        border-color: var(--border-accent);
        box-shadow: 0 4px 24px var(--gold-glow);
        transform: translateY(-2px);
    }

    .news-card a {
        color: var(--text-primary) !important;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.92rem;
        line-height: 1.4;
    }

    .news-card a:hover {
        color: var(--gold-light) !important;
    }

    .news-card .meta {
        color: var(--text-muted);
        font-size: 0.76rem;
        font-family: var(--font-mono);
        margin-top: 0.3rem;
        margin-bottom: 0.5rem;
    }

    .news-card .snippet {
        color: var(--text-secondary);
        font-size: 0.85rem;
        line-height: 1.6;
    }

    /* ═══════════════════════════════════════════════════════════════
       METRIC CARDS — used in KPI row
    ═══════════════════════════════════════════════════════════════ */
    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 1.2rem 1.4rem;
        transition: border-color 0.2s, box-shadow 0.2s;
    }

    .metric-card:hover {
        border-color: var(--border-accent);
        box-shadow: 0 0 24px var(--gold-glow);
    }

    .metric-card .label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-muted);
        margin-bottom: 0.35rem;
    }

    .metric-card .value {
        font-size: 1.6rem;
        font-weight: 700;
        color: var(--text-primary);
        font-family: var(--font-mono);
    }

    .metric-card .delta {
        font-size: 0.78rem;
        margin-top: 0.25rem;
        font-family: var(--font-mono);
    }

    .metric-card .delta.up   { color: var(--success); }
    .metric-card .delta.down { color: var(--danger); }

    /* ═══════════════════════════════════════════════════════════════
       SECTION HEADER BADGE
    ═══════════════════════════════════════════════════════════════ */
    .section-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: var(--gold-glow-soft);
        border: 1px solid var(--border-accent);
        border-radius: 100px;
        padding: 0.25rem 0.85rem;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--gold);
        margin-bottom: 0.6rem;
    }

    /* ═══════════════════════════════════════════════════════════════
       SCROLLBAR
    ═══════════════════════════════════════════════════════════════ */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb {
        background: #2a2a3a;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover { background: var(--border-accent); }

    /* ═══════════════════════════════════════════════════════════════
       PLOTLY CHART WRAPPER
    ═══════════════════════════════════════════════════════════════ */
    [data-testid="stPlotlyChart"] {
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 0.5rem;
        background: var(--bg-card);
    }

    /* ═══════════════════════════════════════════════════════════════
       LOGIN CARD
    ═══════════════════════════════════════════════════════════════ */
    .login-wrapper {
        max-width: 380px;
        margin: 4rem auto;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: 2.5rem 2rem;
        box-shadow: 0 8px 48px rgba(0,0,0,0.5);
    }

   /* ═══════════════════════════════════════════════════════════════
   HIDE STREAMLIT BRANDING ONLY
═══════════════════════════════════════════════════════════════ */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }

/* Style the native sidebar toggle arrow to match the theme */
[data-testid="collapsedControl"] button {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-accent) !important;
    border-radius: var(--radius) !important;
    color: var(--gold) !important;
}
    </style>
    """, unsafe_allow_html=True)



# ─── Helper renderers ──────────────────────────────────────────────────────────

def render_news_card(article: dict):
    """Drop-in replacement for the raw st.markdown news block."""
    st.markdown(f"""
    <div class="news-card">
        <a href="{article['link']}" target="_blank">{article['title']}</a>
        <div class="meta">🔗 {article['source']} &nbsp;·&nbsp; {article['date']}</div>
        <div class="snippet">{article['snippet'][:220]}{'…' if len(article['snippet']) > 220 else ''}</div>
    </div>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: str, delta: str = "", delta_up: bool = True):
    """
    Usage:
        render_metric_card("Market Cap", "$1.2T", "+4.2%", delta_up=True)
    """
    delta_class = "up" if delta_up else "down"
    delta_html = f'<div class="delta {delta_class}">{delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_section_badge(text: str):
    st.markdown(f'<div class="section-badge">{text}</div>', unsafe_allow_html=True)