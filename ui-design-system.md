# 🎨 NovaAgent UI Design System
**เวอร์ชัน:** 1.0 | **วันที่:** 2026-10-27 | **โปรเจกต์:** NovaAgent-Clean  
**ภาษา:** ไทย | **สไตล์:** Dashboard ผู้ดูแลระบบ · ปลอดภัย · เข้าถึงง่าย

---

## 1. ภาพรวมการออกแบบ (Design Brief)

ผลิตภัณฑ์นี้คือ **แดชบอร์ดผู้ดูแลระบบ** สำหรับจัดการข้อมูลและการดำเนินงานของ NovaAgent  
ผู้ใช้หลัก: ผู้ดูแลระบบ (admin) ที่ต้องมองภาพรวม ตรวจสอบรายการ จัดการรายละเอียด และตั้งค่าระบบ

**เป้าหมายหลักของหน้าแรก:** แสดงสถิติสำคัญและกิจกรรมล่าสุดแบบเห็นทันที  
**โทนภาพ:** เข้มข้น แต่มืออาชีพ · สีเข้มเป็นหลัก · โฟกัสที่เนื้อหา ไม่แต่งแต้มเกินจำเป็น

---

## 2. Design Tokens (ตัวแปรดีไซน์)

เก็บเป็น CSS variables ใช้ได้จริงในโปรเจกต์

```css
:root {
  /* ===== สีหลัก (Color Palette) ===== */
  --color-primary:   #0fffd1;   /* Cyan neon – ปุ่มหลัก, โฟกัส, แอ็กชันสำคัญ */
  --color-secondary: #70ffea;   /* Cyan soft – รายละเอียดรอง */
  --color-accent:    #ff0055;   /* Red accent – ลบ, คำเตือน, อันตราย */
  --color-bg:        #0a0a0c;   /* Background หลัก – ดำเข้ม */
  --color-surface:   #141418;   /* Surface – การ์ด, พื้นผิว component */
  --color-surface-2: #1e1e26;   /* Surface รอง – hover state */
  --color-text:      #e8e8f0;   /* ข้อความหลัก */
  --color-text-dim:  #9aa0b0;   /* ข้อความรอง / placeholder */
  --color-border:    #2a2a36;   /* เส้นขอบ component */
  --color-focus:     #0fffd1;   /* Focus ring ตามสี primary */

  /* == personaggi == */
  --color-success: #00ff88;
  --color-warning: #ffcc00;
  --color-error:   #ff0055;

  /* ===== タイพอกราฟี (Typography) ===== */
  --font-sans:      'Inter', system-ui, -apple-system, sans-serif;
  --font-mono:      'JetBrains Mono', 'Fira Code', monospace;

  --text-xs:  0.75rem;   /* 12px – คำอธิบายย่อ */
  --text-sm:  0.875rem;  /* 14px – ข้อความย่อย */
  --text-base: 1rem;     /* 16px – ข้อความหลัก */
  --text-lg:  1.125rem;  /* 18px – หัวเรื่องย่อย */
  --text-xl:  1.25rem;   /* 20px – หัวเรื่อง */
  --text-2xl: 1.5rem;    /* 24px – หัวเรื่องใหญ่ */

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;

  /* ===== ระยะห่าง (Spacing) ===== */
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */

  /* ===== รัศมีมุม = ขอบ = เงา ===== */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  --border-width: 1px;
  --border-style: solid;

  --shadow-sm:  0 1px 2px rgba(0,0,0,0.4);
  --shadow-md:  0 4px 6px rgba(0,0,0,0.4);
  --shadow-lg:  0 10px 15px rgba(0,0,0,0.5);

  /* ===== Breakpoints (Responsive) ===== */
  --bp-mobile:   320px;
  --bp-tablet:   768px;
  --bp-desktop:  1024px;
  --bp-wide:     1440px;

  /* ===== Z-index ===== */
  --z-dropdown: 100;
  --z-modal:    1000;
  --z-toast:    2000;
}
```

หลักการใช้สี:
- **Primary** ใช้เฉพาะปุ่มหลักและลิงก์สำคัญเท่านั้น ไม่ทาให้ทั่วหน้าจอ
- **Surface** แยกพื้นผิวการโต้ตอบ (การ์ด, モดอล) ออกจากพื้นหลัก
- **Border** เส้นขอบบาง ลดความรกทางสายตา
- Contrast ขั้นต่ำ 4.5:1 ตามมาตรฐาน accessibility

---

## 3. Wireframe (โครงสร้างหน้าจอแบบข้อความ)

โครงร่าง 4 หน้าจอหลัก ตามโครงสร้าง Top Nav + Left Sidebar + Content Area (12-column grid)

### โครงร่างโดยรวม (ทุกหน้า)

```
┌─────────────────────────────────────────────────────────────────┐
│  [Logo]  NovaAgent   [Search]  [Bell]  [Avatar]   ← Top Nav    │
├─────────────┬───────────────────────────────────────────────────┤
│             │                                                   │
│  Dashboard  │  ┌─────────────────────────────────────────────┐  │
│  Users      │  │                                             │  │
│  Settings   │  │           Content Area (12-col)             │  │
│  Logs       │  │                                             │  │
│             │  │                                             │  │
│  ← Sidebar  │  │                                             │  │
│             │  └─────────────────────────────────────────────┘  │
└─────────────┴───────────────────────────────────────────────────┘
```

### 3.1 หน้าหลัก (Home / Overview)

```
┌─────────────────────────────────────────────────────────────────┐
│  Overview                                                          │
│  สถิติภาพรวมของระบบ                                            │
├──────────────┬──────────────┬──────────────┬─────────────────────┤
│  ผู้ใช้ทั้งหมด│  การแจ้งเตือน │  ระบบออนไลน์   │  การใช้งาน CPU      │
│  1,234       │  12          │  98%         │  45%                │
├──────────────┴──────────────┴──────────────┴─────────────────────┤
│  กิจกรรมล่าสุด                                                    │
│  ┌─────────────┬──────────────────────────────────────────────┐ │
│  │ เวลา        │  รายละเอียด                                  │ │
│  │ 10:15       │  เข้าสู่ระบบสำเร็จ – admin                    │ │
│  │ 10:08       │  อัปโหลดไฟล์ report.pdf                       │ │
│  │ 09:52       │  เปลี่ยนรหัสผ่าน                               │ │
│  └─────────────┴──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 หน้ารายการ (Data List)

```
┌─────────────────────────────────────────────────────────────────┐
│  รายการข้อมูล                                                    │
│  [ค้นหา..............] [ตัวกรอง▼] [เพิ่มรายการ+]              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┬─────────────┬────────────┬────────────┬──────────┐ │
│  │ #       │ ชื่อ        │ สถานะ     │ วันที่     │ ปฏิบัติการ│ │
│  ├─────────┼─────────────┼────────────┼────────────┼──────────┤ │
│  │ 001     │ สมชาย ใจดี  │ active     │ 27 ต.ค.   │ [ดู][แก้] │ │
│  │ 002     │ สมหญี รักดี │ pending    │ 27 ต.ค.   │ [ดู][แก้] │ │
│  │ 003     │ สมศรี สวยงาม │ inactive   │ 26 ต.ค.   │ [ดู][ลบ] │ │
│  └─────────┴─────────────┴────────────┴────────────┴──────────┘ │
│                                                                   │
│  หน้า 1 จาก 5  [ก่อนหน้า] [ถัดไป]                              │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 หน้ารายละเอียด (Details)

```
┌─────────────────────────────────────────────────────────────────┐
│  รายละเอียด – #001 สมชาย ใจดี                                  │
│  [← กลับไปรายการ]                                               │
├──────────────┬───────────────────────────────────────────────────┤
│  รูปโปรไฟล์ │                                                   │
│  [avatar]    │  ชื่อ: สมชาย ใจดี                               │
│              │  อีเมล: somchai@example.com                      │
│              │  สถานะ: active                                   │
│              │  วันที่สมัคร: 15 ม.ค. 2026                       │
│              │                                                   │
│              │  [แก้ไขข้อมูล] [รีเซตรหัสผ่าน] [ลบบัญชี]        │
│                                                                   │
│  ประวัติการใช้งาน                                               │
│  ┌─────────────┬─────────────────────────────────────────────┐ │
│  │ เวลา        │  กิจกรรม                                    │ │
│  │ 10:15       │  เข้าสู่ระบบ                                │ │
│  └─────────────┴─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 หน้าตั้งค่า (Settings)

```
┌─────────────────────────────────────────────────────────────────┐
│  การตั้งค่า                                                      │
│  ปรับแต่งการทำงานของระบบ                                      │
├──────────────┬───────────────────────────────────────────────────┤
│  โปรไฟล์     │                                                   │
│  ความปลอดภัย │  [ชื่อผู้ใช้]  ___________________              │
│  การแจ้งเตือน │  [อีเมล]      ___________________              │
│  การเชื่อมต่อ │                                                │
│              │  [เปิดใช้งานการแจ้งเตือนทางอีเมล] [v]         │
│              │                                                │
│              │  [บันทึกการเปลี่ยนแปลง]                       │
│             Sidebar                                            │
└──────────────┴───────────────────────────────────────────────────┘
```

---

## 4. คอมโพเนนต์พื้นฐาน (Component Library)

ตัวอย่างในรูปแบบ Markdown + HTML/CSS พร้อมนำไปใช้จริง

### 4.1 ปุ่ม (Button)

```html
<!-- ปุ่มหลัก -->
<button class="btn btn-primary">บันทึกการเปลี่ยนแปลง</button>

<!-- ปุ่มรอง -->
<button class="btn btn-secondary">ยกเลิก</button>

<!-- ปุ่มอันตราย -->
<button class="btn btn-danger">ลบรายการนี้</button>

<!-- ปุ่มตัวอักษร -->
<button class="btn btn-text">ดูรายละเอียด</button>
```

```css
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-tight);
  border: var(--border-width) var(--border-style) transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
  text-decoration: none;
}

.btn:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px var(--color-focus);
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-bg);
}

.btn-primary:hover {
  background: var(--color-secondary);
}

.btn-secondary {
  background: var(--color-surface-2);
  color: var(--color-text);
  border-color: var(--color-border);
}

.btn-secondary:hover {
  background: var(--color-border);
}

.btn-danger {
  background: var(--color-accent);
  color: #fff;
}

.btn-danger:hover {
  opacity: 0.9;
}

.btn-text {
  background: transparent;
  color: var(--color-primary);
  padding: var(--space-2) 0;
}

.btn-text:hover {
  text-decoration: underline;
}
```

### 4.2 อินพุต (Input)

```html
<div class="field">
  <label class="field-label" for="email">อีเมล</label>
  <input type="email" id="email" class="field-input" placeholder="name@example.com">
  <p class="field-hint">ใช้สำหรับเข้าสู่ระบบและรีเซตรหัสผ่าน</p>
</div>
```

```css
.field {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.field-label {
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text);
}

.field-input {
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-sans);
  font-size: var(--text-base);
  background: var(--color-surface);
  border: var(--border-width) var(--border-style) var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text);
}

.field-input:focus {
  border-color: var(--color-primary);
  outline: none;
  box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1);
}

.field-hint {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  margin: 0;
}
```

### 4.3 การ์ด (Card)

```html
<div class="card">
  <h3 class="card-title">สถิติผู้ใช้</h3>
  <p class="card-value">1,234 คน</p>
  <p class="card-sub">เพิ่มขึ้น 12% จากสัปดาห์ที่แล้ว</p>
</div>
```

```css
.card {
  background: var(--color-surface);
  border: var(--border-width) var(--border-style) var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
}

.card-title {
  font-size: var(--text-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin: 0 0 var(--space-2) 0;
}

.card-value {
  font-size: var(--text-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text);
  margin: 0 0 var(--space-2) 0;
}

.card-sub {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  margin: 0;
}
```

### 4.4 ตาราง (Table)

```html
<div class="table-wrap">
  <table class="table">
    <thead>
      <tr>
        <th>#</th>
        <th>ชื่อ</th>
        <th>สถานะ</th>
        <th>วันที่</th>
        <th class="table-actions">ปฏิบัติการ</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>001</td>
        <td>สมชาย ใจดี</td>
        <td><span class="badge badge-success">active</span></td>
        <td>27 ต.ค. 2569</td>
        <td class="table-actions">
          <button class="btn btn-text">ดู</button>
          <button class="btn btn-text">แก้ไข</button>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

```css
.table-wrap {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-sans);
  font-size: var(--text-sm);
}

.table th,
.table td {
  padding: var(--space-4);
  text-align: left;
  border-bottom: var(--border-width) var(--border-style) var(--color-border);
}

.table th {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-dim);
  background: var(--color-surface-2);
}

.table td {
  color: var(--color-text);
}

.table tr:hover {
  background: rgba(255,255,255,0.03);
}

.table-actions {
  white-space: nowrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-xs);
  font-weight: var(--font-weight-bold);
  border-radius: var(--radius-full);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge-success {
  background: rgba(0, 255, 136, 0.15);
  color: var(--color-success);
}
```

---

## 5. แนวทาง Responsive (มือถือ vs แท็บเล็ต vs เดสก์ท็อป)

| อุปกรณ์ | Breakpoint | Layout |
|---------|-----------|--------|
| มือถือ | < 768px | Sidebar ซ่อน (แฮมเบอร์เกอร์เมนู), Top Nav ยังคงอยู่, Content เต็มความกว้าง, ตารางเลื่อนแนวนอนได้ |
| แท็บเล็ต | 768–1023px | Sidebar ย่อเป็นไอคอนเท่านั้น, Content เต็มพื้นที่เหลือ |
| เดสก์ท็อป | ≥ 1024px | แสดงเต็มรูปแบบ (Top Nav + Sidebar + Content) |

```css
/* มือถือ: ซ่อน sidebar เริ่มต้น */
@media (max-width: 767px) {
  .sidebar {
    position: fixed;
    left: -250px;
    top: 0;
    bottom: 0;
    width: 250px;
    transition: left 0.3s ease;
    z-index: var(--z-dropdown);
  }

  .sidebar.open {
    left: 0;
  }

  .content {
    margin-left: 0;
    padding: var(--space-4);
  }

  .top-nav {
    padding: var(--space-3) var(--space-4);
  }
}

/* แท็บเล็ต: ย่อ sidebar */
@media (min-width: 768px) and (max-width: 1023px) {
  .sidebar {
    width: 72px;
    overflow: hidden;
  }

  .sidebar .nav-label {
    display: none;
  }

  .content {
    margin-left: 72px;
  }
}

/* เดสก์ท็อป: แสดงเต็มรูปแบบ */
@media (min-width: 1024px) {
  .sidebar {
    width: 250px;
  }

  .content {
    margin-left: 250px;
    padding: var(--space-6);
  }
}
```

---

## 6. Accessibility (ความเข้าถึง)

- **Contrast:** ข้อความบนพื้นผิวต้องมี contrast อย่างน้อย 4.5:1
- **Focus ring:** มองเห็นชัดเจนเมื่อกด Tab ผ่านปุ่มและฟอร์ม
- **ARIA labels:** ปุ่มและฟอร์มทุกตัวมี aria-label หรือ aria-labelledby
- **Screen reader:** โครงสร้าง HTML ตามความหมาย (semantic HTML: `<nav>`, `<main>`, `<section>`, `<h1>`–`<h6>`)
- **Reduced motion:** เคารพ `prefers-reduced-motion` โดยปิดแอนิเมชันที่ไม่จำเป็น

---

## 7. ขั้นตอนต่อไป (Next Steps)

1. นำ Design Tokens ไปใส่ในไฟล์ CSS / CSS-in-JS ของโปรเจกต์
2. สร้าง React/Vue components จากตัวอย่างคอมโพเนนต์ข้างต้น
3. เชื่อมต่อกับ API จริงในหน้า Data List และ Details
4. ทดสอบบนอุปกรณ์จริงและตรวจสอบ accessibility ด้วย screen reader
5. ปรับแต่งแบรนด์และสีตามตัวตนของ NovaAgent (ถ้าต้องการเปลี่ยนจากธีม neon-cyan)

---

*สร้างโดยระบบออกแบบ UI ของ NovaAgent — พร้อมนำไปพัฒนาต่อได้ทันทีครับบอส ⚔️*