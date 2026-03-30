# 🚀 Deploy Smart Police Report บน Render

คู่มือการ deploy ระบบ **Smart Police Report Hybrid** บน **Render.com**

## 🌟 ข้อดีของ Render

✅ **Free Tier** ใช้ได้จริง (750 ชั่วโมง/เดือน)
✅ **Auto-deploy** จาก GitHub
✅ **Built-in SSL** certificates
✅ **Zero-config** deployment
✅ **Support** Node.js + Python
✅ **Environment variables** ง่าย
✅ **Custom domains** ฟรี

## 📋 ขั้นตอนการ Deploy

### Step 1: เตรียม GitHub Repository

```bash
# Initialize Git (ถ้ายังไม่มี)
git init
git add .
git commit -m "Initial commit for Render deployment"

# สร้าง repository บน GitHub และ push
git remote add origin https://github.com/YOUR_USERNAME/smart-police-report.git
git branch -M main
git push -u origin main
```

### Step 2: สมัคร Render Account

1. ไปที่ [render.com](https://render.com)
2. สมัครด้วย GitHub account
3. Connect GitHub repository

### Step 3: Deploy Python API (Backend)

#### 3.1 สร้าง Web Service
1. คลิก **"New +"** → **"Web Service"**
2. เชื่อมต่อ GitHub repository
3. ตั้งค่าดังนี้:

```yaml
Name: smart-police-api
Runtime: Python 3
Build Command: cd python-services && pip install -r requirements-core.txt
Start Command: cd python-services && uvicorn main_api:app --host 0.0.0.0 --port $PORT
```

#### 3.2 Environment Variables
เพิ่ม Environment Variables:

| Key | Value | Description |
|-----|-------|-------------|
| `PYTHON_ENV` | `production` | Production environment |
| `TELEGRAM_BOT_TOKEN` | `YOUR_BOT_TOKEN` | จาก @BotFather |
| `GOOGLE_SHEET_ID` | `YOUR_SHEET_ID` | จาก Google Sheets URL |
| `GOOGLE_SHEET_NAME` | `Smart_Police_Database` | ชื่อ Google Sheets |
| `GOOGLE_CREDENTIALS_JSON` | `{...}` | เนื้อหาไฟล์ service_account.json |

#### 3.3 สำหรับ Google Credentials
คัดลอกเนื้อหาไฟล์ `service_account.json`:
```bash
cat shared/service_account.json
```
วางในตัวแปร `GOOGLE_CREDENTIALS_JSON` (รูปแบบ JSON)

### Step 4: Deploy Node.js Bot (Frontend)

#### 4.1 สร้าง Web Service ใหม่
1. คลิก **"New +"** → **"Web Service"**
2. เลือก repository เดียวกัน
3. ตั้งค่าดังนี้:

```yaml
Name: smart-police-bot
Runtime: Node
Build Command: cd telegram-bot && npm install
Start Command: cd telegram-bot && npm start
```

#### 4.2 Environment Variables
| Key | Value | Description |
|-----|-------|-------------|
| `NODE_ENV` | `production` | Production environment |
| `TELEGRAM_BOT_TOKEN` | `YOUR_BOT_TOKEN` | เดียวกับ Python API |
| `PYTHON_API_URL` | `https://smart-police-api.onrender.com` | URL ของ Python API |

### Step 5: เชื่อม Services

หลังจาก deploy ทั้งคู่แล้ว:

1. **Python API**: `https://smart-police-api.onrender.com`
2. **Node.js Bot**: `https://smart-police-bot.onrender.com`

อัปเดต Environment Variables:
- Python API: `BOT_API_URL` = `https://smart-police-bot.onrender.com`
- Node.js Bot: `PYTHON_API_URL` = `https://smart-police-api.onrender.com`

## 🔧 การตั้งค่าเพิ่มเติม

### Custom Domain (ถ้าต้องการ)
```yaml
# ใน Render Dashboard
Settings → Custom Domains
Add Domain: your-domain.com
```

### Health Check URLs
- Python API: `https://smart-police-api.onrender.com/health`
- Node.js Bot: `https://smart-police-bot.onrender.com/health`

### Auto-Deploy
Render จะ auto-deploy เมื่อ push ไปที่ `main` branch

## 📊 Monitoring & Logs

### ดู Logs
```bash
# ใน Render Dashboard
Service → Logs → Live Logs
```

### Health Monitoring
```bash
# ทดสอบ API
curl https://smart-police-api.onrender.com/health

# ทดสอบ Bot
curl https://smart-police-bot.onrender.com/health
```

## 🚨 Troubleshooting

### 1. Build ล้มเหลว
```bash
# ตรวจสอบ logs ใน Render Dashboard
# แก้ไข dependencies หรือ build commands
```

### 2. Environment Variables
```bash
# ตรวจสอบว่าตั้งค่าครบถ้วน
# Google Credentials ต้องเป็น valid JSON
```

### 3. Service Communication
```bash
# ตรวจสอบ URL ของ services
# ใช้ internal URLs: https://service-name.onrender.com
```

### 4. Cold Start
```bash
# Free tier มี cold start (รอ 30 วินาที)
# ใช้ cron job เพื่อ keep alive:
# https://cron-job.org
```

## 💰 ราคา & Limits

### Free Tier
- **750 ชั่วโมง/เดือน** (25 วัน)
- **Sleep หลัง 15 นาที** ไม่มีการใช้งาน
- **512 MB RAM**
- **0.1 vCPU**

### Upgrade Options
- **Starter**: $7/เดือน (24/7, 512MB)
- **Standard**: $25/เดือน (1GB RAM, 1 vCPU)

## 🔒 Security Best Practices

### Environment Variables
```bash
# ไม่เก็บ secrets ใน code
# ใช้ Environment Variables เสมอ
```

### API Keys
```bash
# ใช้ API keys ที่มี scope จำกัด
# หมุนเวียน keys เป็นประจำ
```

### CORS Policy
```python
# ใน main_api.py
allow_origins=["https://your-domain.com"]  # แทน "*"
```

## 🚀 Production Optimization

### 1. Database
```bash
# เพิ่ม PostgreSQL (Render)
# ใช้แทน Google Sheets สำหรับ high-volume data
```

### 2. Caching
```bash
# เพิ่ม Redis (Render)
# Cache Google Sheets responses
```

### 3. CDN
```bash
# ใช้ Cloudflare หน้า Render
# เพิ่มความเร็วและลด latency
```

### 4. Monitoring
```bash
# ใช้ Render Metrics
# เพิ่ม external monitoring (UptimeRobot)
```

## 📈 Scaling Strategy

### Phase 1: Free Tier
- 2 services (Python + Node.js)
- Basic functionality
- Limited users

### Phase 2: Paid Plans
- 24/7 uptime
- More RAM/CPU
- Custom domains

### Phase 3: Multiple Regions
- Load balancing
- Database clusters
- Global CDN

## 🔄 CI/CD Pipeline

### GitHub Actions (ทางเลือก)
```yaml
# .github/workflows/deploy.yml
name: Deploy to Render
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          cd telegram-bot && npm test
          cd python-services && python -m pytest
```

## ✅ Pre-Deploy Checklist

- [ ] GitHub repository ready
- [ ] Telegram bot token
- [ ] Google Sheets configured
- [ ] Service account JSON
- [ ] Environment variables prepared
- [ ] Health check endpoints working
- [ ] CORS configured properly

## 🎯 ขั้นตอนถัดไป

1. **Deploy basic version**
2. **Test functionality**
3. **Add custom domain**
4. **Set up monitoring**
5. **Implement caching**
6. **Add database**
7. **Scale to paid plans**

---

## 📞 Support

- **Render Docs**: [docs.render.com](https://docs.render.com)
- **Community**: [community.render.com](https://community.render.com)
- **GitHub Issues**: สำหรับโปรเจกต์นี้

**พร้อม Deploy บน Render แล้ว! 🚀**