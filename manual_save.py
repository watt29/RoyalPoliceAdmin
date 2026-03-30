
import os
from datetime import datetime
from services.sheets_service import SheetsService
from config import Config

def manual_save_order():
    config = Config()
    sheets = SheetsService(config.GOOGLE_CREDENTIALS_PATH, config.GOOGLE_SHEET_ID)
    
    if not sheets.connect():
        print("Failed to connect to Google Sheets.")
        return

    text_detail = """ประชุมรับตรวจราชการ ณ ห้องประชุมนันทโชติ ชั้น ๒ ภ.จว.พระนครศรีอยุธยา
ประกอบด้วย: หน.สภ.นครหลวง, สภ.ภาชี, สภ.ลาดบัวหลวง, สภ.มหาราช, สภ.โรงช้าง, สภ.บ้านแพรก, สภ.ข้างใหญ่, สภ.บางปะอิน, สภ.พระอินทร์ราชา, สภ.บางปะหัน, สภ.บ้านขล้อ, สภ.พระนครศรีอยุธยา, สภ.ผักไห่, และ สภ.ลาดชะโต"""
    
    deadline = "19 มี.ค. 2569 (08.30 น.)"
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    # Orders cols: ["Detail", "Commander", "Deadline", "Status", "Urgency", "Note", "Timestamp"]
    row = [
        text_detail,
        "ภ.จว.พระนครศรีอยุธยา",
        deadline,
        "Pending",
        "Normal",
        "บันทึกตามความต้องการของผู้ใช้ (Manual)",
        timestamp
    ]
    
    if sheets.append_order(row):
        print("Successfully saved to Orders sheet!")
    else:
        print("Failed to save to Orders sheet.")

if __name__ == "__main__":
    manual_save_order()
