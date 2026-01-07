import streamlit as st
from google import genai
from google.genai import types # เพิ่มการตั้งค่าความปลอดภัย
import yt_dlp
import os
import time

st.set_page_config(page_title="TikTok Fact-Checker AI", page_icon="🩺")
st.title("🩺 TikTok Fact-Checker AI")

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except:
    st.error("❌ ไม่พบ API Key ใน Secrets")
    st.stop()

url = st.text_input("วางลิงก์ TikTok ที่ต้องการตรวจสอบ:")

if st.button("🚀 เริ่มการตรวจสอบ"):
    if url:
        with st.status("🛠️ กำลังดำเนินการ...", expanded=True) as status:
            # --- 1. ดาวน์โหลด ---
            st.write("📥 กำลังดาวน์โหลด...")
            ydl_opts = {'format': 'best', 'outtmpl': 'temp_v.mp4', 'overwrites': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # --- 2. อัปโหลด ---
            st.write("🧠 กำลังส่งให้ AI...")
            with open("temp_v.mp4", "rb") as f:
                uploaded_file = client.files.upload(file=f, config={'mime_type': 'video/mp4'})
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(3)
                uploaded_file = client.files.get(name=uploaded_file.name)

            # --- 3. วิเคราะห์ (แบบปรับจูนพิเศษ) ---
            st.write("⚖️ AI กำลังวิเคราะห์ข้อมูลสุขภาพ...")
            prompt = "ถอดสคริปต์ภาษาไทยและตรวจสอบความถูกต้องทางการแพทย์ของคลิปนี้"
            
            try:
                # ปรับ Safety Settings ให้ยอมรับเนื้อหาการแพทย์เพื่อการศึกษา
                response = client.models.generate_content(
                    model='gemini-1.5-flash', 
                    contents=[prompt, uploaded_file],
                    config=types.GenerateContentConfig(
                        safety_settings=[
                            types.SafetySetting(category='HATE_SPEECH', threshold='BLOCK_NONE'),
                            types.SafetySetting(category='HARASSMENT', threshold='BLOCK_NONE'),
                            types.SafetySetting(category='DANGEROUS_CONTENT', threshold='BLOCK_NONE'),
                            types.SafetySetting(category='SEXUALLY_EXPLICIT', threshold='BLOCK_NONE'),
                        ]
                    )
                )
                status.update(label="✨ วิเคราะห์เสร็จสิ้น!", state="complete")
                st.subheader("📝 รายงานผลการตรวจสอบ")
                st.markdown(response.text)
            except Exception as e:
                # แสดงสาเหตุของ Error ให้ชัดเจน
                if "429" in str(e):
                    st.error("⚠️ โควตาเต็ม! กรุณารอ 1-2 นาทีแล้วลองใหม่ครับ")
                elif "safety" in str(e).lower():
                    st.error("🛡️ เนื้อหาถูกบล็อกโดยตัวกรองความปลอดภัยของ AI")
                else:
                    st.error(f"❌ เกิดข้อผิดพลาดจาก AI: {e}")
    else:
        st.warning("⚠️ กรุณาวางลิงก์ก่อนครับ")
