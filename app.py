import streamlit as st
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

st.set_page_config(
    page_title="Academic English AI Trainer",
    page_icon="📖",
    layout="centered"
)

# ─── 2. REDESIGNED CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,400&family=Plus+Jakarta+Sans:wght@300;400;500;600&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    font-family: 'Plus Jakarta Sans', sans-serif;
    background-color: #F7F5F0;
}

/* Dark mode base — Streamlit sets data-theme on <html> */
html[data-theme="dark"] .stApp { background-color: #141412; }

/* Global dark text override — Streamlit's own text elements */
html[data-theme="dark"] p,
html[data-theme="dark"] span,
html[data-theme="dark"] div,
html[data-theme="dark"] label,
html[data-theme="dark"] li,
html[data-theme="dark"] .stMarkdown,
html[data-theme="dark"] .stText,
html[data-theme="dark"] [data-testid="stMarkdownContainer"] p,
html[data-theme="dark"] [data-testid="stMarkdownContainer"] li {
    color: #D8D4CC;
}

/* Keep gold accent elements their color in dark */
html[data-theme="dark"] strong { color: #E8E4DC; }

#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding-top: 2.5rem;
    padding-bottom: 5rem;
    max-width: 740px;
}

/* ── Header ── */
.app-title {
    font-family: 'Fraunces', serif;
    font-size: 2.6rem;
    color: #1C1B18;
    margin-bottom: 0.1rem;
    font-weight: 600;
    letter-spacing: -0.03em;
    line-height: 1.15;
}
html[data-theme="dark"] .app-title { color: #F0EDE6; }

.app-sub {
    font-size: 0.8rem;
    color: #9B968A;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-weight: 500;
    margin-bottom: 2.5rem;
}

.title-accent {
    display: inline-block;
    width: 36px;
    height: 3px;
    background: #D4A853;
    border-radius: 2px;
    margin-bottom: 1.2rem;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    border-radius: 10px !important;
    border-color: #E2DDD5 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.875rem !important;
    background: #FAFAF8 !important;
    color: #1C1B18 !important;
}
html[data-theme="dark"] .stTextInput > div > div > input {
    background: #1E1D1A !important;
    border-color: #38362F !important;
    color: #E8E4DC !important;
}
html[data-theme="dark"] .stTextInput label,
html[data-theme="dark"] .stSelectbox label,
html[data-theme="dark"] .stCheckbox label,
html[data-theme="dark"] .stTextInput > label,
html[data-theme="dark"] .stSelectbox > label {
    color: #A8A49C !important;
}
/* Selectbox in dark — the div wrapper */
html[data-theme="dark"] .stSelectbox [data-baseweb="select"] > div:first-child {
    background: #1E1D1A !important;
    border-color: #38362F !important;
}
html[data-theme="dark"] .stSelectbox [data-baseweb="select"] span,
html[data-theme="dark"] .stSelectbox [data-baseweb="select"] div {
    color: #E8E4DC !important;
}
/* Selectbox dropdown list */
html[data-theme="dark"] [data-baseweb="popover"] li,
html[data-theme="dark"] [data-baseweb="menu"] li,
html[data-theme="dark"] [role="option"] {
    background: #1E1D1A !important;
    color: #D8D4CC !important;
}
html[data-theme="dark"] [data-baseweb="popover"] li:hover,
html[data-theme="dark"] [role="option"]:hover {
    background: #2A2924 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #EEEBE4;
    padding: 5px;
    border-radius: 12px;
    border: none;
    margin-bottom: 1.75rem;
}
html[data-theme="dark"] .stTabs [data-baseweb="tab-list"] {
    background: #1E1D1A;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 7px 16px;
    font-size: 0.82rem;
    font-weight: 500;
    color: #7A7569;
    background: transparent;
    border: none;
    font-family: 'Plus Jakarta Sans', sans-serif;
    letter-spacing: 0.01em;
}
html[data-theme="dark"] .stTabs [data-baseweb="tab"] { color: #5C5850; }
.stTabs [aria-selected="true"] {
    background: #FFFFFF !important;
    color: #1C1B18 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 0 0 0.5px rgba(0,0,0,0.06) !important;
}
html[data-theme="dark"] .stTabs [aria-selected="true"] {
    background: #2E2D29 !important;
    color: #F0EDE6 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none; }

/* ── Buttons ── */
.stButton > button {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    border-radius: 10px !important;
    border: 1.5px solid #E2DDD5 !important;
    background: #FFFFFF !important;
    color: #1C1B18 !important;
    padding: 9px 18px !important;
    transition: all 0.15s ease !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}
.stButton > button:hover {
    border-color: #D4A853 !important;
    background: #FDF9F2 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 3px 10px rgba(212,168,83,0.15) !important;
}
html[data-theme="dark"] .stButton > button {
    background: #222220 !important;
    border-color: #3A3935 !important;
    color: #D8D4CC !important;
}
html[data-theme="dark"] .stButton > button:hover {
    background: #2A2924 !important;
    border-color: #D4A853 !important;
    color: #F0EDE6 !important;
}
/* Disabled buttons in dark */
html[data-theme="dark"] .stButton > button:disabled {
    color: #4A4845 !important;
    border-color: #2A2924 !important;
}

/* ── Flashcard Scene ── */
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

/* Front face — same in both modes */
.flashcard-front {
    background: #1C1B18;
    color: white;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2), 0 1px 3px rgba(0,0,0,0.1);
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(255,255,255,0.06);
}

/* Back face */
.flashcard-back {
    background: #FDFCF9;
    border: 1.5px solid #E8E4DC;
    transform: rotateY(180deg);
    box-shadow: 0 8px 32px rgba(0,0,0,0.06);
    align-items: flex-start;
    justify-content: flex-start;
    gap: 10px;
    overflow-y: auto;
}
html[data-theme="dark"] .flashcard-back {
    background: #252420;
    border-color: #38362F;
}

.card-word {
    font-family: 'Fraunces', serif;
    font-size: 2.6rem;
    color: #D4A853;
    text-align: center;
    letter-spacing: -0.02em;
    line-height: 1.1;
}
.card-pron {
    font-size: 1rem;
    opacity: 0.55;
    color: #fff;
    font-weight: 300;
    letter-spacing: 0.04em;
}
.card-hint {
    font-size: 0.75rem;
    color: rgba(255,255,255,0.35);
    margin-top: 0.75rem;
    letter-spacing: 0.05em;
}

.back-label {
    font-size: 0.65rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9B968A;
}
.back-value {
    font-size: 0.95rem;
    color: #1C1B18;
    line-height: 1.6;
    margin-top: 1px;
}
html[data-theme="dark"] .back-value { color: #D8D4CC !important; }

/* ── Quiz Box ── */
.flashcard-quiz-box {
    background: #1C1B18;
    color: white;
    border-radius: 16px;
    padding: 2.25rem 2rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    margin-bottom: 1.25rem;
}
html[data-theme="dark"] .flashcard-quiz-box {
    background: #252420;
    border: 1px solid #38362F;
}
.quiz-word-title {
    font-family: 'Fraunces', serif;
    font-size: 2.4rem;
    color: #D4A853;
    letter-spacing: -0.02em;
}
.quiz-word-pron {
    font-size: 0.95rem;
    color: rgba(255,255,255,0.45);
    margin-top: 0.4rem;
}

/* Quiz answer options */
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: #FFFFFF !important;
    color: #1C1B18 !important;
    border: 1.5px solid #E2DDD5 !important;
    border-radius: 10px !important;
    padding: 12px 16px !important;
    text-align: left !important;
    font-weight: 400 !important;
    font-size: 0.875rem !important;
    line-height: 1.4 !important;
    height: auto !important;
    min-height: 52px !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    border-color: #D4A853 !important;
    background: #FDF9F2 !important;
}
html[data-theme="dark"] div[data-testid="stHorizontalBlock"] .stButton > button {
    background: #252420 !important;
    color: #D8D4CC !important;
    border-color: #38362F !important;
}
html[data-theme="dark"] div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    background: #2E2D29 !important;
    border-color: #D4A853 !important;
    color: #F0EDE6 !important;
}

/* ── Passage Card ── */
.passage-card {
    background: #FFFFFF;
    border-left: 3px solid #D4A853;
    border-radius: 0 14px 14px 0;
    padding: 1.5rem 1.75rem;
    font-size: 0.975rem;
    line-height: 2;
    color: #2A2924;
    margin-bottom: 1.25rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
html[data-theme="dark"] .passage-card {
    background: #1E1D1A;
    color: #C8C4BC !important;
    border-left-color: #D4A853;
    border: 1px solid #38362F;
    border-left: 3px solid #D4A853;
}

/* ── Quiz Cards ── */
.quiz-card {
    background: #FFFFFF;
    border: 1.5px solid #EDEAE3;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
html[data-theme="dark"] .quiz-card {
    background: #1E1D1A;
    border-color: #38362F;
}
.quiz-q {
    font-family: 'Fraunces', serif;
    font-size: 1.15rem;
    color: #1C1B18;
    line-height: 1.5;
    margin-top: 6px;
}
html[data-theme="dark"] .quiz-q { color: #E8E4DC !important; }
.quiz-type-badge {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    color: #9B968A;
    background: #F0EDE6;
    padding: 2px 9px;
    border-radius: 5px;
}
html[data-theme="dark"] .quiz-type-badge {
    background: #2A2924;
    color: #7A7569;
}

/* ── Chat Bubbles ── */
.chat-bubble-user {
    background: #1C1B18;
    color: #F0EDE6 !important;
    border-radius: 18px 18px 4px 18px;
    padding: 0.75rem 1.1rem;
    font-size: 0.9rem;
    max-width: 78%;
    margin-left: auto;
    margin-bottom: 10px;
    font-weight: 400;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    line-height: 1.55;
}
html[data-theme="dark"] .chat-bubble-user {
    background: #D4A853;
    color: #1C1B18 !important;
}
.chat-bubble-ai {
    background: #FFFFFF;
    color: #1C1B18 !important;
    border-radius: 18px 18px 18px 4px;
    padding: 0.75rem 1.1rem;
    font-size: 0.9rem;
    max-width: 78%;
    margin-right: auto;
    margin-bottom: 10px;
    border: 1.5px solid #EDEAE3;
    line-height: 1.55;
}
html[data-theme="dark"] .chat-bubble-ai {
    background: #252420;
    border-color: #38362F;
    color: #C8C4BC !important;
}

/* ── Result Boxes ── */
.result-correct {
    background: #F2FAF4;
    border: 1px solid #A8D5B5;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #1A4A28;
    font-size: 0.9rem;
    line-height: 1.6;
    margin-top: 0.5rem;
}
html[data-theme="dark"] .result-correct {
    background: #172318;
    border-color: #2D5E36;
    color: #7EC896 !important;
}
html[data-theme="dark"] .result-correct strong { color: #A8DFBA !important; }
.result-wrong {
    background: #FEF5F5;
    border: 1px solid #F5B8B8;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #6B1A1A;
    font-size: 0.9rem;
    line-height: 1.6;
    margin-top: 0.5rem;
}
html[data-theme="dark"] .result-wrong {
    background: #231515;
    border-color: #5E2D2D;
    color: #D48888 !important;
}
html[data-theme="dark"] .result-wrong strong { color: #E8AAAA !important; }

/* ── Dividers & misc ── */
hr { border-color: #EDEAE3 !important; margin: 1.5rem 0 !important; }
html[data-theme="dark"] hr { border-color: #2E2D29 !important; }

.stProgress > div > div > div {
    background-color: #D4A853 !important;
    border-radius: 4px;
}
.stProgress > div > div {
    background-color: #EDEAE3 !important;
    border-radius: 4px;
}
html[data-theme="dark"] .stProgress > div > div {
    background-color: #2E2D29 !important;
}

/* Caption & small text */
.stCaption { color: #9B968A !important; font-size: 0.8rem !important; }
html[data-theme="dark"] .stCaption { color: #6B6760 !important; }

/* ── Section headers inside tabs ── */
h4 {
    font-family: 'Fraunces', serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em !important;
    color: #1C1B18 !important;
    font-size: 1.35rem !important;
}
html[data-theme="dark"] h4 { color: #F0EDE6 !important; }

/* Subheader / h3 */
html[data-theme="dark"] h3 { color: #E8E4DC !important; }

/* ── Warning / info / success / error boxes ── */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
    font-size: 0.875rem !important;
}
html[data-theme="dark"] .stAlert [data-testid="stMarkdownContainer"] p {
    color: inherit !important;
}

/* ── Chat input box ── */
html[data-theme="dark"] .stChatInput textarea {
    background: #1E1D1A !important;
    border-color: #38362F !important;
    color: #E8E4DC !important;
}
html[data-theme="dark"] .stChatInput textarea::placeholder { color: #5C5850 !important; }

/* ── Text input placeholder ── */
html[data-theme="dark"] .stTextInput input::placeholder { color: #5C5850 !important; }

/* Score / progress text in quizzes */
html[data-theme="dark"] .stMarkdown p { color: #C8C4BC; }
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
def call_gemini(prompt: str) -> str | None:
    try:
        client = genai.Client(api_key=api_key)
        config = genai.types.GenerateContentConfig(
            max_output_tokens=500,
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
# TAB 1 — FLASHCARDS
# ==============================================================================
with tab1:
    st.markdown("#### 📇 คลังคำศัพท์อัจฉริยะ")
    st.caption(f"หัวข้อ: **{topic}** · ระดับ: **{user_level}**")

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

    if st.button("🔄 เจนคำศัพท์ชุดใหม่ (5 ใบ)", key="gen_cards"):
        with st.spinner("AI กำลังคัดเลือกคำศัพท์วิชาการยอดเยี่ยม..."):
            raw = call_gemini(f"""
You are an academic English vocabulary teacher.
Generate 5 vocabulary flashcards for topic: "{topic}", level: "{user_level}".
Return ONLY a valid JSON array, no markdown, no extra text.
Each object must have exactly these keys:
{{"word":"...","pronunciation":"...","definition":"...","thai":"...","example":"..."}}
""")
            if raw:
                try:
                    st.session_state["cards"] = parse_json(raw)
                    st.session_state["card_idx"] = 0
                    st.session_state["flash_score"] = 0
                    st.session_state["flash_status"] = None
                    if "current_options" in st.session_state: del st.session_state["current_options"]
                    st.rerun()
                except Exception as e:
                    st.error(f"แปลงข้อมูล JSON ล้มเหลว: {e}\n\n{raw}")

    if "cards" in st.session_state and st.session_state["cards"]:
        cards = st.session_state["cards"]
        idx = st.session_state.get("card_idx", 0)

        # ── Study Mode ──
        if st.session_state["flash_mode"] == "study":
            st.subheader("👀 ฝึกจำคำศัพท์")

            if "study_idx" not in st.session_state: st.session_state["study_idx"] = 0
            s_idx = st.session_state["study_idx"]
            if s_idx >= len(cards): st.session_state["study_idx"] = 0; s_idx = 0

            card = cards[s_idx]

            if f"flipped_{s_idx}" not in st.session_state:
                st.session_state[f"flipped_{s_idx}"] = False

            is_flipped = st.session_state[f"flipped_{s_idx}"]
            flip_class = "flipped" if is_flipped else ""

            st.markdown(f"""
            <div class="flashcard-scene">
                <div class="flashcard {flip_class}">
                    <div class="flashcard-face flashcard-front">
                        <div class="card-word">{card['word']}</div>
                        <div class="card-pron">{card.get('pronunciation','')}</div>
                        <div class="card-hint">คลิกปุ่มด้านล่างเพื่อพลิกดูความหมาย</div>
                    </div>
                    <div class="flashcard-face flashcard-back">
                        <div style="width:100%;">
                            <div class="back-label">ความหมายภาษาไทย</div>
                            <div class="back-value" style="font-weight:600; font-size:1.05rem;">{card.get('thai','')}</div>
                        </div>
                        <div style="width:100%; margin-top:6px;">
                            <div class="back-label">Definition</div>
                            <div class="back-value">{card['definition']}</div>
                        </div>
                        <div style="width:100%; margin-top:6px;">
                            <div class="back-label">Example</div>
                            <div class="back-value" style="font-style:italic; color:#6B6460;">"{card.get('example','')}"</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

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
                st.markdown(f"<p style='text-align:center; font-size:0.82rem; color:#9B968A; margin-top:10px; font-weight:500; letter-spacing:0.05em;'>ใบที่ {s_idx + 1} / {len(cards)}</p>", unsafe_allow_html=True)
            with col_b3:
                if st.button("ถัดไป ➡️", disabled=(s_idx == len(cards) - 1), use_container_width=True):
                    st.session_state["study_idx"] = s_idx + 1
                    st.rerun()

            st.markdown("---")
            st.info("💡 ทยอยจำให้ครบทั้ง 5 คำก่อน แล้วกดแท็บ **[🎮 โหมดเกมควิซ]** ด้านบน เพื่อทำแบบทดสอบเก็บคะแนน")

        # ── Quiz Mode ──
        elif st.session_state["flash_mode"] == "quiz":
            if "flash_score" not in st.session_state: st.session_state["flash_score"] = 0
            if "flash_status" not in st.session_state: st.session_state["flash_status"] = None

            if idx >= len(cards):
                st.balloons()
                st.markdown(f"""
                <div style="background:#F2FAF4; border-radius:16px; padding:2rem; text-align:center; border:1px solid #A8D5B5; margin: 1rem 0;">
                    <h2 style="font-family:'Fraunces',serif; color:#1A4A28; margin:0 0 0.5rem 0; font-size:1.75rem;">🏁 จบเซ็ตแล้ว!</h2>
                    <p style="color:#2E6930; margin:0; font-size:1rem;">คะแนนรวม: <span style="font-family:'Fraunces',serif; font-size:2.25rem; font-weight:600;">{st.session_state['flash_score']}</span> / {len(cards)}</p>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🔄 เริ่มเล่นใหม่", use_container_width=True):
                    st.session_state["card_idx"] = 0
                    st.session_state["flash_score"] = 0
                    st.session_state["flash_status"] = None
                    if "current_options" in st.session_state: del st.session_state["current_options"]
                    st.rerun()
            else:
                card = cards[idx]

                if "current_options" not in st.session_state:
                    correct_ans = card.get('thai', '')
                    wrong_answers = [c.get('thai', '') for i, c in enumerate(cards) if i != idx and c.get('thai', '')]
                    while len(wrong_answers) < 3:
                        wrong_answers.append("คำศัพท์วิชาการตัวลวง")
                    selected_options = random.sample(wrong_answers, 3) + [correct_ans]
                    random.shuffle(selected_options)
                    st.session_state["current_options"] = selected_options

                col_prog, col_sco = st.columns([3, 1])
                with col_prog:
                    st.markdown(f"<p style='font-size:0.82rem; color:#9B968A; font-weight:500; margin-bottom:4px;'>ข้อที่ {idx + 1} / {len(cards)}</p>", unsafe_allow_html=True)
                    st.progress((idx) / len(cards))
                with col_sco:
                    st.markdown(f"<p style='text-align:right; font-weight:600; color:#D4A853; font-size:1rem; margin-top:4px;'>🏆 {st.session_state['flash_score']} คะแนน</p>", unsafe_allow_html=True)

                st.markdown(f"""
                <div class="flashcard-quiz-box">
                    <div class="quiz-word-title">{card['word']}</div>
                    <div class="quiz-word-pron">{card.get('pronunciation','')}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<p style='font-size:0.82rem; font-weight:600; color:#9B968A; letter-spacing:0.05em; text-transform:uppercase;'>เลือกคำแปลที่ถูกต้อง</p>", unsafe_allow_html=True)
                options = st.session_state["current_options"]

                col1, col2 = st.columns(2)
                col3, col4 = st.columns(2)
                choice_buttons = [col1, col2, col3, col4]
                user_choice = None

                for i, col in enumerate(choice_buttons):
                    with col:
                        if st.button(f"{i+1}. {options[i]}", key=f"opt_{idx}_{i}", use_container_width=True, disabled=(st.session_state["flash_status"] is not None)):
                            user_choice = options[i]

                if user_choice:
                    if user_choice == card.get('thai', ''):
                        st.session_state["flash_status"] = "correct"
                        st.session_state["flash_score"] += 1
                        st.rerun()
                    else:
                        st.session_state["flash_status"] = "wrong"
                        st.rerun()

                if st.session_state["flash_status"] == "correct":
                    st.markdown(f"""
                    <div class="result-correct">
                        🎉 <strong>ถูกต้อง!</strong> แปลว่า <strong>{card.get('thai','')}</strong><br>
                        <span style="opacity:0.8;">{card['definition']}</span><br>
                        <em style="opacity:0.7;">"{card.get('example','')}"</em>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("ข้อถัดไป ➡️", key="next_c", use_container_width=True):
                        st.session_state["card_idx"] = idx + 1
                        st.session_state["flash_status"] = None
                        if "current_options" in st.session_state: del st.session_state["current_options"]
                        st.rerun()

                elif st.session_state["flash_status"] == "wrong":
                    st.markdown(f"""
                    <div class="result-wrong">
                        ❌ <strong>ยังไม่ถูกครับ</strong> — คำตอบที่ถูกต้องคือ <strong>{card.get('thai','')}</strong><br>
                        <span style="opacity:0.8;">{card['definition']}</span><br>
                        <em style="opacity:0.7;">"{card.get('example','')}"</em>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("ข้ามไปข้อถัดไป ➡️", key="next_w", use_container_width=True):
                        st.session_state["card_idx"] = idx + 1
                        st.session_state["flash_status"] = None
                        if "current_options" in st.session_state: del st.session_state["current_options"]
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
""")
            if raw:
                try:
                    st.session_state["article"] = parse_json(raw)
                    st.session_state["reading_result"] = None
                except Exception as e:
                    st.error(f"แปลง JSON ไม่ได้: {e}\n\n{raw}")

    if "article" in st.session_state and st.session_state["article"]:
        art = st.session_state["article"]

        st.markdown(
            f'<span style="display:inline-block; background:#F0EDE6; color:#6B6460; font-size:0.7rem;'
            'font-weight:600; letter-spacing:0.09em; text-transform:uppercase;'
            f'padding:3px 10px; border-radius:5px; margin-bottom:0.75rem">{art.get("topic","")}</span>',
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
                f'<span style="margin-right:1.25rem; display:inline-block;">'
                f'<strong style="color:#1C1B18;">{v["word"]}</strong>'
                f'<span style="color:#6B6460; margin-left:4px;">— {v["meaning"]}</span></span>'
                for v in art["vocab"]
            )
            st.markdown(
                '<div style="background:#FAFAF7; border:1px solid #EDEAE3; color:#1C1B18; border-radius:12px; padding:0.85rem 1.1rem;'
                'font-size:0.85rem; margin-bottom:1.25rem; line-height:2.2;">'
                '<span style="font-size:0.65rem; letter-spacing:0.1em; text-transform:uppercase; color:#9B968A; font-weight:600; display:block; margin-bottom:4px;">คำศัพท์ในบทความ</span>'
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

    if st.button("🎲 สร้างชุดคำถามใหม่", key="gen_quiz"):
        with st.spinner("กำลังสร้างคำถาม..."):
            raw = call_gemini(f"""
You are an academic English vocabulary quiz creator.
Create 4 vocabulary review questions for topic: "{topic}", level: "{user_level}".
Mix question types: fill-in-the-blank, definition-to-word, or usage question.
Return ONLY valid JSON array, no markdown:
[{{"type":"fill_blank","question":"...","answer":"...","hint":"..."}}, ...]
""")
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

            with st.container():
                st.markdown(
                    f'<div class="quiz-card">'
                    f'<span class="quiz-type-badge">{label}</span>'
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

Return ONLY a JSON array of objects matching the structure, with 'index' (int), 'ok' (boolean status), and 'fb' (if correct: return 'ถูกต้อง! 🎉', if wrong: write 1 short gentle explanation sentence in Thai explaining why the correct answer is right).
Do not include markdown format wrappers.
""")
                if raw_feedback:
                    try:
                        parsed_feedback_list = parse_json(raw_feedback)
                        for item in parsed_feedback_list:
                            idx = item["index"]
                            correct_ans = quiz[idx]["answer"]
                            st.session_state["quiz_results"][idx] = {
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
        history_str = "\n".join(f'{"Student" if m["role"]=="user" else "Tutor"}: {m["text"]}' for m in st.session_state.chat_history)

        with st.spinner("AI กำลังพิมพ์ตอบ..."):
            reply = call_gemini(f"You are an English teacher. Reply to user: '{user_chat}' based on history:\n{history_str}\nKeep it short and ask a new question.")
            if reply: st.session_state.chat_history.append({"role": "assistant", "text": reply})
        st.rerun()

    if st.button("🧹 ล้างประวัติการสนทนา"):
        st.session_state.chat_history = []
        st.rerun()
