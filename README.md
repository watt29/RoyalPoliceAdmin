# Telegram Smart Memo & Auto-Notification System

ระบบจดบันทึกส่วนตัวผ่าน Telegram ที่เชื่อมต่อกับ Google Sheets พร้อมระบบแจ้งเตือนแอดมิน

## 🚀 ฟีเจอร์หลัก

- **📝 จดบันทึก**: บันทึกข้อมูลด้วยคำสั่ง `จด` หรือ `บันทึก`
- **🔍 ค้นหาอัจฉริยะ**: ค้นหาข้อมูลด้วยคีย์เวิร์ดสั้นๆ (รองรับ partial matching)
- **📊 บันทึกประวัติ**: ทุกการใช้งานถูกบันทึกลง Google Sheets
- **🔔 แจ้งเตือนแอดมิน**: แจ้งเตือนเมื่อมีการบันทึกใหม่หรือคำถามที่ตอบไม่ได้

## 📋 วิธีใช้งาน

### คำสั่งพื้นฐาน
- `/start` - เริ่มต้นใช้งานบอท
- `/help` - ดูคำแนะนำ

### การจดบันทึก
```
จด รหัสไวไฟ 1234abcd
บันทึก ที่จอดรถ ชั้น 4
```

### การค้นหา
```
ไวไฟ
ที่จอด
รหัส
```

## 🛠️ การติดตั้งและตั้งค่า

### 1. ติดตั้ง Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. สร้าง Telegram Bot
1. คุยกับ [@BotFather](https://t.me/BotFather) ใน Telegram
2. ส่งคำสั่ง `/newbot`
3. ตั้งชื่อและ username ให้บอท
4. คัดลอก **Bot Token** ที่ได้รับ

### 3. ตั้งค่า Google Cloud & Sheets

#### 3.1 สร้าง Google Cloud Project
1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. สร้างโปรเจกต์ใหม่
3. เปิดใช้งาน **Google Sheets API** และ **Google Drive API**

#### 3.2 สร้าง Service Account
1. ไปที่ `IAM & Admin` > `Service Accounts`
2. คลิก `Create Service Account`
3. ตั้งชื่อ (เช่น `telegram-bot-service`)
4. คลิก `Create and Continue`
5. ข้ามขั้นตอน Grant access
6. คลิก `Done`

#### 3.3 สร้าง JSON Key
1. คลิกที่ Service Account ที่สร้าง
2. ไปที่ `Keys` tab
3. คลิก `Add Key` > `Create new key`
4. เลือก `JSON` แล้วคลิก `Create`
5. ดาวน์โหลดไฟล์ JSON และเปลี่ยนชื่อเป็น `service_account.json`

#### 3.4 ตั้งค่า Google Sheets
1. สร้าง Google Sheets ใหม่ หรือใช้ที่มีอยู่แล้ว
2. แชร์ Sheets กับ Service Account Email (จากไฟล์ JSON)
3. ให้สิทธิ์ `Editor`

**🔧 Quick Setup Tools:**
- `python setup_google_cloud.py` - คำแนะนำการตั้งค่า Google Cloud ทีละขั้น
- `python setup_wizard.py` - ตัวช่วยตั้งค่าอัตโนมัติ
- `python quick_setup.py` - ตั้งค่าเริ่มต้นเร็วๆ

### 4. ตั้งค่า Environment Variables
1. คัดลอก `.env.example` เป็น `.env`
2. แก้ไขค่าในไฟล์ `.env`:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id_here
GOOGLE_SHEET_NAME=Smart_Memo_Database
GOOGLE_SHEET_ID=1xxwyReavlHXmKqEIEdem7zUAdlVS5Kv2D_7S6Rsf2UA
GOOGLE_CREDENTIALS_PATH=service_account.json
```

**หา Admin Chat ID:**
1. ส่งข้อความไปหาบอทของคุณ
2. เข้าไปที่: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. ดูในส่วน `chat.id`

### 5. รันบอท

#### 5.1 ใช้ Setup Wizard (แนะนำ)
```bash
python setup_wizard.py
```
ตัวช่วยนี้จะตรวจสอบทุกอย่างและแนะนำขั้นตอนถัดไป

#### 5.2 รันแบบ Manual
```bash
# ทดสอบการเชื่อมต่อ
python test_connection.py

# วิเคราะห์โครงสร้างชีต
python analyze_sheet.py

# รันบอท
python telegram_memo_bot.py
```

## 📁 โครงสร้างไฟล์

```
telegram-memo-bot/
├── telegram_memo_bot.py    # Main bot application
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore           # Git ignore file
├── service_account.json  # Google credentials (ไม่รวมใน git)
├── README.md            # This file
├── setup_google_cloud.py # Google Cloud setup guide
├── setup_wizard.py      # Complete setup wizard
├── quick_setup.py       # Quick setup script
├── test_connection.py   # Connection testing tool
└── analyze_sheet.py     # Sheet structure analyzer
```

## 📊 โครงสร้างฐานข้อมูล (Google Sheets Structure)

บอทตัวนี้ได้รับการออกแบบมาเพื่อช่วยงานธุรการตำรวจโดยเฉพาะ โดยเชื่อมต่อกับชีตหลัก 4 ชีตดังนี้:

### 1. Contacts (ข้อมูลรายชื่อเจ้าหน้าที่)
- **หน้าที่:** เก็บข้อมูลบุคลากรทั้งหมดเพื่อการติดต่อและประสานงานด่วน
- **คอลัมน์สำคัญ:** ชื่อ-นามสกุล, ตำแหน่ง, เบอร์โทร, สังกัด, เลขบัตรประชาชน, วันเกิด, ธนาคาร, เลขบัญชี
- **การใช้งาน:** ค้นหาเบอร์โทรหรือเลขบัญชีธนาคารเพื่อทำเรื่องงบประมาณหรือเบี้ยเลี้ยง

### 2. Vehicles (ฐานข้อมูลยานพาหนะ)
- **หน้าที่:** ติดตามสถานะและข้อมูลทางเทคนิคของรถยนต์และรถจักรยานยนต์ในสังกัด
- **คอลัมน์สำคัญ:** ทะเบียนรถ, ทะเบียนโล่, ยี่ห้อ, เลขตัวถัง, เลขเครื่องยนต์, หน่วยงานผู้ใช้, สถานภาพ (ใช้การได้/จำหน่าย)
- **การใช้งาน:** ค้นหาเลขโล่หรือทะเบียนเพื่อตรวจสอบสถานะรถในพริบตา

### 3. Orders (ฐานข้อมูลข้อสั่งการ/ภารกิจ)
- **หน้าที่:** บันทึกคำสั่งจากผู้บังคับบัญชาและการมอบหมายภารกิจรายวัน
- **คอลัมน์สำคัญ:** รายละเอียดภารกิจ, ชื่อผู้สั่ง, วันที่ครบกำหนด, สถานะ (Pending/Done), ความเร่งด่วน, หมายเหตุ, วันที่บันทึก
- **การใช้งาน:** สรุปยอดงานค้างหรืองานที่นายสั่งประจำวันผ่านปุ่ม "งานวันนี้"

### 4. Reminders (ระบบแจ้งเตือน)
- **หน้าที่:** จดบันทึกสิ่งที่ต้องทำหรือการนัดหมายที่สำคัญ
- **คอลัมน์สำคัญ:** หัวข้อ, เนื้อหา, เวลาที่นัดหมาย, สถานะ, วันที่สร้าง
- **การใช้งาน:** ป้องกันการลืมนัดหมายประชุมหรือกำหนดส่งรายงานสำคัญ

### 5. Budgets (ข้อมูลการเบิกจ่ายงบประมาณ)
- **หน้าที่:** ติดตามการใช้เงินงบประมาณในแต่ละหมวดหมู่ (OT, ค่าน้ำมัน, ค่าสาธารณูปโภค ฯลฯ)
- **คอลัมน์สำคัญ:** รายการ, งบประมาณ, เบิกจ่ายแล้ว, คงเหลือ, หมายเหตุ
- **การใช้งาน:** พิมพ์ "สรุปงบ" เพื่อดูสถานะการเงินและการใช้จ่ายกี่เปอร์เซ็นต์ของงบทั้งหมด

### 6. ExpenditureStatus (สถานะการเบิกจ่ายรายเดือน)
- **หน้าที่:** ตรวจสอบว่าค่าใช้จ่ายรายเดือน (ค่าน้ำ, ค่าไฟ, ค่าไปรษณีย์) เบิกจ่ายไปถึงเดือนไหนแล้ว
- **คอลัมน์สำคัญ:** รายการ, เบิกถึงเดือน, หมายเหตุ
- **การใช้งาน:** ควบคุมความต่อเนื่องของการจ่ายเงินให้เป็นปัจจุบัน (ป้องกันการค้างชำระ)

---

### ชีตระบบ (System Sheets)
- **Inquiry_Logs:** บันทึกประวัติการพิมพ์ถาม-ตอบ และการค้นหาของยูสเซอร์ทุกคน (เพื่อการตรวจสอบย้อนหลัง)
- **Memory_Base / Config:** เก็บค่าการตั้งค่าเบื้องหลังของระบบ AI และบอท

## 🔧 การปรับแต่ง

### เปลี่ยนคำสั่ง
แก้ไขใน `telegram_memo_bot.py` ที่ฟังก์ชัน `handle_message()`:

```python
# เปลี่ยนคำสั่งจาก "จด" เป็นคำอื่น
if text.startswith(('จด ', 'บันทึก ', 'เก็บ ')):
```

### ปรับจำนวนผลลัพธ์ค้นหา
แก้ไขใน `config.py`:

```python
MAX_SEARCH_RESULTS = 10  # เปลี่ยนจาก 5 เป็น 10
```

## 🚨 การแก้ไขปัญหา

### ปัญหาที่พบบ่อย

1. **Bot Token ไม่ถูกต้อง**
   - ตรวจสอบว่าคัดลอก Token มาครบถ้วน
   - ลองสร้างบอทใหม่

2. **Google Sheets ไม่ได้รับสิทธิ์**
   - ตรวจสอบว่าแชร์ Sheets กับ Service Account Email
   - ตรวจสอบว่าเปิดใช้งาน API ครบถ้วน

3. **Service Account ไม่ทำงาน**
   - ตรวจสอบ path ของไฟล์ `service_account.json`
   - ตรวจสอบว่าไฟล์ไม่เสียหาย

4. **Admin ไม่ได้รับการแจ้งเตือน**
   - ตรวจสอบ Admin Chat ID
   - ตรวจสอบว่าแอดมินอยู่ในกลุ่มที่บอทสามารถส่งข้อความได้

## 📝 บันทึกการเปลี่ยนแปลง

- **v1.0** - เริ่มต้นระบบพื้นฐาน
  - ฟังก์ชันจดบันทึก
  - ฟังก์ชันค้นหาแบบ partial matching
  - ระบบแจ้งเตือนแอดมิน
  - บันทึกประวัติการใช้งาน

## 🤝 การมีส่วนร่วม

สามารถแจ้งปัญหาหรือขอเพิ่มฟีเจอร์ได้ผ่าน GitHub Issues

## 📄 ใบอนุญาต

MIT License
