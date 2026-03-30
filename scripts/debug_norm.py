import sys
import os
sys.path.append(os.getcwd())

from services.sheets_service import SheetsService
from config import Config

def debug_normalization():
    try:
        config = Config()
        s = SheetsService(config.GOOGLE_CREDENTIALS_PATH, config.GOOGLE_SHEET_ID)
        s.connect()
        
        test_names = [
            "ด.ต.อานนท์ คงบุตร",
            "ด.ต. อานนท์ คงบุตร",
            "ด.ต.อานนท์  คงบุตร",
            "อานนท์ คงบุตร",
            "ด.ต.อานนท์            คงบุตร"
        ]
        
        print("--- Normalization Results ---")
        for name in test_names:
            norm = s._normalize(name)
            print(f"Original: '{name}'")
            print(f"Normalized: '{norm}'")
            print("-" * 20)
            
        print("\n--- SalaryHistory Sheet Match Test ---")
        ws = s.spreadsheet.worksheet('SalaryHistory')
        all_rows = ws.get_all_values()
        
        target_norm = s._normalize("ด.ต.อานนท์ คงบุตร")
        found = False
        for row in all_rows[1:]:
            row_name_norm = s._normalize(row[0])
            print(f"Checking row: '{row[0]}' -> Norm: '{row_name_norm}'")
            if row_name_norm == target_norm:
                print(f"✅ MATCH FOUND! s_info: {row[1:]}")
                found = True
                break
        
        if not found:
            print("❌ NO MATCH FOUND in SalaryHistory")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_normalization()
