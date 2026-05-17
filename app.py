import streamlit as st
from google import genai
from google.genai.errors import APIError
import json
import re

st.set_page_config(page_title="Academic English AI Trainer", page_icon="📖", layout="centered")

# ─── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* ── hide default streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 720px; }

/* ── page title ── */
.app-title {
    font-family: 'DM Serif Display', serif;
    font-size: 2rem;
    color: #1a1a2e;
    margin-bottom: 0.15rem;
}
.app-sub {
    font-size: 0.85rem;
    color: #888;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

/* ── tab bar ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #f4f4f6;
    padding: 6px;
    border-radius: 14px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 18px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #666;
    background: transparent;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #1a1a2e !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.08);
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTabs [data-baseweb="tab-border"] { display: none; }

/* ── buttons ── */
.stButton > button {
    background: #1a1a2e;
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 10px 22px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    font-weight: 500;
    transition: all 0.2s ease;
    width: 100%;
}
.stButton > button:hover {
    background: #2d2d50;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(26,26,46,0.18);
}
.stButton > button:active { transform: translateY(0); }

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background: #f9f9fb;
    border-right: 1px solid #ececf0;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label {
    font-size: 0.8rem;
    font-weight: 500;
    color: #555;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── flashcard flip ── */
.flashcard-scene {
    width: 100%;
    height: 240px;
    perspective: 900px;
    cursor: pointer;
    margin: 0.5rem 0 1rem;
}
.flashcard {
    width: 100%;
    height: 100%;
    position: relative;
    transform-style: preserve-3d;
    transition: transform 0.55s cubic-bezier(0.4, 0, 0.2, 1);
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
    align-items: center;
    justify-content: center;
    padding: 2rem;
    gap: 10px;
}
.flashcard-front {
    background: linear-gradient(135deg, #1a1a2e 0%, #2d2d50 100%);
    color: white;
    box-shadow: 0 10px 40px rgba(26,26,46,0.22);
}
.flashcard-back {
    background: #ffffff;
    border: 1.5px solid #e8e8f0;
    transform: rotateY(180deg);
    box-shadow: 0 10px 40px rgba(0,0,0,0.08);
    align-items: flex-start;
    justify-content: flex-start;
    padding: 1.75rem 2rem;
    gap: 14px;
}
.card-word {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    letter-spacing: -0.01em;
}
.card-pron {
    font-size: 1rem;
    opacity: 0.6;
    letter-spacing: 0.04em;
}
.card-hint {
    font-size: 0.75rem;
    opacity: 0.45;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 1rem;
}
.back-label {
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 2px;
}
.back-value {
    font-size: 0.95rem;
    color: #1a1a2e;
    line-height: 1.6;
}
.back-example {
    font-size: 0.88rem;
    color: #555;
    font-style: italic;
    line-height: 1.65;
    border-top: 1px solid #f0f0f4;
    padding-top: 12px;
    margin-top: 4px;
}

/* ── card nav dots ── */
.dot-nav {
    display: flex;
    justify-content: center;
    gap: 7px;
    margin: 0.5rem 0 1rem;
}
.dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #d8d8e0;
    display: inline-block;
    transition: all 0.2s;
}
.dot.active {
    background: #1a1a2e;
    width: 22px;
    border-radius: 4px;
}

/* ── reading passage ── */
.passage-card {
    background: #f9f9fb;
    border-left: 3px solid #1a1a2e;
    border-radius: 0 14px 14px 0;
    padding: 1.4rem 1.6rem;
    font-size: 0.97rem;
    line-height: 1.85;
    color: #1a1a2e;
    margin-bottom: 1.25rem;
}

/* ── answer result ── */
.result-correct {
    background: #f0faf4;
    border: 1px solid #6fcf97;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #1e6b3f;
    font-size: 0.9rem;
    line-height: 1.6;
}
.result-wrong {
    background: #fff5f5;
    border: 1px solid #f48c8c;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #8b1a1a;
    font-size: 0.9rem;
    line-height: 1.6;
}

/* ── quiz question card ── */
.quiz-card {
    background: #fff;
    border: 1.5px solid #e8e8f0;
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
.quiz-q {
    font-family: 'DM Serif Display', serif;
    font-size: 1.25rem;
    color: #1a1a2e;
    margin-bottom: 0.5rem;
}
.quiz-type-badge {
    display: inline-block;
    background: #ececf8;
    color: #5555aa;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 6px;
    margin-bottom: 0.75rem;
}

/* ── chat ── */
.chat-bubble-user {
    background: #1a1a2e;
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 0.75rem 1.1rem;
    font-size: 0.92rem;
    line-height: 1.6;
    max-width: 80%;
    margin-left: auto;
    margin-bottom: 10px;
}
.chat-bubble-ai {
    background: #f4f4f8;
    color: #1a1a2e;
    border-radius: 18px 18px 18px 4px;
    padding: 0.75rem 1.1rem;
    font-size: 0.92rem;
    line-height: 1.6;
    max-width: 80%;
    margin-right: auto;
    margin-bottom: 10px;
}
.chat-wrap { padding: 0.5rem 0; }

/* ── selectbox & text input ── */
.stSelectbox > div > div,
.stTextInput > div > div > input {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
st.sidebar.markdown("### ⚙️ ตั้งค่า")
api_key = st.sidebar.text_input("Gemini API Key", type="password", placeholder="AIza...")
user_level = st.sidebar.selectbox(
    "ระดับภาษาอังกฤษ",
    ["Level 1: Beginner", "Level 2: Intermediate", "Level 3: Advanced"]
)
topic = st.sidebar.selectbox(
    "หัวข้อที่สนใจ",
    ["General Academic", "Science & Technology", "Social Sciences",
     "Business & Economics", "Medicine & Health", "Law & Ethics", "Literature & Arts"]
)
st.sidebar.markdown("---")
st.sidebar.caption("💡 รับ API Key ฟรีที่ [Google AI Studio](https://aistudio.google.com/app/apikey)")

# ─── GEMINI HELPER ────────────────────────────────────────────────────────────
def call_gemini(prompt: str) -> str | None:
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except APIError as e:
        st.error(f"🚨 Gemini API Error {e.code}: {e.message}")
        return None
    except Exception as e:
        st.error(f"❌ {e}")
        return None

def parse_json(text: str):
    clean = re.sub(r"```(?:json)?|```", "", text or "").strip()
    return json.loads(clean)

# ─── TITLE ───────────────────────────────────────────────────────────────────
st.markdown('<p class="app-title">Academic English Trainer</p>', unsafe_allow_html=True)
st.markdown('<p class="app-sub">AI-Powered · Gemini · ฝึกภาษาอังกฤษเชิงวิชาการ</p>', unsafe_allow_html=True)

if not api_key:
    st.markdown("#### 🔑 ใส่ Gemini API Key เพื่อเริ่มใช้งาน")
    main_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="AIza...",
        help="รับคีย์ฟรีที่ https://aistudio.google.com/app/apikey"
    )
    if main_key:
        api_key = main_key
    else:
        st.caption("💡 รับ API Key ฟรีที่ [Google AI Studio](https://aistudio.google.com/app/apikey)")
        st.stop()

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📇 Flashcards", "📄 Reading", "🧩 Vocab Quiz", "💬 Chat"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FLASHCARDS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("#### สร้างแฟลชการ์ดคำศัพท์")
    st.caption(f"หัวข้อ: **{topic}** · ระดับ: **{user_level}**")

    if st.button("🔄 สร้างการ์ดชุดใหม่ (5 ใบ)", key="gen_cards"):
        with st.spinner("กำลังสร้างการ์ด..."):
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
                    st.session_state["card_flipped"] = False
                except Exception as e:
                    st.error(f"แปลง JSON ไม่ได้: {e}\n\n{raw}")

    # ── render flashcard ──
    if "cards" in st.session_state and st.session_state["cards"]:
        cards = st.session_state["cards"]
        idx   = st.session_state.get("card_idx", 0)
        flipped = st.session_state.get("card_flipped", False)
        card  = cards[idx]

        # dot nav
        dots_html = '<div class="dot-nav">' + "".join(
            f'<span class="dot{"  active" if i == idx else ""}"></span>'
            for i in range(len(cards))
        ) + "</div>"
        st.markdown(dots_html, unsafe_allow_html=True)

        # card HTML
        flip_class = "flipped" if flipped else ""
        card_html = f"""
<div class="flashcard-scene" onclick="
    var el = this.querySelector('.flashcard');
    el.classList.toggle('flipped');
">
  <div class="flashcard {flip_class}">
    <div class="flashcard-face flashcard-front">
      <div class="card-word">{card['word']}</div>
      <div class="card-pron">{card.get('pronunciation','')}</div>
      <div class="card-hint">แตะเพื่อดูความหมาย</div>
    </div>
    <div class="flashcard-face flashcard-back">
      <div>
        <div class="back-label">Definition</div>
        <div class="back-value">{card['definition']}</div>
      </div>
      <div>
        <div class="back-label">ความหมาย</div>
        <div class="back-value">{card.get('thai','')}</div>
      </div>
      <div class="back-example">"{card.get('example','')}"</div>
    </div>
  </div>
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)

        # nav buttons
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("← ก่อนหน้า", key="prev_card", disabled=(idx == 0)):
                st.session_state["card_idx"] = idx - 1
                st.session_state["card_flipped"] = False
                st.rerun()
        with col_info:
            st.markdown(
                f'<p style="text-align:center;color:#888;font-size:0.85rem;margin-top:0.6rem">'
                f'{idx+1} / {len(cards)}</p>',
                unsafe_allow_html=True
            )
        with col_next:
            if st.button("ถัดไป →", key="next_card", disabled=(idx == len(cards) - 1)):
                st.session_state["card_idx"] = idx + 1
                st.session_state["card_flipped"] = False
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — READING (interactive)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### อ่านบทความและตอบคำถาม")
    st.caption(f"หัวข้อ: **{topic}** · ระดับ: **{user_level}**")

    if st.button("📖 โหลดบทความใหม่", key="gen_article"):
        with st.spinner("กำลังสร้างบทความ..."):
            raw = call_gemini(f"""
You are an academic English reading teacher.
Write a short academic passage (3-5 sentences) about "{topic}" for level "{user_level}".
Then create 1 comprehension question with a short open-ended answer (not multiple choice).
Return ONLY valid JSON, no markdown:
{{"passage":"...","question":"...","model_answer":"...","explanation_th":"..."}}
""")
            if raw:
                try:
                    st.session_state["article"] = parse_json(raw)
                    st.session_state["reading_answer"] = ""
                    st.session_state["reading_result"] = None
                except Exception as e:
                    st.error(f"แปลง JSON ไม่ได้: {e}\n\n{raw}")

    if "article" in st.session_state and st.session_state["article"]:
        art = st.session_state["article"]

        st.markdown(f'<div class="passage-card">{art["passage"]}</div>', unsafe_allow_html=True)
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
                        "explain": art["explanation_th"],
                    }

        if st.session_state.get("reading_result"):
            res = st.session_state["reading_result"]
            fb_lower = (res["feedback"] or "").lower()
            css_class = "result-correct" if any(w in fb_lower for w in ["correct","good","right","great","well"]) else "result-wrong"
            st.markdown(
                f'<div class="{css_class}">'
                f'<b>ผลการตรวจ:</b><br>{res["feedback"]}<br><br>'
                f'<b>เฉลย:</b> {res["model"]}'
                f'</div>',
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

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # render history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-wrap"><div class="chat-bubble-user">{msg["text"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-wrap"><div class="chat-bubble-ai">{msg["text"]}</div></div>', unsafe_allow_html=True)

    user_chat = st.chat_input("พิมพ์ตอบเป็นภาษาอังกฤษ...")
    if user_chat:
        st.session_state.chat_history.append({"role": "user", "text": user_chat})
        history_str = "\n".join(
            f'{"Student" if m["role"]=="user" else "Tutor"}: {m["text"]}'
            for m in st.session_state.chat_history
        )
        with st.spinner("กำลังพิมพ์ตอบ..."):
            reply = call_gemini(f"""
You are a friendly academic English tutor.
Student level: "{user_level}", topic: "{topic}".
Gently correct any noticeable grammar errors in the student's last message before replying.
Keep responses concise and encouraging. Mix Thai when helpful for Beginner level.

Conversation:
{history_str}

Reply to the student's last message naturally.
""")
            if reply:
                st.session_state.chat_history.append({"role": "assistant", "text": reply})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🧹 ล้างประวัติการสนทนา", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()/* ── tab bar ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: #f4f4f6;
    padding: 6px;
    border-radius: 14px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 18px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #666;
    background: transparent;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #1a1a2e !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.08);
}
.stTabs [data-baseweb="tab-highlight"] { display: none; }
.stTabs [data-baseweb="tab-border"] { display: none; }

/* ── buttons ── */
.stButton > button {
    background: #1a1a2e;
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 10px 22px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.88rem;
    font-weight: 500;
    transition: all 0.2s ease;
    width: 100%;
}
.stButton > button:hover {
    background: #2d2d50;
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(26,26,46,0.18);
}
.stButton > button:active { transform: translateY(0); }

/* ── sidebar ── */
[data-testid="stSidebar"] {
    background: #f9f9fb;
    border-right: 1px solid #ececf0;
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label {
    font-size: 0.8rem;
    font-weight: 500;
    color: #555;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── flashcard flip ── */
.flashcard-scene {
    width: 100%;
    height: 240px;
    perspective: 900px;
    cursor: pointer;
    margin: 0.5rem 0 1rem;
}
.flashcard {
    width: 100%;
    height: 100%;
    position: relative;
    transform-style: preserve-3d;
    transition: transform 0.55s cubic-bezier(0.4, 0, 0.2, 1);
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
    align-items: center;
    justify-content: center;
    padding: 2rem;
    gap: 10px;
}
.flashcard-front {
    background: linear-gradient(135deg, #1a1a2e 0%, #2d2d50 100%);
    color: white;
    box-shadow: 0 10px 40px rgba(26,26,46,0.22);
}
.flashcard-back {
    background: #ffffff;
    border: 1.5px solid #e8e8f0;
    transform: rotateY(180deg);
    box-shadow: 0 10px 40px rgba(0,0,0,0.08);
    align-items: flex-start;
    justify-content: flex-start;
    padding: 1.75rem 2rem;
    gap: 14px;
}
.card-word {
    font-family: 'DM Serif Display', serif;
    font-size: 2.2rem;
    letter-spacing: -0.01em;
}
.card-pron {
    font-size: 1rem;
    opacity: 0.6;
    letter-spacing: 0.04em;
}
.card-hint {
    font-size: 0.75rem;
    opacity: 0.45;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 1rem;
}
.back-label {
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #aaa;
    margin-bottom: 2px;
}
.back-value {
    font-size: 0.95rem;
    color: #1a1a2e;
    line-height: 1.6;
}
.back-example {
    font-size: 0.88rem;
    color: #555;
    font-style: italic;
    line-height: 1.65;
    border-top: 1px solid #f0f0f4;
    padding-top: 12px;
    margin-top: 4px;
}

/* ── card nav dots ── */
.dot-nav {
    display: flex;
    justify-content: center;
    gap: 7px;
    margin: 0.5rem 0 1rem;
}
.dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #d8d8e0;
    display: inline-block;
    transition: all 0.2s;
}
.dot.active {
    background: #1a1a2e;
    width: 22px;
    border-radius: 4px;
}

/* ── reading passage ── */
.passage-card {
    background: #f9f9fb;
    border-left: 3px solid #1a1a2e;
    border-radius: 0 14px 14px 0;
    padding: 1.4rem 1.6rem;
    font-size: 0.97rem;
    line-height: 1.85;
    color: #1a1a2e;
    margin-bottom: 1.25rem;
}

/* ── answer result ── */
.result-correct {
    background: #f0faf4;
    border: 1px solid #6fcf97;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #1e6b3f;
    font-size: 0.9rem;
    line-height: 1.6;
}
.result-wrong {
    background: #fff5f5;
    border: 1px solid #f48c8c;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    color: #8b1a1a;
    font-size: 0.9rem;
    line-height: 1.6;
}

/* ── quiz question card ── */
.quiz-card {
    background: #fff;
    border: 1.5px solid #e8e8f0;
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.05);
}
.quiz-q {
    font-family: 'DM Serif Display', serif;
    font-size: 1.25rem;
    color: #1a1a2e;
    margin-bottom: 0.5rem;
}
.quiz-type-badge {
    display: inline-block;
    background: #ececf8;
    color: #5555aa;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 6px;
    margin-bottom: 0.75rem;
}

/* ── chat ── */
.chat-bubble-user {
    background: #1a1a2e;
    color: white;
    border-radius: 18px 18px 4px 18px;
    padding: 0.75rem 1.1rem;
    font-size: 0.92rem;
    line-height: 1.6;
    max-width: 80%;
    margin-left: auto;
    margin-bottom: 10px;
}
.chat-bubble-ai {
    background: #f4f4f8;
    color: #1a1a2e;
    border-radius: 18px 18px 18px 4px;
    padding: 0.75rem 1.1rem;
    font-size: 0.92rem;
    line-height: 1.6;
    max-width: 80%;
    margin-right: auto;
    margin-bottom: 10px;
}
.chat-wrap { padding: 0.5rem 0; }

/* ── selectbox & text input ── */
.stSelectbox > div > div,
.stTextInput > div > div > input {
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
st.sidebar.markdown("### ⚙️ ตั้งค่า")
api_key = st.sidebar.text_input("Gemini API Key", type="password", placeholder="AIza...")
user_level = st.sidebar.selectbox(
    "ระดับภาษาอังกฤษ",
    ["Level 1: Beginner", "Level 2: Intermediate", "Level 3: Advanced"]
)
topic = st.sidebar.selectbox(
    "หัวข้อที่สนใจ",
    ["General Academic", "Science & Technology", "Social Sciences",
     "Business & Economics", "Medicine & Health", "Law & Ethics", "Literature & Arts"]
)
st.sidebar.markdown("---")
st.sidebar.caption("💡 รับ API Key ฟรีที่ [Google AI Studio](https://aistudio.google.com/app/apikey)")

# ─── GEMINI HELPER ────────────────────────────────────────────────────────────
def call_gemini(prompt: str) -> str | None:
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return response.text
    except APIError as e:
        st.error(f"🚨 Gemini API Error {e.code}: {e.message}")
        return None
    except Exception as e:
        st.error(f"❌ {e}")
        return None

def parse_json(text: str):
    clean = re.sub(r"```(?:json)?|```", "", text or "").strip()
    return json.loads(clean)

# ─── TITLE ───────────────────────────────────────────────────────────────────
st.markdown('<p class="app-title">Academic English Trainer</p>', unsafe_allow_html=True)
st.markdown('<p class="app-sub">AI-Powered · Gemini · ฝึกภาษาอังกฤษเชิงวิชาการ</p>', unsafe_allow_html=True)

if not api_key:
    st.warning("⚠️ กรุณาใส่ Gemini API Key ที่แถบด้านซ้ายก่อนใช้งาน")
    st.stop()

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📇 Flashcards", "📄 Reading", "🧩 Vocab Quiz", "💬 Chat"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FLASHCARDS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("#### สร้างแฟลชการ์ดคำศัพท์")
    st.caption(f"หัวข้อ: **{topic}** · ระดับ: **{user_level}**")

    if st.button("🔄 สร้างการ์ดชุดใหม่ (5 ใบ)", key="gen_cards"):
        with st.spinner("กำลังสร้างการ์ด..."):
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
                    st.session_state["card_flipped"] = False
                except Exception as e:
                    st.error(f"แปลง JSON ไม่ได้: {e}\n\n{raw}")

    # ── render flashcard ──
    if "cards" in st.session_state and st.session_state["cards"]:
        cards = st.session_state["cards"]
        idx   = st.session_state.get("card_idx", 0)
        flipped = st.session_state.get("card_flipped", False)
        card  = cards[idx]

        # dot nav
        dots_html = '<div class="dot-nav">' + "".join(
            f'<span class="dot{"  active" if i == idx else ""}"></span>'
            for i in range(len(cards))
        ) + "</div>"
        st.markdown(dots_html, unsafe_allow_html=True)

        # card HTML
        flip_class = "flipped" if flipped else ""
        card_html = f"""
<div class="flashcard-scene" onclick="
    var el = this.querySelector('.flashcard');
    el.classList.toggle('flipped');
">
  <div class="flashcard {flip_class}">
    <div class="flashcard-face flashcard-front">
      <div class="card-word">{card['word']}</div>
      <div class="card-pron">{card.get('pronunciation','')}</div>
      <div class="card-hint">แตะเพื่อดูความหมาย</div>
    </div>
    <div class="flashcard-face flashcard-back">
      <div>
        <div class="back-label">Definition</div>
        <div class="back-value">{card['definition']}</div>
      </div>
      <div>
        <div class="back-label">ความหมาย</div>
        <div class="back-value">{card.get('thai','')}</div>
      </div>
      <div class="back-example">"{card.get('example','')}"</div>
    </div>
  </div>
</div>
"""
        st.markdown(card_html, unsafe_allow_html=True)

        # nav buttons
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("← ก่อนหน้า", key="prev_card", disabled=(idx == 0)):
                st.session_state["card_idx"] = idx - 1
                st.session_state["card_flipped"] = False
                st.rerun()
        with col_info:
            st.markdown(
                f'<p style="text-align:center;color:#888;font-size:0.85rem;margin-top:0.6rem">'
                f'{idx+1} / {len(cards)}</p>',
                unsafe_allow_html=True
            )
        with col_next:
            if st.button("ถัดไป →", key="next_card", disabled=(idx == len(cards) - 1)):
                st.session_state["card_idx"] = idx + 1
                st.session_state["card_flipped"] = False
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — READING (interactive)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("#### อ่านบทความและตอบคำถาม")
    st.caption(f"หัวข้อ: **{topic}** · ระดับ: **{user_level}**")

    if st.button("📖 โหลดบทความใหม่", key="gen_article"):
        with st.spinner("กำลังสร้างบทความ..."):
            raw = call_gemini(f"""
You are an academic English reading teacher.
Write a short academic passage (3-5 sentences) about "{topic}" for level "{user_level}".
Then create 1 comprehension question with a short open-ended answer (not multiple choice).
Return ONLY valid JSON, no markdown:
{{"passage":"...","question":"...","model_answer":"...","explanation_th":"..."}}
""")
            if raw:
                try:
                    st.session_state["article"] = parse_json(raw)
                    st.session_state["reading_answer"] = ""
                    st.session_state["reading_result"] = None
                except Exception as e:
                    st.error(f"แปลง JSON ไม่ได้: {e}\n\n{raw}")

    if "article" in st.session_state and st.session_state["article"]:
        art = st.session_state["article"]

        st.markdown(f'<div class="passage-card">{art["passage"]}</div>', unsafe_allow_html=True)
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
                        "explain": art["explanation_th"],
                    }

        if st.session_state.get("reading_result"):
            res = st.session_state["reading_result"]
            fb_lower = (res["feedback"] or "").lower()
            css_class = "result-correct" if any(w in fb_lower for w in ["correct","good","right","great","well"]) else "result-wrong"
            st.markdown(
                f'<div class="{css_class}">'
                f'<b>ผลการตรวจ:</b><br>{res["feedback"]}<br><br>'
                f'<b>เฉลย:</b> {res["model"]}'
                f'</div>',
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

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # render history
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-wrap"><div class="chat-bubble-user">{msg["text"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-wrap"><div class="chat-bubble-ai">{msg["text"]}</div></div>', unsafe_allow_html=True)

    user_chat = st.chat_input("พิมพ์ตอบเป็นภาษาอังกฤษ...")
    if user_chat:
        st.session_state.chat_history.append({"role": "user", "text": user_chat})
        history_str = "\n".join(
            f'{"Student" if m["role"]=="user" else "Tutor"}: {m["text"]}'
            for m in st.session_state.chat_history
        )
        with st.spinner("กำลังพิมพ์ตอบ..."):
            reply = call_gemini(f"""
You are a friendly academic English tutor.
Student level: "{user_level}", topic: "{topic}".
Gently correct any noticeable grammar errors in the student's last message before replying.
Keep responses concise and encouraging. Mix Thai when helpful for Beginner level.

Conversation:
{history_str}

Reply to the student's last message naturally.
""")
            if reply:
                st.session_state.chat_history.append({"role": "assistant", "text": reply})
        st.rerun()

    if st.session_state.chat_history:
        if st.button("🧹 ล้างประวัติการสนทนา", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()
