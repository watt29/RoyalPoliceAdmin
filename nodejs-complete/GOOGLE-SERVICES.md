# 🌐 Google Services Integration

## 📊 Google Sheets + 📁 Google Drive

Smart Police Report Bot v3.0 ได้รวม Google Services เข้าด้วยกันแล้ว!

### 🔗 Service Links

**📊 Google Sheets (Database):**
```
https://docs.google.com/spreadsheets/d/1xxwyReavlHXmKqEIEdem7zUAdlVS5Kv2D_7S6Rsf2UA/edit?gid=0#gid=0
```

**📁 Google Drive (File Storage):**
```
https://drive.google.com/drive/folders/1W7HAAqSSLNpRMmIKbtqjmm_ayp_PnBOT?lfhs=2
```

---

## 🛠️ Configuration

### Environment Variables
```env
# Google Sheets (Database)
GOOGLE_SHEET_ID=1xxwyReavlHXmKqEIEdem7zUAdlVS5Kv2D_7S6Rsf2UA
GOOGLE_SHEET_NAME=Smart_Memo_Database

# Google Drive (File Storage)
GOOGLE_DRIVE_FOLDER_ID=1W7HAAqSSLNpRMmIKbtqjmm_ayp_PnBOT

# Service Account (Same for both services)
GOOGLE_CREDENTIALS={"type":"service_account",...}
```

### Service Account Permissions
ต้องให้สิทธิ์ Service Account:
```
✅ Editor access to Google Sheets
✅ Editor access to Google Drive folder
✅ Can create files and folders
✅ Can read and write data
```

---

## 🧪 Testing

### 1. Test All Google Services
```bash
npm run test:google
```

### 2. Test Individual Services
```bash
# Test Bot Connection
npm run test:bot

# Test System
npm test

# Test Google Services only
node test-google-services.js
```

### 3. Expected Test Results
```
🔍 Testing Google Services Integration...
============================================

📊 Testing Google Sheets Service...
✅ Google Sheets - Connected successfully
📝 Testing data write...
✅ Data write - Success
🔍 Testing data search...
✅ Data search - Success

📁 Testing Google Drive Service...
✅ Google Drive - Connected successfully
📂 Target Folder ID: 1W7HAAqSSLNpRMmIKbtqjmm_ayp_PnBOT
📝 Testing file upload...
✅ File upload - Success
📋 Testing file listing...
✅ File listing - Success

============================================
📊 Test Results Summary:
📊 Google Sheets: ✅ PASS - All operations successful
📁 Google Drive: ✅ PASS - All operations successful

🎯 Overall: ✅ ALL SYSTEMS GO!
```

---

## 🎯 Features

### 📊 Google Sheets Features

**Data Storage:**
- ✅ Contacts (บุคลากร)
- ✅ Vehicles (ยานพาหนะ)
- ✅ Orders (คำสั่ง/ภารกิจ)
- ✅ Arrests (การจับกุม)
- ✅ Equipment (อุปกรณ์)
- ✅ FirearmRegistry (ทะเบียนอาวุธปืน)

**Operations:**
- ✅ Auto data insertion
- ✅ Smart search across all sheets
- ✅ Data validation
- ✅ Export to CSV
- ✅ Real-time updates

### 📁 Google Drive Features

**File Management:**
- ✅ Upload files from Telegram
- ✅ Download files to users
- ✅ File search and listing
- ✅ Folder organization
- ✅ Auto backup

**Supported File Types:**
```
📄 Documents: .txt, .md, .pdf, .doc, .docx
📊 Spreadsheets: .csv, .xls, .xlsx
🖼️ Images: .jpg, .jpeg, .png, .gif
📦 Data: .json, .xml
💾 Archives: .zip, .rar
```

---

## 💻 Usage Examples

### 1. Auto Data Saving
```
User: นาย สมชาย ใจดี พ.ต.ต. โทร 081-234-5678 สภ.บางแค

Bot: ✅ บันทึกข้อมูลบุคลากรสำเร็จ
     📊 Saved to Google Sheets: Contacts
     📄 Row added with timestamp
```

### 2. File Upload
```
User: [Uploads document via Telegram]

Bot: ✅ อัปโหลดไฟล์สำเร็จ
     📁 Saved to Google Drive
     🔗 File Link: https://drive.google.com/file/d/xxx
     📊 Size: 2.3 MB
```

### 3. Search Across Services
```
User: /ค้นหา สมชาย

Bot: 🔍 ผลการค้นหา: สมชาย

     📊 From Google Sheets:
     1. [Contacts] นาย สมชาย ใจดี
     2. [Orders] คำสั่งโดย สมชาย

     📁 From Google Drive:
     3. [Files] รายงาน_สมชาย.pdf
     4. [Files] memo_สมชาย.txt
```

### 4. Export Data
```
User: /export contacts csv

Bot: 📄 ส่งออกข้อมูลสำเร็จ
     [Sends CSV file from Google Sheets]
     📊 จำนวน: 156 รายการ
     🔗 Google Drive backup: [link]
```

---

## 🔧 Advanced Configuration

### 1. Multiple Folder Support
```javascript
// In GoogleDriveService.js
const folderStructure = {
  reports: 'folder_id_1',
  backups: 'folder_id_2',
  uploads: 'folder_id_3'
};
```

### 2. Auto Backup Schedule
```javascript
// Auto backup to Google Drive every 6 hours
cron.schedule('0 */6 * * *', async () => {
  await this.backupToGoogleDrive();
});
```

### 3. File Sync
```javascript
// Sync local files with Google Drive
await this.driveService.syncFolder('./user-files');
```

---

## 🛡️ Security Features

### 1. Access Control
- ✅ Service Account authentication
- ✅ Folder-level permissions
- ✅ File type validation
- ✅ Size limits enforcement

### 2. Data Protection
- ✅ Encrypted transmission (HTTPS)
- ✅ Private folders only
- ✅ No public sharing
- ✅ Audit trail in logs

### 3. Backup Strategy
- ✅ Auto backup to Google Drive
- ✅ Daily snapshots
- ✅ Versioning support
- ✅ Recovery procedures

---

## 📊 Monitoring & Analytics

### 1. Health Checks
```bash
# Check service status
curl https://your-app.onrender.com/health

# Response includes Google Services status
{
  "status": "healthy",
  "services": {
    "sheets": "connected",
    "drive": "connected"
  }
}
```

### 2. Usage Analytics
- 📈 Data insertion rate
- 📁 File upload volume
- 🔍 Search frequency
- 💾 Storage usage

### 3. Error Monitoring
- 🚨 Connection failures
- ❌ Permission errors
- 📊 Rate limiting
- 💾 Storage quota

---

## 🚀 Deployment Notes

### Render.com Environment Variables
```env
GOOGLE_SHEET_ID=1xxwyReavlHXmKqEIEdem7zUAdlVS5Kv2D_7S6Rsf2UA
GOOGLE_DRIVE_FOLDER_ID=1W7HAAqSSLNpRMmIKbtqjmm_ayp_PnBOT
GOOGLE_CREDENTIALS={"type":"service_account","project_id":"telegram-smart-memo",...}
```

### Production Optimizations
- ✅ Connection pooling
- ✅ Request batching
- ✅ Caching strategy
- ✅ Error recovery
- ✅ Rate limit handling

---

## 🎉 Ready to Use!

🌐 **Google Services Integration** เสร็จสมบูรณ์!

**ระบบพร้อม:**
- ✅ บันทึกข้อมูลใน Google Sheets อัตโนมัติ
- ✅ เก็บไฟล์ใน Google Drive อัจฉริยะ
- ✅ ค้นหาข้ามทั้ง 2 บริการ
- ✅ สำรองข้อมูลอัตโนมัติ
- ✅ Export/Import ครบครัน

🚀 **เริ่มใช้งานได้เลย:** `npm start`