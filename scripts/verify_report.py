import sys
import os
sys.path.append(os.getcwd())

from services.sheets_service import SheetsService
from config import Config

def verify_and_report():
    try:
        config = Config()
        s = SheetsService(config.GOOGLE_CREDENTIALS_PATH, config.GOOGLE_SHEET_ID)
        s.connect()
        s._load_salary_ref_data()
        s._load_rank_mapping()
        
        print("\n--- Salary Comparison Step 21.5 ---")
        p2_21_5 = s._current_ref_data.get("ป2_21.5", "Not Found")
        p3_21_5 = s._current_ref_data.get("ป3_21.5", "Not Found")
        print(f"ป.2 ขั้น 21.5: {p2_21_5}")
        print(f"ป.3 ขั้น 21.5: {p3_21_5}")
        
        print("\n--- Rank Mapping Check ---")
        print(f"Rank Map Keys: {list(s._rank_map.keys())[:5]}... (Total: {len(s._rank_map)})")
        name = "ด.ต.อานนท์ คงบุตร"
        name_light = s._normalize_light(name).replace(" ", "")
        found_lvl = None
        for r_n, r_l in s._rank_map.items():
            if r_n in name_light:
                found_lvl = r_l
                print(f"Match found: '{r_n}' -> '{r_l}'")
                break
        
        print("\n--- Final Unit Report Generation ---")
        report = s.get_unit_salary_report("มหาราช")
        print(report)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_and_report()
