# 🗺️ PROJECT MAP — NovaAgent

## 🏠 ไฟล์ระบบหลัก (Root)
- `app.py` -> ตัวรันระบบหลัก
- `config.json` -> ค่าตั้งต้นทั้งหมด (โมเดล, พอร์ต, รหัสผ่าน)
- `AGENT.md` -> ตัวตนและกฎของ Agent
- `PROJECT-MAP.md` -> แผนที่ไฟล์นี้ (ที่เธอกำลังอ่าน)

## 🎨 หน้าตาเว็บ (Templates)
- `channel/web/chat.html` -> **หน้าหลัก!** โหลด CSS/JS ทั้งหมด
- `channel/web/templates/layout/sidebar.html` -> เมนูซ้าย (โลโก้, เมนู)
- `channel/web/templates/layout/login.html` -> หน้า Login
- `channel/web/templates/layout/header.html` -> แถบด้านบน

## 🎨 สไตล์ (CSS) — ไฟล์ที่ต้องแก้บ่อย!
- `channel/web/static/CSJS/css/base.css` -> **ไฟล์หลัก!** (พื้นหลัง, ตัวหนังสือ, โลโก้)
- `channel/web/static/CSJS/css/chat.css` -> บับเบิ้ลแชท, ช่องพิมพ์
- `channel/web/static/CSJS/css/theme-tools.css` -> กล่อง Tool
- `channel/web/static/CSJS/css/markdown.css` -> สไตล์ Markdown

## ⚙️ โค้ดหลังบ้าน (Python)
- `channel/web/core/_common.py` -> ระบบ Auth (รหัสผ่าน, Token)
- `channel/web/core/channel.py` -> ตัวจัดการ Web Channel
- `channel/web/api/chat.py` -> API รับส่งข้อความ
- `channel/web/api/auth.py` -> API Login/Logout
- `agent/chat/service.py` -> ตัวจัดการ Stream ของ AI
- `models/openai_compatible_bot.py` -> ตัวเชื่อมต่อ API
- `models/openai/responses_adapter.py` -> ตัวแปลง `/responses` (เคยแก้ให้ return False)

## 🖼️ รูปภาพ (Assets)
- `channel/web/static/logos/hacker-bg.png` -> ภาพพื้นหลังแฮกเกอร์
- `channel/web/static/logos/hacker-logo.jpg` -> โลโก้แฮกเกอร์
- `channel/web/static/logo.svg` -> โลโก้เก่า (บางจุดยังใช้)

## 🧠 สกิลและ Knowledge
- `skills/` -> โฟลเดอร์เก็บสกิลทั้งหมด (77 ตัว)
- `knowledge/` -> คลังความรู้ (Knowledge Graph)
- `memory/` -> ความจำระยะยาว

## ⚠️ กฎเหล็กสำหรับสลี่
1. **แก้ CSS:** ให้ดูที่ `channel/web/static/CSJS/css/` เท่านั้น (ห้ามแก้ `css/` เก่า)
2. **แก้ HTML:** ให้ดูที่ `channel/web/templates/` หรือ `chat.html`
3. **แก้ Auth:** ดูที่ `channel/web/core/_common.py`
4. **ก่อนแก้ไฟล์สำคัญ:** ให้ Backup ก่อน (`cp file file.bak`)
5. **ถ้าเจอ Error `/responses`:** ตรวจสอบ `api_type` ใน `config.json` ต้องเป็น `"chat"`
6. **ถ้าเจอ Error `/embeddings`:** ปิด `knowledge` ใน `config.json` ชั่วคราว
