import sys
import os
sys.path.append(os.getcwd())

from services.sheets_service import SheetsService
from config import Config

def init_rank_mapping():
    try:
        config = Config()
        s = SheetsService(config.GOOGLE_CREDENTIALS_PATH, config.GOOGLE_SHEET_ID)
        s.connect()
        
        # Check if worksheet exists, create if not
        try:
            ws = s.spreadsheet.add_worksheet(title='RankMapping', rows='50', cols='5')
            print("Created new RankMapping worksheet.")
        except:
            ws = s.spreadsheet.worksheet('RankMapping')
            ws.clear()
            print("Updated existing RankMapping worksheet.")
            
        data = [
            ['ยศ (Rank)', 'ระดับ (Level)', 'หมายเหตุ'],
            ['พลตำรวจเอก (ผบ.ตร.)', 'ส.9', 'ระดับสูงสุด'],
            ['พลตำรวจเอก', 'ส.8', 'พล.ต.อ.'],
            ['พล.ต.อ.', 'ส.8', ''],
            ['พลตำรวจโท', 'ส.7', 'พล.ต.ท.'],
            ['พล.ต.ท.', 'ส.7', ''],
            ['พลตำรวจตรี', 'ส.6', 'พล.ต.ต.'],
            ['พล.ต.ต.', 'ส.6', ''],
            ['พันตำรวจเอก (พิเศษ)', 'ส.5', 'พ.ต.อ.(พิเศษ)'],
            ['พ.ต.อ.(พิเศษ)', 'ส.5', ''],
            ['พันตำรวจเอก', 'ส.4', 'พ.ต.อ.'],
            ['พ.ต.อ.', 'ส.4', ''],
            ['พันตำรวจโท', 'ส.3', 'พ.ต.ท.'],
            ['พ.ต.ท.', 'ส.3', ''],
            ['พันตำรวจตรี', 'ส.2', 'พ.ต.ต.'],
            ['พ.ต.ต.', 'ส.2', ''],
            ['ร้อยตำรวจเอก', 'ส.1', 'ร.ต.อ.'],
            ['ร.ต.อ.', 'ส.1', ''],
            ['ร้อยตำรวจโท', 'ส.1', 'ร.ต.ท.'],
            ['ร.ต.ท.', 'ส.1', ''],
            ['ร้อยตำรวจตรี', 'ส.1', 'ร.ต.ต.'],
            ['ร.ต.ต.', 'ส.1', ''],
            ['ดาบตำรวจ', 'ป.3', 'ด.ต.'],
            ['ด.ต.', 'ป.3', ''],
            ['จ่าสิบตำรวจ (พิเศษ)', 'ป.2', 'จ.ส.ต.(พิเศษ)'],
            ['จ.ส.ต.(พิเศษ)', 'ป.2', ''],
            ['จ่าสิบตำรวจ', 'ป.1', 'จ.ส.ต.'],
            ['จ.ส.ต.', 'ป.1', ''],
            ['สิบตำรวจเอก', 'ป.1', 'ส.ต.อ.'],
            ['ส.ต.อ.', 'ป.1', ''],
            ['สิบตำรวจโท', 'ป.1', 'ส.ต.ท.'],
            ['ส.ต.ท.', 'ป.1', ''],
            ['สิบตำรวจตรี', 'ป.1', 'ส.ต.ต.'],
            ['ส.ต.ต.', 'ป.1', ''],
            ['พลตำรวจ', 'พ.1', '']
        ]
        
        ws.update(values=data, range_name='A1')
        print("✅ บันทึก RankMapping สำเร็จ")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    init_rank_mapping()
