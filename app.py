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

# ─── 2. STUNNING RESPONSIVE CSS (รองรับ Dark Mode & สวยสไตล์แอป Duolingo) ──────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;700&display=swap');

.stApp {
    font-family: 'DM Sans', sans-serif;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 4rem; max-width: 720px; }

/* หัวข้อใหญ่ของแอป */
.app-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.3rem;
    color: #ffcb6b; /* สีทองอร่าม สว่างคมชัดในจอ Dark Mode */
    text-shadow: 0px 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 0.15rem;
    font-weight: 700;
}
.app-sub {
    font-size: 0.9rem;
    color: #a0a0b0;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

/* แผงควบคุมการตั้งค่าด้านบน (ใช้แทน Sidebar) */
.settings-dashboard {
    background: linear-gradient(135deg, rgba(45, 45, 80, 0.4) 0%, rgba(26, 26, 46, 0.6) 100%);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 18px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.25);
}
.settings-title {
    color: #ffcb6b;
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 1rem;
}

/* ── Tab Bar ดีไซน์โมเดิร์น ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(240, 240, 245, 0.1);
    padding: 6px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.05);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 18px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #a0a0b0;
    background: transparent;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #1a1a2e !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* ── 3D Flashcard CSS ── */
.flashcard-scene {
    width: 100%;
    height: 250px;
    perspective: 1000px;
    margin: 1rem 0;
}
.flashcard {
    width: 100%;
    height: 100%;
    position: relative;
    transform-style: preserve-3d;
    transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: 18px;
}
.flashcard.flipped { transform: rotateY(180deg); }
.flashcard-face {
    position: absolute;
    inset: 0;
    border-radius: 18px;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
    display: flex;
    flex-direction: column;
    padding: 2rem;
}
.flashcard-front {
    background: linear-gradient(135deg, #1a1a2e 0%, #2d2d50 100%);
    color: white;
    box-shadow: 0 10px 30px rgba(26,26,46,0.3);
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(255,255,255,0.1);
}
.flashcard-back {
    background: #ffffff;
    border: 1.5px solid #e8e8f0;
    transform: rotateY(180deg);
    box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    align-items: flex-start;
    justify-content: flex-start;
    gap: 8px;
}
.card-word { font-family: 'DM Serif Display', serif; font-size: 2.5rem; color: #ffcb6b; text-align: center; }
.card-pron { font-size: 1.1rem; opacity: 0.8; color: #fff; }
.back-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #888; }
.back-value { font-size: 1rem; color: #1a1a2e; line-height: 1.5; }

/* ── Quiz Box & Reading CSS ── */
.flashcard-quiz-box {
    background: linear-gradient(135deg, #1a1a2e 0%, #2d2d50 100%);
    color: white;
    border-radius: 18px;
    padding: 2.5rem 2rem;
    text-align: center;
    box-shadow: 0 10px 30px rgba(26,26,46,0.2);
    margin-bottom: 1.5rem;
    border: 1px solid rgba(255,255,255,0.1);
}
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: rgba(255, 255, 255, 0.95);
    color: #1a1a2e;
    border: 1.5px solid #ececf0;
    border-radius: 12px;
    padding: 14px 20px;
    text-align: left;
    font-weight: 500;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover {
    background: #f4f4fb;
    border-color: #ffcb6b;
    transform: translateY(-1px);
}
.stButton > button {
    background: #ffcb6b;
    color: #1a1a2e;
    border-radius: 10px;
    padding: 10px 22px;
    font-weight: 600;
}
.passage-card {
    background: rgba(255,255,255,0.05);
    border-left: 4px solid #ffcb6b;
    border-radius: 4px 14px 14px 4px;
    padding: 1.5rem 1.75rem;
    font-size: 1rem;
    line-height: 1.9;
    color: inherit;
    margin-bottom: 1.25rem;
}
.quiz-card {
    background: rgba(255,255,255,0.03);
    border: 1.5px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
}
.quiz-q { font-family: 'DM Serif Display', serif; font-size: 1.25rem; color: inherit; }

/* ── Chat CSS ── */
.chat-bubble-user {
    background: #ffcb6b; color: #1a1a2e; border-radius: 18px 18px 4px 18px;
    padding: 0.8rem 1.2rem; font-size: 0.95rem; max-width: 80%; margin-left: auto; margin-bottom: 10px;
    font-weight: 500;
}
.chat-bubble-ai {
    background: rgba(255,255,255,0.08); color: inherit; border-radius: 18px 18px 18px 4px;
    padding: 0.8rem 1.2rem; font-size: 0.95rem; max-width: 80%; margin-right: auto; margin-bottom: 10px;
    border: 1px solid rgba(255,255,255,0.05);
}
</style>
""", unsafe_allow_html=True)

# ─── 3. APP HEADER ───────────────────────────────────────────────────────────
st.markdown('<p class="app-title">Academic English Trainer</p>', unsafe_allow_html=True)
st.markdown('<p class="app-sub">AI-Powered · Gemini · ฝึกภาษาอังกฤษเชิงวิชาการ</p>', unsafe_allow_html=True)

# ─── 4. SETTINGS DASHBOARD (กล่องตั้งค่าที่ย้ายมาไว้หน้าหลัก) ────────────────────
with st.container():
    st.markdown("""
    <div class="settings-dashboard">
        <div class="settings-title">⚙️ แผงควบคุมและตั้งค่าบทเรียน</div>
    """, unsafe_allow_html=True)
    
    col_k1, col_k2 = st.columns([2, 3])
    with col_k1:
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
            
    with col_k2:
        col_lvl, col_tpc = st.columns(2)
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

# บล็อกหยุดถ้ายังไม่ใส่คีย์
api_key = st.session_state["saved_key"]
if not api_key:
    st.warning("⚠️ โปรดระบุ Gemini API Key ในช่องตั้งค่าด้านบนเพื่อเชื่อมต่อระบบบอทและเข้าสู่บทเรียนครับ!")
    st.stop()

# ─── 5. GEMINI HELPER ────────────────────────────────────────────────────────
def call_gemini(prompt: str) -> str | None:
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
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

# ─── 6. TABS CONTROL ──────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📇 Flashcards", "📄 Reading", "🧩 Vocab Quiz", "💬 Chat"])

# ==============================================================================
# TAB 1 — FLASHCARDS (มีทั้งโหมดเรียนรู้ 3D Flip และโหมดเกมโชว์ 4 ช้อยส์)
# ==============================================================================
with tab1:
    st.markdown("#### 📇 คลังคำศัพท์อัจฉริยะ (Vocab Study & Quiz)")
    st.caption(f"หัวข้อคอร์สในปัจจุบัน: **{topic}** · ระดับผู้เรียน: **{user_level}**")

    # ปุ่มสลับโหมดการเรียนรู้
    if "flash_mode" not in st.session_state:
        st.session_state["flash_mode"] = "study"  # เริ่มต้นที่โหมดเรียนรู้ก่อนเสมอ

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

    # ปุ่มดึงคำศัพท์ใหม่จาก Gemini
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

    # ตรวจสอบว่ามีข้อมูลคำศัพท์ในระบบหรือยัง
    if "cards" in st.session_state and st.session_state["cards"]:
        cards = st.session_state["cards"]
        idx = st.session_state.get("card_idx", 0)

        # ----------------------------------------------------------------------
        # โหมดที่ 1: โหมดเรียนรู้ (STUDY MODE - พลิกดูการ์ด 3D)
        # ----------------------------------------------------------------------
        if st.session_state["flash_mode"] == "study":
            st.subheader("👀 ฝึกจำคำศัพท์ (คลิกที่การ์ดเพื่อพลิกดูความหมาย)")
            
            # ควบคุมอินเด็กซ์ของโหมดเรียนรู้แยกอิสระ
            if "study_idx" not in st.session_state: st.session_state["study_idx"] = 0
            s_idx = st.session_state["study_idx"]
            
            if s_idx >= len(cards): st.session_state["study_idx"] = 0; s_idx = 0
            
            card = cards[s_idx]
            
            # ตัวแปรเช็คสถานะการพลิกการ์ด (เปิด/ปิด)
            if f"flipped_{s_idx}" not in st.session_state:
                st.session_state[f"flipped_{s_idx}"] = False
                
            is_flipped = st.session_state[f"flipped_{s_idx}"]
            flip_class = "flipped" if is_flipped else ""

            # HTML/CSS ทำเอฟเฟกต์การพลิกการ์ดแบบคลาสสิก ไม่ตีกับปุ่มด้านล่าง
            st.markdown(f"""
            <div class="flashcard-scene">
                <div class="flashcard {flip_class}">
                    <!-- หน้าแรก: คำศัพท์ -->
                    <div class="flashcard-face flashcard-front">
                        <div class="card-word">{card['word']}</div>
                        <div class="card-pron">{card.get('pronunciation','')}</div>
                        <div class="card-hint">💡 คลิกปุ่มด้านล่างเพื่อพลิกดูความหมาย</div>
                    </div>
                    <!-- หน้าหลัง: คำแปลและตัวอย่าง -->
                    <div class="flashcard-face flashcard-back" style="overflow-y: auto;">
                        <div style="width:100%;">
                            <div class="back-label">ความหมายภาษาไทย</div>
                            <div class="back-value" style="font-weight:bold; color:#1a1a2e; font-size:1.1rem;">{card.get('thai','')}</div>
                        </div>
                        <div style="width:100%; margin-top:5px;">
                            <div class="back-label">Definition</div>
                            <div class="back-value">{card['definition']}</div>
                        </div>
                        <div class="back-example" style="width:100%;">
                            <b>Example:</b><br>"{card.get('example','')}"
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ปุ่มกดเพื่อคลิกพลิกการ์ด (แก้ปัญหา UI บนเบราว์เซอร์บางตัวที่คลิกบน Div ตรงๆ ไม่ติด)
            if st.button("🔄 พลิกการ์ด (Flip)", key=f"flip_btn_{s_idx}", use_container_width=True):
                st.session_state[f"flipped_{s_idx}"] = not st.session_state[f"flipped_{s_idx}"]
                st.rerun()

            # แถบควบคุมเลื่อนการ์ด ซ้าย-ขวา
            st.markdown("<br>", unsafe_allow_html=True)
            col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
            with col_b1:
                if st.button("⬅️ ก่อนหน้า", disabled=(s_idx == 0), use_container_width=True):
                    st.session_state["study_idx"] = s_idx - 1
                    st.rerun()
            with col_b2:
                st.markdown(f"<p style='text-align:center; font-size:0.9rem; color:#666; margin-top:8px;'>ใบที่ {s_idx + 1} / {len(cards)}</p>", unsafe_allow_html=True)
            with col_b3:
                if st.button("ถัดไป ➡️", disabled=(s_idx == len(cards) - 1), use_container_width=True):
                    st.session_state["study_idx"] = s_idx + 1
                    st.rerun()
                    
            st.markdown("---")
            st.info("💡 ทลอยจำให้ครบทั้ง 5 คำก่อน แล้วกดคลิกที่แท็บ **[🎮 โหมดเกมควิซ]** ด้านบน เพื่อทำแบบทดสอบเก็บคะแนนกันครับ!")

        # ----------------------------------------------------------------------
        # โหมดที่ 2: โหมดทำควิซเกมโชว์ (QUIZ MODE - 4 ตัวเลือกเดิม)
        # ----------------------------------------------------------------------
        elif st.session_state["flash_mode"] == "quiz":
            if "flash_score" not in st.session_state: st.session_state["flash_score"] = 0
            if "flash_status" not in st.session_state: st.session_state["flash_status"] = None

            if idx >= len(cards):
                st.balloons()
                st.markdown(f"""
                <div style="background:#e8f4ea; border-radius:12px; padding:2rem; text-align:center; border:1px solid #c3e6cb; margin: 1rem 0;">
                    <h2 style="color:#1e4620; margin:0 0 0.5rem 0;">🏁 เก่งมาก! ทดสอบครบจบเซ็ตแล้ว</h2>
                    <h4 style="color:#2e6930; margin:0;">คะแนนรวมของคุณ: <span style="font-size:2rem; font-weight:bold;">{st.session_state['flash_score']}</span> / {len(cards)} คะแนน</h4>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔄 เริ่มเล่นเกมใหม่อีกครั้ง", use_container_width=True):
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
                    st.markdown(f"**คำถามข้อที่: {idx + 1} / {len(cards)}")
                    st.progress((idx) / len(cards))
                with col_sco:
                    st.markdown(f"<p style='text-align:right; font-weight:bold; color:#ff9800; font-size:1.1rem;'>🏆 Score: {st.session_state['flash_score']}</p>", unsafe_allow_html=True)

                st.markdown(f"""
                <div class="flashcard-quiz-box">
                    <div class="quiz-word-title">{card['word']}</div>
                    <div class="quiz-word-pron">{card.get('pronunciation','')}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<p style='font-size:0.9rem; font-weight:bold; color:#555;'>เลือกคำแปลภาษาไทยที่ถูกต้อง:</p>", unsafe_allow_html=True)
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
                    st.success(f"🎉 ถูกต้อง! ** แปลว่า: **{card.get('thai','')}**")
                    st.markdown(f"""
                    <div style="background:#f0faf1; padding:1rem; border-radius:10px; color:#1e6b3f; font-size:0.9rem; margin-bottom:1rem; border-left:4px solid #6fcf97;">
                        <b>Definition:</b> {card['definition']}<br>
                        <b>Example:</b> "{card.get('example','')}"
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("ข้อถัดไป ➡️", key="next_c", use_container_width=True):
                        st.session_state["card_idx"] = idx + 1
                        st.session_state["flash_status"] = None
                        if "current_options" in st.session_state: del st.session_state["current_options"]
                        st.rerun()

                elif st.session_state["flash_status"] == "wrong":
                    st.error(f"❌ ยังไม่ถูกเฉลยคลาดเคลื่อนครับ")
                    st.info(f"💡 คำตอบที่ถูกต้องคือ: **{card.get('thai','')}**")
                    st.markdown(f"""
                    <div style="background:#fff5f5; padding:1rem; border-radius:10px; color:#8b1a1a; font-size:0.9rem; margin-bottom:1rem; border-left:4px solid #f48c8c;">
                        <b>Definition:</b> {card['definition']}<br>
                        <b>Example:</b> "{card.get('example','')}"
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("ข้ามไปข้อถัดไป ➡️", key="next_w", use_container_width=True):
                        st.session_state["card_idx"] = idx + 1
                        st.session_state["flash_status"] = None
                        if "current_options" in st.session_state: del st.session_state["current_options"]
                        st.rerun()
                        
# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — READING (interactive)
# ══════════════════════════════════════════════════════════════════════════════

READING_TOPICS = [
    "Artificial Intelligence", "Climate Change", "Public Health",
    "Space Exploration", "Economics & Trade", "Psychology",
    "Renewable Energy", "Human Rights", "Biotechnology",
    "Urban Planning", "History of Science", "Media & Communication",
    "Education Systems", "Nutrition & Diet", "Cybersecurity",
]

with tab2:
    st.markdown("#### อ่านบทความและตอบคำถาม")
    
    # 1. กำหนดฟังก์ชันสำหรับปุ่มสุ่ม (Callback) เพื่อเปลี่ยนค่าใน session_state อย่างปลอดภัย
    def randomize_topic_callback():
        import random
        st.session_state["reading_topic_sel"] = random.choice(READING_TOPICS)
        st.session_state["article"] = None
        st.session_state["reading_result"] = None

    col_sel, col_rand = st.columns([3, 1])
        
    with col_sel:
        reading_topic = st.selectbox("เลือกหัวข้อบทความ:", READING_TOPICS, key="reading_topic_sel")
            
    with col_rand:
        st.markdown("<div style='margin-top:1.6rem'>", unsafe_allow_html=True)
        # เรียกใช้ on_click เพื่อรันฟังก์ชัน callback ด้านบน
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
            f'<span style="display:inline-block;background:#ececf8;color:#5555aa;font-size:0.75rem;' +
            'font-weight:500;letter-spacing:0.07em;text-transform:uppercase;' +
            f'padding:3px 12px;border-radius:6px;margin-bottom:0.75rem">{art.get("topic","")}</span>',
            unsafe_allow_html=True
        )

        display_passage = art["passage"]
        display_passage = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', display_passage)
        st.markdown(f'<div class="passage-card">{display_passage}</div>', unsafe_allow_html=True)

        # ── TTS: ฟังบทความ ──
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

        # ปรับแก้สีกล่องศัพท์ตรงนี้เพื่อรองรับ Dark Mode ให้ตัวหนังสือคมชัด
        if art.get("vocab"):
            vocab_items = "".join(
                f'<span style="margin-right:1.2rem; display:inline-block; color:#1e1e2f">'
                f'<b>{v["word"]}</b> — <span style="color:#4a4a5a">{v["meaning"]}</span></span>'
                for v in art["vocab"]
            )
            st.markdown(
                '<div style="background:#f4f4fb; color:#1e1e2f; border-radius:10px; padding:0.75rem 1rem;' +
                'font-size:0.85rem; margin-bottom:1rem; line-height:2">' +
                '<span style="font-size:0.7rem; letter-spacing:0.08em; text-transform:uppercase; color:#666677; display:block; margin-bottom:4px">คำศัพท์ในบทความ</span>' +
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
                f'<div class="{css_class}">' +
                f'<b>ผลการตรวจ:</b><br>{res["feedback"]}<br><br>' +
                f'<b>เฉลย:</b> {res["model"]}</div>',
                unsafe_allow_html=True
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — VOCAB QUIZ
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("#### ทบทวนคำศัพท์")
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
                        f'<div class="{css}">{icon} เฉลย: <b>{result["ans"]}</b><br>{result["fb"]}</div>',
                        unsafe_allow_html=True
                    )

        if st.button("📝 ส่งคำตอบทั้งหมด", key="submit_quiz"):
            for i, q in enumerate(quiz):
                u_ans = st.session_state["quiz_answers"].get(i, "").strip()
                correct_ans = q["answer"]
                is_ok = u_ans.lower().strip() == correct_ans.lower().strip()
                if not is_ok and u_ans:
                    fb = call_gemini(f"""
The vocabulary question: "{q['question']}"
Correct answer: "{correct_ans}"
Student answered: "{u_ans}"
In 1 sentence Thai: explain gently why the correct answer is "{correct_ans}".
""")
                else:
                    fb = "ถูกต้อง! 🎉" if is_ok else "ยังไม่ได้ตอบ"
                st.session_state["quiz_results"][i] = {
                    "ok": is_ok,
                    "ans": correct_ans,
                    "fb": fb or "",
                }
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — CHAT
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### สนทนากับ AI Tutor")
    st.caption("พูดคุยเป็นภาษาอังกฤษ — AI จะช่วยแก้ไขและโต้ตอบ")

    # ลิสต์คำถามชวนคุยสารพัดประโยชน์ (เพิ่มหรือเปลี่ยนคำถามตรงนี้ได้ตามใจชอบ)
    ICE_BREAKERS = [
        "What did you do today? Tell me a little bit about your day.",
        "What is your favorite food, and why do you like it?",
        "If you could travel anywhere in the world right now, where would you go?",
        "What are your hobbies? What do you like to do in your free time?",
        "Tell me about a movie or a book that you really like.",
        "What kind of job do you do, or what are you studying right now?",
        "How is the weather today in your city?"
    ]

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # 🌟 จุดแก้ไขที่ 1: ถ้าห้องแชตว่างเปล่า ให้สุ่มคำถามเปิดประโยคทันที
    if not st.session_state.chat_history:
        import random
        starting_question = random.choice(ICE_BREAKERS)
        first_greeting = f"Hello! 👋 I'm your English practice partner. Let's practice together! Here is my first question for you:\n\n**{starting_question}**"
        st.session_state.chat_history.append({"role": "assistant", "text": first_greeting})

    # render history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-wrap"><div class="chat-bubble-user">{msg["text"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-wrap"><div class="chat-bubble-ai">{msg["text"]}</div></div>', unsafe_allow_html=True)

    user_chat = st.chat_input("พิมพ์ตอบเป็นภาษาอังกฤษ...")
    if user_chat:
        st.session_state.chat_history.append({"role": "user", "text": user_chat})
        
        # จัดโครงสร้างประวัติแชตเพื่อส่งต่อให้ Gemini
        history_str = "\n".join(
            f'{"Student" if m["role"]=="user" else "Tutor"}: {m["text"]}'
            for m in st.session_state.chat_history
        )
        
        with st.spinner("กำลังพิมพ์ตอบ..."):
            # 🌟 จุดแก้ไขที่ 2: ปรับ Prompt บังคับให้ตรวจแกรมม่าละเอียดยิ่งขึ้น และต้องถามคำถามใหม่กลับมาเสมอ
            reply = call_gemini(f"""
You are a friendly and encouraging English conversation partner and teacher.
The user is at level "{user_level}", topic: "{topic}".

Please respond to the student's last message by following these steps:
1. Grammar Correction: Check the student's last message. If there are any grammatical errors, point them out gently, explain the mistake in simple Thai, and provide the corrected version. (If it's already correct, praise them briefly).
2. Reply & Keep the conversation going: Respond to the content of their answer naturally like a friend, and then ask ONE new follow-up question related to the topic to keep them talking.

Keep your response friendly, clear, and well-structured. Mix Thai when helpful for Beginner level.

Conversation History:
{history_str}
""")
            if reply:
                st.session_state.chat_history.append({"role": "assistant", "text": reply})
        st.rerun()

    if st.session_state.chat_history:
        # 🌟 จุดแก้ไขที่ 3: ปุ่มล้างประวัติการแชต เมื่อกดแล้วแชตจะว่างเปล่า และลูปด้านบนจะสุ่มคำถามใหม่ให้ทันที
        if st.button("🧹 ล้างประวัติการสนทนา / สุ่มคำถามใหม่", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()
