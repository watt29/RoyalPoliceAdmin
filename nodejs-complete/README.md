# Smart Police Report Bot v3.0 - 100% Node.js

🚔 **ระบบรายงานตำรวจอัจฉริยะ - เทคโนโลยี Node.js เต็มรูปแบบ**

[![Node.js](https://img.shields.io/badge/Node.js-18%2B-green)](https://nodejs.org)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot%20API-blue)](https://core.telegram.org/bots)
[![Google Sheets](https://img.shields.io/badge/Google-Sheets%20API-red)](https://developers.google.com/sheets)

## ✨ คุณสมบัติ

### 🤖 AI ขั้นสูง
- วิเคราะห์ข้อความภาษาไทยอัตโนมัติ
- ตรวจจับความตั้งใจ (Intent Detection)
- แยกแยะข้อมูลอัจฉริยะ (Entity Extraction)
- บันทึกข้อมูลอัตโนมัติ

### 📊 จัดการข้อมูล
- **บุคลากร**: ชื่อ, ตำแหน่ง, เบอร์โทร, หน่วยงาน
- **ยานพาหนะ**: หมายเลขโล่, ทะเบียน, ยี่ห้อ, สถานะ
- **คำสั่ง**: รายละเอียด, ผู้สั่ง, กำหนดเวลา, ความเร่งด่วน
- **ไฟล์**: สร้าง, แก้ไข, ลบ, อ่าน, สำรองข้อมูล

### 🔍 ค้นหาอัจฉริยะ
- ค้นหาข้ามทุกประเภทข้อมูล
- รองรับภาษาไทย-อังกฤษ
- ค้นหาแบบ Fuzzy Matching
- ผลลัพธ์แสดงทันทีแบบ Real-time

### 📈 รายงานและวิเคราะห์
- รายงานสรุปประจำวัน
- สถิติเชิงลึก
- ส่งออกข้อมูล CSV
- การแจ้งเตือนอัตโนมัติ

## 🚀 การติดตั้ง

### 1. ข้อกำหนดของระบบ

```bash
Node.js >= 18.0.0
NPM >= 8.0.0
Google Cloud Account
Telegram Bot Token
```

### 2. ติดตั้งโครงการ

```bash
# Clone or download โปรเจ็กต์
cd nodejs-complete

# ติดตั้ง dependencies
npm install

# ตั้งค่าไฟล์สภาพแวดล้อม
cp .env.example .env
```

### 3. การตั้งค่า

#### 3.1 สร้าง Telegram Bot

1. ติดต่อ [@BotFather](https://t.me/BotFather) ใน Telegram
2. ส่งคำสั่ง `/newbot`
3. ตั้งชื่อบอทและ username
4. คัดลอก **Bot Token** ใส่ในไฟล์ `.env`

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

#### 3.2 ตั้งค่า Google Sheets API

1. เข้า [Google Cloud Console](https://console.cloud.google.com/)
2. สร้างโปรเจ็กต์ใหม่
3. เปิด Google Sheets API
4. สร้าง Service Account
5. ดาวน์โหลด JSON key file
6. เปลี่ยนชื่อเป็น `service_account.json`
7. วางไฟล์ในโฟลเดอร์โปรเจ็กต์

#### 3.3 สร้าง Google Sheet

1. สร้าง Google Sheet ใหม่
2. ตั้งชื่อ "Smart_Memo_Database"
3. สร้าง Sheet ย่อย:
   - `Contacts`
   - `Vehicles`
   - `Orders`
4. แชร์ Sheet ให้ Service Account (client_email)
5. คัดลอก Sheet ID ใส่ในไฟล์ `.env`

```env
GOOGLE_SHEET_ID=your_sheet_id_here
```

### 4. เริ่มใช้งาน

#### Windows:
```cmd
start.bat
```

#### Linux/Mac:
```bash
npm start
```

#### Development Mode:
```bash
npm run dev
```

## 💻 การใช้งาน

### คำสั่งพื้นฐาน

```
/start          - เริ่มใช้งาน
/help           - คู่มือการใช้งาน
/ค้นหา [คำค้น]   - ค้นหาข้อมูล
/ไฟล์           - แสดงรายชื่อไฟล์
```

### บันทึกข้อมูลอัตโนมัติ

ส่งข้อความธรรมดา ระบบจะวิเคราะห์และบันทึกอัตโนมัติ:

```
นาย สมชาย ใจดี พ.ต.ต. โทร 081-234-5678 สภ.บางแค
→ บันทึกเป็นข้อมูลบุคลากร

โล่ 1234 ทะเบียน กข-5678 Toyota สถานะ ใช้งานได้
→ บันทึกเป็นข้อมูลยานพาหนะ

คำสั่ง ให้ตรวจตราพื้นที่ เร่งด่วน กำหนด 18:00
→ บันทึกเป็นคำสั่ง/ภารกิจ
```

### จัดการไฟล์

```
/สร้าง memo.txt     - สร้างไฟล์ใหม่
/แก้ไข memo.txt     - แก้ไขไฟล์
/ลบ memo.txt        - ลบไฟล์
/อ่าน memo.txt      - อ่านไฟล์
```

### ส่งออกข้อมูล

```
/export contacts csv    - ส่งออกข้อมูลบุคลากร
/export vehicles csv    - ส่งออกข้อมูลยานพาหนะ
/export orders csv      - ส่งออกข้อมูลคำสั่ง
```

### รายงาน

```
/รายงาน สรุป         - รายงานสรุป
/รายงาน สถิติ        - รายงานสถิติ
/รายงาน รายวัน       - รายงานประจำวัน
```

## 🔧 การกำหนดค่า

### ไฟล์ .env

```env
# Telegram Settings
TELEGRAM_BOT_TOKEN=your_bot_token
ADMIN_CHAT_ID=your_admin_chat_id

# Google Sheets Settings
GOOGLE_SHEET_NAME=Smart_Memo_Database
GOOGLE_SHEET_ID=your_sheet_id
GOOGLE_CREDENTIALS_PATH=service_account.json

# Server Settings
NODE_ENV=production
PORT=3000

# Security & Limits
MAX_FILE_SIZE=52428800
MAX_FILES_PER_USER=100
RATE_LIMIT_MAX_REQUESTS=100
```

## 📁 โครงสร้างโปรเจ็กต์

```
nodejs-complete/
├── index.js                 # แอปหลัก
├── package.json             # การตั้งค่า NPM
├── .env                     # ตัวแปรสภาพแวดล้อม
├── service_account.json     # Google Service Account
├── start.bat                # สคริปต์เริ่มงาน Windows
├── README.md                # เอกสารนี้
├── services/
│   ├── GoogleSheetsService.js   # บริการ Google Sheets
│   ├── AIProcessor.js           # ประมวลผล AI
│   └── DataProcessor.js         # ประมวลผลข้อมูล
├── handlers/
│   ├── ContactHandler.js        # จัดการข้อมูลบุคลากร
│   ├── VehicleHandler.js        # จัดการข้อมูลยานพาหนะ
│   ├── OrderHandler.js          # จัดการคำสั่ง
│   └── FileHandler.js           # จัดการไฟล์
├── logs/                    # ไฟล์ Log
├── user-files/             # ไฟล์ผู้ใช้
├── temp/                   # ไฟล์ชั่วคราว
└── exports/               # ไฟล์ส่งออก
```

## 🛡️ ความปลอดภัย

### การจำกัดการเข้าถึง
- Rate Limiting (100 requests/15 นาที)
- File Type Validation
- File Size Limits (50MB)
- Path Traversal Protection

### การป้องกันข้อมูล
- Environment Variables
- Service Account Authentication
- Encrypted Communications (HTTPS/TLS)
- Input Sanitization

## ⚡ ประสิทธิภาพ

### การจัดเก็บข้อมูล
- Memory Caching (5 นาทีต่อ session)
- File System Optimization
- Database Connection Pooling

### การประมวลผล
- Asynchronous Operations
- Stream Processing
- Batch Operations
- Background Jobs

## 🚀 การ Deploy

### Render.com (แนะนำ)

1. สร้าก repository ใน GitHub
2. เชื่อมต่อ Render.com กับ GitHub
3. เลือก Web Service
4. ตั้งค่า Environment Variables
5. Deploy อัตโนมัติ

### Railway.app

```bash
# ติดตั้ง Railway CLI
npm install -g @railway/cli

# Login และ Deploy
railway login
railway init
railway up
```

### VPS/Server

```bash
# ติดตั้ง PM2
npm install -g pm2

# เริ่มด้วย PM2
pm2 start index.js --name "smart-police-bot"
pm2 save
pm2 startup
```

## 📊 การติดตาม

### Health Check
```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "version": "3.0.0",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "uptime": 3600
}
```

### Logs
- `logs/error.log` - ข้อผิดพลาด
- `logs/combined.log` - Log ทั้งหมด
- Console Output - Log แบบ Real-time

## 🤝 การสนับสนุน

### 📞 ติดต่อ
- **Email**: support@smartpolicebot.com
- **Telegram**: @SmartPoliceBotSupport
- **GitHub Issues**: [รายงานปัญหา](https://github.com/your-repo/issues)

### 📚 เอกสารเพิ่มเติม
- [API Reference](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Contributing Guide](docs/CONTRIBUTING.md)

## 📄 License

MIT License - ดูไฟล์ `LICENSE` สำหรับรายละเอียด

---

## 🎉 พร้อมใช้งาน!

```bash
# เริ่มใช้งานได้เลย
npm start

# หรือบน Windows
start.bat
```

🚔 **Smart Police Report Bot v3.0** - ระบบรายงานตำรวจอัจฉริยะ 100% Node.js
⚡ **Performance สูงสุด | ความปลอดภัยสูงสุด | ใช้งานง่ายสุด**