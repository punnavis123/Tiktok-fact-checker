import streamlit as st
from google import genai
from google.genai import types
import yt_dlp
import os
import time

# --- 1. ตั้งค่าหน้าเว็บ ---
st.set_page_config(page_title="TikTok Fact-Checker AI", page_icon="🩺")
st.title("🩺 TikTok Fact-Checker AI")
st.write("ระบบตรวจสอบข้อมูลสุขภาพด้วยพลัง AI (Gemini 2.5)")

# --- 2. ดึงกุญแจ API (ใช้ชื่อ GEMINI_API_KEY ตามที่คุณตั้งไว้ในหน้า Secrets) ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error("❌ ไม่พบ API Key! กรุณาตรวจสอบชื่อในช่อง Secrets ของ Streamlit")
    st.stop()

url = st.text_input("วางลิงก์ TikTok ที่ต้องการตรวจสอบ:")

if st.button("🚀 เริ่มการตรวจสอบ"):
    if url:
        with st.status("🛠️ กำลังเริ่มกระบวนการ...", expanded=True) as status:
            # --- ขั้นตอนที่ 1: ดาวน์โหลดวิดีโอ ---
            st.write("📥 กำลังดาวน์โหลดวิดีโอ...")
            ydl_opts = {'format': 'best', 'outtmpl': 'temp_v.mp4', 'overwrites': True}
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception as e:
                st.error(f"ดาวน์โหลดล้มเหลว: {e}")
                st.stop()

            # --- ขั้นตอนที่ 2: อัปโหลดไปที่ Google ---
            st.write("🧠 กำลังส่งข้อมูลให้ AI...")
            with open("temp_v.mp4", "rb") as f:
                uploaded_file = client.files.upload(file=f, config={'mime_type': 'video/mp4'})
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(3)
                uploaded_file = client.files.get(name=uploaded_file.name)

            # --- ขั้นตอนที่ 3: วิเคราะห์พร้อมแก้ไขชื่อ Safety Categories ---
            st.write("⚖️ AI กำลังวิเคราะห์ข้อมูลสุขภาพ...")
            prompt = "ถอดสคริปต์ภาษาไทยและตรวจสอบความน่าเชื่อถือทางการแพทย์ของสมุนไพรในคลิปนี้"

            try:
                # แก้ไขชื่อ Category ให้มีคำว่า HARM_CATEGORY_ นำหน้า
                response = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=[prompt, uploaded_file],
                    config=types.GenerateContentConfig(
                        safety_settings=[
                            types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_NONE'),
                            types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_NONE'),
                            types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                            types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                        ]
                    )
                )
                status.update(label="✨ วิเคราะห์เสร็จสิ้น!", state="complete")
                st.subheader("📝 รายงานการตรวจสอบ")
                st.markdown(response.text)
            except Exception as e:
                st.error(f"❌ AI ไม่สามารถแสดงผลได้: {e}")
                
            # ลบไฟล์วิดีโอออกหลังใช้เสร็จเพื่อประหยัดพื้นที่
            if os.path.exists("temp_v.mp4"):
                os.remove("temp_v.mp4")
    else:
        st.warning("⚠️ กรุณาวางลิงก์วิดีโอก่อนครับ")
