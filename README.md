# NovaAgent — Brandable AI Agent

> **คิดเป็นระบบ สร้างได้จริง และตรวจสอบได้**
>
> NovaAgent คือแพลตฟอร์ม AI Agent แบบปรับแต่งแบรนด์ได้ สำหรับคนที่ต้องการรวมการสนทนา เครื่องมือ ความรู้ หน่วยความจำ และทีมเอเจนต์ไว้ในบ้านหลังเดียว

สร้างโดย **ภาณุพันธ์ (Panupan)** · แบรนด์ **boss.slilelo**

[GitHub](https://github.com/appleid7899067-netizen/NovaAgent-Brandable)

---

## ทำไม NovaAgent ถึงแตกต่าง

NovaAgent ไม่ได้เป็นเพียงหน้าต่างแชทที่เรียกโมเดลแล้วจบ แต่เป็น **ชั้นควบคุมสำหรับ AI Agent** ที่เชื่อมความสามารถหลายส่วนเข้าด้วยกัน:

- 🧠 **Multi-provider routing** — เชื่อมต่อและสลับผู้ให้บริการ LLM ตามการตั้งค่า
- 🧩 **Skill-based tools** — ขยายความสามารถด้วยชุดทักษะสำหรับงานโค้ด เว็บ UI งานสื่อ และระบบอัตโนมัติ
- 🧠 **Layered memory** — แยกบริบทระหว่างการสนทนา ความจำรายวัน และความจำหลัก
- 📚 **Knowledge workspace** — จัดเก็บความรู้เป็นหมวดหมู่และค้นคืนกลับมาใช้ได้
- 👥 **Multi-agent collaboration** — แบ่งบทบาทระหว่างผู้ประสานงาน ตัวสร้าง และผู้ตรวจสอบ
- 🔍 **Expert review API** — แยก endpoint สำหรับตรวจโค้ดและงานเชิงผู้เชี่ยวชาญ
- ✅ **Tasks API** — จัดการงานด้วย persistence ที่ตรวจสอบได้
- 🎙️ **Voice interaction** — รองรับเสียงผ่าน server TTS และ browser speech recognition เมื่ออุปกรณ์รองรับ
- 🎨 **Brandable web UI** — ปรับชื่อ สี ธีม และประสบการณ์หน้าแชทให้เป็นตัวเอง

จุดแข็งของระบบจึงไม่ได้อยู่ที่คำโฆษณาว่าโมเดล “ฉลาดที่สุด” แต่อยู่ที่ **สถาปัตยกรรมที่ทำให้ AI ใช้เครื่องมือ มีความจำ ทำงานเป็นทีม และตรวจสอบผลลัพธ์ได้**

---

## สถานะความสามารถที่ควรรู้

NovaAgent อยู่ในช่วงพัฒนาและทดลองใช้งานจริง ฟีเจอร์หลักมีโค้ดรองรับแล้ว แต่ความพร้อมใช้งานขึ้นกับ provider, API key, browser และการตั้งค่าของเครื่อง:

- โหมดเสียงแบบ browser real-time ใช้ได้เมื่อ browser รองรับ Web Speech API
- อุปกรณ์หรือ browser ที่ไม่รองรับจะใช้เส้นทางอัปโหลดเสียงแทน ซึ่งไม่ใช่ real-time แบบเดียวกัน
- endpoint และ provider บางตัวต้องเปิดใช้งานแยกและมี credentials ของผู้ใช้
- ก่อนนำขึ้น production ควรเพิ่ม integration test และทดสอบบน browser/device เป้าหมาย

นี่คือระบบที่ **ขยายต่อได้จริงและตรวจสอบตามหลักฐานได้** ไม่ใช่การรับประกันว่าทุกฟีเจอร์ทำงานเหมือนกันบนทุกอุปกรณ์

---

## เริ่มต้นใช้งาน

### 1. ติดตั้ง dependencies

```bash
pip install -r requirements.txt
```

### 2. ตั้งค่า secrets ในเครื่อง

สร้าง `secrets.local.json` (ไฟล์นี้ถูก ignore โดย Git):

```json
{
  "openrouter": ["ใส่คีย์ของคุณที่นี่"],
  "groq": ["ใส่คีย์ของคุณที่นี่"]
}
```

อย่า commit API key, token หรือ credential ใด ๆ ขึ้น repository

### 3. รัน NovaAgent

```bash
BRAND_NAME=boss.slilelo python app.py
```

### 4. เปิดหน้าเว็บ

ไปที่ <http://localhost:9999>

---

## API และบริการที่เกี่ยวข้อง

| บริการ | Port | เส้นทางหลัก | หน้าที่ |
|:--|:--:|:--|:--|
| NovaAgent Core | 9999 | `/` | หน้าแชทหลัก |
| Gold API | 8000 | `/api/gold` | ข้อมูลราคาทองคำ |
| Expert API | 8001 | `/api/expert/review` | ตรวจโค้ด |
| Tasks API | 8002 | `/tasks` | จัดการงาน |
| Puter Bridge | 8741 | `/v1/models` | LLM gateway |
| Ollama | 11434 | `/api/tags` | โมเดล local เมื่อเปิดใช้งาน |

บริการที่ไม่ได้เปิดใช้งานจะไม่พร้อมใช้งานโดยอัตโนมัติ เพียงเพราะมีรายการอยู่ในเอกสาร

---

## โครงสร้างโดยย่อ

```text
NovaAgent-Brandable/
├── agent/              # แกนการทำงานของ Agent
├── channel/            # Web UI และช่องทางการเชื่อมต่อ
├── expert_system/      # Expert API
├── knowledge/          # พื้นที่จัดเก็บความรู้
├── models/             # การเชื่อมต่อ LLM
├── skills/             # ชุดทักษะที่ขยายได้
├── tasks_api/          # Tasks API
├── app.py              # จุดเริ่มต้นระบบ
├── config.json         # config เฉพาะเครื่อง (gitignored)
└── secrets.local.json  # API keys เฉพาะเครื่อง (gitignored)
```

---

## ตรวจสอบก่อนส่งงาน

ก่อน commit การเปลี่ยนแปลงที่เกี่ยวกับโค้ด ให้ตรวจอย่างน้อย:

```bash
git diff --check
python -m compileall -q voice channel/web/api channel/web/core config.py
node --check channel/web/static/CSJS/js/chat/call.js
node --check channel/web/static/CSJS/js/chat/render.js
```

การตรวจเหล่านี้ช่วยจับ syntax และ formatting error แต่ไม่แทนการทดสอบ integration หรือการทดสอบผ่าน browser จริง

---

## การพัฒนาอย่างปลอดภัย

ใช้ branch ทดลองสำหรับงานใหม่ แล้วตรวจสอบก่อนรวมเข้า `main`:

```text
experiment/*  →  review + tests  →  main  →  push backup
```

`main` เป็นจุดย้อนกลับของโปรเจกต์ ส่วนไฟล์เฉพาะกิจหรือสคริปต์ที่เขียนทับไฟล์โดยตรงไม่ควรถูก commit จนกว่าจะผ่านการ review

---

## License และเครดิต

MIT License — ดูรายละเอียดใน `LICENSE`

สร้างต่อยอดจาก [CowAgent](https://github.com/zhayujie/CowAgent) และใช้โครงการโอเพนซอร์สอย่าง FastAPI, Tailwind CSS และ provider integrations ตามที่ระบุใน dependencies

<div align="center">

**สร้างด้วย 💜 โดย ภาณุพันธ์ (Panupan)**

</div>
