# 📄 Data Schemas Reference

ไฟล์นี้เก็บโครงสร้างมาตรฐานของแต่ละประเภทข้อมูล เพื่อให้ Smart Recorder ทำการ Mapping ข้อมูลได้แม่นยำ

## 🛡️ ยุทธภัณฑ์ (Equipment)
- **Sheet Name**: `Equipment`
- **Keywords**: ยุทธภัณฑ์, เสื้อเกราะ, อาวุธปืน, อาวุธ, กระสุน, วิทยุสื่อสาร, รถยนต์, ยานพาหนะ
- **Columns**:
  1. Category: หมวดหมู่ (Auto-detect)
  2. Item: รายการ/ประเภท
  3. Total: จำนวนทั้งหมด (Numeric)
  4. InUse: เบิกใช้/จ่าย (Numeric)
  5. InStock: คงคลัง/เหลือ (Numeric)
  6. Note: หมายเหตุ
  7. Updated_At: วันที่อัปเดต

## 👤 รายชื่อ/ทำเนียบ (Contacts)
- **Sheet Name**: `Contacts`
- **Keywords**: รายชื่อ, ทำเนียบ, ยศ, สังกัด, เบอร์โทร, ตำแหน่ง, ผบ.หมู่, สภ.
- **Known Callsigns (นามเรียกขาน)**: บางปะอิน 613, วังน้อย 01, วังน้อย 211, วังน้อย 221, วังน้อย 238, วังน้อย 325, วังน้อย 326, วังน้อย 328, วังน้อย 332, วังน้อย 351, วังน้อย 353, วังน้อย 361, วังน้อย 511, วังน้อย 514
- **Columns**:
  - Name, Rank, Phone, Agency, ID, Birth, Bank, Account, Note

## 💰 สถานะเบิกจ่าย (Expenditure)
- **Sheet Name**: `ExpenditureStatus`
- **Keywords**: เบิกเงิน, ค่าตอบแทน, พงส.
- **Columns**:
  - Item, Month, Note
