---
name: smart-recorder
description: สกิลการบันทึกข้อมูลอัจฉริยะ รองรับข้อมูลตารางที่ไม่มี Tab, ข้อมูลตัวเลขติดกัน และการแยกหมวดหมู่อัตโนมัติ
version: 1.0.0
---

# 🧠 Smart Recorder Skill (V1.0.0)

## 🎯 วัตถุประสงค์
แปลงข้อมูลข้อความดิบ (Raw Text) จาก Telegram ให้เป็นข้อมูลโครงสร้าง (Structured Data) เพื่อบันทึกลง Google Sheets โดยเน้นความยืดหยุ่นสูงต่อความผิดเพี้ยนของรูปแบบข้อมูล

## 🛠️ ความสามารถหลัก (Core Intelligence)

### 1. Mashed Number Splitter (ตรรกะแยกตัวเลขติดกัน)
- **ปัญหา**: Telegram มักลบ Tab ทำให้ตัวเลขค่าสถิติติดกัน เช่น `16016`
- **ความฉลาด**: ใช้สมการ `Total = InUse + InStock` เพื่อหาจุดตัดตัวเลขที่ถูกต้องโดยอัตโนมัติ

### 2. Auto-Index Shift Detection (ระบบตรวจจับลำดับอัตโนมัติ)
- **ปัญหา**: ข้อมูลมักมีคอลัมน์ "ลำดับ" (1, 2, 3) นำหน้า แต่ในหัวตารางไม่ได้ระบุไว้
- **ความฉลาด**: ตรวจสอบช่องแรกของข้อมูล หากเป็นตัวเลขลำดับ (Index) ระบบจะขยับ Index การ Mapping ข้อมูลที่เหลือให้อัตโนมัติ

### 3. Prefix & Context Handling
- **คำสั่งนำหน้า**: รองรับคำว่า "จด", "บันทึก", "เก็บข้อมูล" นำหน้าหัวตาราง
- **การตรวจจับหมวด**: วิเคราะห์ Keywords (เสื้อเกราะ, อาวุธ, รถยนต์, กระสุน) เพื่อเลือกลง Sheet ให้ถูกใบ

## 📋 รูปแบบข้อมูลที่รองรับ (Schemas)
*ดูรายละเอียดใน `references/data_schemas.md`*

1. **Equipment**: [Category, Item, Total, InUse, InStock, Note, Timestamp]
2. **Contacts**: [Name, Rank, Phone, Agency, ID, Birth, Bank, Account, Note, Timestamp]
3. **Expenditure**: [Item, Month, Remark]

## 🔄 การทำ Versioning
- **v1.0.0**: เปิดตัวระบบ Smart Splitter และ Auto-Shift
- **Next Version Plan**: รองรับการอ่านรูปภาพตาราง (OCR Integration)
