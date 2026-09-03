"""
Streamlit UI for the multi-agent research pipeline.

Run with:
    streamlit run app.py

Expects `pipeline.py` (with run_research_pipeline_stream / run_research_pipeline)
and its `agents` module (invoke_search_agent, invoke_scrape_agent, writer_chain,
critic_chain) to be importable from this directory.
"""

import html
import re
import time
from datetime import datetime

import streamlit as st

from pipeline import run_research_pipeline_stream

# --------------------------------------------------------------------------- #
# Page config & styling
# --------------------------------------------------------------------------- #

st.set_page_config(
    page_title="Research Agent",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --ink:        #10141C;
        --surface:    #171D28;
        --surface-2:  #1E2635;
        --line:       #2B3444;
        --brass:      #C9A15C;
        --brass-dim:  #8A7345;
        --teal:       #4FD1C5;
        --coral:      #E5786C;
        --text:       #ECEEF3;
        --text-dim:   #8A93A6;
        --text-faint: #5C6577;
    }

    #MainMenu, footer, header[data-testid="stHeader"] {visibility: hidden;}

    .stApp {
        background:
            radial-gradient(1200px 600px at 12% -10%, #1a2130 0%, transparent 55%),
            var(--ink);
        color: var(--text);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    p, span, div, label, li { color: var(--text); }

    ::selection { background: var(--brass); color: #10141C; }
    a { color: var(--brass); }

    *:focus-visible {
        outline: 2px solid var(--brass) !important;
        outline-offset: 2px;
    }

    /* ---------- Header ---------- */
    .app-header {
        padding: 2.4rem 2.6rem 2.1rem;
        border-radius: 4px;
        background: linear-gradient(180deg, var(--surface) 0%, var(--ink) 100%);
        border: 1px solid var(--line);
        border-left: 3px solid var(--brass);
        margin-bottom: 1.75rem;
    }
    .app-kicker {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        color: var(--brass);
        margin-bottom: 0.6rem;
    }
    .app-header h1 {
        margin: 0;
        font-family: 'Fraunces', Georgia, serif;
        font-weight: 600;
        font-size: 2.6rem;
        letter-spacing: -0.01em;
        color: var(--text);
        line-height: 1.1;
    }
    .app-header h1 em { font-style: italic; color: var(--brass); }
    .app-header p {
        margin: 0.7rem 0 0 0;
        max-width: 640px;
        color: var(--text-dim);
        font-size: 1rem;
        line-height: 1.55;
    }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--line);
    }
    .sidebar-title {
        font-family: 'Fraunces', Georgia, serif;
        font-size: 1.35rem;
        font-weight: 600;
        color: var(--text);
        margin-bottom: 0.3rem;
    }
    .sidebar-subtitle {
        font-size: 0.85rem;
        color: var(--text-dim);
        line-height: 1.5;
        margin-bottom: 0.2rem;
    }
    .sidebar-empty {
        font-size: 0.83rem;
        color: var(--text-faint);
        font-style: italic;
    }
    .history-item { font-size: 0.85rem; margin-bottom: 0.7rem; }
    .history-item .h-topic { color: var(--text); display: block; }
    .history-item .h-time {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: var(--text-faint);
    }

    /* ---------- Input card (main area) ---------- */
    .st-key-input_card {
        background: var(--surface);
        border: 1px solid var(--line);
        border-left: 3px solid var(--brass);
        border-radius: 4px;
        padding: 2.1rem 2.4rem 2rem;
        margin-bottom: 1.9rem;
    }
    .input-eyebrow {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.06em;
        color: var(--text-faint);
        margin-bottom: 0.9rem;
    }
    .st-key-input_card .stTextArea textarea {
        background: var(--ink);
        color: var(--text);
        border: 1px solid var(--line);
        border-radius: 4px;
        font-size: 1.08rem;
        line-height: 1.6;
        padding: 1.1rem 1.2rem;
    }
    .st-key-input_card .stTextArea textarea::placeholder { color: var(--text-faint); }
    .st-key-input_card .stTextArea textarea:focus {
        border-color: var(--brass);
        box-shadow: 0 0 0 1px var(--brass);
    }
    .chip-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.05em;
        color: var(--text-faint);
        margin: 1.2rem 0 0.6rem;
    }
    /* example chips: quiet, small, clearly secondary */
    .st-key-chip_row .stButton > button {
        font-size: 0.82rem;
        color: var(--text-dim);
        background: transparent;
    }
    .st-key-chip_row .stButton > button:hover {
        color: var(--brass);
        border-color: var(--brass-dim);
    }

    /* run button: the one unmistakable call to action */
    .st-key-run_row { margin-top: 1.3rem; }
    .st-key-run_row .stButton > button {
        font-size: 1.05rem;
        font-weight: 700;
        padding: 0.9rem 1.5rem;
        letter-spacing: 0.01em;
        box-shadow: 0 6px 24px rgba(201,161,92,0.25);
    }
    .st-key-run_row .stButton > button:hover {
        box-shadow: 0 8px 28px rgba(201,161,92,0.38);
    }

    /* ---------- Section labels ---------- */
    .panel-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        letter-spacing: 0.03em;
        color: var(--text-faint);
        border-bottom: 1px solid var(--line);
        padding-bottom: 0.6rem;
        margin-bottom: 1.1rem;
    }

    /* ---------- Timeline (progress, in sidebar) ---------- */
    .timeline { display: flex; flex-direction: column; }
    .tl-item { display: flex; gap: 0.85rem; }
    .tl-rail { display: flex; flex-direction: column; align-items: center; width: 26px; flex-shrink: 0; }
    .tl-dot {
        width: 26px; height: 26px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.74rem; font-weight: 600;
        border: 1.5px solid var(--line);
        background: var(--ink);
        color: var(--text-faint);
        transition: all 0.35s ease;
        flex-shrink: 0;
    }
    .tl-line { width: 1.5px; flex: 1; min-height: 24px; background: var(--line); transition: background 0.35s ease; }
    .tl-content { padding-bottom: 1.3rem; padding-top: 0.05rem; }
    .tl-label { font-weight: 600; font-size: 0.86rem; color: var(--text-faint); transition: color 0.3s ease; }
    .tl-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.66rem; color: var(--text-faint); margin-top: 0.15rem;
    }

    .tl-item.done .tl-dot   { border-color: var(--teal); background: rgba(79,209,197,0.12); color: var(--teal); }
    .tl-item.done .tl-line  { background: var(--teal); opacity: 0.55; }
    .tl-item.done .tl-label { color: var(--text); }
    .tl-item.done .tl-sub   { color: var(--teal); }

    .tl-item.running .tl-dot {
        border-color: var(--brass);
        background: rgba(201,161,92,0.14);
        color: var(--brass);
        animation: pulse 1.6s ease-out infinite;
    }
    .tl-item.running .tl-label { color: var(--text); }
    .tl-item.running .tl-sub   { color: var(--brass); }

    .tl-item.error .tl-dot   { border-color: var(--coral); background: rgba(229,120,108,0.14); color: var(--coral); }
    .tl-item.error .tl-label { color: var(--coral); }
    .tl-item.error .tl-sub   { color: var(--coral); }

    @keyframes pulse {
        0%   { box-shadow: 0 0 0 0 rgba(201,161,92,0.45); }
        70%  { box-shadow: 0 0 0 8px rgba(201,161,92,0); }
        100% { box-shadow: 0 0 0 0 rgba(201,161,92,0); }
    }

    /* ---------- Output surfaces ---------- */
    .output-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; margin: -0.4rem 0 1.2rem; }
    .output-meta .meta-topic {
        font-family: 'Fraunces', Georgia, serif;
        font-size: 1.15rem;
        color: var(--text);
        margin-right: 0.4rem;
    }
    .meta-pill {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.03em;
        color: var(--text-dim);
        background: var(--surface-2);
        border: 1px solid var(--line);
        border-radius: 999px;
        padding: 0.22rem 0.7rem;
    }
    .meta-pill.ok { color: var(--teal); border-color: rgba(79,209,197,0.35); }

    .empty-state {
        border: 1px dashed var(--line);
        border-radius: 4px;
        padding: 2.6rem 1.5rem;
        text-align: center;
        color: var(--text-faint);
        font-size: 0.9rem;
    }
    .empty-state .glyph { font-size: 1.6rem; margin-bottom: 0.6rem; opacity: 0.6; }

    .status-banner {
        display: flex;
        gap: 0.7rem;
        align-items: flex-start;
        border: 1px solid var(--line);
        border-left: 3px solid var(--coral);
        background: var(--surface);
        border-radius: 4px;
        padding: 1.1rem 1.3rem;
        font-size: 0.9rem;
        color: #F0A79C;
        line-height: 1.55;
    }
    .status-banner .glyph { color: var(--coral); font-size: 1.05rem; flex-shrink: 0; }

    /* doc card header (used above a plain st.markdown body for real markdown rendering) */
    .doc-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 1rem;
        background: var(--surface-2);
        border: 1px solid var(--line);
        border-bottom: none;
        border-radius: 4px 4px 0 0;
        padding: 0.7rem 1.5rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.05em;
        color: var(--text-faint);
    }
    .doc-head .doc-meta { color: var(--text-faint); white-space: nowrap; }
    .doc-head.brass span:first-child { color: var(--brass); }
    .doc-head.coral span:first-child { color: var(--coral); }
    .doc-head.teal  span:first-child { color: var(--teal); }

    /* prose bodies: report + review, rendered via real st.markdown for correct heading/bold parsing */
    .st-key-doc_report, .st-key-doc_review {
        background: var(--surface);
        border: 1px solid var(--line);
        border-top: none;
        border-radius: 0 0 4px 4px;
        padding: 2rem 2.2rem 1.4rem;
        animation: reveal 0.45s ease;
    }
    .st-key-doc_report { border-left: 3px solid var(--brass); }
    .st-key-doc_review { border-left: 3px solid var(--coral); }
    .st-key-doc_report h1, .st-key-doc_report h2, .st-key-doc_report h3,
    .st-key-doc_review h1, .st-key-doc_review h2, .st-key-doc_review h3 {
        font-family: 'Fraunces', Georgia, serif;
        color: var(--text);
    }
    .st-key-doc_report h1, .st-key-doc_review h1 { font-size: 1.7rem; margin-top: 0; }
    .st-key-doc_report h2, .st-key-doc_review h2 { font-size: 1.35rem; }
    .st-key-doc_report h3, .st-key-doc_review h3 { font-size: 1.1rem; }
    .st-key-doc_report p, .st-key-doc_report li,
    .st-key-doc_review p, .st-key-doc_review li {
        color: #D6DAE3;
        line-height: 1.75;
        font-size: 0.98rem;
    }
    .st-key-doc_report strong, .st-key-doc_review strong { color: var(--text); }
    .st-key-doc_report a, .st-key-doc_review a { color: var(--brass); }

    /* raw bodies: search + scrape, plain escaped text reflowed into paragraphs */
    .doc-raw {
        background: var(--surface);
        border: 1px solid var(--line);
        border-top: none;
        border-left: 3px solid var(--teal);
        border-radius: 0 0 4px 4px;
        max-height: 480px;
        overflow-y: auto;
        animation: reveal 0.45s ease;
    }
    .doc-raw-body {
        padding: 1.5rem 1.7rem 1.7rem;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        line-height: 1.8;
        color: #C7CCD8;
        max-width: 74ch;
    }
    .doc-raw-body p { margin: 0 0 1.05rem 0; word-break: break-word; }
    .doc-raw-body p:last-child { margin-bottom: 0; }
    .doc-empty { color: var(--text-faint); font-style: italic; }

    .doc-raw::-webkit-scrollbar { width: 9px; }
    .doc-raw::-webkit-scrollbar-track { background: var(--surface); }
    .doc-raw::-webkit-scrollbar-thumb { background: var(--line); border-radius: 5px; }
    .doc-raw::-webkit-scrollbar-thumb:hover { background: var(--brass-dim); }

    @keyframes reveal {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    /* ---------- Streamlit widget restyle ---------- */
    .stButton > button {
        border-radius: 4px;
        border: 1px solid var(--line);
        background: var(--surface-2);
        color: var(--text);
        font-weight: 500;
        transition: border-color 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease;
    }
    .stButton > button:hover { border-color: var(--brass); color: var(--brass); transform: translateY(-1px); }
    .stButton > button[kind="primary"] {
        background: var(--brass);
        border-color: var(--brass);
        color: #14181F;
        font-weight: 700;
    }
    .stButton > button[kind="primary"]:hover { background: #D8AE68; color: #14181F; }
    .stButton > button[kind="primary"]:disabled {
        background: var(--surface-2);
        color: var(--text-faint);
        border-color: var(--line);
        box-shadow: none;
    }

    .stDownloadButton > button {
        border-radius: 4px;
        border: 1px solid var(--brass-dim);
        background: transparent;
        color: var(--brass);
        font-size: 0.85rem;
    }
    .stDownloadButton > button:hover { background: rgba(201,161,92,0.1); border-color: var(--brass); }

    div[data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid var(--line); }
    button[data-baseweb="tab"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: var(--text-faint);
        background: transparent;
    }
    button[data-baseweb="tab"][aria-selected="true"] { color: var(--brass); }
    div[data-baseweb="tab-highlight"] { background-color: var(--brass); height: 2px; }

    hr { border-color: var(--line) !important; }
    [data-testid="stCaptionContainer"] { color: var(--text-faint); }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Session state
# --------------------------------------------------------------------------- #

defaults = {
    "is_running": False,
    "steps": {
        1: {"label": "Searching the web", "status": "pending", "notice": ""},
        2: {"label": "Scraping top resources", "status": "pending", "notice": ""},
        3: {"label": "Writing the report", "status": "pending", "notice": ""},
        4: {"label": "Reviewing the report", "status": "pending", "notice": ""},
    },
    "result": None,
    "error": None,
    "topic": "",
    "history": [],       # list of {topic, timestamp, duration}
    "completed_at": None,
    "duration": None,
    "topic_text": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

STATUS_SUB = {"pending": "Waiting", "running": "In progress", "done": "Complete", "error": "Failed"}


def format_raw_text(text: str) -> str:
    """Escape and reflow raw agent output into readable paragraphs with clickable URLs."""
    text = (text or "").strip()
    if not text:
        return '<p class="doc-empty">Nothing captured for this step.</p>'

    def make_links(paragraph: str) -> str:
        escaped = html.escape(paragraph)
        url_pattern = r"https?://[^\s<>'\"]+|www\.[^\s<>'\"]+"
        return re.sub(
            url_pattern,
            lambda match: (
                f'<a href="{match.group(0)}" target="_blank" '
                'rel="noopener noreferrer">'
                f'{match.group(0)}</a>'
            ),
            escaped,
        )

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    rendered = []
    for para in paragraphs:
        para_lines = [make_links(line) for line in para.splitlines() if line.strip()]
        if not para_lines:
            continue
        rendered.append(f"<p>{'<br>'.join(para_lines)}</p>")

    return "".join(rendered) if rendered else '<p class="doc-empty">Nothing captured for this step.</p>'


def text_stats(text: str) -> str:
    """Return a short 'N words · ~M min read' meta string."""
    words = len((text or "").split())
    if not words:
        return "0 words"
    minutes = max(1, round(words / 200))
    return f"{words:,} words, ~{minutes} min read"


def format_duration(seconds) -> str:
    if not seconds:
        return "—"
    seconds = int(round(seconds))
    if seconds < 60:
        return f"{seconds}s"
    m, s = divmod(seconds, 60)
    return f"{m}m {s:02d}s"


def reset_steps():
    st.session_state.steps = {
        1: {"label": "Searching the web", "status": "pending", "notice": ""},
        2: {"label": "Scraping top resources", "status": "pending", "notice": ""},
        3: {"label": "Writing the report", "status": "pending", "notice": ""},
        4: {"label": "Reviewing the report", "status": "pending", "notice": ""},
    }
    st.session_state.result = None
    st.session_state.error = None


def render_progress():
    """Draws the pipeline timeline into whatever placeholder progress_placeholder points at."""
    with progress_placeholder.container():
        st.markdown('<div class="panel-title">PIPELINE PROGRESS</div>', unsafe_allow_html=True)

        items = list(st.session_state.steps.items())
        parts = ['<div class="timeline">']
        for idx, (step_num, info) in enumerate(items):
            status = info["status"]
            sub = info["notice"] or STATUS_SUB[status]
            marker = "✓" if status == "done" else ("✕" if status == "error" else str(step_num))
            is_last = idx == len(items) - 1
            parts.append(f'<div class="tl-item {status}">')
            parts.append('<div class="tl-rail">')
            parts.append(f'<div class="tl-dot">{marker}</div>')
            if not is_last:
                parts.append('<div class="tl-line"></div>')
            parts.append('</div>')
            parts.append(
                f'<div class="tl-content">'
                f'<div class="tl-label">{info["label"]}</div>'
                f'<div class="tl-sub">{sub}</div>'
                f'</div>'
            )
            parts.append('</div>')
        parts.append('</div>')

        st.markdown("".join(parts), unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Sidebar — branding + live pipeline progress + run history
# --------------------------------------------------------------------------- #

with st.sidebar:
    st.markdown('<div class="sidebar-title">Research Agent</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-subtitle">An automated pipeline that searches, reads, '
        'writes, and reviews a topic for you.</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    progress_placeholder = st.empty()
    render_progress()

    st.divider()
    st.markdown('<div class="panel-title">RECENT RUNS</div>', unsafe_allow_html=True)
    if st.session_state.history:
        for h in reversed(st.session_state.history[-8:]):
            st.markdown(
                f'<div class="history-item">'
                f'<span class="h-topic">{h["topic"]}</span>'
                f'<span class="h-time">{h["timestamp"]} · {h.get("duration", "")}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div class="sidebar-empty">Your completed runs will appear here.</div>',
            unsafe_allow_html=True,
        )

# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #

st.markdown(
    """
    <div class="app-header">
        <div class="app-kicker">MULTI-AGENT RESEARCH PIPELINE</div>
        <h1>Turn a question into a <em>sourced report</em></h1>
        <p>Give it a topic. One agent searches, one reads the sources closely, one drafts
        the report, and one reviews it before you see it.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------- #
# Input card (main area)
# --------------------------------------------------------------------------- #

example_topics = [
    "Latest advances in solid-state batteries",
    "How large language models handle reasoning",
    "The economics of vertical farming",
]

with st.container(key="input_card"):
    st.markdown('<div class="input-eyebrow">START A RESEARCH RUN</div>', unsafe_allow_html=True)

    topic_slot = st.empty()

    st.markdown('<div class="chip-label">OR START FROM AN EXAMPLE</div>', unsafe_allow_html=True)
    with st.container(key="chip_row"):
        chip_cols = st.columns(3, gap="small")
        for i, ex in enumerate(example_topics):
            if chip_cols[i].button(ex, use_container_width=True, key=f"ex_{i}"):
                st.session_state["topic_text"] = ex

    topic_input = topic_slot.text_area(
        "Topic",
        key="topic_text",
        placeholder="e.g. The impact of quantum computing on cryptography",
        height=140,
        label_visibility="collapsed",
    )

    with st.container(key="run_row"):
        run_clicked = st.button(
            "Run research" if not st.session_state.is_running else "Running…",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.is_running,
        )

st.write("")

# --------------------------------------------------------------------------- #
# Output (main area, full width, below the input card)
# --------------------------------------------------------------------------- #

output_placeholder = st.empty()


def render_output():
    with output_placeholder.container():
        st.markdown('<div class="panel-title">OUTPUT</div>', unsafe_allow_html=True)

        if st.session_state.error:
            st.markdown(
                f'<div class="status-banner"><span class="glyph">⚠</span>'
                f'<span>The pipeline stopped: {html.escape(st.session_state.error)}</span></div>',
                unsafe_allow_html=True,
            )
            return

        if not st.session_state.result:
            st.markdown(
                """
                <div class="empty-state">
                    <div class="glyph">＋</div>
                    Enter a topic above and run the pipeline.<br>Your report will appear here.
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

        result = st.session_state.result
        report = result.get("report") or ""
        review = result.get("critic_feedback") or ""

        # meta strip
        meta_html = (
            '<div class="output-meta">'
            f'<span class="meta-topic">{html.escape(st.session_state.topic)}</span>'
            '<span class="meta-pill ok">4/4 stages complete</span>'
            f'<span class="meta-pill">{st.session_state.completed_at or ""}</span>'
            f'<span class="meta-pill">{format_duration(st.session_state.duration)}</span>'
            '</div>'
        )
        st.markdown(meta_html, unsafe_allow_html=True)

        tab_report, tab_review, tab_search, tab_scrape = st.tabs(
            ["REPORT", "REVIEW", "SEARCH RESULTS", "SOURCES"]
        )

        with tab_report:
            st.markdown(
                f'<div class="doc-head brass"><span>REPORT</span>'
                f'<span class="doc-meta">{text_stats(report)}</span></div>',
                unsafe_allow_html=True,
            )
            with st.container(key="doc_report"):
                st.markdown(report if report else "_No report generated._")
            st.write("")
            st.download_button(
                "Download report (.md)",
                data=report,
                file_name=f"{st.session_state.topic.strip().replace(' ', '_') or 'report'}.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with tab_review:
            st.markdown(
                f'<div class="doc-head coral"><span>REVIEW</span>'
                f'<span class="doc-meta">{text_stats(review)}</span></div>',
                unsafe_allow_html=True,
            )
            with st.container(key="doc_review"):
                st.markdown(review if review else "_No feedback available._")

        with tab_search:
            search_text = result.get("search_results") or ""
            st.markdown(
                f'<div class="doc-head teal"><span>SEARCH RESULTS</span>'
                f'<span class="doc-meta">{len(search_text)} chars</span></div>'
                f'<div class="doc-raw"><div class="doc-raw-body">{format_raw_text(search_text)}</div></div>',
                unsafe_allow_html=True,
            )

        with tab_scrape:
            scraped_text = result.get("scraped_content") or ""
            st.markdown(
                f'<div class="doc-head teal"><span>SOURCES</span>'
                f'<span class="doc-meta">{len(scraped_text)} chars</span></div>'
                f'<div class="doc-raw"><div class="doc-raw-body">{format_raw_text(scraped_text)}</div></div>',
                unsafe_allow_html=True,
            )


render_output()

# --------------------------------------------------------------------------- #
# Run the pipeline
# --------------------------------------------------------------------------- #

if run_clicked:
    if not topic_input or not topic_input.strip():
        st.warning("Please enter a research topic first.")
    else:
        st.session_state.is_running = True
        st.session_state.topic = topic_input.strip()
        reset_steps()
        render_progress()
        render_output()

        start_ts = time.time()

        try:
            for event in run_research_pipeline_stream(st.session_state.topic):
                step = event.get("step")

                if step == "final":
                    elapsed = time.time() - start_ts
                    st.session_state.result = event["state"]
                    st.session_state.completed_at = datetime.now().strftime("%I:%M %p")
                    st.session_state.duration = elapsed
                    st.session_state.history.append(
                        {
                            "topic": st.session_state.topic,
                            "timestamp": datetime.now().strftime("%b %d, %H:%M"),
                            "duration": format_duration(elapsed),
                        }
                    )
                    break

                status = event.get("status")
                if step in st.session_state.steps:
                    st.session_state.steps[step]["status"] = status
                    st.session_state.steps[step]["notice"] = event.get("notice", "")

                if status == "error":
                    st.session_state.error = event.get("error", "Unknown error")
                    break

                render_progress()
                time.sleep(0.05)  # small pause so the UI visibly updates

        except Exception as exc:  # safety net around the generator itself
            st.session_state.error = str(exc)

        st.session_state.is_running = False
        render_progress()
        render_output()

        if st.session_state.result:
            st.toast("Report ready.", icon="✅")
        elif st.session_state.error:
            st.toast("Pipeline stopped. See details above.", icon="❌")