import sys
import os
sys.path.append(os.getcwd())

from services.sheets_service import SheetsService
from config import Config

def fix_salary_data():
    try:
        config = Config()
        s = SheetsService(config.GOOGLE_CREDENTIALS_PATH, config.GOOGLE_SHEET_ID)
        s.connect()
        s._load_salary_ref_data()
        
        target_name = "ด.ต.อานนท์ คงบุตร"
        new_lvl = "ป.3"
        new_step = "21.5"
        
        # Get correct salary from reference
        norm_lvl = s._normalize(new_lvl)
        ref_key = f"{norm_lvl}_{new_step}"
        correct_sal = s._current_ref_data.get(ref_key)
        
        if not correct_sal:
            print(f"❌ Error: Could not find salary for {new_lvl} Step {new_step} in reference table.")
            return

        print(f"🔄 Updating {target_name} to {new_lvl} Step {new_step} (Salary: {correct_sal})...")
        
        # SalaryHistory schema: [Name, Level, Step, Salary, EvalSummary, Note]
        row_data = [target_name, new_lvl, new_step, correct_sal, "", "ปรับปรุงข้อมูลให้ตรงตาม พ.ร.บ. 2565 (ด.ต. = ป.3)"]
        
        if s.upsert_salary_bulk([row_data]):
            print(f"✅ แก้ไขข้อมูล {target_name} เรียบร้อยแล้ว")
        else:
            print(f"❌ ไม่สามารถแก้ไขข้อมูลได้")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_salary_data()
