# 🗺️ SETTINGS-MAP — แผนที่ "จุดตั้งค่าทุกจุด" ของ UI เว็บ NovaAgent

> สแกนเมื่อ 27 ตุลาคม 2026 โดยสลี่ (Astra)
> ไฟล์นี้ตอบคำถาม: **แต่ละตัวปรับได้ที่หน้าไหน → element id อะไร → ผูกกับ key ไหนใน config.json → บันทึกผ่าน endpoint ไหน → ไฟล์/บรรทัดไหน**

---

## 🧱 0. ภาพรวมสถาปัตยกรรม (สำคัญ — อ่านก่อน)

| ส่วน | path จริง | หมายเหตุ |
|---|---|---|
| หน้าเว็บหลัก (single page) | `channel/web/chat.html` | โหลด layout + ทุก view |
| Layout | `templates/layout/{header,sidebar,session-panel,login}.html` | header = ปุ่ม theme/lang/logout |
| หน้าจอแต่ละหน้า (10 หน้า) | `templates/views/*.html` | `chat, agents, config, skills, memory, knowledge, channels, tasks, logs, custom, artifacts` |
| Modal ต่าง ๆ | `templates/modals/*.html` | custom-provider, mcp-editor, menu-editor, task-edit, team-chat ฯลฯ |
| JS logic ของ view | `static/js/views/*.js` | `config.js` = หน้าตั้งค่า |
| CSS ที่ **โหลดจริง** | `/assets/CSJS/css/*` → `static/CSJS/css/` | ⚠️ **ไม่ใช่** `static/css/` |
| Backend config API | `channel/web/api/config.py` | route `/config` (GET/POST) + `/api/external_api` |

### ⚠️ กับดัก 3 ข้อที่ต้องรู้

1. **CSS เสิร์ฟจาก `static/CSJS/css/` ไม่ใช่ `static/css/`**
   - `chat.html` อ้าง `/assets/CSJS/css/*.css` → เสิร์ฟโฟลเดอร์ `static/CSJS/css/`
   - `static/css/` เป็นสำเนาเก่า (มี `custom-theme.css` ที่ไม่ได้ถูกโหลด)
   - แก้สีให้แก้ที่ `static/CSJS/css/` (แล้วค่อย sync กลับ)

2. **`static/css/custom-theme.css` = ไฟล์ตาย** 🔴
   - เป็นธีม Cyberpunk (ชมพู `#ff007f` + ฟ้า `#00f0ff`) ที่เคยสร้างไว้
   - **ไม่มีหน้าไหน link ไฟล์นี้เลย** → ไม่มีผลกับ UI จริง
   - สีจริงมาจาก Tailwind inline config ใน `chat.html` บรรทัด ~32

3. **สีหลัก (brand) จริงอยู่ที่ Tailwind config ใน `chat.html`** (บรรทัด 25-45)
   ```
   primary: 50 #E6F9FF · 100 #C7F0FE · 200 #A5E3FB · 300 #7ADCF9
            400 #00D4FF (ฟ้านีออน) · 500 #00B8E0 · 600 #7B61FF (ม่วง) · 700 #5B41DF
            800 #4A33B5 · 900 #3A268B
   ```
   → **แก้สีแบรนด์ทั้งเว็บ = แก้ที่ `chat.html` บล็อกนี้ที่เดียว**

---

## ⚙️ 1. หน้าตั้งค่า (VIEW: Config) — `#view-config`

- **หน้า:** `templates/views/config.html` (433 บรรทัด)
- **logic:** `static/js/views/config.js` (794 บรรทัด)
- **เข้าถึง:** เมนู sidebar `data-i18n="menu_config"` → route `/settings`
- **มี 2 แท็บ:** `基础配置 (basic)` และ `模型配置 (models)` → สลับด้วย `switchConfigTab('basic'|'models')`

### แท็บ Basic — 5 การ์ด

| การ์ด | ตัวควบคุม | element id | key ใน config.json | หมายเหตุ |
|---|---|---|---|---|
| **模型配置** (ม่วง `fa-microchip`) | 模型厂商 (provider) | `cfg-provider` | `bot_type` / `use_linkai` | dropdown |
| | 模型 (model) | `cfg-model-select` + `cfg-model-custom` | `model` | มี "__custom__" |
| | API Key | `cfg-api-key` | ตาม provider (เช่น `open_ai_api_key`) | masked |
| | API Base | `cfg-api-base` | ตาม provider (เช่น `open_ai_api_base`) | |
| **Agent 配置** (เขียว `fa-robot`) | **最大上下文 Token** | `cfg-max-tokens` | `agent_max_context_tokens` | 0–10,000,000 step 1000 |
| | **最大记忆轮次** | `cfg-max-turns` | `agent_max_context_turns` | 1–1000 |
| | **最大执行步数** ← "รอบ" | `cfg-max-steps` | `agent_max_steps` | 1–1000 |
| | Deep Thinking | `cfg-enable-thinking` | `enable_thinking` | toggle |
| | 思考强度 | `cfg-reasoning-effort` | `reasoning_effort_by_model` | โผล่เมื่อเปิด thinking |
| | Sub Agents | `cfg-subagent` | `subagent.enabled` (nested) | toggle |
| | Self-Evolution | `cfg-self-evolution` | `self_evolution_enabled` | toggle |
| **安全设置** (เหลือง `fa-lock`) | 默认权限 | `cfg-permission` | `agent_permission_mode` | dropdown |
| | 访问密码 | `cfg-password` | `web_password` | masked |
| **对话 API** (violet `fa-plug`) | เปิด/ปิด | `cfg-api-enabled` | `external_api_enabled` | → `/api/external_api` |
| | API Key | `cfg-api-token` | `external_api_token` | regenerate ได้ |
| **系统** (sky `fa-sliders-h`) | 语言 | `cfg-lang-select` | `cow_lang` | zh/zh-Hant/en/th |
| | Task Notifications | `cfg-task-notify` | (browser) | |
| | Notification Sound | `cfg-task-notify-sound` | (browser) | |

**ปุ่ม Save แยกกัน 3 ปุ่ม:** `cfg-model-save` (saveModelConfig) · `cfg-agent-save` (saveAgentConfig) · `cfg-password-save` (savePasswordConfig)

### แท็บ Models (advanced)
- container: `#config-panel-models` → `#models-content`
- โหลดด้วย `loadModelsView()` → ดูรายละเอียดที่ `static/js/views/models.js` + `api/models.py`
- จัดการ custom provider, capability cards (chat/vision/asr/tts/embedding/image/search)

### 🔌 API Dashboard (ท้ายหน้า config.html บรรทัด 416-432)
- ลิงก์ไป `/assets/api-dashboard.html` (เปิดแท็บใหม่) — ไม่ใช่ settings จริง

---

## 🔌 2. Backend — endpoint `/config`

- **ไฟล์:** `channel/web/api/config.py` · **route:** `web_channel.py:132` → `ConfigHandler`
- **GET** `/config` → คืน config ปัจจุบัน (API key ถูก mask)
- **POST** `/config` body: `{ "updates": { key: value } }`

**`EDITABLE_KEYS`** (allowlist — key นอกนี้ถูกเมิน, config.py:37-49):
```
cow_lang, model, bot_type, use_linkai,
open_ai_api_base, deepseek_api_base, qianfan_api_base, claude_api_base, gemini_api_base,
zhipu_ai_api_base, moonshot_base_url, ark_base_url, custom_api_base, mimo_api_base,
open_ai_api_key, deepseek_api_key, qianfan_api_key, claude_api_key, gemini_api_key,
zhipu_ai_api_key, dashscope_api_key, moonshot_api_key,
ark_api_key, minimax_api_key, linkai_api_key, custom_api_key, mimo_api_key,
custom_providers,
agent_max_context_tokens, agent_max_context_turns, agent_max_steps,
enable_thinking, reasoning_effort, reasoning_effort_by_model, self_evolution_enabled,
web_password, agent_permission_mode
```

**ผลข้างเคียงตอน POST (สำคัญ):**
- แก้ `agent_max_context_tokens` / `agent_max_steps` → เรียก `agent_bridge.apply_runtime_limits()` **มีผลทันทีไม่ต้องรีสตาร์ท** (config.py:284-291)
- แก้ `bot_type` / `use_linkai` / `model` → `Bridge().reset_bot()` (config.py:272-279)
- แก้ `cow_lang` → `i18n.resolve_language()` มีผลทันที (config.py:242-247)
- `subagent_enabled` → เขียนแบบ **nested** ลง `subagent.enabled` (config.py:53-55)
- `reasoning_effort_by_model` → **merge** ไม่ใช่ replace (config.py:203-213)
- `web_password` ล้างค่า + host = 0.0.0.0 → คืน `warning` (config.py:249-267)

**ไฟล์ที่เขียน:** `~/NovaAgent-Clean/config.json` ผ่าน `_write_config_file_for_write()`

---

## 🎨 3. หน้าอื่น ๆ ทั้งหมด (สีประจำหน้า)

| # | หน้า | route | template | สี accent หลัก | CSS |
|---|---|---|---|---|---|
| 1 | **对话 Chat** | `/` | `views/chat.html` | amber / blue / emerald / rose | `chat.css` + `sessions.css` + `call.css` |
| 2 | **Agents** | `/agents` | `views/agents.html` | primary (ฟ้า-ม่วง) + red | `agents.css` |
| 3 | **配置 Config** | `/settings` | `views/config.html` | amber/lock, emerald/robot, violet/api, sky/system | `components.css` |
| 4 | **Skills** | `/skills` | `views/skills.html` | primary | `components.css` |
| 5 | **Memory** | `/memory` | `views/memory.html` | **purple** | `components.css` |
| 6 | **Knowledge** | `/knowledge` | `views/knowledge.html` | emerald + primary | `knowledge.css` |
| 7 | **Channels** | `/channels` | `views/channels.html` | primary | `components.css` |
| 8 | **Tasks** | `/scheduler` | `views/tasks.html` | primary + rose | `components.css` |
| 9 | **Logs** | `/logs` | `views/logs.html` | amber/emerald/red (status) | `components.css` |
| 10 | **Custom (แก้เมนู)** | `/custom/<id>` | `views/custom.html` | ตามเมนูที่เพิ่ม | `menu.css` |
| + | **Artifacts** | `/artifacts` | `views/artifacts.html` | — | `artifacts.css` |

**ธีมกลาง:**
- สลับ light/dark: ปุ่ม `#theme-icon` ใน header → `theme.js` → เก็บที่ `localStorage['cow_theme']`
- โหมด dark = `document.documentElement.classList.add('dark')`
- CSS ที่โหลด (ลำดับสำคัญมาก): `base → sessions → components → markdown → chat → workspace → knowledge → agents → artifacts → menu → call → bolt-style-chat → theme-thinking → theme-tools`

---

## 🎯 4. สรุป — จะแก้ "สี" ต้องทำยังไง

| อยากเปลี่ยน | แก้ที่ | ไฟล์ |
|---|---|---|
| สีแบรนด์ (ปุ่ม/ลิงก์/accent หลัก) ทั้งเว็บ | Tailwind `colors.primary` | `chat.html` บรรทัด 32-37 |
| สีพื้นหลัง/ตัวอักษร dark mode | CSS variables | `static/CSJS/css/base.css` |
| ธีมเฉพาะหน้า (chat/memory ฯลฯ) | CSS ของหน้านั้น | `static/CSJS/css/<page>.css` |
| สีปุ่มโทร/ส่งข้อความ | `.call-fab, .composer-send-btn` | (ถ้าอยากให้มีผลจริง → ย้ายเข้า `CSJS/css/`) |
| ⚠️ `static/css/custom-theme.css` | **ไม่มีผล** — ต้อง copy เนื้อหาไป `CSJS/` + link ใน `chat.html` ก่อน | |

---

## 🧪 5. หมายเหตุการตรวจสอบ

- ไม่มีการแก้ไฟล์ใด ๆ ในการสแกนรอบนี้ (read-only) — เอกสารนี้สร้างใหม่ไฟล์เดียว
- ทุก element id / key ยืนยันจากโค้ดจริง ไม่ได้เดา
- ถ้า UI เปลี่ยนในอนาคต ให้เช็กซ้ำที่ `templates/views/config.html` + `static/js/views/config.js` เป็นหลัก
