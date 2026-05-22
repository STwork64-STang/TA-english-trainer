import streamlit as st
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval
from google import genai
from google.genai.errors import APIError
import json
import re
import random
from gtts import gTTS
import io

# ─── 1. INITIALIZE SESSION STATE ─────────────────────────────────────────────
if "user_level" not in st.session_state:
    st.session_state["user_level"] = "Level 1: Beginner"
if "topic" not in st.session_state:
    st.session_state["topic"] = "General Academic"
if "flash_mode" not in st.session_state:
    st.session_state["flash_mode"] = "study"
if "saved_key" not in st.session_state:
    st.session_state["saved_key"] = ""
if "oxford_mode" not in st.session_state:
    st.session_state["oxford_mode"] = False

st.set_page_config(
    page_title="Academic English AI Trainer",
    page_icon="📖",
    layout="centered"
)

# ─── OXFORD DB LOADER ────────────────────────────────────────────────────────
import os

@st.cache_data
def load_oxford_db() -> dict:
    """Load oxford_db.json if it exists. Returns {} if not found."""
    path = os.path.join(os.path.dirname(__file__), "oxford_db.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

OXFORD_DB = load_oxford_db()
OXFORD_DB_AVAILABLE = bool(OXFORD_DB)
def get_oxford_cards_local(level: str, n: int = 5) -> list[dict]:
    """Pick n random cards from local oxford_db.json by mapping CEFR levels."""
    if not OXFORD_DB:
        return []
        
    # แปลงระดับจากหน้าบ้านให้ตรงกับ Key ในไฟล์ JSON (ปรับให้ตรงกับคีย์ที่มีในไฟล์ของคุณ)
    if "Beginner" in level:
        # ลองดึงคีย์ A1 ถ้าไม่มีให้ลองหา A2 หรือถ้าเก็บเป็น "A1-A2" ก็เปลี่ยนเป็น OXFORD_DB.get("A1-A2", [])
        pool = OXFORD_DB.get("A1", []) + OXFORD_DB.get("A2", [])
    elif "Intermediate" in level:
        pool = OXFORD_DB.get("B1", []) + OXFORD_DB.get("B2", [])
    else:
        pool = OXFORD_DB.get("C1", []) + OXFORD_DB.get("C2", [])
        
    if not pool:
        return []
        
    return random.sample(pool, min(n, len(pool)))

# Fallback seed words (used only when oxford_db.json not yet generated)
OXFORD_SEED_FALLBACK = {
    "A1-A2": ["able","accept","agree","allow","answer","arrive","ask","become",
               "begin","believe","carry","change","choose","create","decide"],
    "B1-B2": ["analyse","anticipate","assess","collaborate","consequence",
               "demonstrate","evaluate","facilitate","identify","investigate"],
    "C1-C2": ["articulate","autonomous","coerce","disseminate","empirical",
               "exacerbate","extrapolate","paradigm","scrutinize","substantiate"],
}

def get_oxford_seed_fallback(level: str, n: int = 8) -> list[str]:
    if "Beginner" in level:
        pool = OXFORD_SEED_FALLBACK["A1-A2"]
    elif "Intermediate" in level:
        pool = OXFORD_SEED_FALLBACK["B1-B2"]
    else:
        pool = OXFORD_SEED_FALLBACK["C1-C2"]
    return random.sample(pool, min(n, len(pool)))

# ─── 2. CSS — WARM READING NOOK (light mode locked) ──────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,400&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;0,8..60,600;1,8..60,400&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

/* ── WARM READING PALETTE ──
   Warm parchment background, aged-paper cards, amber ink accents.
   Feels like sitting with a good book under a lamp.
*/
:root {
    --ink:         #1E1810;   /* deep warm almost-black for text       */
    --ink-muted:   #6B5E4A;   /* secondary text, labels                */
    --ink-faint:   #9E8E78;   /* placeholder, captions                 */
    --parchment:   #F5F0E4;   /* app background — aged paper           */
    --page:        #FBF8F2;   /* card / panel surface                  */
    --page-warm:   #F8F3E8;   /* slightly richer card variant          */
    --rule:        #DDD5C4;   /* dividers, borders                     */
    --rule-light:  #EAE4D8;   /* very light borders                    */
    --amber:       #C8922A;   /* primary accent — amber ink            */
    --amber-light: #E8B855;   /* highlight                             */
    --amber-bg:    #FDF4E0;   /* amber tint background                 */
    --amber-deep:  #9E6E18;   /* pressed / hover deep amber            */
    --sepia-1:     #3A2E1E;   /* flashcard dark face                   */
    --sepia-2:     #4A3C26;   /* flashcard dark hover                  */
    --correct-bg:  #EFF7EE;
    --correct-bd:  #A8C9A0;
    --correct-txt: #1C4A1E;
    --wrong-bg:    #FBF0EE;
    --wrong-bd:    #E0A8A0;
    --wrong-txt:   #5A1A18;
}

*, *::before, *::after { box-sizing: border-box; }

/* Force light everywhere — override Streamlit's theming */
.stApp,
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stMainBlockContainer"],
section[data-testid="stSidebar"] {
    background-color: var(--parchment) !important;
    color: var(--ink) !important;
}

/* Subtle paper texture via SVG noise */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
    background-repeat: repeat;
    pointer-events: none;
    z-index: 0;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 2.5rem;
    padding-bottom: 5rem;
    max-width: 740px;
    position: relative;
    z-index: 1;
}

/* ── Header ── */
.app-title {
    font-family: 'Fraunces', serif;
    font-size: 2.6rem;
    color: var(--ink);
    margin-bottom: 0.1rem;
    font-weight: 600;
    letter-spacing: -0.03em;
    line-height: 1.15;
}
.app-sub {
    font-size: 0.78rem;
    color: var(--ink-faint);
    letter-spacing: 0.13em;
    text-transform: uppercase;
    font-weight: 500;
    margin-bottom: 2.5rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.title-accent {
    display: inline-block;
    width: 36px;
    height: 3px;
    background: var(--amber);
    border-radius: 2px;
    margin-bottom: 1.2rem;
}

/* ── Inputs & Selects ── */
.stTextInput > div > div > input,
.stSelectbox [data-baseweb="select"] > div:first-child {
    border-radius: 10px !important;
    border-color: var(--rule) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.875rem !important;
    background: var(--page) !important;
    color: var(--ink) !important;
}
.stTextInput label,
.stSelectbox label,
.stCheckbox label {
    color: var(--ink-muted) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.82rem !important;
}
/* Dropdown list */
[data-baseweb="popover"] li,
[data-baseweb="menu"] li,
[role="option"] {
    background: var(--page) !important;
    color: var(--ink) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
[data-baseweb="popover"] li:hover,
[role="option"]:hover {
    background: var(--amber-bg) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--page-warm);
    padding: 5px;
    border-radius: 12px;
    border: 1px solid var(--rule-light);
    margin-bottom: 1.75rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--ink-muted);
    background: transparent;
    border: none;
    font-family: 'Plus Jakarta Sans', sans-serif;
    letter-spacing: 0.01em;
}
.stTabs [aria-selected="true"] {
    background: var(--page) !important;
    color: var(--ink) !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 0 0 0.5px rgba(0,0,0,0.04) !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none; }

/* ── Buttons ── */
.stButton > button {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    border-radius: 10px !important;
    border: 1.5px solid var(--rule) !important;
    background: var(--page) !important;
    color: var(--ink) !important;
    padding: 9px 18px !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}
.stButton > button:hover {
    border-color: var(--amber) !important;
    background: var(--amber-bg) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 3px 10px rgba(200,146,42,0.18) !important;
    color: var(--amber-deep) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
    background: var(--amber-bg) !important;
}

/* ── Oxford Badge ── */
.oxford-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: var(--amber-bg);
    border: 1px solid var(--amber-light);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--amber-deep);
    font-family: 'Plus Jakarta Sans', sans-serif;
    margin-bottom: 0.5rem;
}

/* ── Flashcard ── */
.flashcard-scene {
    width: 100%;
    height: 240px;
    perspective: 1200px;
    margin: 1rem 0;
}
.flashcard {
    width: 100%;
    height: 100%;
    position: relative;
    transform-style: preserve-3d;
    transition: transform 0.55s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 16px;
}
.flashcard.flipped { transform: rotateY(180deg); }
.flashcard-face {
    position: absolute;
    inset: 0;
    border-radius: 16px;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    display: flex;
    flex-direction: column;
    padding: 2rem 2.25rem;
}
/* Front — warm dark sepia */
.flashcard-front {
    background: var(--sepia-1);
    /* subtle warm grain */
    background-image:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.05'/%3E%3C/svg%3E"),
        linear-gradient(135deg, var(--sepia-1) 0%, var(--sepia-2) 100%);
    color: white;
    box-shadow: 0 8px 32px rgba(0,0,0,0.25), 0 1px 3px rgba(0,0,0,0.1);
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(255,255,255,0.06);
}
/* Back — warm parchment */
.flashcard-back {
    background: var(--page);
    border: 1.5px solid var(--rule);
    transform: rotateY(180deg);
    box-shadow: 0 8px 32px rgba(0,0,0,0.06);
    align-items: flex-start;
    justify-content: flex-start;
    gap: 10px;
    overflow-y: auto;
}
.card-word {
    font-family: 'Fraunces', serif;
    font-size: 2.6rem;
    color: var(--amber);
    text-align: center;
    letter-spacing: -0.02em;
    line-height: 1.1;
}
.card-pron {
    font-size: 1rem;
    opacity: 0.5;
    color: #fff;
    font-weight: 300;
    letter-spacing: 0.04em;
    font-family: 'Source Serif 4', serif;
}
.card-hint {
    font-size: 0.73rem;
    color: rgba(255,255,255,0.3);
    margin-top: 0.75rem;
    letter-spacing: 0.05em;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.card-oxford {
    position: absolute;
    top: 14px;
    right: 18px;
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--amber-light);
    opacity: 0.7;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.back-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--ink-faint);
    font-family: 'Plus Jakarta Sans', sans-serif;
}
.back-value {
    font-size: 0.95rem;
    color: var(--ink);
    line-height: 1.65;
    margin-top: 1px;
    font-family: 'Source Serif 4', serif;
}

/* ── Quiz box ── */
.flashcard-quiz-box {
    background: var(--sepia-1);
    background-image: linear-gradient(135deg, var(--sepia-1) 0%, var(--sepia-2) 100%);
    color: white;
    border-radius: 16px;
    padding: 2.25rem 2rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    margin-bottom: 1.25rem;
}
.quiz-word-title {
    font-family: 'Fraunces', serif;
    font-size: 2.4rem;
    color: var(--amber);
    letter-spacing: -0.02em;
}
.quiz-word-pron {
    font-size: 0.95rem;
    color: rgba(255,255,255,0.4);
    margin-top: 0.4rem;
    font-family: 'Source Serif 4', serif;
}
.quiz-oxford-tag {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--amber-light);
    opacity: 0.65;
    margin-top: 0.6rem;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Quiz answer options */
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: var(--page) !important;
    color: var(--ink) !important;
    border: 1.5px solid var(--rule) !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    text-align: left !important;
    font-weight: 400 !important;
    font-size: 0.875rem !important;
    line-height: 1.4 !important;
    height: auto !important;
    min-height: 52px !important;
    font-family: 'Source Serif 4', serif !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    border-color: var(--amber) !important;
    background: var(--amber-bg) !important;
    color: var(--amber-deep) !important;
}

/* ── Passage Card — the "reading book" feel ── */
.passage-card {
    background: var(--page);
    border-left: 3px solid var(--amber);
    border-radius: 0 14px 14px 0;
    padding: 1.75rem 2rem;
    font-family: 'Source Serif 4', serif;
    font-size: 1.05rem;
    line-height: 1.9;
    color: var(--ink);
    margin-bottom: 1.25rem;
    box-shadow:
        0 1px 4px rgba(0,0,0,0.04),
        inset 0 0 0 1px var(--rule-light);
    letter-spacing: 0.01em;
}

/* ── Quiz Cards ── */
.quiz-card {
    background: var(--page);
    border: 1.5px solid var(--rule-light);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.quiz-q {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    color: var(--ink);
    line-height: 1.5;
    margin-top: 6px;
}
.quiz-type-badge {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: var(--ink-muted);
    background: var(--page-warm);
    padding: 2px 9px;
    border-radius: 5px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* ── Chat Bubbles ── */
.chat-bubble-user {
    background: var(--sepia-1);
    color: #F5EDD8 !important;
    border-radius: 18px 18px 4px 18px;
    padding: 0.75rem 1.1rem;
    font-family: 'Source Serif 4', serif;
    font-size: 0.95rem;
    max-width: 78%;
    margin-left: auto;
    margin-bottom: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    line-height: 1.6;
}
.chat-bubble-ai {
    background: var(--page);
    color: var(--ink) !important;
    border-radius: 18px 18px 18px 4px;
    padding: 0.75rem 1.1rem;
    font-family: 'Source Serif 4', serif;
    font-size: 0.95rem;
    max-width: 78%;
    margin-right: auto;
    margin-bottom: 10px;
    border: 1.5px solid var(--rule-light);
    line-height: 1.6;
}

/* ── Result Boxes ── */
.result-correct {
    background: var(--correct-bg);
    border: 1px solid var(--correct-bd);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: var(--correct-txt);
    font-family: 'Source Serif 4', serif;
    font-size: 0.95rem;
    line-height: 1.65;
    margin-top: 0.5rem;
}
.result-wrong {
    background: var(--wrong-bg);
    border: 1px solid var(--wrong-bd);
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: var(--wrong-txt);
    font-family: 'Source Serif 4', serif;
    font-size: 0.95rem;
    line-height: 1.65;
    margin-top: 0.5rem;
}

/* ── Misc ── */
hr { border-color: var(--rule) !important; margin: 1.5rem 0 !important; }

.stProgress > div > div > div {
    background-color: var(--amber) !important;
    border-radius: 4px;
}
.stProgress > div > div {
    background-color: var(--rule-light) !important;
    border-radius: 4px;
}

.stCaption {
    color: var(--ink-faint) !important;
    font-size: 0.8rem !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

h4 {
    font-family: 'Fraunces', serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    color: var(--ink) !important;
    font-size: 1.35rem !important;
}

/* Streamlit text elements */
p, span, div, label, li,
.stMarkdown,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: var(--ink);
    font-family: 'Plus Jakarta Sans', sans-serif;
}

/* Alert boxes */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
    font-size: 0.875rem !important;
    background: var(--page-warm) !important;
}

/* Chat input */
.stChatInput textarea {
    background: var(--page) !important;
    border-color: var(--rule) !important;
    color: var(--ink) !important;
    font-family: 'Source Serif 4', serif !important;
}
.stChatInput textarea::placeholder { color: var(--ink-faint) !important; }

/* Text input placeholder */
.stTextInput input::placeholder { color: var(--ink-faint) !important; }

/* Vocab pill row */
.vocab-pill-row {
    background: var(--page-warm);
    border: 1px solid var(--rule-light);
    border-radius: 12px;
    padding: 0.85rem 1.1rem;
    font-size: 0.87rem;
    margin-bottom: 1.25rem;
    line-height: 2.2;
}
.vocab-pill-label {
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--ink-faint);
    font-weight: 600;
    display: block;
    margin-bottom: 4px;
    font-family: 'Plus Jakarta Sans', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ─── 3. APP HEADER ───────────────────────────────────────────────────────────
st.markdown('<div class="title-accent"></div>', unsafe_allow_html=True)
st.markdown('<p class="app-title">Academic English<br>Trainer</p>', unsafe_allow_html=True)
st.markdown('<p class="app-sub">AI-Powered · Gemini · ฝึกภาษาอังกฤษเชิงวิชาการ</p>', unsafe_allow_html=True)

# ─── 4. SETTINGS DASHBOARD ───────────────────────────────────────────────────
col_key, col_lvl, col_tpc = st.columns([2, 2, 2])

with col_key:
    api_input = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza...",
        value=st.session_state["saved_key"],
        help="รับคีย์ฟรีที่ https://aistudio.google.com/app/apikey"
    )
    if api_input != st.session_state["saved_key"]:
        st.session_state["saved_key"] = api_input
        st.rerun()

with col_lvl:
    user_level = st.selectbox(
        "ระดับภาษาอังกฤษ",
        ["Level 1: Beginner", "Level 2: Intermediate", "Level 3: Advanced"],
        index=["Level 1: Beginner", "Level 2: Intermediate", "Level 3: Advanced"].index(st.session_state["user_level"])
    )
    if user_level != st.session_state["user_level"]:
        st.session_state["user_level"] = user_level
        st.rerun()

with col_tpc:
    topic = st.selectbox(
        "หัวข้อที่สนใจ",
        ["General Academic", "Science & Technology", "Social Sciences", "Business & Economics", "Medicine & Health", "Law & Ethics", "Literature & Arts"],
        index=["General Academic", "Science & Technology", "Social Sciences", "Business & Economics", "Medicine & Health", "Law & Ethics", "Literature & Arts"].index(st.session_state["topic"])
    )
    if topic != st.session_state["topic"]:
        st.session_state["topic"] = topic
        st.rerun()

api_key = st.session_state["saved_key"]
if not api_key:
    st.warning("⚠️ โปรดระบุ Gemini API Key ในช่องตั้งค่าด้านบนเพื่อเชื่อมต่อระบบบอทและเข้าสู่บทเรียนครับ!")
    st.stop()

# ─── 5. GEMINI HELPER ────────────────────────────────────────────────────────
def call_gemini(prompt: str, max_tokens: int = 500) -> str | None:
    try:
        client = genai.Client(api_key=api_key)
        config = genai.types.GenerateContentConfig(
            max_output_tokens=max_tokens,
            temperature=0.3
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=config
        )
        return response.text
    except APIError as e:
        st.error(f"🚨 Gemini API Error {e.code}: {e.message}")
        return None
    except Exception as e:
        st.error(f"❌ {e}")
        return None

def parse_json(text: str):
    if not text:
        return {}
    clean = text.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        clean = "\n".join(lines).strip()
    return json.loads(clean)

# ─── 6. TABS ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📇 Flashcards", "📄 Reading", "🧩 Vocab Quiz", "💬 Chat"])

# ==============================================================================
# TAB 1 — FLASHCARDS  (with Adaptive Leitner System)
# ==============================================================================
with tab1:
    st.markdown("#### 📇 คลังคำศัพท์อัจฉริยะ")
    st.caption(f"หัวข้อ: **{topic}** · ระดับ: **{user_level}**")

    # จัดระเบียบชื่อระดับ (Clean user_level ให้เหลือแค่ "A1", "B2" เพื่อคุยกับ JSON รู้เรื่อง)
    clean_level = user_level.split()[0] if user_level else ""

    # Oxford 5000 toggle
    oxford_on = st.toggle(
        "🎓 Oxford 5000 Mode — เลือกคำจาก Oxford 5000 เท่านั้น",
        value=st.session_state["oxford_mode"],
        key="oxford_toggle_tab1"
    )
    if oxford_on != st.session_state["oxford_mode"]:
        st.session_state["oxford_mode"] = oxford_on
        st.rerun()

    if st.session_state["oxford_mode"]:
        st.markdown(
            '<div class="oxford-badge">📘 Oxford 5000 Active</div>',
            unsafe_allow_html=True
        )

    if "flash_mode" not in st.session_state:
        st.session_state["flash_mode"] = "study"

    col_m1, col_m2 = st.columns(2)
    with col_m1:
        if st.button("📖 โหมดเรียนรู้ (Flip Card)", key="set_mode_study", use_container_width=True):
            st.session_state["flash_mode"] = "study"
            st.rerun()
    with col_m2:
        if st.button("🎮 โหมดเกมควิซ (Quiz Mode)", key="set_mode_quiz", use_container_width=True):
            st.session_state["flash_mode"] = "quiz"
            st.rerun()

    st.markdown("---")

    # แสดงสถานะ DB (ปรับปรุงตัวนับคำศัพท์ด้วยการแมปคีย์ระดับภาษาให้ตรงกับ JSON)
    if OXFORD_DB_AVAILABLE and st.session_state["oxford_mode"]:
        total_cards = sum(len(v) for v in OXFORD_DB.values())
        
        # 1. ตรวจสอบระดับที่ผู้ใช้เลือกจากหน้าบ้าน (ยึดตามค่าในกล่อง selectbox ของคุณ)
        current_user_level = st.session_state.get("user_level", "Level 1: Beginner")
        
        # 2. แปลงกลุ่มคีย์ให้ตรงกับโครงสร้างไฟล์ JSON
        # (โค้ดนี้จะไปดึงจำนวนคำสะสมของแต่ละระดับย่อยมารวมกันให้สะท้อนตามจริง)
        if "Beginner" in current_user_level:
            level_cards = len(OXFORD_DB.get("A1", [])) + len(OXFORD_DB.get("A2", []))
        elif "Intermediate" in current_user_level:
            level_cards = len(OXFORD_DB.get("B1", [])) + len(OXFORD_DB.get("B2", []))
        else:  # Advanced
            level_cards = len(OXFORD_DB.get("C1", [])) + len(OXFORD_DB.get("C2", []))
            
        st.caption(f"📦 Oxford DB: **{total_cards:,}** คำทั้งหมด · ระดับนี้มี **{level_cards:,}** คำ · ใช้ระบบสุ่มผสม AI แปลสด ⚡")
    
    elif st.session_state["oxford_mode"] and not OXFORD_DB_AVAILABLE:
        st.warning("⚠️ ยังไม่มี oxford_db.json — จะใช้ AI สร้างแทน (รัน generate_oxford_db.py ก่อนเพื่อประหยัด token)")
        
    # ปุ่มสุ่มการ์ด
    btn_label = "🎲 สุ่มคำศัพท์ใหม่จากคลัง (5 ใบ)" if (OXFORD_DB_AVAILABLE and st.session_state["oxford_mode"]) else "🔄 เจนคำศัพท์ใหม่ด้วย AI (5 ใบ)"
    if st.button(btn_label, key="gen_cards"):
        picked_cards = None
        
        if st.session_state["oxford_mode"] and OXFORD_DB_AVAILABLE:
            # 1. สุ่มศัพท์ดิบจากไฟล์ JSON มา 5 คำโดยใช้ clean_level
            picked_raw = get_oxford_cards_local(clean_level, 5)
            
            if picked_raw:
                # 2. ส่งคำศัพท์ดิบไปให้ AI ช่วยเติม คำแปล, คำอ่าน และประโยคตัวอย่าง ให้สมบูรณ์
                with st.spinner("🔮 AI กำลังเตรียมคำแปลและประโยคตัวอย่างอัจฉริยะสำหรับคุณ..."):
                    words_list = [item['word'] for item in picked_raw]
                    
                    raw_ai_response = call_gemini(f"""
                    You are an expert English-Thai lexicographer.
                    I will give you 5 words: {words_list}
                    For each word, you MUST provide:
                    1. "pronunciation": IPA pronunciation (e.g. /əˈbaʊt/)
                    2. "thai": Accurate Thai translation suitable for level {user_level}
                    3. "example": A clear, meaningful English example sentence.
                    4. "definition": A short simple English definition.
                    
                    Return ONLY a valid JSON array matching this exact format:
                    [
                      {{"word": "about", "pronunciation": "/əˈbaʊt/", "definition": "Concerning or on the subject of", "thai": "เกี่ยวกับ", "example": "What are you talking about?", "oxford": true}}
                    ]
                    """, max_tokens=800)
                    
                    try:
                        # 3. นำข้อมูลที่ AI เติมให้เต็มแล้วบันทึกเข้าตัวแปร
                        picked_cards = parse_json(raw_ai_response)
                    except Exception as e:
                        st.error(f"AI คืนค่ารูปแบบไม่ถูกต้อง กรุณากดสุ่มใหม่อีกครั้ง: {e}")
            
            if not picked_cards:
                st.error(f"ไม่พบคำในระดับ '{clean_level}' ใน oxford_db.json หรือ AI แปลผลพลาด กรุณากดลองอีกครั้ง")
        
        else:
            # ── โหมด AI ปกติ (หรือ Oxford แต่ยังไม่มี DB) ──
            with st.spinner("AI กำลังคัดเลือกคำศัพท์วิชาการยอดเยี่ยม..."):
                if st.session_state["oxford_mode"]:
                    seed_words = get_oxford_seed_fallback(user_level, 8)
                    oxford_instruction = (
                        f'IMPORTANT: You MUST choose 5 words from this Oxford 5000 seed list: {seed_words}. '
                        'Each card must include a field "oxford": true.'
                    )
                else:
                    oxford_instruction = 'Include "oxford": false in each card.'

                raw = call_gemini(f"""
You are an academic English vocabulary teacher.
Generate 5 vocabulary flashcards for topic: "{topic}", level: "{user_level}".
{oxford_instruction}
Return ONLY a valid JSON array, no markdown, no extra text.
Each object must have exactly these keys:
{{"word":"...","pronunciation":"...","definition":"...","thai":"...","example":"...","oxford":true/false}}
""", max_tokens=700)
                if raw:
                    try:
                        picked_cards = parse_json(raw)
                    except Exception as e:
                        st.error(f"แปลงข้อมูล JSON ล้มเหลว: {e}\n\n{raw}")

        # ถ้าโหลดหรือเจนคำศัพท์สำเร็จ ให้ทำระบบฉีด Logic ความจำตั้งต้นเข้าไป
        if picked_cards:
            for card in picked_cards:
                card["streak"] = 0         # จำนวนครั้งที่ตอบถูกติดกันเริ่มต้น
                card["mastered"] = False   # สถานะจำได้แม่นยำแล้ว
            
            st.session_state["cards"] = picked_cards
            st.session_state["study_idx"] = 0 # รีเซ็ตหน้าเรียนรู้ให้กลับไปใบที่ 1
            st.session_state["card_idx"] = 0
            st.session_state["flash_score"] = 0
            st.session_state["flash_status"] = None
            if "current_options" in st.session_state:
                del st.session_state["current_options"]
            st.rerun()

    # ── เริ่มส่วนการแสดงผลเนื้อหาคำศัพท์ ──
    if "cards" in st.session_state and st.session_state["cards"]:
        cards = st.session_state["cards"]
        idx = st.session_state.get("card_idx", 0)

        # Safety Check ป้องกัน Index เกินกรณีข้อมูลเปลี่ยนไปมา
        if idx >= len(cards):
            idx = 0
            st.session_state["card_idx"] = 0

        # ── Study Mode ──
        if st.session_state["flash_mode"] == "study":
            st.subheader("👀 ฝึกจำคำศัพท์")

            if "study_idx" not in st.session_state:
                st.session_state["study_idx"] = 0
            s_idx = st.session_state["study_idx"]
            if s_idx >= len(cards):
                st.session_state["study_idx"] = 0
                s_idx = 0

            card = cards[s_idx]
            is_oxford = card.get("oxford", False)

            if f"flipped_{s_idx}" not in st.session_state:
                st.session_state[f"flipped_{s_idx}"] = False

            is_flipped = st.session_state[f"flipped_{s_idx}"]
            flip_class = "flipped" if is_flipped else ""

            oxford_tag = '<div class="card-oxford">Oxford 5000</div>' if is_oxford else ""

            components.html(f"""
            <!DOCTYPE html>
            <html>
            <head>
            <style>
              :root {{
                --ink: #1E1810; --ink-muted: #6B5E4A;
                --page: #FBF8F2; --rule: #DDD5C4;
                --amber: #C8922A; --amber-light: #E8B855; --amber-bg: #FDF4E0;
                --sepia-1: #3A2E1E; --sepia-2: #4A3C26;
              }}
              body {{ margin: 0; background: transparent; font-family: sans-serif; }}
            
              .flashcard-scene {{
                width: 100%; height: 240px;
                perspective: 1200px; margin: 0.5rem 0;
              }}
              .flashcard {{
                width: 100%; height: 100%;
                position: relative;
                transform-style: preserve-3d;
                transition: transform 0.55s cubic-bezier(0.4,0,0.2,1);
                border-radius: 16px;
                cursor: pointer;
              }}
              .flashcard.flipped {{ transform: rotateY(180deg); }}
            
              .flashcard-face {{
                position: absolute; inset: 0;
                border-radius: 16px;
                backface-visibility: hidden;
                -webkit-backface-visibility: hidden;
                display: flex; flex-direction: column;
                padding: 2rem 2.25rem;
              }}
              .flashcard-front {{
                background: linear-gradient(135deg, var(--sepia-1), var(--sepia-2));
                color: white;
                box-shadow: 0 8px 32px rgba(0,0,0,0.25);
                align-items: center; justify-content: center; text-align: center;
              }}
              .flashcard-back {{
                background: var(--page);
                border: 1.5px solid var(--rule);
                transform: rotateY(180deg);
                align-items: flex-start; justify-content: flex-start;
                gap: 10px; overflow-y: auto;
              }}
            
              .card-word {{
                font-size: 2.6rem; color: var(--amber);
                letter-spacing: -0.02em; line-height: 1.1; font-weight: 600;
              }}
              .card-pron {{ font-size: 1rem; opacity: 0.5; color: #fff; margin-top: 4px; }}
              .card-hint {{ font-size: 0.73rem; color: rgba(255,255,255,0.35); margin-top: 0.75rem; }}
              .card-oxford {{
                position: absolute; top: 14px; right: 18px;
                font-size: 0.6rem; font-weight: 700; letter-spacing: 0.1em;
                text-transform: uppercase; color: var(--amber-light); opacity: 0.7;
              }}
              .back-label {{
                font-size: 0.65rem; font-weight: 600; letter-spacing: 0.1em;
                text-transform: uppercase; color: #9E8E78; margin-bottom: 2px;
              }}
              .back-value {{
                font-size: 0.95rem; color: var(--ink); line-height: 1.65;
              }}
              .back-section {{ width: 100%; margin-top: 6px; }}
            
              .flip-btn {{
                margin-top: 12px;
                width: 100%;
                padding: 10px;
                border-radius: 10px;
                border: 1.5px solid var(--rule);
                background: var(--page);
                color: var(--ink);
                font-size: 0.875rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.15s ease;
              }}
              .flip-btn:hover {{
                border-color: var(--amber);
                background: var(--amber-bg);
                color: #9E6E18;
              }}
            
              .nav-row {{
                display: flex; gap: 8px; margin-top: 8px;
              }}
              .nav-btn {{
                flex: 1; padding: 9px;
                border-radius: 10px;
                border: 1.5px solid var(--rule);
                background: var(--page);
                color: var(--ink);
                font-size: 0.85rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.15s ease;
              }}
              .nav-btn:hover {{
                border-color: var(--amber);
                background: var(--amber-bg);
                color: #9E6E18;
              }}
              .nav-btn:disabled {{
                opacity: 0.35; cursor: not-allowed;
              }}
              .counter {{
                text-align: center; font-size: 0.82rem;
                color: #9E8E78; padding-top: 10px;
                flex: 1;
              }}
            </style>
            </head>
            <body>
            
            <div class="flashcard-scene">
              <div class="flashcard" id="fc">
            
                <div class="flashcard-face flashcard-front">
                  {'<div class="card-oxford">Oxford 5000</div>' if card.get('oxford') else ''}
                  <div class="card-word">{card['word']}</div>
                  <div class="card-pron">{card.get('pronunciation','')}</div>
                  <div class="card-hint">คลิกที่การ์ดหรือปุ่มด้านล่างเพื่อพลิก</div>
                </div>
            
                <div class="flashcard-face flashcard-back">
                  <div class="back-section">
                    <div class="back-label">ความหมายภาษาไทย</div>
                    <div class="back-value" style="font-weight:600; font-size:1.05rem;">{card.get('thai','')}</div>
                  </div>
                  <div class="back-section">
                    <div class="back-label">Definition</div>
                    <div class="back-value">{card.get('definition','')}</div>
                  </div>
                  <div class="back-section">
                    <div class="back-label">Example</div>
                    <div class="back-value" style="font-style:italic; color:#6B5E4A;">"{card.get('example','')}"</div>
                  </div>
                </div>
            
              </div>
            </div>
            
            <button class="flip-btn" onclick="toggleFlip()">🔄 พลิกการ์ด</button>
            
            <script>
              const fc = document.getElementById('fc');
            
              // พลิกด้วยการคลิกที่การ์ดก็ได้
              fc.addEventListener('click', toggleFlip);
            
              function toggleFlip() {{
                fc.classList.toggle('flipped');
              }}
            
              function navigate(dir) {{
                // ส่ง message ออกไปให้ Streamlit รับผ่าน postMessage
                window.parent.postMessage({{type: 'navigate', dir: dir}}, '*');
              }}
            </script>
            
            </body>
            </html>
            """, height=380)

            if st.button("🔄 พลิกการ์ด", key=f"flip_btn_{s_idx}", use_container_width=True):
                st.session_state[f"flipped_{s_idx}"] = not st.session_state[f"flipped_{s_idx}"]
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
            with col_b1:
                if st.button("⬅️ ก่อนหน้า", disabled=(s_idx == 0), use_container_width=True):
                    st.session_state["study_idx"] = s_idx - 1
                    st.rerun()
            with col_b2:
                st.markdown(
                    f"<p style='text-align:center; font-size:0.82rem; color:var(--ink-faint); margin-top:10px; "
                    f"font-weight:500; letter-spacing:0.05em; font-family:\"Plus Jakarta Sans\",sans-serif;'>"
                    f"ใบที่ {s_idx + 1} / {len(cards)}</p>",
                    unsafe_allow_html=True
                )
            with col_b3:
                if st.button("ถัดไป ➡️", disabled=(s_idx == len(cards) - 1), use_container_width=True):
                    st.session_state["study_idx"] = s_idx + 1
                    st.rerun()

            st.markdown("---")
            st.info("💡 จำให้ครบทั้ง 5 คำก่อน แล้วกดแท็บ 🎮 โหมดเกมควิซ เพื่อทำแบบทดสอบเก็บคะแนน")

        # ── Quiz Mode ──
        elif st.session_state["flash_mode"] == "quiz":
            if "flash_score" not in st.session_state:
                st.session_state["flash_score"] = 0
            if "flash_status" not in st.session_state:
                st.session_state["flash_status"] = None

            # ตรวจหาการ์ดที่ผู้เล่นยังจำไม่ได้ (mastered == False)
            unmastered_cards = [c for c in cards if not c.get("mastered", False)]

            # กรณีชนะเกม: บรรลุเป้าหมายครบถ้วนทุกคำ
            if not unmastered_cards:
                st.balloons()
                st.markdown(f"""
                <div style="background:var(--correct-bg); border-radius:16px; padding:2rem; text-align:center; border:1px solid var(--correct-bd); margin: 1rem 0;">
                    <h2 style="font-family:'Fraunces',serif; color:var(--correct-txt); margin:0 0 0.5rem 0; font-size:1.75rem;">🏆 ยอดเยี่ยม! จำได้ครบเซ็ตแล้ว</h2>
                    <p style="color:var(--correct-txt); margin:0; font-size:1rem; font-family:'Plus Jakarta Sans',sans-serif;">คุณผ่านเงื่อนไขตอบถูก 3 ครั้งติดต่อกันครบทั้ง {len(cards)} คำเรียบร้อย!</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🔄 เริ่มเล่นใหม่อีกครั้ง", use_container_width=True):
                    for c in cards:
                        c["streak"] = 0
                        c["mastered"] = False
                    st.session_state["card_idx"] = 0
                    st.session_state["flash_score"] = 0
                    st.session_state["flash_status"] = None
                    if "current_options" in st.session_state:
                        del st.session_state["current_options"]
                    st.rerun()
            
            else:
                # ดึงข้อมูลการ์ดใบปัจจุบันมาเล่นควิซ
                card = cards[idx]
                is_oxford = card.get("oxford", False)

                # สุ่มตัวเลือกคำตอบรอบใหม่
                if "current_options" not in st.session_state:
                    correct_ans = card.get('thai', '')
                    wrong_answers = [c.get('thai', '') for i, c in enumerate(cards) if i != idx and c.get('thai', '')]
                    while len(wrong_answers) < 3:
                        wrong_answers.append("คำศัพท์วิชาการตัวลวง")
                    selected_options = random.sample(wrong_answers, 3) + [correct_ans]
                    random.shuffle(selected_options)
                    st.session_state["current_options"] = selected_options

                # ส่วนแถบแสดง Progress ความจำรวมในกอง
                mastered_count = len(cards) - len(unmastered_cards)
                col_prog, col_sco = st.columns([3, 1])
                with col_prog:
                    st.markdown(f"<p style='font-size:0.82rem; color:var(--ink-faint); font-weight:500; margin-bottom:4px; font-family:\"Plus Jakarta Sans\",sans-serif;'>จำได้แม่นยำแล้ว {mastered_count} / {len(cards)} คำ</p>", unsafe_allow_html=True)
                    st.progress(mastered_count / len(cards))
                with col_sco:
                    st.markdown(f"<p style='text-align:right; font-weight:600; color:var(--amber); font-size:1rem; margin-top:4px; font-family:\"Plus Jakarta Sans\",sans-serif;'>🏆 รวม {st.session_state['flash_score']} คะแนน</p>", unsafe_allow_html=True)

                oxford_quiz_tag = '<div class="quiz-oxford-tag">Oxford 5000</div>' if is_oxford else ""
                
                # แสดงคะแนนตอบถูกต่อเนื่อง (Streak) รายข้อเป็นรูปดาว
                current_streak = card.get("streak", 0)
                stars_ui = f'<div style="font-size:0.85rem; color:#f59e0b; margin-top:6px;">🔥 จำได้ต่อเนื่อง: {"⭐" * current_streak if current_streak > 0 else "🎯 พยายามเข้า"} ({current_streak}/3)</div>'

                st.markdown(f"""
                <div class="flashcard-quiz-box">
                    <div class="quiz-word-title">{card['word']}</div>
                    <div class="quiz-word-pron">{card.get('pronunciation','')}</div>
                    {stars_ui}
                    {oxford_quiz_tag}
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<p style='font-size:0.82rem; font-weight:600; color:var(--ink-faint); letter-spacing:0.05em; text-transform:uppercase; font-family:\"Plus Jakarta Sans\",sans-serif;'>เลือกคำแปลที่ถูกต้อง</p>", unsafe_allow_html=True)
                options = st.session_state["current_options"]

                col1, col2 = st.columns(2)
                col3, col4 = st.columns(2)
                choice_buttons = [col1, col2, col3, col4]
                user_choice = None

                for i, col in enumerate(choice_buttons):
                    with col:
                        if st.button(f"{i+1}. {options[i]}", key=f"opt_{idx}_{i}", use_container_width=True, disabled=(st.session_state["flash_status"] is not None)):
                            user_choice = options[i]

                # ── ประมวลผลเมื่อผู้ใช้งานกดตอบ ──
                if user_choice:
                    if user_choice == card.get('thai', ''):
                        st.session_state["flash_status"] = "correct"
                        st.session_state["flash_score"] += 1
                        
                        # อัปเดตสเตตัสฉลาด: เพิ่มพลังตอบถูกสะสม
                        card["streak"] += 1
                        if card["streak"] >= 3:
                            card["mastered"] = True
                        st.rerun()
                    else:
                        st.session_state["flash_status"] = "wrong"
                        
                        # อัปเดตสเตตัสฉลาด: ตอบผิดโดนรีเซ็ตความจำข้อนี้ใหม่หมดทันที!
                        card["streak"] = 0
                        st.rerun()

                # หน้าจอสรุปผลลัพธ์หลังเลือกตอบ
                if st.session_state["flash_status"] == "correct":
                    st.markdown(f"""
                    <div class="result-correct">
                        🎉 <strong>ถูกต้อง!</strong> แปลว่า <strong>{card.get('thai','')}</strong><br>
                        <span style="opacity:0.85;">{card['definition']}</span><br>
                        <em style="opacity:0.7;">"{card.get('example','')}"</em>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if st.button("ข้อถัดไป ➡️", key="next_c", use_container_width=True):
                        # วนหาการ์ดใบถัดไปในกองที่ยังไม่เซียน (mastered == False)
                        remains = [c for c in cards if not c.get("mastered", False)]
                        if remains:
                            # สุ่มสลับคำที่เหลือมาถามเพื่อความท้าทาย ไม่จำซ้ำที่เดิม
                            next_card = random.choice(remains)
                            st.session_state["card_idx"] = cards.index(next_card)
                        
                        st.session_state["flash_status"] = None
                        if "current_options" in st.session_state:
                            del st.session_state["current_options"]
                        st.rerun()

                elif st.session_state["flash_status"] == "wrong":
                    st.markdown(f"""
                    <div class="result-wrong">
                        ❌ <strong>ยังไม่ถูกครับ</strong> — คำตอบที่ถูกต้องคือ <strong>{card.get('thai','')}</strong><br>
                        <span style="opacity:0.85;">{card['definition']}</span><br>
                        <em style="opacity:0.7;">"{card.get('example','')}"</em>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    if st.button("ข้ามไปข้อถัดไป ➡️", key="next_w", use_container_width=True):
                        # แม้จะตอบผิดก็ให้สุ่มคำอื่นที่ยังไม่ผ่านขึ้นมาทดสอบวนลูปต่อไป
                        remains = [c for c in cards if not c.get("mastered", False)]
                        if remains:
                            next_card = random.choice(remains)
                            st.session_state["card_idx"] = cards.index(next_card)
                            
                        st.session_state["flash_status"] = None
                        if "current_options" in st.session_state:
                            del st.session_state["current_options"]
                        st.rerun()

# ==============================================================================
# TAB 2 — READING
# ==============================================================================
READING_TOPICS = [
    "Artificial Intelligence", "Climate Change", "Public Health",
    "Space Exploration", "Economics & Trade", "Psychology",
    "Renewable Energy", "Human Rights", "Biotechnology",
    "Urban Planning", "History of Science", "Media & Communication",
    "Education Systems", "Nutrition & Diet", "Cybersecurity",
]

with tab2:
    st.markdown("#### 📄 อ่านบทความและตอบคำถาม")

    def randomize_topic_callback():
        st.session_state["reading_topic_sel"] = random.choice(READING_TOPICS)
        st.session_state["article"] = None
        st.session_state["reading_result"] = None

    col_sel, col_rand = st.columns([3, 1])
    with col_sel:
        reading_topic = st.selectbox("เลือกหัวข้อบทความ:", READING_TOPICS, key="reading_topic_sel")
    with col_rand:
        st.markdown("<div style='margin-top:1.6rem'>", unsafe_allow_html=True)
        st.button("🎲 สุ่ม", key="random_topic", on_click=randomize_topic_callback)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("📖 โหลดบทความใหม่", key="gen_article"):
        with st.spinner(f"กำลังสร้างบทความเรื่อง {reading_topic}..."):
            raw = call_gemini(f"""
You are an academic English reading teacher.
Write a short academic passage (8-15 sentences) about "{reading_topic}" for level "{user_level}".
Include 3-5 advanced vocabulary words naturally in the passage.
Then create 1 comprehension question with a short open-ended answer (not multiple choice).
Also list the key vocabulary words used with brief English definitions.
Return ONLY valid JSON, no markdown:
{{"topic":"{reading_topic}","passage":"...","question":"...","model_answer":"...","vocab":[{{"word":"...","meaning":"..."}}]}}
""", max_tokens=700)
            if raw:
                try:
                    st.session_state["article"] = parse_json(raw)
                    st.session_state["reading_result"] = None
                    if "tts_audio" in st.session_state:
                        del st.session_state["tts_audio"]
                except Exception as e:
                    st.error(f"แปลง JSON ไม่ได้: {e}\n\n{raw}")

    if "article" in st.session_state and st.session_state["article"]:
        art = st.session_state["article"]

        st.markdown(
            f'<span style="display:inline-block; background:var(--amber-bg); color:var(--amber-deep); '
            f'font-size:0.7rem; font-weight:600; letter-spacing:0.09em; text-transform:uppercase; '
            f'padding:3px 10px; border-radius:5px; margin-bottom:0.75rem; '
            f'font-family:\'Plus Jakarta Sans\',sans-serif;">{art.get("topic","")}</span>',
            unsafe_allow_html=True
        )

        display_passage = art["passage"]
        display_passage = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', display_passage)
        st.markdown(f'<div class="passage-card">{display_passage}</div>', unsafe_allow_html=True)

        col_tts, col_speed = st.columns([2, 1])
        with col_speed:
            slow_mode = st.checkbox("🐢 ช้าลง", key="tts_slow")
        with col_tts:
            if st.button("🔊 ฟังบทความ", key="tts_play"):
                with st.spinner("กำลังสร้างเสียง..."):
                    try:
                        tts = gTTS(text=art["passage"], lang="en", slow=slow_mode)
                        audio_buf = io.BytesIO()
                        tts.write_to_fp(audio_buf)
                        audio_buf.seek(0)
                        st.session_state["tts_audio"] = audio_buf.read()
                    except Exception as e:
                        st.error(f"สร้างเสียงไม่ได้: {e}")
        if st.session_state.get("tts_audio"):
            st.audio(st.session_state["tts_audio"], format="audio/mp3")

        if art.get("vocab"):
            vocab_items = "".join(
                f'<span style="margin-right:1.25rem; display:inline-block; font-family:\'Plus Jakarta Sans\',sans-serif;">'
                f'<strong style="color:var(--ink);">{v["word"]}</strong>'
                f'<span style="color:var(--ink-muted); margin-left:4px;">— {v["meaning"]}</span></span>'
                for v in art["vocab"]
            )
            st.markdown(
                f'<div class="vocab-pill-row">'
                f'<span class="vocab-pill-label">คำศัพท์ในบทความ</span>'
                f'{vocab_items}</div>',
                unsafe_allow_html=True
            )

        st.markdown(f'**คำถาม:** {art["question"]}')
        user_ans = st.text_input(
            "พิมพ์คำตอบของคุณเป็นภาษาอังกฤษ:",
            key="reading_ans_input",
            placeholder="Type your answer here…"
        )

        if st.button("✅ ส่งคำตอบ", key="submit_reading"):
            if not user_ans.strip():
                st.warning("กรุณาพิมพ์คำตอบก่อนส่ง")
            else:
                with st.spinner("AI กำลังตรวจคำตอบ..."):
                    feedback = call_gemini(f"""
Passage: "{art['passage']}"
Question: "{art['question']}"
Model answer: "{art['model_answer']}"
Student's answer: "{user_ans}"
Evaluate the student's answer briefly.
- First line: state if it's correct/partially correct/incorrect.
- Then 2-3 sentences of gentle explanation in Thai.
Keep it encouraging and concise.
""")
                    st.session_state["reading_result"] = {
                        "feedback": feedback,
                        "model": art["model_answer"],
                    }

        if st.session_state.get("reading_result"):
            res = st.session_state["reading_result"]
            fb_lower = (res["feedback"] or "").lower()
            css_class = "result-correct" if any(w in fb_lower for w in ["correct","good","right","great","well"]) else "result-wrong"
            st.markdown(
                f'<div class="{css_class}">'
                f'<strong>ผลการตรวจ:</strong><br>{res["feedback"]}<br><br>'
                f'<strong>เฉลย:</strong> {res["model"]}</div>',
                unsafe_allow_html=True
            )

# ==============================================================================
# TAB 3 — VOCAB QUIZ
# ==============================================================================
with tab3:
    st.markdown("#### 🧩 ทบทวนคำศัพท์")
    st.caption("AI จะถามให้เดาคำศัพท์จากนิยามหรือตัวอย่างประโยค")

    # Oxford 5000 toggle for quiz tab
    oxford_quiz_on = st.toggle(
        "🎓 Oxford 5000 Mode",
        value=st.session_state["oxford_mode"],
        key="oxford_toggle_tab3"
    )
    if oxford_quiz_on != st.session_state["oxford_mode"]:
        st.session_state["oxford_mode"] = oxford_quiz_on

    if st.button("🎲 สร้างชุดคำถามใหม่", key="gen_quiz"):
        with st.spinner("กำลังสร้างคำถาม..."):
            if st.session_state["oxford_mode"]:
                seed_words = get_oxford_seed(user_level, 6)
                oxford_instr = (
                    f'Use words from this Oxford 5000 list where relevant: {seed_words}. '
                    'Mark each question with "oxford": true if the target word is from that list.'
                )
            else:
                oxford_instr = 'Set "oxford": false for all questions.'

            raw = call_gemini(f"""
You are an academic English vocabulary quiz creator.
Create 4 vocabulary review questions for topic: "{topic}", level: "{user_level}".
{oxford_instr}
Mix question types: fill-in-the-blank, definition-to-word, or usage question.
Return ONLY valid JSON array, no markdown:
[{{"type":"fill_blank","question":"...","answer":"...","hint":"...","oxford":false}}, ...]
""", max_tokens=700)
            if raw:
                try:
                    st.session_state["quiz"] = parse_json(raw)
                    st.session_state["quiz_answers"] = {}
                    st.session_state["quiz_results"] = {}
                except Exception as e:
                    st.error(f"แปลง JSON ไม่ได้: {e}\n\n{raw}")

    if "quiz" in st.session_state and st.session_state["quiz"]:
        quiz = st.session_state["quiz"]
        type_labels = {
            "fill_blank": "Fill in the blank",
            "definition_to_word": "What's the word?",
            "usage": "Usage question",
        }

        for i, q in enumerate(quiz):
            label = type_labels.get(q.get("type",""), "Question")
            ans_key = f"quiz_ans_{i}"
            is_oxford_q = q.get("oxford", False)
            oxford_tag = " · <span style='color:var(--amber);font-weight:700;font-size:0.65rem;letter-spacing:0.08em;'>Oxford 5000</span>" if is_oxford_q else ""

            with st.container():
                st.markdown(
                    f'<div class="quiz-card">'
                    f'<span class="quiz-type-badge">{label}{oxford_tag}</span>'
                    f'<div class="quiz-q">Q{i+1}. {q["question"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

                user_quiz_ans = st.text_input(
                    f"คำตอบข้อ {i+1}:",
                    key=ans_key,
                    placeholder=f"Hint: {q.get('hint','')}"
                )
                st.session_state["quiz_answers"][i] = user_quiz_ans

                result = st.session_state["quiz_results"].get(i)
                if result:
                    css = "result-correct" if result["ok"] else "result-wrong"
                    icon = "✅" if result["ok"] else "❌"
                    st.markdown(
                        f'<div class="{css}">{icon} เฉลย: <strong>{result["ans"]}</strong><br>{result["fb"]}</div>',
                        unsafe_allow_html=True
                    )

        if st.button("📝 ส่งคำตอบทั้งหมด", key="submit_quiz"):
            quiz_data_to_send = []
            for i, q in enumerate(quiz):
                u_ans = st.session_state["quiz_answers"].get(i, "").strip()
                quiz_data_to_send.append({
                    "index": i,
                    "question": q['question'],
                    "correct_answer": q['answer'],
                    "student_answer": u_ans
                })

            with st.spinner("AI กำลังตรวจคำตอบทั้งหมด..."):
                raw_feedback = call_gemini(f"""
You are an expert English teacher. Evaluate these student answers.
Data: {json.dumps(quiz_data_to_send)}
Return ONLY a JSON array with 'index' (int), 'ok' (boolean), and 'fb'
(if correct: 'ถูกต้อง! 🎉', if wrong: 1 short gentle explanation in Thai).
No markdown wrappers.
""")
                if raw_feedback:
                    try:
                        parsed_feedback_list = parse_json(raw_feedback)
                        for item in parsed_feedback_list:
                            idx2 = item["index"]
                            correct_ans = quiz[idx2]["answer"]
                            st.session_state["quiz_results"][idx2] = {
                                "ok": item["ok"],
                                "ans": correct_ans,
                                "fb": item["fb"]
                            }
                    except Exception as e:
                        st.error(f"ประมวลผลผลลัพธ์ล้มเหลว: {e}")
            st.rerun()

# ==============================================================================
# TAB 4 — CHAT
# ==============================================================================
with tab4:
    st.markdown("#### 💬 สนทนากับ AI Tutor")

    ICE_BREAKERS = [
        "What did you do today? Tell me a little bit about your day.",
        "What is your favorite food, and why do you like it?",
        "If you could travel anywhere in the world right now, where would you go?"
    ]

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if not st.session_state.chat_history:
        starting_question = random.choice(ICE_BREAKERS)
        first_greeting = f"Hello! 👋 Let's practice English together! Here is my first question:\n\n**{starting_question}**"
        st.session_state.chat_history.append({"role": "assistant", "text": first_greeting})

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-bubble-user">{msg["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-bubble-ai">{msg["text"]}</div>', unsafe_allow_html=True)

    user_chat = st.chat_input("พิมพ์ตอบตรงนี้เพื่อคุยภาษาอังกฤษ...")
    if user_chat:
        st.session_state.chat_history.append({"role": "user", "text": user_chat})
        history_str = "\n".join(
            f'{"Student" if m["role"]=="user" else "Tutor"}: {m["text"]}'
            for m in st.session_state.chat_history
        )
        with st.spinner("AI กำลังพิมพ์ตอบ..."):
            reply = call_gemini(
                f"You are a warm and encouraging English teacher. "
                f"Reply to the student based on this conversation:\n{history_str}\n"
                f"Keep it conversational (2-4 sentences), gently correct any grammar errors, then ask a follow-up question."
            )
            if reply:
                st.session_state.chat_history.append({"role": "assistant", "text": reply})
        st.rerun()

    if st.button("🧹 ล้างประวัติการสนทนา"):
        st.session_state.chat_history = []
        st.rerun()
