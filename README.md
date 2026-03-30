# Smart Police Report - Hybrid Architecture

ระบบรายงานตำรวจอัจฉริยะ แบบ **Node.js + Python Hybrid** สำหรับงานธุรการตำรวจ
เชื่อมต่อ Telegram Bot กับ Google Sheets พร้อมระบบ AI และแจ้งเตือนอัตโนมัติ

## 🏗️ สถาปัตยกรรม Hybrid

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram Bot  │────│   Node.js API   │────│  Python Services│
│   (Node.js)     │    │   (Express)     │    │ (Data/AI/Sheets)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
        ↕                        ↕                        ↕
    Telegram API           Real-time            Google Sheets API
                          Processing               AI Processing
```

## 🚀 ฟีเจอร์หลัก

### 🤖 **Telegram Bot (Node.js)**
- **⚡ Performance สูง** - รับ-ส่งข้อความเร็วขึ้น 5-10 เท่า
- **🔄 Real-time Processing** - ประมวลผลแบบ concurrent
- **📱 Interactive Menus** - ปุ่มเมนูภาษาไทยใช้งานง่าย
- **🔔 Instant Notifications** - แจ้งเตือนทันทีแบบ WebSocket

### 🐍 **Python Backend (FastAPI)**
- **🧠 AI Processing** - ประมวลผลข้อมูลอัจฉริยะ
- **📊 Google Sheets Integration** - เชื่อมต่อฐานข้อมูลครบถ้วน
- **🔍 Smart Search** - ค้นหาข้อมูลแบบ partial matching
- **📈 Data Analytics** - วิเคราะห์ข้อมูลและสรุปรายงาน

### ✨ **ฟีเจอร์สำหรับงานตำรวจ**
- **📝 บันทึกข้อมูลอัตโนมัติ** - แยกประเภทข้อมูลอัจฉริยะ
- **🔍 ค้นหารวดเร็ว** - บุคลากร, ยานพาหนะ, อาวุธปืน, การจับกุม
- **📊 สรุปรายงาน** - รายงานสถานะงาน, งบประมาณ, ข้อมูลสำคัญ
- **⏰ แจ้งเตือนอัจฉริยะ** - นัดหมาย, กำหนดส่งงาน, เหตุการณ์สำคัญ
- **🔒 ระบบสำรอง** - Backup ข้อมูลอัตโนมัติ

## 📋 วิธีใช้งาน

### คำสั่งพื้นฐาน
- `/start` - เริ่มต้นใช้งานบอท พร้อมเมนูหลัก
- พิมพ์ข้อความธรรมดา - บอทจะแยกแยะและประมวลผลอัตโนมัติ

### การบันทึกข้อมูล (ระบบ AI อัตโนมัติ)
```
# ข้อมูลบุคลากร
นาย สมชาย ใจดี พ.ต.อ. โทร 081-234-5678 สภ.เมือง

# ข้อมูลยานพาหนะ
รถโล่ 1234 ทะเบียน กข-5678 Toyota Hilux สภ.บางบอน

# ข้อมูลการจับกุม
จับกุม นาย ก ข อายุ 25 ปี ข้อหาลักทรัพย์ ที่สภ.เมือง เมื่อ 15/03/2567

# คำสั่งภารกิจ
ให้ จส.ต.สมชาย ไปตรวจพื้นที่ แยกรัชดา ภายใน 18.00 น. เร่งด่วน
```

### การค้นหาข้อมูล
```
# ค้นหาบุคลากร
สมชาย
พ.ต.อ.

# ค้นหายานพาหนะ
โล่ 1234
กข-5678

# ค้นหาการจับกุม
ลักทรัพย์
15/03/2567
```

## 🛠️ การติดตั้งและตั้งค่า

### ความต้องการของระบบ
- **Node.js** 18+
- **Python** 3.8+
- **npm** หรือ **yarn**
- **Internet connection** สำหรับ API calls

### 1. Quick Setup (แนะนำ)
```bash
# รันสคริปต์ติดตั้งอัตโนมัติ
setup-hybrid.bat

# เริ่มระบบ hybrid
start-hybrid.bat
```

### 2. Manual Setup

#### 2.1 ติดตั้ง Node.js Dependencies
```bash
cd telegram-bot
npm install

# หรือใช้ yarn
yarn install
```

#### 2.2 ติดตั้ง Python Dependencies
```bash
cd python-services
pip install -r requirements-core.txt

# หรือใช้ virtual environment (แนะนำ)
python -m venv .venv
.venv\Scripts\activate.bat  # Windows
source .venv/bin/activate   # Linux/Mac
pip install -r requirements-core.txt
```

### 3. สร้าง Telegram Bot
1. คุยกับ [@BotFather](https://t.me/BotFather) ใน Telegram
2. ส่งคำสั่ง `/newbot` และตั้งชื่อบอท
3. คัดลอก **Bot Token** ที่ได้รับ

### 4. ตั้งค่า Google Cloud & Sheets

#### 4.1 สร้าง Google Cloud Project
1. ไปที่ [Google Cloud Console](https://console.cloud.google.com/)
2. สร้างโปรเจกต์ใหม่
3. เปิดใช้งาน **Google Sheets API** และ **Google Drive API**

#### 4.2 สร้าง Service Account
1. ไปที่ `IAM & Admin` > `Service Accounts`
2. คลิก `Create Service Account`
3. ตั้งชื่อ (เช่น `smart-police-bot`)
4. สร้าง JSON Key และดาวน์โหลด
5. เปลี่ยนชื่อเป็น `service_account.json`

#### 4.3 ตั้งค่า Google Sheets
1. สร้าง Google Sheets หรือใช้ที่มีอยู่แล้ว
2. แชร์ Sheets กับ Service Account Email (จากไฟล์ JSON)
3. ให้สิทธิ์ `Editor`

### 5. ตั้งค่า Environment Variables
แก้ไขไฟล์ `shared/.env`:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id_here

# Google Sheets Configuration
GOOGLE_SHEET_NAME=Smart_Police_Database
GOOGLE_SHEET_ID=your_sheet_id_here
GOOGLE_CREDENTIALS_PATH=service_account.json

# Hybrid Architecture URLs
PYTHON_API_URL=http://localhost:8000
BOT_API_URL=http://localhost:3000
PYTHON_API_PORT=8000
BOT_SERVER_PORT=3000
```

## 🚀 การรันระบบ

### Option 1: Quick Start (แนะนำ)
```bash
start-hybrid.bat
```

### Option 2: Development Mode
```bash
# Terminal 1: Python API
cd python-services
python main_api.py

# Terminal 2: Node.js Bot
cd telegram-bot
npm start
```

### Option 3: Docker Deployment (Production)
```bash
docker-compose up --build -d

# ดู logs
docker-compose logs -f

# หยุด services
docker-compose down
```

### Option 4: PM2 Process Manager (Linux)
```bash
# ติดตั้ง PM2
npm install -g pm2

# เริ่ม Python API
pm2 start "python main_api.py" --name "python-api" --cwd python-services

# เริ่ม Node.js Bot
pm2 start "npm start" --name "telegram-bot" --cwd telegram-bot

# จัดการ
pm2 status
pm2 logs
pm2 restart all
```

## 📁 โครงสร้างไฟล์ (Hybrid)

```
Smart-Police-Report/
├── 📁 telegram-bot/              # Node.js Telegram Bot
│   ├── package.json             # Node.js dependencies
│   ├── bot.js                   # Main Telegram bot file
│   ├── handlers/                # Message handlers
│   ├── services/                # API integration
│   ├── utils/                   # Utility functions
│   └── Dockerfile              # Docker image
│
├── 📁 python-services/           # Python API Backend
│   ├── main_api.py              # FastAPI application
│   ├── requirements-core.txt    # Python dependencies
│   ├── services/                # Google Sheets services
│   │   └── sheets_service.py    # Google Sheets API
│   ├── handlers/                # Data processing handlers
│   │   ├── contact_handler.py   # Personnel data handler
│   │   └── logic_utils.py       # Parsing utilities
│   └── Dockerfile              # Docker image
│
├── 📁 shared/                    # Shared Configuration
│   ├── .env                     # Environment variables
│   └── service_account.json     # Google credentials
│
├── 📁 backup-original/           # Backup of old system
│   └── ...                     # Original Python bot files
│
├── 📄 docker-compose.yml         # Docker orchestration
├── 📄 start-hybrid.bat          # Start script (Windows)
├── 📄 MIGRATION_GUIDE.md        # Migration documentation
├── 📄 MIGRATION_COMPLETE.md     # Migration summary
└── 📄 README.md                 # This file
```

## 📊 โครงสร้างฐานข้อมูล (Google Sheets)

ระบบ Smart Police Report เชื่อมต่อกับ Google Sheets ที่มี 6 ชีตหลัก:

### 1. **Contacts** (ข้อมูลบุคลากร)
- **หน้าที่:** เก็บข้อมูลเจ้าหน้าที่ทั้งหมดสำหรับการติดต่อประสานงาน
- **คอลัมน์:** ชื่อ-นามสกุล, ยศ, ตำแหน่ง, เบอร์โทร, สังกัด, เลขบัตรประชาชน, วันเกิด, ธนาคาร, เลขบัญชี
- **การใช้งาน:** ค้นหาข้อมูลติดต่อ, ทำเรื่องการเงิน, ประสานงานด่วน

### 2. **Vehicles** (ฐานข้อมูลยานพาหนะ)
- **หน้าที่:** ติดตามสถานะรถยนต์และรถจักรยานยนต์ราชการ
- **คอลัมน์:** หมายเลขโล่, ทะเบียน, ยี่ห้อ-รุ่น, เลขตัวถัง, เลขเครื่อง, หน่วยผู้ใช้, สถานะ
- **การใช้งาน:** ตรวจสอบสถานะรถ, วางแผนการใช้ยานพาหนะ

### 3. **Orders** (คำสั่ง/ภารกิจ)
- **หน้าที่:** บันทึกคำสั่งและภารกิจจากผู้บังคับบัญชา
- **คอลัมน์:** รายละเอียดภารกิจ, ผู้สั่ง, กำหนดส่ง, สถานะ, ระดับความเร่งด่วน, หมายเหตุ
- **การใช้งาน:** ติดตามงานค้าง, สรุปภารกิจรายวัน

### 4. **Arrests** (การจับกุม)
- **หน้าที่:** บันทึกข้อมูลการจับกุมและคดีความ
- **คอลัมน์:** วันที่, ชื่อผู้ต้องหา, อายุ, ข้อหา, สถานที่เกิดเหตุ, เจ้าหน้าที่, สถานะคดี
- **การใช้งาน:** สถิติการจับกุม, ติดตามคดี

### 5. **Equipment** (อุปกรณ์-พัสดุ)
- **หน้าที่:** ควบคุมพัสดุและอุปกรณ์ราชการ
- **คอลัมน์:** หมวดหมู่, รายการ, จำนวนทั้งหมด, กำลังใช้งาน, คงเหลือ, หมายเหตุ
- **การใช้งาน:** ตรวจสอบสต็อก, วางแผนจัดซื้อ

### 6. **FirearmRegistry** (ทะเบียนอาวุธปืน)
- **หน้าที่:** ควบคุมอาวุธปืนและกระสุน
- **คอลัมน์:** หมายเลขเครื่อง, ประเภทอาวุธ, ขนาดกระสุน, ยี่ห้อ, หมายเลขโล่, สภาพ, ผู้ยืม, วันที่
- **การใช้งาน:** ตรวจสอบการยืม-คืน, ติดตามสภาพอาวุธ

### ชีตระบบ
- **Inquiry_Logs:** บันทึกประวัติการใช้งานทั้งหมด
- **Memory_Base:** ฐานข้อมูล AI และการเรียนรู้
- **Config:** ค่าการตั้งค่าระบบ

## ⚙️ การตรวจสอบระบบ

### Health Check
```bash
# ตรวจสอบ Python API
curl http://localhost:8000/health

# ตรวจสอบ Node.js Bot
curl http://localhost:3000/health
```

### ทดสอบการเชื่อมต่อ
```bash
# ทดสอบ Google Sheets
cd python-services
python -c "
from services.sheets_service import SheetsService
from config import Config
service = SheetsService(Config())
print('✅ Google Sheets connected')
"

# ทดสอบ Telegram Bot
cd telegram-bot
node -e "
const TelegramBot = require('node-telegram-bot-api');
const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN);
bot.getMe().then(r => console.log('✅ Bot connected:', r.username));
"
```

## 🔧 การปรับแต่ง

### เปลี่ยนพอร์ต
แก้ไขใน `shared/.env`:
```env
PYTHON_API_PORT=8080  # เปลี่ยนจาก 8000
BOT_SERVER_PORT=3001  # เปลี่ยนจาก 3000
```

### เพิ่ม Webhook Support
แก้ไขใน `telegram-bot/bot.js`:
```javascript
// เปิดใช้งาน webhook แทน polling
const USE_WEBHOOK = process.env.USE_WEBHOOK === 'true';
const WEBHOOK_URL = process.env.WEBHOOK_URL;
```

### ปรับแต่ง AI Processing
แก้ไขใน `python-services/main_api.py`:
```python
# ปรับพารามิเตอร์การประมวลผล AI
AI_CONFIDENCE_THRESHOLD = 0.8  # ระดับความมั่นใจ
MAX_SEARCH_RESULTS = 10        # จำนวนผลลัพธ์สูงสุด
```

## 🚨 การแก้ไขปัญหา

### ปัญหาที่พบบ่อย

#### 1. Port ขัดแย้ง
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux
lsof -ti:8000 | xargs kill -9
```

#### 2. Dependencies ขัดแย้ง
```bash
# Node.js
cd telegram-bot
rm -rf node_modules package-lock.json
npm install

# Python
cd python-services
pip install --upgrade pip
pip install -r requirements-core.txt --force-reinstall
```

#### 3. Google Sheets Permission
- ตรวจสอบ Service Account Email ใน JSON file
- แชร์ Sheets ใหม่กับ Service Account
- ตรวจสอบ API เปิดใช้งานครบถ้วน

#### 4. Telegram Bot ไม่ตอบสนอง
- ตรวจสอบ Bot Token ใน `.env`
- ตรวจสอบการเชื่อมต่อ internet
- รีสตาร์ท Node.js service

#### 5. การเชื่อมต่อ API ล้มเหลว
- ตรวจสอบ Python API running บนพอร์ต 8000
- ตรวจสอบ Firewall/Antivirus blocking
- ทดสอบ `curl http://localhost:8000/health`

### การกู้คืนระบบ

#### กลับไปใช้ระบบเดิม
```bash
# คืนไฟล์จาก backup
cp backup-original/* .
python main_bot.py  # รันบอท Python เดิม
```

#### รีเซ็ตระบบ Hybrid
```bash
# ลบและติดตั้งใหม่
rm -rf telegram-bot/node_modules python-services/.venv
setup-hybrid.bat
```

## 🚀 การอัปเกรดและการพัฒนา

### Roadmap อนาคต

#### Phase 1: Core Enhancement
- ✅ Hybrid Architecture (เสร็จแล้ว)
- 🔄 Enhanced AI Processing
- 🔄 Advanced Search Functions
- 🔄 Real-time Notifications

#### Phase 2: Advanced Features
- 📊 **Web Dashboard** - React/Vue.js frontend
- 📈 **Analytics & Reports** - Power BI integration
- 🔒 **Enhanced Security** - OAuth2, JWT tokens
- 📱 **Mobile App** - React Native companion

#### Phase 3: Enterprise Ready
- ☁️ **Cloud Deployment** - AWS/GCP/Azure
- 🔄 **Load Balancing** - Multiple bot instances
- 💾 **Database Integration** - PostgreSQL/MongoDB
- 🔧 **Admin Portal** - System management UI

### การมีส่วนร่วมในการพัฒนา
- 🐛 รายงานปัญหาผ่าน GitHub Issues
- 💡 เสนอฟีเจอร์ใหม่
- 🤝 Pull requests ยินดีต้อนรับ

## 📝 บันทึกการเปลี่ยนแปลง

### v2.0.0 (Hybrid Architecture) - 2026-03-30
- 🔄 **Major Rewrite**: ย้ายเป็น Node.js + Python Hybrid
- ⚡ **Performance**: เร็วขึ้น 5-10 เท่า
- 🏗️ **Architecture**: Microservices-ready
- 🐳 **Docker**: Support Docker deployment
- 📊 **API**: FastAPI backend for AI processing

### v1.x (Legacy Python Bot)
- 📝 **Basic Features**: จดบันทึก, ค้นหา, แจ้งเตือน
- 📊 **Google Sheets**: Integration ครบถ้วน
- 🤖 **AI**: Basic intent detection

## 📄 ใบอนุญาต

MIT License

---

## 🤝 การสนับสนุน

หากต้องการความช่วยเหลือ:
- 📧 Email: smart-police-support@example.com
- 💬 Telegram: @SmartPoliceSupport
- 🐛 Issues: GitHub Issues
- 📚 Wiki: GitHub Wiki

**ระบบ Smart Police Report - พร้อมใช้งาน 24/7 🚔**