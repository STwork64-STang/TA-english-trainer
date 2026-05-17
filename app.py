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

# ─── 2. HYBRID RESPONSIVE CSS ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;700&display=swap');

.stApp {
    font-family: 'DM Sans', sans-serif;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem; padding-bottom: 4rem; max-width: 720px; }

.app-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2.3rem;
    color: var(--text-color); 
    margin-bottom: 0.15rem;
    font-weight: 700;
}
.app-sub {
    font-size: 0.9rem;
    color: #888899;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

.settings-dashboard {
    background: var(--background-color);
    background-image: linear-gradient(135deg, rgba(120, 120, 150, 0.08) 0%, rgba(120, 120, 150, 0.03) 100%);
    border: 1px solid rgba(120, 120, 150, 0.2);
    border-radius: 18px;
    padding: 1.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 24px rgba(0,0,0,0.05);
}

.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(120, 120, 150, 0.08);
    padding: 6px;
    border-radius: 14px;
    border: 1px solid rgba(120, 120, 150, 0.1);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 18px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #888899;
    background: transparent;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: var(--background-color) !important;
    color: var(--text-color) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

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
    background: linear-gradient(135deg, #2b3a60 0%, #1a233d 100%);
    color: white;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(255,255,255,0.05);
}
.flashcard-back {
    background: var(--background-color);
    border: 1.5px solid rgba(120, 120, 150, 0.2);
    transform: rotateY(180deg);
    box-shadow: 0 10px 30px rgba(0,0,0,0.08);
    align-items: flex-start;
    justify-content: flex-start;
    gap: 8px;
}
.card-word { font-family: 'DM Serif Display', serif; font-size: 2.5rem; color: #ffcb6b; text-align: center; }
.card-pron { font-size: 1.1rem; opacity: 0.8; color: #fff; }
.back-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: #888; }
.back-value { font-size: 1rem; color: var(--text-color); line-height: 1.5; }

.flashcard-quiz-box {
    background: linear-gradient(135deg, #2b3a60 0%, #1a233d 100%);
    color: white;
    border-radius: 18px;
    padding: 2.5rem 2rem;
    text-align: center;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    margin-bottom: 1.5rem;
}
div[data-testid="stHorizontalBlock"] .stButton > button {
    background: var(--background-color);
    color: var(--text-color);
    border: 1.5px solid rgba(120, 120, 150, 0.2);
    border-radius: 12px;
    padding: 14px 20px;
    text-align: left;
    font-weight: 500;
}
div[data-testid="stHorizontalBlock"] .stButton > button:hover {
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
    background: rgba(120, 120, 150, 0.05);
    border-left: 4px solid #ffcb6b;
    border-radius: 4px 14px 14px 4px;
    padding: 1.5rem 1.75rem;
    font-size: 1rem;
    line-height: 1.9;
    color: var(--text-color);
    margin-bottom: 1.25rem;
}
.quiz-card {
    background: rgba(120, 120, 150, 0.02);
    border: 1.5px solid rgba(120, 120, 150, 0.15);
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
}
.quiz-q { font-family: 'DM Serif Display', serif; font-size: 1.25rem; color: var(--text-color); }

.chat-bubble-user {
    background: #ffcb6b; color: #1a1a2e; border-radius: 18px 18px 4px 18px;
    padding: 0.8rem 1.2rem; font-size: 0.95rem; max-width: 80%; margin-left: auto; margin-bottom: 10px;
    font-weight: 500;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.chat-bubble-ai {
    background: rgba(120, 120, 150, 0.08); color: var(--text-color); border-radius: 18px 18px 18px 4px;
    padding: 0.8rem 1.2rem; font-size: 0.95rem; max-width: 80%; margin-right: auto; margin-bottom: 10px;
    border: 1px solid rgba(120, 120, 150, 0.05);
}
</style>
""", unsafe_allow_html=True)

# ─── 3. APP HEADER ───────────────────────────────────────────────────────────
st.markdown('<p class="app-title">Academic English Trainer</p>', unsafe_allow_html=True)
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

# ─── 5. GEMINI HELPER (ปรับแต่ง Configuration เพื่อเซฟโควต้าคำตอบ) ───────────────
def call_gemini(prompt: str) -> str | None:
    try:
        client = genai.Client(api_key=api_key)
        # ใช้ GenerationConfig เพื่อจำกัดความยาวของคำตอบ ป้องกัน AI บ่นยาวเกินจำเป็น
        config = genai.types.GenerationConfig(
            max_output_tokens=500,  
            temperature=0.3        
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash", 
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

# ─── 6. TABS CONTROL ──────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📇 Flashcards", "📄 Reading", "🧩 Vocab Quiz", "💬 Chat"])

# ==============================================================================
# TAB 1 — FLASHCARDS
# ==============================================================================
with tab1:
    st.markdown("#### 📇 คลังคำศัพท์อัจฉริยะ (Vocab Study & Quiz)")
    st.caption(f"หัวข้อคอร์สในปัจจุบัน: **{topic}** · ระดับผู้เรียน: **{user_level}**")

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

        # ── โหมดเรียนรู้ ──
        if st.session_state["flash_mode"] == "study":
            st.subheader("👀 ฝึกจำคำศัพท์ (คลิกที่การ์ดเพื่อพลิกดูความหมาย)")
            
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
                        <div class="card-hint">💡 คลิกปุ่มด้านล่างเพื่อพลิกดูความหมาย</div>
                    </div>
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

            if st.button("🔄 พลิกการ์ด (Flip)", key=f"flip_btn_{s_idx}", use_container_width=True):
                st.session_state[f"flipped_{s_idx}"] = not st.session_state[f"flipped_{s_idx}"]
                st.rerun()

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
            st.info("💡 ทยอยจำให้ครบทั้ง 5 คำก่อน แล้วกดคลิกที่แท็บ **[🎮 โหมดเกมควิซ]** ด้านบน เพื่อทำแบบทดสอบเก็บคะแนนกันครับ!")

        # ── โหมดทำควิซ ──
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
    st.markdown("#### อ่านบทความและตอบคำถาม")
    
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
            f'<span style="display:inline-block;background:#ececf8;color:#5555aa;font-size:0.75rem;' +
            'font-weight:500;letter-spacing:0.07em;text-transform:uppercase;' +
            f'padding:3px 12px;border-radius:6px;margin-bottom:0.75rem">{art.get("topic","")}</span>',
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

# ==============================================================================
# TAB 3 — VOCAB QUIZ (ปรับปรุงระบบ Batch ยิง API รอบเดียวเพื่อประหยัดโควต้า)
# ==============================================================================
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

        # ปุ่มส่งคำตอบที่ยุบรวมการยิง API เป็นครั้งเดียว (Batching)
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
            
            with st.spinner("AI กำลังตรวจคำตอบทั้งหมดพร้อมกันในครั้งเดียว..."):
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
                        st.error(f"ประมวลผลผลลัพธ์ล้มเหลว กรุณาลองใหม่อีกครั้ง: {e}")
            st.rerun()

# ==============================================================================
# TAB 4 — CHAT
# ==============================================================================
with tab4:
        st.header("💬 BME Classroom Roleplay")
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["text"])
                if message["role"] == "assistant":
                    clean_msg = message["text"].replace('"', '')
                    text_to_speech_button(clean_msg, "🔊 ฟังเสียงอาจารย์ประโยคนี้")

        if user_chat := st.chat_input("พิมพ์ตอบอาจารย์เป็นภาษาอังกฤษตรงนี้..."):
            with st.chat_message("user"):
                st.markdown(user_chat)
            st.session_state.chat_history.append({"role": "user", "text": user_chat})
            
            with st.chat_message("assistant"):
                with st.spinner("อาจารย์กำลังพิมพ์ตอบ..."):
                    prompt = f"""
                    You are a friendly Biomedical Engineering professor talking to a student whose English level is '{user_level}'.
                    Keep responses short (1-2 sentences), easy to understand. Respond naturally in English. No markdown formatting.
                    History: {st.session_state.chat_history}
                    """
                    result = call_gemini_safely(prompt)
                    if result:
                        st.markdown(result)
                        st.session_state.chat_history.append({"role": "assistant", "text": result})
                        st.rerun()

        if st.button("🧹 ล้างประวัติการสนทนา (เริ่มคุยใหม่)"):
            st.session_state.chat_history = []
            st.rerun()
