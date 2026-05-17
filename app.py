import streamlit as st
from google import genai
from google.genai import types

# ตั้งค่าหน้าตาของแอปพลิเคชัน
st.set_page_config(page_title="BME English AI Trainer", page_icon="🧬", layout="centered")

st.title("🧬 BME English AI Trainer")
st.subheader("โปรแกรมฝึกภาษาอังกฤษอัจฉริยะสำหรับวิศวกรรมชีวการแพทย์")
st.write("---")

# 1. ส่วนตั้งค่า API Key และระดับภาษา
st.sidebar.header("⚙️ การตั้งค่าระบบ AI")
api_key = st.sidebar.text_input("ใส่ Gemini API Key ของคุณที่นี่:", type="password")
user_level = st.sidebar.selectbox(
    "เลือกระดับภาษาอังกฤษของคุณปัจจุบัน:",
    ["Level 1: Beginner (ศัพท์น้อย, เน้นประโยคสั้นมาก)", 
     "Level 2: Intermediate (พอรู้ศัพท์ BME บ้าง, เริ่มอ่านเป็นย่อหน้า)", 
     "Level 3: Advanced (เน้นเตรียมตัวอ่าน Text Book และนำเสนองาน)"]
)

# ตรวจสอบว่าใส่ API Key หรือยัง
if not api_key:
    st.warning("⚠️ กรุณาใส่ Gemini API Key ที่แถบด้านซ้ายมือ เพื่อเปิดใช้งานสมองของ AI ครับ")
    st.info("💡 วิธีเอาคีย์ฟรี: ไปที่เว็บ Google AI Studio -> กด Create API Key -> ก๊อปปี้มาวางได้เลย ไม่เสียเงินครับ")
else:
    # เชื่อมต่อกับ Gemini Client
    client = genai.Client(api_key=api_key)

    # สร้างเมนูแท็บ 4 โมดูลหลัก
    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 คำศัพท์ประจำวัน", 
        "📄 อ่านบทความวิชาการ", 
        "✍️ ฝึกเขียนและตรวจแรมม่า", 
        "💬 แชทจำลองสถานการณ์"
    ])

    # ----------------------------------------------------
    # TAB 1: คำศัพท์ประจำวัน (Dynamic Vocab)
    # ----------------------------------------------------
    with tab1:
        st.header("📚 Biomedical Vocabulary Generator")
        st.write("กดปุ่มด้านล่างเพื่อให้ AI สุ่มคำศัพท์ BME ที่เหมาะกับระดับของคุณ")
        
        if st.button("🔄 สุ่มคำศัพท์ใหม่สำหรับวันนี้"):
            with st.spinner("AI กำลังเลือกคำศัพท์ที่เหมาะกับคุณ..."):
                prompt = f"""
                You are a Biomedical Engineering English Professor. 
                Generate 3 vocabulary words suitable for a student at level: '{user_level}'.
                For each word, provide:
                1. The word
                2. Thai pronunciation (คำอ่านภาษาไทย)
                3. Meaning in Thai (ความหมายภาษาไทย)
                4. A simple example sentence related to Biomedical Engineering.
                Respond in friendly Thai explanation.
                """
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt
                )
                st.markdown(response.text)

    # ----------------------------------------------------
    # TAB 2: อ่านบทความวิชาการ (Adaptive Reading)
    # ----------------------------------------------------
    with tab2:
        st.header("📄 Adaptive Academic Reading")
        st.write("AI จะเจนบทความสั้นๆ เกี่ยวกับ BME พร้อมคำถามจับใจความตามระดับของคุณ")
        
        if st.button("📖 เจนบทความใหม่"):
            with st.spinner("AI กำลังแต่งบทความ..."):
                prompt = f"""
                Write a short paragraph about Biomedical Engineering suitable for a student at level: '{user_level}'.
                After the paragraph, ask 1 multiple-choice question (with A, B, C options) to check understanding.
                Provide the correct answer and a brief explanation in Thai at the very end hidden under a note.
                """
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt
                )
                st.session_state['current_reading'] = response.text
        
        if 'current_reading' in st.session_state:
            st.markdown(st.session_state['current_reading'])

    # ----------------------------------------------------
    # TAB 3: ฝึกเขียนและตรวจแกรมม่า (Grammar Corrector)
    # ----------------------------------------------------
    with tab3:
        st.header("✍️ AI Grammar Tutor")
        st.write("พิมพ์ประโยคภาษาอังกฤษของคุณด้านล่าง (เช่น แนะนำตัว, อธิบายแล็บ หรือตอบคำถามจากข้อสอบ) AI จะช่วยตรวจและแก้ไขให้ถูกต้องทันที")
        
        user_text = st.text_area("พิมพ์ข้อความภาษาอังกฤษของคุณที่นี่ (ผิดถูกพิมพ์มาได้เลยไม่ต้องกังวล):", placeholder="e.g., My name is Tang. I want to study BME because I want to make pacemaker.")
        
        if st.button("✨ ส่งให้ AI ตรวจทาน"):
            if user_text:
                with st.spinner("อาจารย์ AI กำลังตรวจงานเขียน..."):
                    prompt = f"""
                    You are a helpful English teacher for a Biomedical Engineering student. 
                    The student's level is '{user_level}'.
                    Review this sentence written by the student: "{user_text}"
                    1. Correct any grammar mistakes.
                    2. Provide a better/more professional version of the sentence.
                    3. Explain the mistakes gently in Thai so they can learn.
                    """
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt
                    )
                    st.success("🤖 ผลการตรวจจาก AI:")
                    st.markdown(response.text)
            else:
                st.error("กรุณาพิมพ์ข้อความก่อนกดส่งครับ")

    # ----------------------------------------------------
    # TAB 4: แชทจำลองสถานการณ์ (Roleplay Chat)
    # ----------------------------------------------------
    with tab4:
        st.header("💬 BME Classroom Roleplay")
        st.write("จำลองสถานการณ์คุยกับอาจารย์ฝรั่งในห้องเรียน BME (พิมพ์คุยโต้ตอบได้เลยครับ)")
        
        # ตั้งค่าระบบจำประวัติการคุย
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        # แสดงข้อความที่คุยกันผ่านมา
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["text"])

        # ช่องรับข้อความใหม่จากผู้ใช้
        if user_chat := st.chat_input("พิมพ์ตอบอาจารย์เป็นภาษาอังกฤษตรงนี้..."):
            # แสดงข้อความฝั่งผู้ใช้
            with st.chat_message("user"):
                st.markdown(user_chat)
            st.session_state.chat_history.append({"role": "user", "text": user_chat})
            
            # ส่งไปถาม AI โดยส่งประวัติการคุยไปด้วย
            with st.chat_message("assistant"):
                with st.spinner("อาจารย์กำลังพิมพ์ตอบ..."):
                    prompt = f"""
                    You are a friendly Biomedical Engineering professor talking to a student whose English level is '{user_level}'.
                    Keep your responses relatively short, easy to understand, and encourage the student.
                    If the student made a noticeable grammar mistake in their last message, gently correct it briefly before continuing the conversation.
                    
                    Conversation history so far:
                    {st.session_state.chat_history}
                    
                    Respond to the student's latest message naturally.
                    """
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt
                    )
                    st.markdown(response.text)
            st.session_state.chat_history.append({"role": "assistant", "text": response.text})

        if st.button("🧹 ล้างประวัติการสนทนา (เริ่มคุยใหม่)"):
            st.session_state.chat_history = []
            st.rerun()
