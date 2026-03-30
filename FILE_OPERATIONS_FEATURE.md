# 📁 File Operations ผ่าน Telegram

ความสามารถในการจัดการไฟล์ผ่าน Telegram Bot

## 🎯 ฟีเจอร์ที่เพิ่มได้

### 1. **การสร้างไฟล์ (CREATE)**

#### 📝 สร้างไฟล์ข้อความ
```bash
# Command
/create filename.txt
Hello World!
This is content.

# หรือแบบ inline
สร้างไฟล์ report.txt: "รายงานประจำวัน..."
```

#### 📊 สร้างไฟล์ CSV/Excel
```bash
# Export จาก Google Sheets
/export contacts csv
/export vehicles excel
```

#### 📄 สร้างรายงาน PDF
```bash
/report daily pdf
/report arrests 2024-03 pdf
```

### 2. **การแก้ไขไฟล์ (EDIT)**

#### ✏️ แก้ไขข้อความ
```bash
# แก้ไขบรรทัดเฉพาะ
/edit filename.txt line 5: "บรรทัดใหม่"

# แก้ไขทั้งไฟล์
/edit report.txt
เนื้อหาใหม่ทั้งหมด...
```

#### 🔄 อัปเดตข้อมูล
```bash
# อัปเดตจาก Sheets
/update contacts.csv
/sync database
```

### 3. **การลบไฟล์ (DELETE)**

#### 🗑️ ลบไฟล์
```bash
/delete filename.txt
/remove old_report.pdf

# ลบพร้อม confirmation
/delete report.pdf --confirm
```

#### 🧹 ลบแบบ bulk
```bash
/cleanup temp_*.txt
/remove --older-than 30d
```

## 🔧 Implementation Plan

### Phase 1: Basic File Operations
```python
# เพิ่มใน main_api.py
@app.post("/file-create")
async def create_file(request: FileCreateRequest):
    # สร้างไฟล์ใหม่
    pass

@app.post("/file-edit")
async def edit_file(request: FileEditRequest):
    # แก้ไขไฟล์
    pass

@app.delete("/file-delete/{filename}")
async def delete_file(filename: str):
    # ลบไฟล์
    pass
```

### Phase 2: Advanced Features
```python
# File management with metadata
class FileManager:
    def __init__(self):
        self.storage_path = "files/"
        self.max_size = 50 * 1024 * 1024  # 50MB

    async def create_file(self, filename, content, user_id):
        # Validate permissions
        # Check file size
        # Create with metadata
        pass

    async def edit_file(self, filename, content, user_id):
        # Check ownership
        # Backup old version
        # Apply changes
        pass

    async def delete_file(self, filename, user_id):
        # Check permissions
        # Move to trash (soft delete)
        # Log deletion
        pass
```

### Phase 3: Integration with Google Drive
```python
# Google Drive integration
class DriveFileManager:
    async def upload_to_drive(self, file_path):
        # Upload to Google Drive
        pass

    async def sync_with_drive(self):
        # Sync local files with Drive
        pass
```

## 🔒 Security Considerations

### 1. **File Type Restrictions**
```python
ALLOWED_EXTENSIONS = {
    'text': ['.txt', '.md', '.log'],
    'document': ['.pdf', '.doc', '.docx'],
    'spreadsheet': ['.csv', '.xlsx'],
    'image': ['.jpg', '.png', '.gif']
}

BLOCKED_EXTENSIONS = ['.exe', '.bat', '.sh', '.py']
```

### 2. **User Permissions**
```python
class PermissionManager:
    def check_file_permission(self, user_id, filename, action):
        # Check if user can create/edit/delete file
        # Based on role and file ownership
        pass
```

### 3. **File Size Limits**
```python
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
MAX_FILES_PER_USER = 100
```

## 🚀 Telegram Bot Commands

### File Commands
```python
# เพิ่มใน telegram-bot/bot.js
bot.onText(/\/create (.+)/, async (msg, match) => {
    const filename = match[1];
    // Handle file creation
});

bot.onText(/\/edit (.+)/, async (msg, match) => {
    const filename = match[1];
    // Handle file editing
});

bot.onText(/\/delete (.+)/, async (msg, match) => {
    const filename = match[1];
    // Handle file deletion
});

bot.onText(/\/list/, async (msg) => {
    // List user's files
});

// Handle file uploads
bot.on('document', async (msg) => {
    const doc = msg.document;
    // Process uploaded file
});
```

## 📱 User Interface

### Interactive File Browser
```javascript
// Inline keyboard for file management
const fileKeyboard = {
    inline_keyboard: [
        [
            { text: '📁 เรียกดูไฟล์', callback_data: 'files_browse' },
            { text: '📝 สร้างไฟล์', callback_data: 'files_create' }
        ],
        [
            { text: '📤 อัปโหลด', callback_data: 'files_upload' },
            { text: '📥 ดาวน์โหลด', callback_data: 'files_download' }
        ],
        [
            { text: '🗑️ จัดการขยะ', callback_data: 'files_trash' },
            { text: '⚙️ ตั้งค่า', callback_data: 'files_settings' }
        ]
    ]
};
```

## 💾 Storage Options

### 1. **Local Storage**
```bash
Smart-Police-Report/
├── 📁 user-files/
│   ├── 📁 user-123/
│   │   ├── 📄 report.pdf
│   │   └── 📝 notes.txt
│   └── 📁 user-456/
└── 📁 shared-files/
    ├── 📊 templates/
    └── 📋 forms/
```

### 2. **Cloud Storage**
- **Google Drive** - Integration with existing Google account
- **Render Storage** - If using Render deployment
- **AWS S3** - For production scale

## 📊 File Types Support

| Type | Extensions | Max Size | Features |
|------|------------|----------|----------|
| **Text** | .txt, .md, .log | 1MB | Edit, Search |
| **Documents** | .pdf, .docx | 10MB | View, Download |
| **Spreadsheets** | .csv, .xlsx | 5MB | Edit, Export |
| **Images** | .jpg, .png | 5MB | View, Compress |
| **Archives** | .zip, .rar | 20MB | Extract, List |

## ⚡ Quick Implementation

### Minimal File Operations
```python
# เพิ่มใน main_api.py
import os
from pathlib import Path

@app.post("/file-operations")
async def handle_file_operation(request: dict):
    action = request.get('action')  # create, edit, delete
    filename = request.get('filename')
    content = request.get('content', '')
    user_id = request.get('user_id')

    user_dir = Path(f"user-files/{user_id}")
    user_dir.mkdir(parents=True, exist_ok=True)
    file_path = user_dir / filename

    if action == 'create':
        if file_path.exists():
            return {"success": False, "error": "File already exists"}
        file_path.write_text(content, encoding='utf-8')
        return {"success": True, "message": f"Created {filename}"}

    elif action == 'edit':
        if not file_path.exists():
            return {"success": False, "error": "File not found"}
        file_path.write_text(content, encoding='utf-8')
        return {"success": True, "message": f"Updated {filename}"}

    elif action == 'delete':
        if not file_path.exists():
            return {"success": False, "error": "File not found"}
        file_path.unlink()
        return {"success": True, "message": f"Deleted {filename}"}
```

## 🎯 Roadmap

### Phase 1 (สัปดาห์ที่ 1-2)
- [x] Basic CRUD operations
- [ ] File upload/download
- [ ] Simple text editor

### Phase 2 (สัปดาห์ที่ 3-4)
- [ ] Google Drive integration
- [ ] File versioning
- [ ] Collaborative editing

### Phase 3 (เดือนที่ 2)
- [ ] Advanced file browser
- [ ] File sharing
- [ ] Automated backups

**พร้อมเริ่มพัฒนาฟีเจอร์ File Operations! 🚀**