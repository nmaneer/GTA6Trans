# GTA6Trans — ซับไทย realtime สำหรับเล่น GTA 6 บน PS5

PS5 ลงโปรแกรมเสริมเองไม่ได้ เลยใช้ **PC ช่วย**: ส่งภาพจาก PS5 เข้า PC → อ่านซับอังกฤษในเกมด้วย OCR →
แปลเป็นไทยด้วย Claude → แสดงซับไทยทับบนจอ

```
PS5 ──HDMI──> Capture card ──HDMI passthrough──> ทีวี (เล่นตามปกติ, ไม่มีดีเลย์)
                    │
                   USB
                    ▼
                   PC  ── OCR ซับอังกฤษ ── Claude แปล ── ซับไทยทับจอ PC
```

## ต้องมีอะไรบ้าง

| | ทางเลือก A: Capture card (แนะนำ) | ทางเลือก B: PS Remote Play |
|---|---|---|
| อุปกรณ์ | Capture card ที่มี HDMI passthrough (เช่น Elgato HD60 X, AVerMedia Live Gamer, หรือรุ่น USB ราคาถูก) | ไม่ต้องซื้อเพิ่ม |
| เล่นที่ไหน | ทีวี (ภาพไม่ดีเลย์) หรือจอ PC | หน้าต่าง Remote Play บน PC |
| ดีเลย์ภาพ | แทบไม่มี (passthrough) | มีบ้างตามความเร็วเน็ตบ้าน |
| ซับไทยขึ้นที่ไหน | จอ PC (วาง PC/โน้ตบุ๊กไว้ข้างทีวี) หรือเล่นผ่านโปรแกรม capture บนจอ PC | ทับหน้าต่าง Remote Play |

> ⚠️ ถ้าใช้ capture card ต้องปิด HDCP ที่ PS5 ก่อน: **Settings → System → HDMI → ปิด "Enable HDCP"**
> (ไม่ปิดจะได้จอดำ) — ตอนดู Netflix/YouTube บน PS5 ค่อยเปิดกลับ

**ในเกม GTA 6:** เปิดซับไตเติลภาษาอังกฤษ (Settings → Display/Audio → Subtitles: On)
แนะนำปรับขนาดซับให้ใหญ่ขึ้น และเปิดพื้นหลังซับถ้ามี — OCR จะอ่านแม่นขึ้นมาก

PC: Windows 10/11 (macOS/Linux ใช้ได้แต่ overlay อาจไม่โปร่งใสเต็มที่), Python 3.10+

## ติดตั้ง

```bash
git clone https://github.com/nmaneer/GTA6Trans.git
cd GTA6Trans
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy config.example.yaml config.yaml   # macOS/Linux: cp config.example.yaml config.yaml
```

ตั้ง API key ของ Claude (สมัครที่ https://console.anthropic.com):

```bash
setx ANTHROPIC_API_KEY "sk-ant-..."     # Windows (เปิด terminal ใหม่หลังตั้ง)
export ANTHROPIC_API_KEY="sk-ant-..."   # macOS/Linux
```

## ตั้งค่าแหล่งภาพ (`config.yaml`)

- **Remote Play หรือเปิดภาพ capture card ในโปรแกรม (OBS / Elgato 4K Capture Utility) เต็มจอ** → `source: screen`
- **อ่านจาก capture card โดยตรง** (หรือ OBS Virtual Camera) → `source: device` แล้วลอง `device_index: 0, 1, 2…`

## เลือกตำแหน่งซับ (ทำครั้งแรกครั้งเดียว)

เข้าเกมให้มีซับขึ้นจอ แล้วรัน:

```bash
python calibrate.py
```

ลากกรอบครอบบริเวณซับอังกฤษ (เผื่อพื้นที่ 2 บรรทัด) → กด Enter โปรแกรมจะบันทึกลง config และลองอ่านให้ดู

## เริ่มใช้งาน

```bash
python run.py                 # ซับไทยทับจอ (กด Esc ที่หน้าต่างซับเพื่อปิด)
python run.py --no-overlay    # แสดงใน terminal อย่างเดียว (ไว้ทดสอบ)
```

## ให้ซับไทยขึ้นบนทีวี LG (webOS)

PC จะคุยกับทีวีผ่าน Wi-Fi แบบเดียวกับแอปรีโมททีวีในมือถือ แล้วส่งซับไทยเป็น **ป๊อปอัปแจ้งเตือนของทีวี**
ซึ่งขึ้นทับทุกช่อง รวมถึงช่อง HDMI ที่ต่อ PS5 อยู่ — เล่นบนทีวีได้เลย ภาพเกมไม่ดีเลย์

```
PS5 ──HDMI──> capture card ──passthrough──> ทีวี LG  ◄── Wi-Fi: ซับไทย (ป๊อปอัป) ──┐
                   └──USB──> PC (OCR + แปล) ───────────────────────────────────────┘
```

1. ทีวีกับ PC ต้องอยู่เครือข่ายเดียวกัน, เปิดทีวีไว้
2. ที่ทีวี: Settings → General → Devices → External Devices → **TV On With Mobile / LG Connect Apps: เปิด**
3. `pip install aiowebostv` (ต้องใช้ Python 3.12 ขึ้นไป)
4. จับคู่ครั้งแรก: `python pair_lgtv.py <IP ทีวี>` → กด **Accept/ยอมรับ** บนทีวีด้วยรีโมท
5. ใส่ใน `config.yaml`: `output: lgtv` และ `lgtv.host: <IP ทีวี>`
6. `python run.py`

ข้อจำกัด (ทีวีกำหนดเอง ปรับไม่ได้): ป๊อปอัปขึ้นตรงมุมล่างของจอ ขนาดตัวอักษรตายตัว อยู่บนจอราว 3-5 วินาที
และถ้าบทพูดมาถี่มาก ป๊อปอัปจะต่อคิวกัน — ถ้าซับตามไม่ทัน ให้เปลี่ยนไปใช้ `claude-haiku-5-5`

## ปรับแต่ง

| ปัญหา | แก้ที่ |
|---|---|
| ซับไทยขึ้นช้า | `translator.model: claude-haiku-5-5` (เร็วกว่าและถูกกว่ามาก), คง `effort: low` |
| อ่านซับไม่ออก / อ่านผิดเยอะ | รัน `calibrate.py` ใหม่ให้กรอบพอดีซับ, เพิ่มขนาดซับในเกม, ลด `min_confidence` |
| ซับไทยกระพริบ/แปลซ้ำ | เพิ่ม `stable_frames` เป็น 3 |
| อยากเห็นอังกฤษด้วย | `overlay.show_english: true` |
| ฟอนต์ไทยไม่สวย | `overlay.font_family: "Leelawadee UI"` หรือ `"Noto Sans Thai"` |
| บทพูดที่ไม่มีซับ (วิทยุ, คนเดินถนน) | เปิด `audio.enabled: true` + `pip install faster-whisper soundcard` (ฟังเสียงที่ออกลำโพง PC ต้องส่งเสียงเกมเข้า PC) |

## ค่าใช้จ่ายโดยประมาณ

แต่ละบรรทัดซับใช้ราว 300–500 token ขาเข้า + 50–150 ขาออก
เล่น 1 ชั่วโมง (~600 บรรทัด) ด้วย `claude-opus-5-5` ประมาณ $2–3, ด้วย `claude-haiku-5-5` ไม่ถึง $0.10
(ข้อความซ้ำจะใช้แคช ไม่เสียเงินซ้ำ)

## โครงสร้างโค้ด

```
gta6sub/
  capture.py     จับภาพจากจอ หรือ capture card
  ocr.py         ตัดพื้นหลัง + อ่านตัวอักษรด้วย RapidOCR
  stabilizer.py  รอให้ซับนิ่งก่อน และไม่แปลบรรทัดเดิมซ้ำ
  translator.py  แปลด้วย Claude โดยส่งบทพูดก่อนหน้าไปเป็นบริบท
  overlay.py     หน้าต่างซับไทยโปร่งใส อยู่บนสุด คลิกทะลุได้
  audio.py       (ทางเลือก) ถอดเสียงด้วย Whisper
  lgtv.py        ส่งซับขึ้นทีวี LG เป็นป๊อปอัปผ่าน Wi-Fi
  main.py        ต่อทุกส่วนเข้าด้วยกัน
```

ทดสอบ: `pip install pytest && python -m pytest tests`
