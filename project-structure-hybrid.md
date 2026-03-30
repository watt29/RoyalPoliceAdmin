# Hybrid Architecture: Node.js + Python

## โครงสร้างโปรเจ็กต์ใหม่

```
Smart-Police-Report-Hybrid/
├── 📁 telegram-bot/              # Node.js Telegram Bot
│   ├── package.json
│   ├── bot.js                    # Main Telegram bot
│   ├── handlers/
│   │   ├── commandHandler.js
│   │   ├── messageHandler.js
│   │   └── menuHandler.js
│   ├── services/
│   │   └── apiService.js         # เชื่อมต่อ Python API
│   └── utils/
│       └── constants.js
│
├── 📁 python-services/           # Python Backend Services
│   ├── requirements.txt
│   ├── main_api.py              # FastAPI server
│   ├── services/
│   │   ├── sheets_service.py    # Google Sheets (เดิม)
│   │   ├── ai_service.py        # AI processing
│   │   └── data_processor.py    # Data extraction
│   └── handlers/
│       └── contact_handler.py   # Logic เดิม
│
├── 📁 shared/                    # Shared configs
│   ├── .env
│   └── service_account.json
│
└── docker-compose.yml            # Deploy ทั้งสอง services
```

## ประโยชน์ของสถาปัตยกรรมใหม่

✅ **Node.js**: รวดเร็วสำหรับ Telegram API, WebSocket, Real-time
✅ **Python**: แข็งแกร่งสำหรับ AI, Data Science, Google APIs
✅ **แยก Concerns**: Bot logic แยกจาก Data processing
✅ **Scalable**: ขยายแต่ละส่วนได้อิสระ
✅ **Maintainable**: แก้ไขง่าย, ทีมแยกพัฒนาได้