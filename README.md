# ReMove: เปลี่ยนความไม่รู้เป็นความถนัด 🎮

**ReMove** เป็น Web Application สำหรับการประเมินความถนัดของมือและการเคลื่อนไหว (Hand Dexterity) ผ่านการวิเคราะห์วิดีโอด้วยเทคโนโลยี Computer Vision และ Machine Learning (MediaPipe) โดยถูกออกแบบให้มีกลิ่นอายของเกมย้อนยุค 8-bit (Retro Game) เพื่อให้ผู้ใช้งานรู้สึกสนุกเหมือนกำลังเล่นเกม

---

## 🌟 ฟีเจอร์หลัก (Key Features)

- **🕹️ 8-bit Retro UI/UX:** อินเทอร์เฟซสไตล์ตู้เกมยุค 90s พร้อมเสียงสังเคราะห์ (Synthesizer Sound Effects)
- **🎥 AI Video Tracking:** ใช้ MediaPipe ในการจับตำแหน่งมือจากวิดีโอแบบเฟรมต่อเฟรม (Frame-by-frame Analysis)
- **🎯 Aimlab Replay:** จำลองการเคลื่อนไหวของมือเทียบกับวิดีโอต้นฉบับเหมือนเกมฝึกยิง (Aimlab) แบบ Real-time
- **📊 Radar Chart & Hitmap:** วิเคราะห์สถิติความเร็ว (Speed), ความแม่นยำ (Accuracy), และคุณภาพ (Quality) พร้อมแผนผังแสดงตำแหน่งที่มีการขยับมือมากที่สุด
- **🧠 Expert System Diagnosis:** สรุปผลความถนัดของมือ เช่น "ถนัดขวาธรรมชาติ", "ถนัดซ้ายธรรมชาติ" หรือตรวจจับภาวะ "Learned Non-Use" (หลีกเลี่ยงการใช้งาน)

---

## 💻 วิธีการติดตั้งและรันโปรแกรมสำหรับอาจารย์/ผู้ใช้งาน

หากต้องการทดสอบรันโปรแกรมด้วยตนเองบนเครื่อง Local Machine สามารถทำได้ดังนี้:

### ข้อกำหนดเบื้องต้น (Prerequisites)
- **Python 3.12** หรือสูงกว่า
- เว็บเบราว์เซอร์ (Chrome / Edge / Firefox)

### ขั้นตอนการรันระบบ
1. โคลน (Clone) โปรเจกต์นี้ลงบนเครื่องของคุณ:
   ```bash
   git clone https://github.com/Iffield/ReMove.git
   cd ReMove
   ```

2. ติดตั้ง Library ที่จำเป็นทั้งหมดด้วยคำสั่ง:
   ```bash
   pip install -r requirements.txt
   ```

3. เริ่มต้นการทำงานของเซิร์ฟเวอร์ (Flask App):
   ```bash
   python app.py
   ```

4. เปิดเว็บบราวเซอร์และเข้าไปที่:
   👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

5. ลองอัปโหลดวิดีโอและดูผลการประเมินได้เลย!

---

## 🛠️ เทคโนโลยีที่ใช้ (Tech Stack)
- **Backend:** Python, Flask
- **Computer Vision:** OpenCV, MediaPipe Tasks API (Vision)
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **UI/Libraries:** NES.css (Retro Styling), Chart.js (Radar Chart), HTML2Canvas (สำหรับเซฟผลลัพธ์)
