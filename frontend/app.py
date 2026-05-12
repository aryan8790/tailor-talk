"""
TailorTalk — Streamlit Chat Frontend
A polished chat interface that talks to the FastAPI backend.
"""

import os
import time
import requests
import streamlit as st

# ─── Configuration ────────────────────────────────────────────────────────────

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_TIMEOUT = 60  # seconds


# ─── Page Setup ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="TailorTalk · Drive Assistant",
    page_icon="🗂️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* ── Import fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    /* ── Root variables ── */
    :root {
        --bg:        #0d0f14;
        --surface:   #161a23;
        --border:    #252b3b;
        --accent:    #4f8ef7;
        --accent2:   #7b5cf7;
        --text:      #e8eaf0;
        --muted:     #6b7394;
        --user-bg:   #1a2540;
        --bot-bg:    #161a23;
        --radius:    14px;
        --font:      'Sora', sans-serif;
        --mono:      'JetBrains Mono', monospace;
    }

    /* ── Global reset ── */
    html, body, [class*="css"] {
        font-family: var(--font) !important;
        background-color: var(--bg) !important;
        color: var(--text) !important;
    }

    /* ── Hide Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }
    .stDeployButton { display: none; }

    /* ── Main container ── */
    .main .block-container {
        max-width: 780px;
        padding: 0 1.5rem 6rem;
        margin: 0 auto;
    }

    /* ── Header ── */
    .tt-header {
        text-align: center;
        padding: 2.5rem 0 1.5rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.5rem;
    }
    .tt-logo {
        font-size: 2rem;
        margin-bottom: .25rem;
    }
    .tt-title {
        font-size: 1.55rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent), var(--accent2));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -.02em;
    }
    .tt-subtitle {
        font-size: .85rem;
        color: var(--muted);
        margin-top: .2rem;
        font-weight: 300;
    }

    /* ── Chat bubbles ── */
    .chat-row {
        display: flex;
        margin: .65rem 0;
        gap: .75rem;
        animation: fadeUp .25s ease;
    }
    .chat-row.user  { flex-direction: row-reverse; }
    .chat-row.bot   { flex-direction: row; }

    .avatar {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        flex-shrink: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        font-weight: 600;
        line-height: 1;
    }
    .avatar.user { background: linear-gradient(135deg, var(--accent), var(--accent2)); }
    .avatar.bot  { background: var(--surface); border: 1px solid var(--border); }

    .bubble {
        max-width: 78%;
        padding: .8rem 1.1rem;
        border-radius: var(--radius);
        font-size: .92rem;
        line-height: 1.65;
        word-break: break-word;
    }
    .bubble.user {
        background: var(--user-bg);
        border: 1px solid var(--accent);
        border-top-right-radius: 4px;
    }
    .bubble.bot {
        background: var(--bot-bg);
        border: 1px solid var(--border);
        border-top-left-radius: 4px;
    }

    /* Markdown inside bubbles */
    .bubble strong { color: var(--accent); font-weight: 600; }
    .bubble a      { color: var(--accent); text-decoration: underline; }
    .bubble code   { font-family: var(--mono); background: rgba(79,142,247,.12);
                     padding: .1em .35em; border-radius: 4px; font-size: .84em; }
    .bubble ul, .bubble ol { padding-left: 1.25rem; }

    /* ── Typing indicator ── */
    .typing {
        display: flex; align-items: center; gap: 5px;
        padding: .6rem 1rem;
    }
    .typing span {
        width: 8px; height: 8px; border-radius: 50%;
        background: var(--muted);
        animation: bounce 1.2s infinite ease-in-out;
    }
    .typing span:nth-child(2) { animation-delay: .2s; }
    .typing span:nth-child(3) { animation-delay: .4s; }

    @keyframes bounce {
        0%, 80%, 100% { transform: scale(.7); opacity: .5; }
        40%           { transform: scale(1);  opacity: 1;  }
    }

    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0);   }
    }

    /* ── Input bar ── */
    .stChatInput > div {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
    }
    .stChatInput textarea {
        background: transparent !important;
        color: var(--text) !important;
        font-family: var(--font) !important;
    }
    .stChatInput button {
        background: var(--accent) !important;
        border-radius: 10px !important;
    }

    /* ── Suggestions ── */
    .suggestion-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: .6rem;
        margin: 1.5rem 0;
    }
    .suggestion-btn {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: .65rem 1rem;
        font-size: .83rem;
        color: var(--muted);
        cursor: pointer;
        text-align: left;
        transition: all .15s ease;
    }
    .suggestion-btn:hover {
        border-color: var(--accent);
        color: var(--text);
        background: rgba(79,142,247,.06);
    }

    /* ── Status badge ── */
    .status-badge {
        display: inline-flex; align-items: center; gap: .4rem;
        font-size: .78rem; color: var(--muted);
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: .3rem .85rem;
        margin-bottom: 1rem;
    }
    .status-dot { width: 7px; height: 7px; border-radius: 50%; background: #3ecf6a; }

    /* Scrollable chat area */
    .chat-area { max-height: 62vh; overflow-y: auto; padding-right: .25rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─── State ────────────────────────────────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history: list[dict] = []

if "pending" not in st.session_state:
    st.session_state.pending = False


# ─── Helpers ─────────────────────────────────────────────────────────────────

def call_backend(user_message: str) -> str:
    """POST to the FastAPI /chat endpoint."""
    payload = {
        "message": user_message,
        "history": st.session_state.history,
    }
    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json=payload,
            timeout=API_TIMEOUT,
        )
        response.raise_for_status()
        return response.json().get("reply", "No response from agent.")
    except requests.exceptions.ConnectionError:
        return (
            "❌ **Cannot reach the backend.** "
            "Make sure the FastAPI server is running at `" + BACKEND_URL + "`."
        )
    except requests.exceptions.Timeout:
        return "⏱️ The request timed out. Please try again."
    except requests.exceptions.HTTPError as e:
        detail = ""
        try:
            detail = response.json().get("detail", "")
        except Exception:
            pass
        return f"❌ Backend error {e.response.status_code}: {detail or str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {e}"


def render_bubble(role: str, content: str):
    icon = "👤" if role == "user" else "🗂️"
    cls = "user" if role == "user" else "bot"
    st.markdown(
        f"""
        <div class="chat-row {cls}">
            <div class="avatar {cls}">{icon}</div>
            <div class="bubble {cls}">{content}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


SUGGESTIONS = [
    "📄 Show me all PDF files",
    "🔍 Find files containing 'budget'",
    "🖼️ List all images in the folder",
    "📅 What was modified last month?",
    "📊 Find any spreadsheets",
    "🔤 Search for files named 'report'",
]


# ─── Layout ───────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="tt-header">
        <div class="tt-logo">🗂️</div>
        <div class="tt-title">TailorTalk Drive Assistant</div>
        <div class="tt-subtitle">Conversational file discovery powered by AI</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Status badge
st.markdown(
    '<div class="status-badge"><span class="status-dot"></span>Connected to Drive</div>',
    unsafe_allow_html=True,
)

# ── Suggestion chips (only when no history) ────────────────────────────────
if not st.session_state.history:
    st.markdown("**Try asking:**")
    cols = st.columns(3)
    for i, suggestion in enumerate(SUGGESTIONS):
        with cols[i % 3]:
            if st.button(suggestion, key=f"sug_{i}", use_container_width=True):
                st.session_state.history.append({"role": "user", "content": suggestion})
                st.session_state.pending = True
                st.rerun()

# ── Chat history ──────────────────────────────────────────────────────────
chat_container = st.container()
with chat_container:
    for turn in st.session_state.history:
        render_bubble(turn["role"], turn["content"])

    # Typing indicator while waiting
    if st.session_state.pending:
        st.markdown(
            '<div class="chat-row bot">'
            '<div class="avatar bot">🗂️</div>'
            '<div class="bubble bot typing">'
            '<span></span><span></span><span></span>'
            '</div></div>',
            unsafe_allow_html=True,
        )

# ── Process pending message ───────────────────────────────────────────────
if st.session_state.pending:
    user_msg = st.session_state.history[-1]["content"]
    reply = call_backend(user_msg)
    st.session_state.history.append({"role": "assistant", "content": reply})
    st.session_state.pending = False
    st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about your files… e.g. 'Find invoices from June'"):
    st.session_state.history.append({"role": "user", "content": prompt})
    st.session_state.pending = True
    st.rerun()

# ── Clear chat button ─────────────────────────────────────────────────────
if st.session_state.history:
    with st.sidebar:
        st.markdown("### Session")
        st.caption(f"{len(st.session_state.history)} messages")
        if st.button("🗑️ Clear chat", use_container_width=True):
            st.session_state.history = []
            st.session_state.pending = False
            st.rerun()
