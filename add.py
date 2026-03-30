"""เพิ่มข้อมูลอาวุธปืน"""
from config import Config
from services.sheets_service import SheetsService
from datetime import datetime

c = Config()
s = SheetsService(c.GOOGLE_CREDENTIALS_PATH, c.GOOGLE_SHEET_ID)
s.connect()

ws = s.firearm_registry_sheet
data = ws.get_all_values()
seq = str(len(data))
ts = datetime.now().strftime('%d/%m/%Y %H:%M')

row = [seq, 'ปืนพกกึ่งอัตโนมัติ', '9มม.', 'Glock 19 Gen 5', 'RTP 50794', '24ก.ค.2565', 'คงคลัง', '-', '20 ก.พ.69', '-', '-', 'สภาพเรียบร้อย', ts]
ws.append_row(row)
print(f"✅ ลำดับ {seq}: Glock 19 Gen 5 9มม. RTP 50794→ [คงคลัง]")
print(f"📊 รวม: {len(data)+1} รายการ")
