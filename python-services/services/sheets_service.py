import logging
import gspread  # type: ignore
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials  # type: ignore
from typing import List, Dict, Optional, Any, Iterable, Union, Tuple, cast
import os
import re
import calendar
import unicodedata

logger = logging.getLogger(__name__)

class SheetsService:
    DIVIDER = "──────────────────────────"
    # Pre-compiled patterns to prevent hangs and syntax warnings
    RANK_PATTERN = re.compile(r'(พ\.ต\.อ\.|พตอ|พ\.ต\.ท\.|พตท|พ\.ต\.ต\.|พตต|ร\.ต\.อ\.|รตอ|ร\.ต\.ท\.|รตท|ร\.ต\.ต\.|รตต|ด\.ต\.|ดต|จ\.ส\.ต\.|จสต|ส\.ต\.อ\.|สตอ|ส\.ต\.ท\.|สตท|ส\.ต\.ต\.|สตต|ร\.ด\.ต\.|รดต|ต\.ต\.|ค\.ต\.|ร\.ค\.ต\.|รคต|จ\.ส\.ค\.|จสค|ส\.ต\.ด\.|สตด|นาย|นาง|นางสาว|น\.ส\.)\s*', re.IGNORECASE)
    CLEAN_PATTERN = re.compile(r'[\s\.\-\/]+')

    gc: Any = None
    spreadsheet: Any = None
    contacts_sheet: Any = None
    orders_sheet: Any = None
    vehicles_sheet: Any = None
    reminders_sheet: Any = None
    budgets_sheet: Any = None
    commanders_sheet: Any = None
    duty_roster_sheet: Any = None
    duty_patterns_sheet: Any = None
    equipment_sheet: Any = None
    salary_sheet: Any = None
    arrests_sheet: Any = None
    firearm_registry_sheet: Any = None
    salary_ref_sheet: Any = None
    _current_ref_data: Dict[str, Any] = {}
    _salary_headers: List[str] = []
    _rank_map: Dict[str, str] = {}
    rank_mapping_sheet: Any = None

    def __init__(self, credentials_path: str, spreadsheet_id: str):
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id
        self.scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        self.gc = None
        self.spreadsheet = None
        self.contacts_sheet = None
        self.orders_sheet = None
        self.vehicles_sheet = None
        self.reminders_sheet = None
        self.budgets_sheet = None
        self.commanders_sheet = None
        self.duty_roster_sheet = None
        self.duty_patterns_sheet = None
        self.equipment_sheet = None
        self.salary_sheet = None
        self.arrests_sheet = None
        self.firearm_registry_sheet = None
        self.salary_ref_sheet = None
        self._current_ref_data = {}
        self._salary_headers = []
        self._rank_map = {}
        self.rank_mapping_sheet = None
        
        # 🎯 Centralized Intent Registry (The "Permanent" Fix for Parsers)
        self.INTENT_REGISTRY = {
            "duty": {"keys": ["เวร", "ตารางเวร", "ใครเวร", "สิบเวร", "อำนวยการ", "รวย"], "targets": ["DutyRoster"]},
            "vehicle": {"keys": ["รถ", "ทะเบียน", "โล่", "ขับรถ", "ยานพาหนะ"], "targets": ["Vehicles"]},
            "commander": {"keys": ["ผู้การ", "ผู้กำกับ", "นาย", "ผบก", "รองผบก", "ผกก", "ผกก.", "พ.ต.อ.สมชาย", "แจ้งธรรมมา"], "targets": ["Commanders", "Orders"]},
            "budget": {"keys": ["งบ", "เบิก", "จ่าย", "สถานะงบ", "เงิน"], "targets": ["Budgets", "ExpenditureStatus"]},
            "order": {"keys": ["สั่ง", "งาน", "ข้อสั่งการ", "ภารกิจ", "ไปไหน", "ทำอะไร", "นัด"], "targets": ["Orders"]},
            "contact": {"keys": ["เบอร์", "โทร", "เจ้าหน้าที่", "สภ", "ที่อยู่"], "targets": ["Contacts", "Commanders"]},
            "equipment": {"keys": ["ยุทธภัณฑ์", "เสื้อเกราะ", "วิทยุ", "กุญแจมือ", "โล่", "คลังอาวุธ"], "targets": ["Equipment"]},
            "firearm": {"keys": ["อาวุธปืน", "ปืน", "ยืมปืน", "เบิกปืน", "ทะเบียนโล่", "ปืนราชการ"], "targets": ["FirearmRegistry", "Equipment"]}
        }
        
        # 🏛️ บัญญัติกฎเหล็ก: กำชับหน้าที่และโครงสร้างของแต่ละชีท (Hardcoded Registry)
        # เคลื่อนย้ายมาไว้ที่ __init__ เพื่อให้ Handler ต่างๆ เรียกใช้งานได้ทันทีโดยไม่ต้องรอ Connect
        self.SHEET_PROFILES = {
            "Orders": {
                "display_name": "ข้อสั่งการ",
                "duty": "เก็บข้อสั่งการจากการประชุม, การตรวจราชการ และภารกิจเร่งด่วน",
                "columns": ["Detail", "Commander", "Deadline", "Status", "Urgency", "Note", "Timestamp"]
            },
            "Contacts": {
                "display_name": "เบอร์โทร/รายชื่อ",
                "duty": "ฐานข้อมูลเบอร์โทรศัพท์และประวัติกำลังพลรายบุคคล",
                "columns": ["Name", "Position", "Callsign", "Phone", "Agency", "ID Card", "Birthday", "Bank", "Account", "Note", "Updated_At"]
            },
            "Vehicles": {
                "display_name": "ยานพาหนะ",
                "duty": "ทะเบียนยานพาหนะหลวง, เลขโล่ และสถานะการใช้งาน/ซ่อมบำรุง",
                "columns": ["ID", "Ref", "Dept", "Type1", "Type2", "Shield", "Plate", "Brand", "Chassis", "Engine", "User", "Repair", "Recorder", "GFMIS", "DateCalc", "Mileage", "DateGet", "Status"]
            },
            # (Arrests profile removed)
            "Equipment": {
                "display_name": "ยุทธภัณฑ์/อุปกรณ์",
                "duty": "บัญชีคุมยุทธภัณฑ์, อาวุธปืน และอุปกรณ์หลวง",
                "columns": ["Category", "Item", "Total", "InUse", "InStock", "Note", "Updated_At"]
            },
            "FirearmRegistry": {
                "display_name": "บัญชีปืนหลวง",
                "duty": "บัญชีอาวุธปืนหลวงรายกระบอก และการเบิกยืม-คืนปืน",
                "columns": ["ลำดับ", "ชนิดอาวุธปืน", "ขนาด", "ยี่ห้อ", "เลขทะเบียนโล่", "วันรับมอบ", "สถานะ", "ผู้ยืม/ผู้เบิก", "วันที่ยืม", "วันที่คืน", "วัตถุประสงค์", "หมายเหตุ", "Updated_At"]
            }
        }

    def connect(self, retries=3):
        """Connect to Google Sheets with Auto-Retry Logic."""
        import time
        for i in range(retries):
            try:
                creds = Credentials.from_service_account_file(self.credentials_path, scopes=self.scopes)
                self.gc = gspread.authorize(creds)
                
                if not self.gc:
                    raise ConnectionError("gspread.authorize returned None")

                self.spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
                
                # --- โครงสร้างชีทหลัก (Sheet Structures - Hardcoded for Clarity) ---
                
                # --- โครงสร้างชีทหลัก (Sheet Structures - Hardcoded for Clarity) ---
                
                # 📝 ชีทข้อสั่งการ (Orders): [รายละเอียด, ผู้สั่งการ, กำหนดส่ง, สถานะ, ความเร่งด่วน, หมายเหตุ, วันที่บันทึก]
                self.orders_sheet = self._get_or_create_sheet("Orders", ["Detail", "Commander", "Deadline", "Status", "Urgency", "Note", "Timestamp"])
                
                # 👥 ชีทบุคคล (Contacts): [ยศ-ชื่อ, ตำแหน่ง, นามเรียกขาน, เบอร์โทร, สังกัด, เลขบัตร, วันเกิด, ธนาคาร, เลขบัญชี, หมายเหตุ, อัปเดตล่าสุด]
                self.contacts_sheet = self._get_or_create_sheet("Contacts", ["Name", "Position", "Callsign", "Phone", "Agency", "ID Card", "Birthday", "Bank", "Account", "Note", "Updated_At"])
                
                # ⏰ ชีทแจ้งเตือน (Reminders): [หัวข้อ, เนื้อหา, เวลาแจ้งเตือน, สถานะ, วันที่สร้าง]
                self.reminders_sheet = self._get_or_create_sheet("Reminders", ["Topic", "Content", "Reminder_Time", "Status", "Created_At"])
                
                # 🚗 ชีทยานพาหนะ (Vehicles): [ID, อ้างอิง, หน่วยงาน, ประเภท1, ประเภท2, เลขโล่, ทะเบียน, ยี่ห้อ, เลขแชสซี, เครื่องยนต์, ผู้ใช้, การซ่อม, ผู้บันทึก, GFMIS, วันคำนวณ, เลขไมล์, วันที่ได้มา, สถานะ]
                self.vehicles_sheet = self._get_or_create_sheet("Vehicles", ["ID", "Ref", "Dept", "Type1", "Type2", "Shield", "Plate", "Brand", "Chassis", "Engine", "User", "Repair", "Recorder", "GFMIS", "DateCalc", "Mileage", "DateGet", "Status"])
                
                # 💰 ชีทงบประมาณ (Budgets): [รายการ, งบประมาณ, เบิกจ่ายแล้ว, คงเหลือ, หมายเหตุ]
                self.budgets_sheet = self._get_or_create_sheet("Budgets", ["Item", "Budget", "Spent", "Balance", "Note"])
                
                # 👮 ชีทผู้บังคับบัญชา (Commanders): [ชื่อ, ตำแหน่ง, เบอร์โทร, สังกัด, เลขบัตร, วันเกิด, ธนาคาร, เลขบัญชี, หมายเหตุ, อัปเดตล่าสุด]
                self.commanders_sheet = self._get_or_create_sheet("Commanders", ["Name", "Position", "Phone", "Agency", "ID Card", "Birthday", "Bank", "Account", "Note", "Updated_At"])
                
                # 📅 ชีทเวร (DutyRoster): [วันที่, เวลา, ชื่อ, นามเรียกขาน, เบอร์โทร, สถานที่, อัปเดตล่าสุด]
                self.duty_roster_sheet = self._get_or_create_sheet("DutyRoster", ["Date", "Time", "Name", "Callsign", "Phone", "Location", "Updated_At"])
                
                # 🛡️ ชีทยุทธภัณฑ์ (Equipment): [หมวดหมู่, รายการ, ทั้งหมด, ใช้งานอยู่, ในคลัง, หมายเหตุ, อัปเดตล่าสุด]
                self.equipment_sheet = self._get_or_create_sheet("Equipment", ["Category", "Item", "Total", "InUse", "InStock", "Note", "Updated_At"])
                
                # (Arrests sheet removed)
                
                # 🔫 ชีทบัญชีอาวุธปืน (FirearmRegistry): [ลำดับ, ชนิด, ขนาด, ยี่ห้อ, ทะเบียนโล่, วันรับ, สถานะ, ผู้ยืม, วันที่ยืม, วันที่คืน, วัตถุประสงค์, หมายเหตุ, อัปเดตล่าสุด]
                self.firearm_registry_sheet = self._get_or_create_sheet("FirearmRegistry", ["ลำดับ", "ชนิดอาวุธปืน", "ขนาด", "ยี่ห้อ", "เลขทะเบียนโล่", "วันรับมอบ", "สถานะ", "ผู้ยืม/ผู้เบิก", "วันที่ยืม", "วันที่คืน", "วัตถุประสงค์", "หมายเหตุ", "Updated_At"])
                
                # 💰 Reference Sheets (for logical validation)
                self.salary_ref_sheet = self._get_or_create_sheet("Salary_Ref", ["Rank", "Level", "Step", "Salary"])
                self.rank_mapping_sheet = self._get_or_create_sheet("Rank_Mapping", ["Source", "Destination"])
                
                logger.info("✅ Successfully connected to Google Sheets.")
                return True
            except Exception as e:
                wait_time = (i + 1) * 2
                logger.warning(f"⚠️ Connect attempt {i+1} failed: {e}. Retrying in {wait_time}s...")
                if i < retries - 1:
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Failed to connect after {retries} attempts.")
                    return False

    def validate_profile_data(self, sheet_type: str, data: Dict) -> Dict:
        """Strict Validation: Checks extracted data against hardcoded profiles."""
        profile = getattr(self, 'SHEET_PROFILES', {}).get(sheet_type)
        if not profile:
            return {"valid": True, "missing": [], "critical_missing": False}
        
        columns = profile.get("columns", [])
        # Define critical fields that MUST be present for a record to be meaningful
        critical_fields = {
            "Orders": ["Detail"],
            "Contacts": ["Name", "Phone"],
            "Vehicles": ["Shield", "Plate"],
            "Equipment": ["Item", "Total"]
        }
        
        required = critical_fields.get(sheet_type, [])
        missing = []
        critical_missing = False
        
        # Check for missing values in the data dict
        for col in required:
            val = data.get(col)
            if not val or val in ["-", "", "ไม่ระบุ", "None"]:
                missing.append(col)
                critical_missing = True
        
        return {
            "valid": not critical_missing,
            "missing": missing,
            "critical_missing": critical_missing,
            "sheet_name": sheet_type
        }

    def _load_salary_ref_data(self):
        """Loads reference salary data into memory for fast lookup."""
        if not self.salary_ref_sheet: return
        try:
            raw_data_untouch: Any = self.salary_ref_sheet.get_all_values()
            raw_data: List[Any] = cast(List[Any], raw_data_untouch) if isinstance(raw_data_untouch, list) else []
            if len(raw_data) < 2: return
            
            headers_row: Any = raw_data[0]
            if not isinstance(headers_row, list): return
            headers: List[str] = [self._normalize(str(h)) for h in headers_row]
            
            self._current_ref_data = {}
            for i in range(len(raw_data)):
                if i == 0: continue
                row: Any = raw_data[i]
                if not isinstance(row, list) or not row: continue
                step = str(row[0])
                headers_list: List[Any] = cast(List[Any], headers)
                for j in range(len(row)):
                    if j == 0: continue
                    if j < len(headers_list):
                        lvl = headers_list[j]
                        salary = row[j]
                        if salary and salary != "-":
                            # Key format: level_step (e.g., s1_35)
                            key = f"{lvl}_{step}"
                            self._current_ref_data[key] = salary
        except Exception as e:
            logger.error(f"Load salary ref error: {e}")

        # --- Also pre-load SalaryHistory Headers for dynamic display ---
        if self.salary_sheet:
            try:
                s_rows = self.salary_sheet.get_all_values()
                if s_rows:
                    self._salary_headers = [h.strip() for h in s_rows[0]]
            except:
                self._salary_headers = ["Name", "ระดับ", "ขั้น", "เงินเดือน", "ประเมินสรุป", "Note"]

    def _load_rank_mapping(self):
        """Loads rank to level mapping for intelligent validation."""
        self._rank_map = {}
        if not self.rank_mapping_sheet: return
        try:
            raw_data: Any = self.rank_mapping_sheet.get_all_values()
            data_list: List[Any] = cast(List[Any], raw_data) if isinstance(raw_data, list) else []
            if len(data_list) < 2: return
            for i in range(len(data_list)):
                if i == 0: continue
                row: Any = data_list[i]
                if isinstance(row, list) and len(row) >= 2:
                    rank_norm = self._normalize_light(str(row[0]))
                    level_norm = self._normalize(str(row[1]))
                    if rank_norm and level_norm:
                        self._rank_map[rank_norm] = level_norm
        except Exception as e:
            logger.error(f"Load rank mapping error: {e}")

    def _get_or_create_sheet(self, title: str, headers: List[str]):
        try:
            return self.spreadsheet.worksheet(title)
        except:
            ws = self.spreadsheet.add_worksheet(title=title, rows="1000", cols=str(len(headers)))
            ws.append_row(headers)
            return ws

    def _normalize(self, text: str) -> str:
        """Robust Thai normalization for search and indexing."""
        if not text: return ""
        
        # 1. Normalize Unicode (NFKC) for consistent Thai characters
        t = unicodedata.normalize('NFKC', str(text)).lower()
        
        # 2. Convert Thai digits to Arabic digits
        thai_digits = "๐๑๒๓๔๕๖๗๘๙"
        arabic_digits = "0123456789"
        for th, ar in zip(thai_digits, arabic_digits):
            t = t.replace(th, ar)
            
        # 3. Remove invisible characters (Zero-width spaces, etc.)
        t = re.sub(r'[\u200B-\u200D\uFEFF]', '', t)
        
        # 4. Fix common Thai typing errors: double vowels/tones
        # e.g., Sarah U + Sarah U (ุุ) -> Sarah U (ุ)
        t = re.sub(r'([ุูิีึืัํ])\1+', r'\1', t)
        
        # 5. Remove rank prefixes (using pre-defined RANK_PATTERN)
        t = self.RANK_PATTERN.sub('', t)
        
        # 6. Final clean-up: remove all spaces and specific punctuation for strict matching
        return self.CLEAN_PATTERN.sub('', t).strip()

    def _normalize_light(self, text: str) -> str:
        """Light normalization: Converts Thai digits, lowers case, restores NFKC, but PRESERVES ranks."""
        if not text: return ""
        t = unicodedata.normalize('NFKC', str(text)).lower()
        thai_digits = "๐๑๒๓๔๕๖๗๘๙"
        arabic_digits = "0123456789"
        for th, ar in zip(thai_digits, arabic_digits):
            t = t.replace(th, ar)
        return t.strip()

    def _enrich_contact_info(self, name: str) -> Dict:
        """Finds full Rank+Name+Surname and Phone from Contacts if only partial name is given."""
        if not self.contacts_sheet or not name or len(name) < 2:
            return {"name": name, "phone": "-"}
        
        try:
            norm_query = self._normalize(name)
            # Try commanders first for high-ranking officers
            for sheet in [self.commanders_sheet, self.contacts_sheet]:
                if not sheet: continue
                raw_data: Any = sheet.get_all_values()
                data: List[Any] = cast(List[Any], raw_data) if isinstance(raw_data, list) else []
                for i in range(len(data)):
                    if i == 0: continue
                    r: Any = data[i]
                    if isinstance(r, (list, tuple)) and len(r) > 0:
                        row_list: List[Any] = cast(List[Any], r)
                        full_name = str(row_list[0])
                        phone_idx = 3
                        row_phone = str(row_list[phone_idx]) if len(row_list) > phone_idx else "-"
                        if norm_query in self._normalize(full_name):
                            return {"name": full_name, "phone": row_phone}
            return {"name": name, "phone": "-"}
        except:
            return {"name": name, "phone": "-"}

    def search_all(self, query: str):
        """Ultra-Fast Bulletproof Search with Scoring and Ranking."""
        if not query: return "❌ กรุณาใส่คำค้นหา"
        
        query_lc = query.lower().strip()
        
        # 📊 Load Reference Data for Auto-Check & Rank Validation
        self._load_salary_ref_data()
        self._load_rank_mapping()
        
        # 📊 Special Case: Unit Salary Report
        unit_report_keywords = ["รายงานเงินเดือน", "สรุปพิจารณา", "บัญชีรายชื่อ", "บัญชีพิจารณา"]
        if any(k in query_lc for k in unit_report_keywords):
            # Extract unit name (e.g., สภ.มหาราช)
            unit_name = query_lc
            for k in unit_report_keywords: unit_name = unit_name.replace(k, "")
            unit_name = unit_name.strip()
            if not unit_name: return "⚠️ กรุณาระบุชื่อหน่วย (เช่น: รายงานเงินเดือน สภ.มหาราช)"
            return self.get_unit_salary_report(unit_name)

        # 📊 Special Case: Official Salary Step Table Request
        ref_keywords = ["แท่งเงินเดือน", "ตารางเงินเดือน", "บัญชีเงินเดือน", "อัตราเงินเดือน", "ขบวนการเงินเดือน"]
        if any(k in query_lc for k in ref_keywords):
            return self._format_salary_ref_table()

        # 🔫 Special Case: Firearm Registry Summary Report
        firearm_report_keywords = ["บัญชีปืน", "สรุปอาวุธปืน", "รายงานอาวุธปืน", "สถานะปืน", "บัญชียืมปืน", "สรุปปืน", "ปืนทั้งหมด", "รายการปืน", "บัญชีอาวุธ"]
        if any(k in query_lc for k in firearm_report_keywords):
            return self.get_firearm_registry_summary()

        total_found: int = 0
        
        # Priority sheets list
        search_targets = [
            (self.commanders_sheet, "🎖️", "Commanders"),
            (self.duty_roster_sheet, "🗓️", "DutyRoster"),
            (self.contacts_sheet, "👤", "Contacts"),
            (self.vehicles_sheet, "🚗", "Vehicles"),
            (self.orders_sheet, "👮", "Orders"),
            (self.budgets_sheet, "💰", "Budgets"),
            (self.equipment_sheet, "🛡️", "Equipment"),
            (self.firearm_registry_sheet, "🔫", "FirearmRegistry"),
        ]

        try:
            # 1. Detect Intents and Target Sheets using Registry
            active_categories, target_sheet_names = self._detect_query_intent(query_lc)
            
            if active_categories:
                search_targets = [t for t in search_targets if t[2] in target_sheet_names]

            # 2. Key Cleaning & Smart Date Extraction
            noise_words = ["จด", "บันทึก", "หา", "ค้น", "เลขบัตร", "บัตร", "ของ", "ใคร", "แจ้ง", "เตือน", "ปี", "พ.ศ.", "วันที่"]
            clean_keywords = [k for k in query_lc.split() if (len(k) > 1 or k.isdigit()) and k not in noise_words]
            if not clean_keywords: clean_keywords = [k for k in query_lc.split() if k not in ["คือ", "ของ", "ใคร"]]
            
            # 🎯 Smart Alias Keyword Expansion (The "Synonym" Parser)
            commander_names = ["สมชาย", "แจ้งธรรมมา", "พ.ต.อ.สมชาย"]
            if any(name in query_lc for name in commander_names) or "ผกก" in query_lc:
                # If searching for the man or the rank, ensure BOTH are in keywords
                if "ผกก" not in " ".join(clean_keywords): clean_keywords.append("ผกก")
                if "สมชาย" not in " ".join(clean_keywords): clean_keywords.append("สมชาย")
            
            query_norm = self._normalize(" ".join(clean_keywords))
            
            # 🎯 Smart Brain: Pre-parse target date (The "Today" Parser)
            target_date = self._parse_thai_date(query_lc)
            if not target_date:
                target_date = self._parse_thai_date(" ".join(clean_keywords))
            
            # 🎯 Smart Default: If asking for 'duty' or 'order' without a date, assume Today
            if not target_date and any(cat in active_categories for cat in ["duty", "order"]):
                target_date = datetime.now()
            
            query_days = [k for k in clean_keywords if k.isdigit() and 1 <= int(k) <= 31]
            scored_results = []

            # 3. Search Loop
            for sheet, icon, title in search_targets:
                if not sheet: continue
                try:
                    data = sheet.get_all_values()
                    raw_rows: List[Any] = data # from prev cast/check
                    rows: List[Any] = []
                    for i in range(len(raw_rows)):
                        if i == 0: continue
                        if title in ["Budgets", "ExpenditureStatus"] and i == 1: continue
                        rows.append(raw_rows[i])

                    # Pre-fetch Salary data if searching person
                    salary_data: Dict[str, Any] = {}
                    if title in ["Contacts", "Commanders"]:
                        if self.salary_sheet:
                            try:
                                raw_s_data: Any = self.salary_sheet.get_all_values()
                                s_rows_all: List[Any] = cast(List[Any], raw_s_data) if isinstance(raw_s_data, list) else []
                                if s_rows_all:
                                    for i in range(len(s_rows_all)):
                                        if i == 0: continue
                                        sr: Any = s_rows_all[i]
                                        if isinstance(sr, list) and len(sr) > 0 and sr[0]:
                                              sr_list: List[Any] = cast(List[Any], sr)
                                              sr_tail: List[Any] = [sr_list[k] for k in range(1, len(sr_list))]
                                              salary_data[self._normalize(str(sr_list[0]))] = sr_tail
                            except: pass

                    for r_untouch in rows:
                        r: List[Any] = cast(List[Any], r_untouch)
                        if not any(r): continue
                        row_str = " ".join([str(x) for x in r if x]).lower()
                        # ... rest of loop unchanged ...
                        row_norm = self._normalize(row_str)
                        
                        r_first: Any = r[0] if len(r) > 0 else ""
                        date_val = str(r_first)
                        date_norm = self._normalize(date_val)
                        
                        score: int = 0
                        
                        # 🔍 CROSS-SHEET Date Check (Smart Parser)
                        is_date_mismatch = False
                        if target_date:
                            found_date_match = False
                            for col_idx, col_val in enumerate(r):
                                try:
                                    col_dt = self._parse_thai_date(str(col_val))
                                    if col_dt and col_dt.date() == cast(datetime, target_date).date():
                                        score = score + 200 # type: ignore
                                        found_date_match = True
                                        break
                                except: pass
                            
                            # If it's DutyRoster or query has strong date intent, we might be strict
                            if title == "DutyRoster" and not found_date_match:
                                is_date_mismatch = True
                        
                        if is_date_mismatch: continue
                        
                        # General Scoring
                        if query_lc in row_str: score = score + 50
                        if query_norm and query_norm in row_norm:
                            score = score + 30
                            if query_norm in date_norm: score = score + 40
                            if query_norm == date_norm: score = score + 100
                        
                        if clean_keywords:
                            kw_matches = [k for k in clean_keywords if self._normalize(k) in row_norm]
                            if len(kw_matches) == len(clean_keywords): 
                                score = score + 100 # All keywords match!
                            elif len(kw_matches) > 0: 
                                score = score + (len(kw_matches) * 20) # Partial match
                            
                            date_kw_matches = sum(1 for k in clean_keywords if self._normalize(k) in date_norm)
                            score = score + (int(date_kw_matches) * 50)

                        # --- 🔍 Name-specific Boost for Personnel ---
                        if title in ["Contacts", "Commanders"] and len(r) > 0:
                            p_name: Any = r[0]
                            name_norm = self._normalize(str(p_name))
                            # If keywords match in the name field, give major boost
                            matches_in_name = [k for k in clean_keywords if self._normalize(k) in name_norm]
                            if len(matches_in_name) == len(clean_keywords):
                                score = score + 300
                            elif len(matches_in_name) > 0:
                                score = score + (len(matches_in_name) * 50)

                        # --- 🚗 Brand/Shield Boost for Vehicles ---
                        if title == "Vehicles" and len(r) > 7:
                            brand_norm = self._normalize(r[7])  # Column 7 = ยี่ห้อ
                            shield_norm = self._normalize(r[5]) if len(r) > 5 else ""  # Column 5 = ทะเบียนโล่
                            plate_norm = self._normalize(r[6]) if len(r) > 6 else ""  # Column 6 = ทะเบียนรถ
                            type_norm = self._normalize(r[3]) if len(r) > 3 else ""  # Column 3 = ประเภทรถ
                            
                            brand_matches = [k for k in clean_keywords if self._normalize(k) in brand_norm]
                            if brand_matches:
                                score += len(brand_matches) * 100
                            shield_matches = [k for k in clean_keywords if self._normalize(k) in shield_norm]
                            if shield_matches:
                                score += 200
                            plate_matches = [k for k in clean_keywords if self._normalize(k) in plate_norm]
                            if plate_matches:
                                score += 200
                            type_matches = [k for k in clean_keywords if self._normalize(k) in type_norm]
                            if type_matches:
                                score += len(type_matches) * 50

                        # --- 🔫 Shield/Brand Boost for Firearms ---
                        if title == "FirearmRegistry" and len(r) > 4:
                            fa_brand_norm = self._normalize(r[3])  # Column 3 = ยี่ห้อ
                            fa_shield_norm = self._normalize(r[4])  # Column 4 = เลขทะเบียนโล่
                            fa_borrower_norm = self._normalize(r[7]) if len(r) > 7 else ""
                            
                            fa_brand_m = [k for k in clean_keywords if self._normalize(k) in fa_brand_norm]
                            if fa_brand_m: score += len(fa_brand_m) * 100
                            fa_shield_m = [k for k in clean_keywords if self._normalize(k) in fa_shield_norm]
                            if fa_shield_m: score += 200
                            fa_borrower_m = [k for k in clean_keywords if self._normalize(k) in fa_borrower_norm]
                            if fa_borrower_m: score += len(fa_borrower_m) * 80

                        # --- 📝 Natural Language Boost for Orders ---
                        if title == "Orders":
                            order_matches = [k for k in clean_keywords if self._normalize(k) in row_norm]
                            if order_matches:
                                score += len(order_matches) * 150 # Major boost for any relevant word in orders
                        
                        if score > 0:
                            current_total: int = total_found
                            total_found = current_total + 1
                            details = []
                            if title == "DutyRoster":
                                label = f"{r[0]} {r[1]}"
                                details = [f"👤 ชื่อ: {r[2]}", f"📟 นามเรียกขาน: {r[3]}", f"📞 เบอร์โทร: {r[4]}", f"📍 สถานที่: {r[5]}"]
                            elif title == "Contacts":
                                s_info = salary_data.get(self._normalize(str(r[0])))
                                scored_results.append({
                                    "type": "person", "sheet": title, "data": r, "salary": s_info, "score": score, "icon": "👤",
                                    "formatted": None
                                })
                                continue
                            elif title == "Commanders":
                                s_info = salary_data.get(self._normalize(str(r[0])))
                                scored_results.append({
                                    "type": "person", "sheet": title, "data": r, "salary": s_info, "score": score, "icon": "🎖️",
                                    "formatted": None
                                })
                                continue
                            elif title == "Vehicles":
                                plate = r[6] if len(r) > 6 and r[6] not in ["-", ""] else ""
                                shield = r[5] if len(r) > 5 and r[5] not in ["-", ""] else ""
                                label = f"ทะเบียน {plate}" if plate else (f"ทะเบียน {shield}" if shield else "ข้อมูลรถ")
                                
                                details = [
                                    f"🚗 ยี่ห้อ: {r[7] if len(r) > 7 else '-'}",
                                    f"📋 ประเภท: {r[3] if len(r) > 3 else '-'} ({r[4] if len(r) > 4 else '-'})",
                                    f"🛡️ ทะเบียนโล่: {shield if shield else '-'}",
                                    f"🔢 ทะเบียนรถ: {plate if plate else '-'}",
                                    f"🆔 ตัวถัง: {r[8] if len(r) > 8 else '-'}",
                                    f"⚙️ เครื่องยนต์: {r[9] if len(r) > 9 else '-'}",
                                    f"👤 หน่วยงานผู้ใช้: {r[10] if len(r) > 10 else '-'}",
                                    f"📟 เลขไมล์: {r[15] if len(r) > 15 else '-'}",
                                    f"📅 วันที่ได้มา: {r[16] if len(r) > 16 else '-'}",
                                    f"🛠️ สถานภาพ: {r[17] if len(r) > 17 else '-'}"
                                ]
                                
                                # Calculate Age
                                if len(r) > 16 and r[16] not in ["-", ""]:
                                    age_str = self._calculate_age(r[16])
                                    if age_str:
                                        details.append(f"⏳ อายุการใช้งาน: **{age_str.replace('อายุ ', '')}**")

                                scoring_formatted: str = f"{icon} **{label}**\n" + "\n".join(details) + f"\n{self.DIVIDER}"
                                scored_results.append({
                                    "type": "standard", "score": score, "formatted": scoring_formatted
                                })
                            elif title == "FirearmRegistry":
                                # Format firearm search result
                                firearm_type = str(r[1]) if len(r) > 1 else "-"
                                caliber = str(r[2]) if len(r) > 2 else "-"
                                brand = str(r[3]) if len(r) > 3 else "-"
                                shield_no = str(r[4]) if len(r) > 4 else "-"
                                date_recv = str(r[5]) if len(r) > 5 else "-"
                                status = str(r[6]) if len(r) > 6 else "-"
                                borrower = str(r[7]) if len(r) > 7 else "-"
                                borrow_date = str(r[8]) if len(r) > 8 else "-"
                                return_date = str(r[9]) if len(r) > 9 else "-"
                                purpose = str(r[10]) if len(r) > 10 else "-"
                                note = str(r[11]) if len(r) > 11 else "-"
                                
                                status_icon = "🟢" if status in ["ในคลัง", "คงคลัง", "พร้อมใช้"] else "🔴" if status in ["ยืมออก", "เบิกใช้"] else "🟡"
                                label = f"{firearm_type} ({brand} {caliber})"
                                details = [
                                    f"🔫 ชนิด: {firearm_type}",
                                    f"📏 ขนาด: {caliber}",
                                    f"🏭 ยี่ห้อ: {brand}",
                                    f"🛡️ เลขทะเบียนโล่: {shield_no}",
                                    f"📅 วันรับมอบ: {date_recv}",
                                    f"{status_icon} สถานะ: {status}",
                                    f"👤 ผู้ยืม/ผู้เบิก: {borrower}",
                                    f"📆 วันที่ยืม: {borrow_date}",
                                    f"🔄 วันที่คืน: {return_date}",
                                    f"📋 วัตถุประสงค์: {purpose}",
                                ]
                                if note and note != "-":
                                    details.append(f"📝 หมายเหตุ: {note}")
                                scoring_formatted: str = f"{icon} **{label}**\n" + "\n".join(details) + f"\n{self.DIVIDER}"
                                scored_results.append({
                                    "type": "standard", "score": score, "formatted": scoring_formatted
                                })
                            elif title == "Orders":
                                # 📝 Premium Orders Card Design
                                detail = str(r[0]) if len(r) > 0 else "-"
                                cmder = str(r[1]) if len(r) > 1 else "-"
                                deadline = str(r[2]) if len(r) > 2 else "-"
                                status = str(r[3]) if len(r) > 3 else "-"
                                urgency = str(r[4]) if len(r) > 4 else "-"
                                timestamp = str(r[6]) if len(r) > 6 else "-"
                                
                                st_icon = "🔵" if status == "Pending" else "🟢" if status == "Done" else "⚪"
                                ug_icon = "🔥" if urgency == "High" else "⚡" if urgency == "Urgent" else ""
                                
                                label = f"📝 **[ ข้อสั่งการ / ภารกิจ ]** {ug_icon}"
                                details = [
                                    f"📌 เรื่อง: **{detail}**",
                                    f"👤 ผู้สั่ง: {cmder}" if cmder != "-" else "",
                                    f"🕒 กำหนด: {deadline}" if deadline != "-" else "",
                                    f"🔘 สถานะ: {st_icon} **{status}** ({urgency})" if status != "-" else "",
                                    f"📅 บันทึกเมื่อ: _{timestamp}_" if timestamp != "-" else ""
                                ]
                                details = [d for d in details if d] # Remove empty lines
                                scoring_formatted = f"{label}\n" + "\n".join(details) + f"\n{self.DIVIDER}"
                                scored_results.append({
                                    "type": "standard", "score": score, "formatted": scoring_formatted
                                })
                            elif title == "Arrests":
                                # ⚖️ Premium Arrests Card Design
                                date_arr = str(r[0]) if len(r) > 0 else "-"
                                dept = str(r[1]) if len(r) > 1 else "-"
                                sus = str(r[2]) if len(r) > 2 else "-"
                                age = str(r[3]) if len(r) > 3 else "-"
                                charge = str(r[6]) if len(r) > 6 else "-"
                                place = str(r[8]) if len(r) > 8 else "-"
                                
                                label = f"⚖️ **สถิติจับกุม (Arrests)**"
                                details = [
                                    f"📅 วันที่จับ: {date_arr}",
                                    f"🏢 หน่วย: {dept}",
                                    f"👤 ผู้ต้องหา: **{sus}** ({age} ปี)",
                                    f"🛡️ ข้อหา: {charge}",
                                    f"📍 สถานที่: {place}"
                                ]
                                scoring_formatted = f"{label}\n" + "\n".join(details) + f"\n{self.DIVIDER}"
                                scored_results.append({
                                    "type": "standard", "score": score, "formatted": scoring_formatted
                                })
                            else:
                                label = r[0]
                                r_list: List[Any] = cast(List[Any], r)
                                r_slice: List[str] = [str(r_list[k]) for k in range(1, min(5, len(r_list))) if r_list[k]]
                                details = [f"▫️ ข้อมูล: {' '.join(r_slice)}"]
                                formatted = f"{icon} **{label}** ({title})\n" + "\n".join(details) + f"\n{self.DIVIDER}"
                                scored_results.append({
                                    "type": "standard", "score": score, "formatted": formatted
                                })

                except Exception as e:
                    logger.error(f"Sheet {title} search error: {e}")

            # 4. Final Ranking and Filtering with Strict Deduplication
            if scored_results:
                best_results: Dict[str, Tuple[int, str]] = {}
                person_results: List[Dict[str, Any]] = []
                
                for item_untouch in scored_results:
                    item: Dict[str, Any] = cast(Dict[str, Any], item_untouch)
                    if item.get("type") == "person":
                        # Deduplicate people by name
                        p_data: List[Any] = cast(List[Any], item.get('data', []))
                        if not p_data: continue
                        person_name = self._normalize(str(p_data[0]))
                        
                        existing_person = next((p for p in person_results if self._normalize(str(cast(List[Any], p.get('data', ['']))[0])) == person_name), None)
                        if existing_person:
                            current_score: int = int(item.get('score', 0))
                            existing_score: int = int(existing_person.get('score', 0))
                            if current_score > existing_score:
                                person_results.remove(existing_person)
                                person_results.append(item)
                        else:
                            person_results.append(item)
                        continue
                    
                    # Standard results
                    s_score: int = int(item.get('score', 0))
                    s_formatted: str = str(item.get('formatted', ''))
                    if s_score < 5: continue
                    
                    # 🎯 Smart Identity Key for non-person items
                    dedup_key = s_formatted
                    if "(DutyRoster)" in s_formatted:
                        try:
                            # Use a safer way to get the identity
                            raw_label = s_formatted.split("**")[1].split("(")[0].strip()
                            date_parts = raw_label.split()
                            # Only take the first 3 parts if available
                            date_parts_list: List[str] = cast(List[str], date_parts)
                            identity_parts: List[str] = [date_parts_list[k] for k in range(min(3, len(date_parts_list)))]
                            dedup_key = f"duty_{self._normalize(''.join(identity_parts))}"
                        except: pass
                    
                    if dedup_key not in best_results or s_score > best_results[dedup_key][0]:
                        best_results[dedup_key] = (s_score, s_formatted)

                # Process Person Results: Table vs Card
                final_people_output: List[str] = []
                if person_results:
                    # Sort by score
                    try:
                        person_results.sort(key=lambda x: int(x.get('score', 0)), reverse=True)
                    except: pass
                    
                    # 💡 Smart Filtering
                    if len(person_results) > 0:
                        top_item: Dict[str, Any] = person_results[0]
                        top_score_val: int = int(top_item.get('score', 0))
                        if top_score_val >= 300:
                            # Keep only results that are at least 70% as good as the top one
                            person_results = [p for p in person_results if int(p.get('score', 0)) >= top_score_val * 0.7]
                    
                    # Limit to top 3 for cards
                    top_people: List[Dict[str, Any]] = []
                    for i in range(len(person_results)):
                        if i >= 3: break
                        top_people.append(person_results[i])
                    
                    # 💡 Decision: Use Table for salary/step queries OR if multiple people found
                    salary_keywords = ["เงินเดือน", "ประเมิน", "เลื่อน", "ขั้น", "สถานะ", "สรุป", "ปี", "บัญชี", "อัตรา", "ตาราง"]
                    is_salary_query = any(k in query_lc for k in salary_keywords)
                    
                    if len(top_people) > 0:
                        # 👤 Always use Individual Cards
                        for i in range(len(top_people)):
                             p_item: Dict[str, Any] = top_people[i]
                             p_icon: str = str(p_item.get('icon', '👤'))
                             p_sheet: str = str(p_item.get('sheet', 'Contacts'))
                             p_salary: Any = p_item.get('salary', None)
                             
                             card_str = self._format_person_card(p_item['data'], p_icon, p_sheet, p_salary)
                             if i > 0: card_str = f"{self.DIVIDER}\n{card_str}"
                             final_people_output.append(card_str)

                # 🏗️ ASSEMBLE CATEGORIZED OUTPUT
                output_blocks: List[str] = []
                
                # Combine other results from best_results
                other_results: List[Tuple[int, str]] = []
                for res_val in best_results.values():
                    other_results.append(res_val)
                other_results.sort(key=lambda x: x[0], reverse=True)
                
                # A. Personnel Section
                if final_people_output:
                    output_blocks.append("🎖️ **[ รายชื่อและผู้บังคับบัญชา ]**")
                    for i in range(min(3, len(final_people_output))):
                        output_blocks.append(final_people_output[i].strip())
                
                # B. Group Other Results by Category
                cats: Dict[str, List[str]] = {"Orders": [], "Vehicles": [], "Firearms": [], "Others": []}
                for _, s_text in other_results:
                    t = s_text.strip()
                    if not t: continue
                    if "ข้อสั่งการ" in t or "ภารกิจ" in t: cats["Orders"].append(t)
                    elif "ยี่ห้อ" in t or "ทะเบียน" in t: cats["Vehicles"].append(t)
                    elif "ปืน" in t or "กระบอก" in t: cats["Firearms"].append(t)
                    else: cats["Others"].append(t)
                
                if cats["Orders"]:
                    output_blocks.append("📝 **[ ภารกิจและข้อสั่งการ ]**")
                    limited_orders = cats["Orders"][:5] # type: ignore
                    output_blocks.extend(limited_orders)
                
                if cats["Vehicles"]:
                    output_blocks.append("🚗 **[ ข้อมูลยานพาหนะ ]**")
                    limited_vehicles = cats["Vehicles"][:5] # type: ignore
                    output_blocks.extend(limited_vehicles)
                
                if cats["Firearms"]:
                    output_blocks.append("🔫 **[ บัญชีอาวุธปืน ]**")
                    limited_firearms = cats["Firearms"][:5] # type: ignore
                    output_blocks.extend(limited_firearms)
                
                if cats["Others"] and not (final_people_output or cats["Orders"] or cats["Vehicles"]):
                    output_blocks.append("📁 **[ ข้อมูลอื่นๆ ]**")
                    limited_others = cats["Others"][:5] # type: ignore
                    output_blocks.extend(limited_others)

                # Final Results Processing
                results = output_blocks
                total_found_sum = len(final_people_output) + sum(len(v) for v in cats.values())
                
                if total_found_sum > len(results) and len(results) > 1:
                    results.append(f"📌 _รวมพบ {total_found_sum} รายการ (แสดงเฉพาะส่วนที่เกี่ยวข้องที่สุด)_")
            else:
                results = []

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"❌ เกิดข้อผิดพลาดในการค้นหา: {e}"

        # 🎯 Smart Inference Fallback (The Brain)
        if not results and (target_date or "duty" in active_categories):
            if not target_date:
                for k in query_lc.split():
                    target_date = self._parse_thai_date(k if len(k) > 5 else " ".join(clean_keywords))
                    if target_date: break
            
            if target_date:
                dt_cast = cast(datetime, target_date)
                is_weekend = dt_cast.weekday() >= 5
                day_type = "📅 วันหยุดราชการ (Weekend)" if is_weekend else "🏢 วันทำงานปกติ (Weekday)"
                day_names = ["วันจันทร์", "วันอังคาร", "วันพุธ", "วันพฤหัสบดี", "วันศุกร์", "วันเสาร์", "วันอาทิตย์"]
                target_day = day_names[dt_cast.weekday()]
                try:
                    pattern_data = self.duty_patterns_sheet.get_all_values()
                    for p in pattern_data[1:]:
                        if target_day in p[0]:
                            name = p[1].strip()
                            if name in ["-", ""]:
                                results.append(f"💡 **วิเคราะห์โดยสมองบอท ({day_type})**\n━━━━━━━━━━━━━━━━━━\n🗓️ วันที่: {dt_cast.strftime('%d/%m/%Y')} ({target_day})\n⚠️ **ยังไม่มีการระบุชื่อเจ้าหน้าที่ประจำวันนี้ในตารางแม่แบบ**\nℹ️ ท่านสามารถไประบุชื่อในชีท DutyPatterns ได้เลยครับ")
                                break
                                
                            callsign = p[2] if len(p) > 2 and p[2] != "-" else "-"
                            phone = p[3] if len(p) > 3 and p[3] != "-" else "-"
                            
                            if phone == "-" or callsign == "-":
                                enriched = self._enrich_contact_info(name)
                                if phone == "-": phone = enriched.get('phone', "-")
                                name = enriched.get('name', name)

                            results.append(f"💡 **วิเคราะห์โดยสมองบอท ({day_type})**\n━━━━━━━━━━━━━━━━━━\n🗓️ วันที่: {dt_cast.strftime('%d/%m/%Y')} ({target_day})\n👤 ชื่อ: {name}\n📟 นามเรียกขาน: {callsign}\n📞 เบอร์โทร: {phone}\nℹ️ *ผลลัพธ์นี้มาจากการคำนวณวันในสัปดาห์ เนื่องจากไม่พบการระบุชื่อรายวัน*")
                            break
                except: pass

        if not results: return "ℹ️ ไม่พบข้อมูลที่ตรงกับคำค้นหาของคุณ"
        
        return "\n\n".join(results)

    def get_all_contacts(self) -> List[Dict]:
        """Fetches all contacts as list of dictionaries."""
        if not self.contacts_sheet: return []
        try:
            raw_data: Any = self.contacts_sheet.get_all_values()
            data: List[List[Any]] = cast(List[List[Any]], raw_data)
            if len(data) < 2: return []
            headers = data[0]
            results = []
            data_rows: List[List[Any]] = [cast(List[Any], data[k]) for k in range(1, len(data))]
            for r_raw in data_rows:
                r: List[Any] = cast(List[Any], r_raw)
                # Map to consistent dictionary keys expected by handlers
                contact: Dict[str, Any] = {
                    'name': r[0] if len(r) > 0 else "-",
                    'pos': r[1] if len(r) > 1 else "-",
                    'callsign': r[2] if len(r) > 2 else "-",
                    'phone': r[3] if len(r) > 3 else "-",
                    'agency': r[4] if len(r) > 4 else "-",
                    'id': r[5] if len(r) > 5 else "-",
                    'birth': r[6] if len(r) > 6 else "-",
                    'bank': r[7] if len(r) > 7 else "-",
                    'acc': r[8] if len(r) > 8 else "-",
                    'note': r[9] if len(r) > 9 else "-",
                    'updated': r[10] if len(r) > 10 else "-"
                }
                results.append(contact)
            return results
        except:
            return []


    def upsert_contacts_bulk(self, bulk_data: List[List]):
        """Fast Bulk Upsert for Contacts."""
        return self._upsert_bulk_generic(self.contacts_sheet, bulk_data)

    def upsert_commanders_bulk(self, bulk_data: List[List]):
        """Fast Bulk Upsert for Commanders."""
        return self._upsert_bulk_generic(self.commanders_sheet, bulk_data)

    def upsert_vehicles_bulk(self, bulk_data: List[List]):
        """Fast Bulk Upsert for Vehicles."""
        return self._upsert_bulk_generic(self.vehicles_sheet, bulk_data)

    def upsert_duty_roster_bulk(self, bulk_data: List[List]):
        """Fast Bulk Upsert for Duty Roster. Key = Date + Time."""
        if not self.duty_roster_sheet: return 0
        try:
            ws = self.duty_roster_sheet
            all_rows = ws.get_all_values()
            existing_map = {}
            if len(all_rows) > 1:
                for i, row in enumerate(all_rows[1:], start=2):
                    if len(row) >= 2:
                        # Key = Date + Time
                        key = self._normalize(f"{row[0]}{row[1]}")
                        existing_map[key] = (i, row)
            
            new_rows = []
            for row in bulk_data:
                key = self._normalize(f"{row[0]}{row[1]}")
                if key in existing_map:
                    idx, old_row = existing_map[key]
                    updated = [new if new not in ["-", "", None] else old 
                               for new, old in zip(row, old_row)]
                    ws.update(values=[updated], range_name=f"A{idx}")
                else:
                    new_rows.append(row)
            
            if new_rows:
                ws.append_rows(new_rows)
            return len(bulk_data)
        except Exception as e:
            logger.error(f"Duty Roster upsert error: {e}")
            return 0

    def upsert_duty_pattern_bulk(self, bulk_data: List[List]):
        """Updates recurring duty patterns. Key = Day (column 0)."""
        if not self.duty_patterns_sheet: return 0
        return self._upsert_bulk_generic(self.duty_patterns_sheet, bulk_data)

    def upsert_equipment_bulk(self, bulk_data: List[List]):
        """Bulk Upsert for Equipment. Key = Category + Item (columns 0+1)."""
        if not self.equipment_sheet: return 0
        try:
            all_rows = self.equipment_sheet.get_all_values()
            existing_map = {}
            if len(all_rows) > 1:
                for i, row in enumerate(all_rows[1:], start=2):
                    if row and len(row) >= 2 and row[0]:
                        key = self._normalize(row[0]) + "::" + self._normalize(row[1])
                        existing_map[key] = (i, row)

            new_rows: List[Any] = []
            updated_keys: List[str] = []
            for row_data in bulk_data:
                key = self._normalize(row_data[0]) + "::" + self._normalize(row_data[1])
                if key in existing_map:
                    idx, existing_row = existing_map[key]
                    updated = [new if new not in ["-", "", None] else old
                               for new, old in zip(row_data, existing_row)]
                    self.equipment_sheet.update(values=[updated], range_name=f"A{idx}")
                    updated_keys.append(key)
                else:
                    new_rows.append(row_data)

            if new_rows:
                self.equipment_sheet.append_rows(new_rows)

            return len(bulk_data)
        except Exception as e:
            logger.error(f"Equipment upsert error: {e}")
            return 0

    def _upsert_bulk_generic(self, sheet, bulk_data: List[List]):
        """Internal generic helper for bulk upserts."""
        if not sheet: return 0
        try:
            # 1. Fetch ALL existing data once
            all_rows = sheet.get_all_values()
            existing_map = {} # norm_name -> row_index (1-indexed)
            
            if len(all_rows) > 1:
                for i, row in enumerate(all_rows[1:], start=2):
                    if row and row[0]:
                        norm_name = self._normalize(row[0])
                        existing_map[norm_name] = (i, row)

            new_rows_g: List[Any] = []
            updated_keys_g: List[str] = []
            
            # 2. Match and Prepare
            for row_data in bulk_data:
                norm_name = self._normalize(row_data[0])
                if norm_name in existing_map:
                    # Update Existing Row
                    idx, existing_row = existing_map[norm_name]
                    updated = [new if new not in ["-", "", None] else old 
                               for new, old in zip(row_data, existing_row)]
                    sheet.update(values=[updated], range_name=f"A{idx}")
                    updated_keys_g.append(norm_name)
                else:
                    new_rows_g.append(row_data)
            
            # 3. Batch Append New Rows
            if new_rows_g:
                sheet.append_rows(new_rows_g)
            
            return len(bulk_data)
        except Exception as e:
            logger.error(f"Bulk upsert error: {e}")
            return 0

    def append_arrests_bulk(self, bulk_data: List[List]):
        """Fast Bulk Append for Arrests."""
        if not self.arrests_sheet or not bulk_data: return 0
        try:
            self.arrests_sheet.append_rows(bulk_data)
            return len(bulk_data)
        except Exception as e:
            logger.error(f"Arrests append error: {e}")
            return 0

    def append_contact(self, row_data: list):
        if not self.contacts_sheet: return False
        try:
            # Simple deduplication (Check Name)
            all_names = self.contacts_sheet.col_values(1)
            new_name_norm = self._normalize(row_data[0])
            
            for i, name in enumerate(all_names[1:], start=2):
                if self._normalize(name) == new_name_norm:
                    # Update row (overwrite empty/ - with new data)
                    existing = self.contacts_sheet.row_values(i)
                    updated = [new if new not in ["-", ""] else old for new, old in zip(row_data, existing)]
                    self.contacts_sheet.update(values=[updated], range_name=f"A{i}")
                    return True
            
            self.contacts_sheet.append_row(row_data)
            return True
        except: return False

    def _parse_thai_date(self, date_str: str):
        """Ultra-Robust Thai Date Parser with Relative Date Support."""
        if not date_str or date_str in ["-", ""]: return None
        now = datetime.now()
        
        # 🎯 Step 0: Handle Relative Dates
        rel_map = {
            "วันนี้": now,
            "พรุ่งนี้": now + timedelta(days=1),
            "เมื่อวาน": now - timedelta(days=1),
            "เมื่อวานนี้": now - timedelta(days=1)
        }
        for k, v in rel_map.items():
            if k in date_str: return v

        try:
            # 🎯 Step 1: Normalize (handles Thai digits -> Arabic digits)
            clean_str = self._normalize_light(date_str).replace(" ", "")
            month_map = {
                'มค': 1, 'กพ': 2, 'มีค': 3, 'เมย': 4, 'พค': 5, 'มิย': 6,
                'กค': 7, 'สค': 8, 'กย': 9, 'ตค': 10, 'พย': 11, 'ธค': 12,
                'มกราคม': 1, 'กุมภาพันธ์': 2, 'มีนาคม': 3, 'เมษายน': 4, 'พฤษภาคม': 5, 'มิถุนายน': 6,
                'กรกฎาคม': 7, 'สิงหาคม': 8, 'กันยายน': 9, 'ตุลาคม': 10, 'พฤศจิกายน': 11, 'ธันวาคม': 12
            }
            
            import re
            match = re.search(r'(\d+)([^\d]+)(\d+)', clean_str)
            if not match: 
                # Try handle "21 กองพล" or simple fragments
                match_simple = re.search(r'(\d+)', clean_str)
                if match_simple and len(clean_str) < 5: # Just a day number
                    day = int(match_simple.group(1))
                    return datetime(now.year, now.month, day)
                return None
            
            d_str, m_str, y_str = match.groups()
            day = int(d_str)
            
            m_clean = re.sub(r'[\.\s\d]', '', m_str)
            month = 1
            for k, v in month_map.items():
                if k in m_clean:
                    month = v
                    break
            
            year_val = int(y_str)
            full_year_be = year_val + 2500 if year_val < 100 else year_val
            
            return datetime(full_year_be - 543, month, day)
        except Exception as e:
            logger.debug(f"Date parse fail ({date_str}): {e}")
            return None

    def get_vehicle_summary(self):
        """Strategic Report: Overview of all police vehicles with Age Analysis."""
        if not self.vehicles_sheet: return "❌ ไม่พบฐานข้อมูลยานพาหนะ"
        try:
            data = self.vehicles_sheet.get_all_values()
            if len(data) < 2: return "✅ ระบบยังไม่มีข้อมูลรถที่บันทึกไว้ครับ"
            
            total = len(data) - 1
            stats = {} # Status -> count
            depts = {} # Dept -> count
            over_8_years = 0
            now = datetime.now()

            for r_raw2 in data[1:]:
                r2: List[Any] = cast(List[Any], r_raw2)
                # Status: col 18 (index 17)
                status = r2[17] if len(r2) > 17 and str(r2[17]).strip() else "ไม่ระบุสถานะ"
                stats[status] = stats.get(status, 0) + 1
                
                # Dept: col 3 (index 2)
                dept = r2[2] if len(r2) > 2 and str(r2[2]).strip() else "ไม่ระบุหน่วย"
                depts[dept] = depts.get(dept, 0) + 1
                
                # Age Analysis: col 17 (index 16) "วันที่ได้มา"
                acq_date = self._parse_thai_date(str(r2[16])) if len(r2) > 16 else None
                if acq_date:
                    age = (now - acq_date).days / 365.25
                    if age >= 8:
                        over_8_years += 1
                r2 = r2  # consumed
            
            report = f"📊 **สรุปสถิตยานพาหนะ (รวม {total} คัน)**\n{self.DIVIDER}\n"
            
            report += f"🚨 **วิเคราะห์อายุรถ:**\n"
            report += f"• อายุเกิน 8 ปี: **{over_8_years} คัน** (ควรพิจารณาจำหน่าย)\n"
            report += f"• อายุไม่เกิน 8 ปี: {total - over_8_years} คัน\n\n"

            report += "📍 **แยกตามหน่วยงาน:**\n"
            for d, c in sorted(depts.items(), key=lambda x: x[1], reverse=True):
                report += f"• {d}: {c} คัน\n"
                
            report += f"\n🛠 **สถานะความพร้อม:**\n"
            for s, c in stats.items():
                icon = "✅" if "ใช้งาน" in s or "ปกติ" in s else "⚠️" if "ซ่อม" in s else "⚪️"
                report += f"{icon} {s}: {c} คัน\n"
            return report
        except Exception as e:
            return f"❌ ข้อผิดพลาดในการสรุป: {e}"

    def _calculate_age(self, birthday_str: str) -> str:
        """Calculates precise age (Years, Months, Days) from a Thai date string."""
        if not birthday_str or birthday_str in ["-", ""]:
            return ""
        try:
            birth_date = self._parse_thai_date(birthday_str)
            if not birth_date:
                return ""
            now = datetime.now()
            
            years = now.year - birth_date.year
            months = now.month - birth_date.month
            days = now.day - birth_date.day
            
            if days < 0:
                months -= 1
                # Get days in previous month
                prev_month = (now.month - 1) if now.month > 1 else 12
                prev_year = now.year if now.month > 1 else now.year - 1
                days_in_prev = calendar.monthrange(prev_year, prev_month)[1]
                days += days_in_prev
                
            if months < 0:
                years -= 1
                months += 12
                
            parts = []
            if years > 0: parts.append(f"{years} ปี")
            if months > 0: parts.append(f"{months} เดือน")
            if days > 0: parts.append(f"{days} วัน")
            
            return "อายุ " + " ".join(parts) if parts else "0 วัน"
        except:
            return ""

    def _calculate_retirement(self, birthday_str: str) -> str:
        """Calculates Thai government retirement date (Sept 30 of age 60/61)."""
        if not birthday_str or birthday_str in ["-", ""]:
            return ""
        try:
            birth_date = self._parse_thai_date(birthday_str)
            if not birth_date:
                return ""
            
            # Retirement logic: Sept 30 of the year reaching 60
            # If born after Sept 30, retirement is next year's Sept 30
            retire_year = birth_date.year + 60
            if (birth_date.month > 9) or (birth_date.month == 9 and birth_date.day > 30):
                retire_year += 1
            
            retire_date = datetime(retire_year, 9, 30)
            retire_be = retire_year + 543
            
            now = datetime.now()
            remaining_years = retire_year - now.year
            if now.month > 9 or (now.month == 9 and now.day > 30):
                remaining_years -= 1
                
            status = f"เกษียณ 30 ก.ย. {retire_be}"
            if remaining_years > 0:
                status += f" (อีก {remaining_years} ปี)"
            elif remaining_years == 0:
                status += " (เกษียณปีนี้)"
            else:
                status += " (เกษียณแล้ว)"
                
            return status
        except:
            return ""

    def _format_person_card(self, r: Any, icon: str, title: str, salary_info: Optional[List[Any]] = None) -> str:
        """Standardized Form-style display for police officers."""
        rl: List[Any] = cast(List[Any], r)
        
        name, pos, call, phone, unit, id_card, birth, bank, acc, note = ("-", "-", "-", "-", "-", "-", "-", "-", "-", "-")
        
        if title == "Contacts":
            # Contacts: ["Name", "Position", "Callsign", "Phone", "Agency", "ID Card", "Birthday", "Bank", "Account", "Note", "Updated_At"]
            if len(rl) > 0: name = str(rl[0])
            if len(rl) > 1: pos = str(rl[1])
            if len(rl) > 2: call = str(rl[2])
            if len(rl) > 3: phone = str(rl[3])
            if len(rl) > 4: unit = str(rl[4])
            if len(rl) > 5: id_card = str(rl[5])
            if len(rl) > 6: birth = str(rl[6])
            if len(rl) > 7: bank = str(rl[7])
            if len(rl) > 8: acc = str(rl[8])
            if len(rl) > 9: note = str(rl[9])
        else: # Commanders
            # Commanders: ["Name", "Position", "Phone", "Agency", "ID Card", "Birthday", "Bank", "Account", "Note", "Updated_At"]
            if len(rl) > 0: name = str(rl[0])
            if len(rl) > 1: pos = str(rl[1])
            if len(rl) > 2: phone = str(rl[2])
            if len(rl) > 3: unit = str(rl[3])
            if len(rl) > 4: id_card = str(rl[4])
            if len(rl) > 5: birth = str(rl[5])
            if len(rl) > 6: bank = str(rl[6])
            if len(rl) > 7: acc = str(rl[7])
            if len(rl) > 8: note = str(rl[8])
            call = "-"

        age_detail = self._calculate_age(birth)
        retirement_detail = self._calculate_retirement(birth)
        
        # Parse Salary Info DYNAMICALLY if available
        lvl, step, sal, eval_history, sal_status, lvl_warning = ("-", "-", "-", "-", "", "")
        dynamic_salary_fields = []
        
        if salary_info and hasattr(self, '_salary_headers') and self._salary_headers:
            all_headers: List[Any] = cast(List[Any], self._salary_headers)
            headers: List[str] = []
            for i in range(len(all_headers)):
                if i == 0: continue # Skip 'Name'
                headers.append(str(all_headers[i]))
                
            for idx in range(len(headers)):
                h = headers[idx]
                val = str(salary_info[idx]) if idx < len(salary_info) else "-"
                norm_h = self._normalize(h)
                if norm_h in ["ระดับ"]: lvl = val
                elif norm_h in ["ขั้น"]: step = val
                elif norm_h in ["เงินเดือน"]: sal = val
                elif norm_h in ["ประเมินสรุป", "ผลการประเมิน"]: eval_history = val
                else:
                    if val and val != "-":
                        dynamic_salary_fields.append(f"▫️ {h}: **{val}**")

            # --- 🔍 Rank-to-Level Consistency Check ---
            if lvl != "-" and hasattr(self, '_rank_map'):
                # Extract rank keywords from name using light normalization
                found_rank_lvl = None
                name_light = self._normalize_light(name).replace(" ", "")
                rank_map_dict: Dict[str, str] = cast(Dict[str, str], self._rank_map)
                for r_name, r_lvl in rank_map_dict.items():
                    if r_name in name_light:
                        found_rank_lvl = r_lvl
                        break
                
                if found_rank_lvl and self._normalize(lvl) != found_rank_lvl:
                    lvl_warning = f" ⚠️ *(ยศนี้ควรเป็น {found_rank_lvl})*"

            # --- 🔍 Salary Auto-Check Logic ---
            official_sal = "-"
            if lvl != "-" and step != "-" and hasattr(self, '_current_ref_data'):
                norm_lvl = self._normalize(lvl)
                key = f"{norm_lvl}_{step}"
                ref_data: Dict[str, str] = cast(Dict[str, str], self._current_ref_data)
                official_sal = ref_data.get(key, "-")
                
                if official_sal != "-" and sal != "-":
                    def _clean(v): return str(v).replace(',', '').replace('฿', '').replace(' ', '').strip()
                    try:
                        act_v = float(_clean(sal))
                        off_v = float(_clean(official_sal))
                        if act_v == off_v:
                            sal_status = " ✅ *(ตรงตามแท่ง)*"
                        else:
                            sal_status = f" ⚠️ *(ไม่ตรงแท่ง: ควรเป็น {official_sal})*"
                    except: pass

        # --- Filter Salary/Level Info ---
        is_maharat = "มหาราช" in str(unit)
        salary_section = []
        if is_maharat:
            salary_section = [
                f"📊 **ข้อมูลกำลังพล:**",
                f"▫️ ระดับ: **{lvl}**{lvl_warning} | ขั้น: **{step}**",
                f"▫️ เงินเดือน: **{sal} ฿**{sal_status}",
            ]
        else:
            # 📉 Financial Warning (Only show if actually Maharat and has salary but missing auth)
            salary_section = []
            if salary_info and not is_maharat:
                salary_section = [f"⚠️ *จำกัดการเข้าถึงข้อมูลรายได้ (รองรับเฉพาะ สภ.มหาราช)*"]

        card = [
            f"{icon} **{name}**",
            f"📍 **ตำแหน่ง:** {pos}" if pos != "-" else "",
        ]
        card.extend(salary_section)
        
        # Add any extra columns found in the sheet
        if dynamic_salary_fields:
            card.extend(dynamic_salary_fields)

        card.extend([
            f"{self.DIVIDER}",
            f"📻 **นามเรียกขาน:** {call}" if call != "-" else "",
            f"📞 **เบอร์โทร:** {phone}" if phone != "-" else "",
            f"🏢 **สังกัด:** {unit}" if unit != "-" else "",
            f"🆔 **เลขบัตร:** {id_card}" if id_card != "-" else "",
            f"🎂 **วันเกิด:** {birth}" if birth != "-" else "",
            f"⏳ **{age_detail}**" if age_detail else "",
            f"🎖️ **{retirement_detail}**" if retirement_detail else "",
            f"🏦 **บัญชีธนาคาร:** {bank} {acc}" if (bank != "-" or acc != "-") else "",
        ])

        # 📈 Career & Financial Section
        if salary_info and is_maharat:
            card.append(f"{self.DIVIDER}")
            card.append("📝 **ผลการประเมินย้อนหลัง:**")
            if eval_history and eval_history != "-":
                clean_history = str(eval_history).replace('<br>', '\n').replace('\\n', '\n')
                for line in clean_history.split('\n'):
                    if line.strip(): card.append(f"   • {line.strip()}")
            else:
                card.append("   *(ยังไม่มีข้อมูลการประเมิน)*")

        # Final Note
        if note and note != "-" and note.strip():
            card.append(f"📝 **หมายเหตุ:** {note}")
        
        # Filter empty lines and join
        final_card = "\n".join([line for line in card if line.strip()])
        return final_card

    def _format_salary_table(self, matched_people: List[Dict]) -> str:
        """Creates a professional Markdown table for Salary & Evaluation history."""
        # Header matches user requested columns exactly
        header = "| ลำดับ | ชื่อ | ตำแหน่ง | ระดับ | ขั้น | เงินเดือน | ผลการประเมินย้อนหลัง |\n"
        divider = "| :--- | :--- | :--- | :--: | :--: | :--- | :--- |\n"
        rows = []
        
        for i, p in enumerate(matched_people, start=1):
            name = p['data'][0] # Keep full name with rank as per user example
            pos = p['data'][1] if len(p['data']) > 1 and p['data'][1] != "-" else "-"
            
            s = p['salary']
            lvl, step, sal, eval_hist = ("-", "-", "-", "-")
            if s:
                lvl = s[0] if len(s) > 0 and s[0] != "-" else "-"
                step = s[1] if len(s) > 1 and s[1] != "-" else "-"
                sal = s[2] if len(s) > 2 and s[2] != "-" else "-"
                eval_hist = s[3] if len(s) > 3 and s[3] != "-" else "-"
                # Support multi-line in table using <br>
                eval_hist = eval_hist.replace("\n", "<br>").replace("\\n", "<br>").strip()
            
            rows.append(f"| {i} | {name} | {pos} | {lvl} | {step} | {sal} | {eval_hist} |")
            
        return header + divider + "\n".join(rows) + "\n"

    def _format_salary_ref_table(self) -> str:
        """Fetch and format the official SalaryReference table."""
        if not self.salary_ref_sheet: return "⚠️ ไม่พบข้อมูลความเชื่อมโยงบัญชีเงินเดือน"
        try:
            data = self.salary_ref_sheet.get_all_values()
            if len(data) < 1: return "⚠️ บัญชีเงินเดือนว่างเปล่า"
            
            headers = data[0]
            rows = data[1:]
            
            # Format as Markdown
            res = ["📊 **บัญชีอัตราเงินเดือนข้าราชการตำรวจ (อ้างอิง พ.ร.บ. 2565)**", f"{self.DIVIDER}"]
            
            # Create Table
            header_str = "| " + " | ".join(headers) + " |"
            divider_str = "| " + " | ".join([":---" for _ in headers]) + " |"
            res.append(header_str)
            res.append(divider_str)
            
            for r in rows:
                res.append("| " + " | ".join(r) + " |")
                
            res.append(f"{self.DIVIDER}")
            res.append("ℹ️ *ข้อมูลนี้ใช้เป็นเกณฑ์ตรวจสอบความถูกต้องของระบบอัตโนมัติ*")
            return "\n".join(res)
        except Exception as e:
            logger.error(f"Format salary ref error: {e}")
            return f"❌ เกิดข้อผิดพลาดในการดึงข้อมูลแท่งเงินเดือน: {e}"

    def upsert_salary_bulk(self, bulk_data: List[List]):
        """Bulk Upsert for Salary History. Key = Name."""
        return self._upsert_bulk_generic(self.salary_sheet, bulk_data)

    def get_unit_salary_report(self, unit_name: str) -> str:
        """Generates a comprehensive salary & evaluation report for a whole unit."""
        if not unit_name: return "❌ ระบุชื่อหน่วยงานไม่ถูกต้อง"
        
        # Normalize unit name for searching
        norm_unit = self._normalize(unit_name)
        self._load_salary_ref_data()
        self._load_rank_mapping()
        
        # 1. Fetch Everyone from Contacts & Commanders
        all_people: List[Dict[str, Any]] = []
        for sheet_tuple in [(self.commanders_sheet, "🎖️", "Commanders"), (self.contacts_sheet, "👤", "Contacts")]:
            sheet: Any = sheet_tuple[0]
            icon: str = sheet_tuple[1]
            title: str = sheet_tuple[2]
            if not sheet: continue
            try:
                data_raw = sheet.get_all_values()
                if not isinstance(data_raw, list): continue
                for i in range(len(data_raw)):
                    if i == 0: continue
                    r = cast(List[Any], data_raw[i])
                    if len(r) > 4: # Has unit info
                        # Agency is at index 4 for Contacts, index 3 for Commanders
                        r_unit = str(r[4]) if title == "Contacts" else str(r[3])
                        if norm_unit in self._normalize(r_unit):
                            all_people.append({"data": r, "icon": icon, "sheet": title})
            except Exception as e:
                logger.error(f"Unit report fetch error {title}: {e}")

        if not all_people:
            return f"❓ ไม่พบข้อมูลเจ้าหน้าที่ในสังกัด '{unit_name}'"

        # 2. Fetch Salary Data
        salary_lookup = {}
        if self.salary_sheet:
            try:
                s_data = self.salary_sheet.get_all_values()
                for s in s_data[1:]:
                    if s and s[0]:
                        salary_lookup[self._normalize(s[0])] = s[1:]
            except: pass

        # 3. Sort by Level/Step (approximate)
        # 4. Generate Cards
        report = [f"📊 **รายงานบัญชีเงินเดือนและประวัติพิจารณา: {unit_name}**", f"📅 ข้อมูล ณ วันที่ {datetime.now().strftime('%d/%m/%Y %H:%M')}", f"{self.DIVIDER}"]
        
        cards = []
        for p in all_people:
            name = p['data'][0]
            s_info = salary_lookup.get(self._normalize(name))
            card = self._format_person_card(p['data'], p['icon'], p['sheet'], s_info)
            cards.append(card)

        # 💡 Intelligent Splitting: If too many cards, suggest table summary
        if len(cards) > 5:
            # Create a summary table first
            table_header = "| ลำดับ | ชื่อ-นามสกุล | ระดับ | ขั้น | เงินเดือน | ประเมิน |"
            table_divider = "| :--- | :--- | :--- | :--- | :--- | :--- |"
            table_rows = []
            for i, p in enumerate(all_people, 1):
                name = p['data'][0]
                s = salary_lookup.get(self._normalize(name), ["-", "-", "-", "-", "-"])
                lvl = s[0] if len(s) > 0 else "-"
                step = s[1] if len(s) > 1 else "-"
                sal = s[2] if len(s) > 2 else "-"
                eval_sum = s[3] if len(s) > 3 else "-"
                
                # --- Quick Auto-Check for Table ---
                sal_icon = ""
                if lvl != "-" and step != "-" and sal != "-" and hasattr(self, '_current_ref_data'):
                    # Robust step normalization (35 -> 35.0 or 35.0 -> 35)
                    try:
                        clean_step = str(float(step)).replace('.0', '') if '.' in str(float(step)) and str(float(step)).endswith('.0') else str(float(step))
                        if '.5' not in clean_step and '.' not in clean_step: # e.g. 35
                           lookups = [f"{self._normalize(lvl)}_{clean_step}", f"{self._normalize(lvl)}_{clean_step}.0"]
                        else:
                           lookups = [f"{self._normalize(lvl)}_{clean_step}"]
                        
                        off_sal = "-"
                        for l_key in lookups:
                            if l_key in self._current_ref_data:
                                off_sal = self._current_ref_data[l_key]
                                break
                        
                        if off_sal != "-":
                            def _c(v): return v.replace(',', '').replace('฿', '').replace(' ', '').strip()
                            if float(_c(sal)) == float(_c(off_sal)): sal_icon = " ✅"
                            else: sal_icon = " ⚠️"
                    except: pass
                
                # Clean eval_sum for table (replace newlines with <br>)
                eval_clean = eval_sum.replace('\n', '<br>').replace('\\n', '<br>').strip()
                
                # --- Rank-to-Level Consistency Check for Table ---
                lvl_disp = lvl
                if lvl != "-" and hasattr(self, '_rank_map'):
                    found_rank_lvl = None
                    name_light = self._normalize_light(name).replace(" ", "")
                    for r_name, r_lvl in self._rank_map.items():
                        if r_name in name_light:
                            found_rank_lvl = r_lvl
                            break
                    if found_rank_lvl and self._normalize(lvl) != found_rank_lvl:
                        lvl_disp = f"{lvl}⚠️"

                table_rows.append(f"| {i} | {name} | {lvl_disp} | {step} | {sal}{sal_icon} | {eval_clean} |")
            
            report.append("\n".join([table_header, table_divider] + table_rows))
            report.append(f"\n{self.DIVIDER}\nℹ️ *หมายเหตุ: พบเจ้าหน้าที่ {len(all_people)} นาย ระบบแสดงตารางสรุปเพื่อความรวดเร็ว หากต้องการดูรายบุคคลกรุณาค้นหาด้วยชื่อครับ*")
            return "\n".join(report)
        else:
            return "\n".join(report + cards)

    def _detect_query_intent(self, query: str) -> Tuple[List[str], List[str]]:
        """Parser: Translates human query into actionable Intents and Target Sheets."""
        active_categories = []
        target_sheets = set()
        
        # 🎯 Step 1: Broad Intent Detection
        for cat, config in self.INTENT_REGISTRY.items():
            if any(k in query for k in config["keys"]):
                active_categories.append(cat)
                for t in config["targets"]: target_sheets.add(t)
        
        # 🎯 Step 2: Smart Aliasing (The "ผกก. = พ.ต.อ.สมชาย" Parser)
        # If searching for commander names, inject the "ผกก" rank search and vice versa
        commander_names = ["สมชาย", "แจ้งธรรมมา", "พ.ต.อ.สมชาย"]
        if any(name in query for name in commander_names):
            if "commander" not in active_categories:
                active_categories.append("commander")
            target_sheets.add("Orders")
            target_sheets.add("Commanders")
            
        # Smart Overrides
        if any(kw in query for kw in ["เงิน", "ขั้น", "พิจารณา", "บัญชี"]):
            target_sheets.add("Contacts")
            target_sheets.add("Commanders")
            
        return active_categories, list(target_sheets)

    def _parse_currency(self, val: str) -> float:
        """Cleans up currency strings like '1,617,650.00' and returns float."""
        if not val or val == "-": return 0.0
        try:
            return float(val.replace(',', '').replace(' ', ''))
        except:
            return 0.0

    def get_budget_summary(self):
        """Minimalist Financial Report: Concise and professional."""
        if not self.budgets_sheet: return "❌ ไม่พบฐานข้อมูลรายการงบประมาณ"
        try:
            data = self.budgets_sheet.get_all_values()
            if len(data) < 3: return "✅ ระบบยังไม่มีรายการงบประมาณครับ"
            
            report = f"💰 **{data[0][0]}**\n📅 {data[1][0]}\n{self.DIVIDER}\n"
            
            for r in data[2:]:
                if not r or not r[0] or r[0] == "รายการ": continue
                item, b_str, s_str, bal_str, note = r[0], r[1], r[2], r[3], r[4]
                
                # Calculation
                def _pc(v: str) -> float:
                    if not v or v == "-": return 0.0
                    try: return float(str(v).replace(',', '').replace(' ', ''))
                    except: return 0.0
                b_val = _pc(b_str)
                s_val = _pc(s_str)
                pct = (s_val / b_val * 100) if b_val > 0 else 0
                
                _div = "━━━━━━━━━━━━━━━━━━"  # same as DIVIDER
                if "รวม" in item:
                    report += f"{_div}\n📊 **{item}**: ใช้ไป {pct:,.2f}% | 💰 คงเหลือ: **{bal_str} ฿**\n   **(งบรวมทั้งสิ้น: {b_str} ฿)**"
                    continue
                icon = "🔴" if "-" in bal_str else "🔹"
                # Compact Line: Item: Spent/Budget (Pct%) | Bal
                line = f"{icon} **{item}**: {pct:,.0f}% (เหลือ {bal_str})"
                report += line + "\n"
            
            return report
        except Exception as e:
            return f"❌ ข้อผิดพลาด: {e}"
    def get_expenditure_status(self):
        """Administrative Tool: Summary of monthly bill payments."""
        if not self.spreadsheet: return "❌ ระบบไม่ได้เชื่อมต่อ"
        try:
            ws = self.spreadsheet.worksheet("ExpenditureStatus")
            data = ws.get_all_values()
            if len(data) < 2: return "✅ ยังไม่มีข้อมูลการเบิกจ่ายรายเดือนครับ"
            
            report = f"📅 **{data[0][0]}**\n{self.DIVIDER}\n"
            for r in data[2:]:
                if not r or not r[0]: continue
                item, month, note = r[0], r[1], r[2]
                report += f"📍 **{item}**\n   ▫️ เบิกจ่ายถึง: {month}\n"
                if note: report += f"   📝 หมายเหตุ: {note}\n"
                report += "\n"
            
            return report
        except Exception as e:
            return f"❌ ข้อผิดพลาด: {e}"

    def upsert_expenditure_bulk(self, bulk_data: List[List]):
        """Specialized Upsert for Monthly Bills."""
        try:
            ws = self.spreadsheet.worksheet("ExpenditureStatus")
            all_rows = ws.get_all_values()
            
            # Start mapping from row 3 (data starts here)
            existing_map = {}
            if len(all_rows) >= 3:
                for i, row in enumerate(all_rows[2:], start=3):
                    if row and row[0]:
                        norm_item = self._normalize(row[0])
                        existing_map[norm_item] = i

            count = 0
            new_rows = []
            for row in bulk_data:
                norm_item = self._normalize(row[0])
                if norm_item in existing_map:
                    idx = existing_map[norm_item]
                    ws.update(values=[row], range_name=f"A{idx}")
                    count += 1
                else:
                    new_rows.append(row)
            
            if new_rows:
                ws.append_rows(new_rows)
                count += len(new_rows)
            
            return count
        except Exception as e:
            logger.error(f"Expenditure upsert error: {e}")
            return 0

    def upsert_budget_bulk(self, bulk_data: List[List]):
        """Upsert budget items. Key = Item (column 0)."""
        if not self.budgets_sheet: return 0
        try:
            all_rows = self.budgets_sheet.get_all_values()
            existing_map = {}
            # Budgets usually have headers in rows 1-2, data starts at row 3
            if len(all_rows) >= 3:
                for i, row in enumerate(all_rows[2:], start=3):
                    if row and row[0]:
                        norm_item = self._normalize(row[0])
                        existing_map[norm_item] = i

            count = 0
            new_rows = []
            for row in bulk_data:
                norm_item = self._normalize(row[0])
                if norm_item in existing_map:
                    idx = existing_map[norm_item]
                    # Update without overwriting existing note if new note is empty
                    existing_row = all_rows[idx-1]
                    updated = [new if new not in ["-", "", None] else old 
                               for new, old in zip(row, existing_row)]
                    self.budgets_sheet.update(values=[updated], range_name=f"A{idx}")
                    count += 1
                else:
                    new_rows.append(row)
            
            if new_rows:
                self.budgets_sheet.append_rows(new_rows)
                count += len(new_rows)
            
            return count
        except Exception as e:
            logger.error(f"Budget upsert error: {e}")
            return 0

    def get_old_vehicles(self):
        """Administrative Tool: Detailed audit of vehicles older than 8 years."""
        if not self.vehicles_sheet: return "❌ ไม่พบฐานข้อมูลยานพาหนะ"
        try:
            raw_data: Any = self.vehicles_sheet.get_all_values()
            data: List[List[Any]] = raw_data if isinstance(raw_data, list) else []
            if len(data) < 2: return "✅ ไม่พบข้อมูลรถในระบบ"
            
            old_list: List[str] = []
            now = datetime.now()
            
            data_rows2: List[List[Any]] = [cast(List[Any], data[k]) for k in range(1, len(data))]
            for r_untouch in data_rows2:
                r: List[Any] = cast(List[Any], r_untouch)
                acq_date = self._parse_thai_date(r[16]) if len(r) > 16 else None
                if acq_date:
                    diff_days = (now - acq_date).days
                    years = diff_days // 365
                    months = (diff_days % 365) // 30
                    
                    if years >= 8:
                        raw_shield = r[5] if len(r)>5 else "-"
                        shield = raw_shield if "โล่" in str(raw_shield) else f"โล่ {raw_shield}"
                        
                        plate = r[6] if (len(r)>6 and r[6] != "-") else "ไม่มีป้าย"
                        v_type = r[4] if len(r)>4 else ""
                        brand = f"{r[7]} {v_type}".strip()
                        status = r[17] if len(r) > 17 else "ไม่ระบุ"
                        
                        msg = (f"🔴 **{shield}** ({brand})\n"
                               f"   ▫️ ทะเบียน: {plate}\n"
                               f"   ▫️ วันที่ได้รับ: {r[16]}\n"
                               f"   ▫️ อายุรถ: **{years} ปี {months} เดือน**\n"
                               f"   ▫️ สถานะปัจจุบัน: {status}")
                        old_list.append(msg)

            if not old_list:
                return "✅ **ข้อมูลชัดเจน:** ไม่พบรถที่มีอายุเกิน 8 ปี ในฐานข้อมูลปัจจุบันครับ"

            report = f"📋 **รายงานตรวจสอบรถอายุเกิน 8 ปี (พบ {len(old_list)} คัน)**\n{self.DIVIDER}\n"
            old_list_typed2: List[str] = cast(List[str], old_list)
            top25: List[str] = [old_list_typed2[k] for k in range(min(25, len(old_list_typed2)))]
            report += "\n\n".join(top25)
            
            if len(old_list) > 25:
                report += f"\n\n{self.DIVIDER}\n⚠️ แสดงเพียง 25 คันแรก เพื่อความชัดเจนในการอ่าน"
            
            return report
        except Exception as e:
            return f"❌ ข้อผิดพลาด: {e}"

    def get_today_summary(self):
        """Strategic Daily Summary for Today."""
        return self.get_date_summary(offset_days=0)

    def get_tomorrow_summary(self):
        """Strategic Daily Summary for Tomorrow."""
        return self.get_date_summary(offset_days=1)

    def get_date_summary(self, offset_days: int = 0):
        """Strategic Daily Summary: Connects Day, Duty Officer, and Recurring Tasks for any date."""
        try:
            target_time = datetime.now() + timedelta(days=offset_days)
            day_names_th = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
            current_day_th = day_names_th[target_time.weekday()]
            
            # 1. Header Section
            label = "สรุปรายงานภารกิจประจำวัน" if offset_days == 0 else "สรุปรายงานภารกิจล่วงหน้า"
            header = (
                f"🏛️ **[ {label} ]**\n"
                f"📅 **ประจำวัน{current_day_th}ที่ {target_time.strftime('%d/%m/%Y')}**\n"
                f"{self.DIVIDER}"
            )
            summary: List[str] = [header]
            
            # 2. Duty Officer Section (เวร 80)
            # Normalize day/month for Thai matching
            day_th_digit = str(target_time.day).translate(str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙"))
            month_th_short = ["ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค."][target_time.month-1]
            search_date_th = f"{day_th_digit} {month_th_short}"
            
            duty_content = "🔘 **เวรอำนวยการ (เวร 80)**\n\n"
            found_duty = False
            if self.duty_roster_sheet:
                try:
                    data_raw = self.duty_roster_sheet.get_all_values()
                    if isinstance(data_raw, list):
                        # Use range-based loop to stay safe with indexing
                        for i in range(1, len(data_raw)):
                            r = cast(List[Any], data_raw[i])
                            if len(r) > 2:
                                # Robust matching: Thai date OR Arabic date OR Day number
                                row_date = str(r[0])
                                if search_date_th in row_date or target_time.strftime('%d/%m/%Y') in row_date or str(target_time.day) == row_date.strip():
                                    # Force-cast self for the linter (fix @_ unknown type)
                                    service_self: Any = self
                                    info: Dict[str, str] = service_self._enrich_contact_info(str(r[2]))
                                    full_name: str = str(info.get('name', r[2]))
                                    phone = str(info.get('phone', "-"))
                                    if phone == "-": phone = str(r[4]) if len(r) > 4 else "-"
                                    callsign = str(r[3]) if len(r) > 3 else "-"
                                    location = str(r[5]) if len(r) > 5 else "สภ.มหาราช"
                                    
                                    duty_content += (
                                        f"👤 ชื่อ: **{full_name}**\n"
                                        f"📟 นามเรียกขาน: **{callsign}**\n"
                                        f"📞 เบอร์โทร: `{phone}`\n"
                                        f"📍 สถานที่: {location}\n"
                                        f"⏰ เวลา: _{str(r[1]) if len(r) > 1 else '08.00 - 08.00'}_"
                                    )
                                    found_duty = True
                                    break
                except Exception as e:
                    logger.error(f"Duty fetch error: {e}")
            
            if not found_duty:
                # Fallback to DutyPatterns
                if self.duty_patterns_sheet:
                    patterns_raw = self.duty_patterns_sheet.get_all_values()
                    if isinstance(patterns_raw, list):
                        for i in range(1, len(patterns_raw)):
                            p = cast(List[Any], patterns_raw[i])
                            if len(p) >= 2 and current_day_th in str(p[0]):
                                raw_name = str(p[1])
                                # Check for alternate weeks in "Name1 / Name2" format
                                if any(k in raw_name for k in ["สลับ", "และ", "/"]):
                                    dt_obj: Any = target_time
                                    iso_cal = dt_obj.isocalendar()
                                    week_num: int = int(iso_cal[1])
                                    alternates: List[str] = [x.strip() for x in re.split(r'และ|สลับ|/|,', raw_name) if x.strip()]
                                    if len(alternates) >= 2:
                                        raw_name = alternates[week_num % 2]
                                
                                service_self: Any = self
                                info: Dict[str, str] = service_self._enrich_contact_info(raw_name)
                                full_name: str = str(info.get('name', raw_name))
                                phone = str(info.get('phone', "-"))
                                if phone == "-": phone = str(p[3]) if len(p) > 3 else "-"
                                callsign = str(p[2]) if len(p) > 2 else "-"
                                
                                duty_content += (
                                    f"👤 ชื่อ: **{full_name}** (เวรปกติ)\n"
                                    f"📟 นามเรียกขาน: **{callsign}**\n"
                                    f"📞 เบอร์โทร: `{phone}`\n"
                                    f"⏰ เวลา: _08.00 - 08.00 (+1)_"
                                )
                                found_duty = True
                                break
                
                if not found_duty:
                    duty_content += "⚠️ _(ยังไม่มีข้อมูลเวรในระบบ - กรุณาระบุในชีท DutyRoster)_"
            
            summary.append(duty_content)
            summary.append(self.DIVIDER)

            # 4. Orders & Tasks Section
            order_content = "📝 **[ ภารกิจและข้อสั่งการ ]**\n"
            found_orders: List[str] = []
            target_str = target_time.strftime('%d/%m/%Y')
            if self.orders_sheet:
                try:
                    rows_raw = self.orders_sheet.get_all_values()
                    if isinstance(rows_raw, list):
                        is_weekend = target_time.weekday() >= 5
                        for i in range(1, len(rows_raw)):
                            r = cast(List[Any], rows_raw[i])
                            if not r or not r[0]: continue
                            detail = str(r[0])
                            
                            # Complex Date Matcher
                            match = False
                            # Check Deadline column (index 2) or Note/Timestamp (index 6)
                            deadline_col = str(r[2]) if len(r) > 2 else ""
                            ts_col = str(r[6]) if len(r) > 6 else ""
                            
                            if target_str in ts_col or target_str in deadline_col: match = True
                            elif current_day_th in detail or current_day_th in deadline_col: match = True
                            elif "เสาร์-อาทิตย์" in detail and is_weekend: match = True
                            elif "จันทร์-ศุกร์" in detail and not is_weekend: match = True
                            
                            if match:
                                cmder_raw: str = str(r[1]) if len(r) > 1 and r[1] not in ["-", ""] else ""
                                stat_raw: str = str(r[3]) if len(r) > 3 and r[3] not in ["-", ""] else ""
                                urg_raw: str = str(r[4]) if len(r) > 4 and r[4] not in ["-", ""] else ""
                                
                                o_line: str = f"🔹 **{detail}**"
                                o_meta: List[str] = []
                                if cmder_raw: o_meta.append(f"👤 {cmder_raw}")
                                if stat_raw and urg_raw: o_meta.append(f"{stat_raw} | {urg_raw}")
                                elif stat_raw or urg_raw: o_meta.append(stat_raw if stat_raw else urg_raw)
                                
                                if o_meta:
                                    o_line += f"\n   └ 🔘 **{' | '.join(o_meta)}**"
                                found_orders.append(str(o_line))
                except Exception as e:
                    logger.error(f"Orders search error: {e}")
            
            if found_orders:
                # Use a slice that's safe
                limit = min(15, len(found_orders))
                top_orders = [found_orders[k] for k in range(limit)]
                summary.append("\n".join(top_orders))
            else:
                summary.append("⚠️ _(ไม่มีภารกิจหรือข้อสั่งการพิเศษสำหรับวันนี้)_")
                
            return "\n".join(summary)
            
        except Exception as e:
            logger.error(f"Critical error in get_date_summary: {e}", exc_info=True)
            return f"❌ **เกิดข้อผิดพลาดในการดึงข้อมูล:** {str(e)}\nกรุณาลองใหม่อีกครั้ง หรือติดต่อผู้ดูแลระบบครับ"


    def get_equipment_summary(self):
        """Strategic Report: Overview of all equipment by category."""
        if not self.equipment_sheet: return "❌ ไม่พบฐานข้อมูลยุทธภัณฑ์"
        try:
            data = self.equipment_sheet.get_all_values()
            if len(data) < 2: return "✅ ระบบยังไม่มีข้อมูลยุทธภัณฑ์ที่บันทึกไว้ครับ"

            categories = {}  # category -> list of items
            grand_total = 0
            grand_inuse = 0
            grand_instock = 0

            for r_raw3 in data[1:]:
                r3: List[Any] = cast(List[Any], r_raw3)
                if not r3 or not r3[0]: continue
                cat = r3[0]
                item = r3[1] if len(r3) > 1 else "-"
                total = int(r3[2]) if len(r3) > 2 and str(r3[2]).isdigit() else 0
                inuse = int(r3[3]) if len(r3) > 3 and str(r3[3]).isdigit() else 0
                instock = int(r3[4]) if len(r3) > 4 and str(r3[4]).isdigit() else 0

                if cat not in categories:
                    categories[cat] = []
                categories[cat].append((item, total, inuse, instock))
                grand_total += total
                grand_inuse += inuse
                grand_instock += instock

            report = f"🛡️ **สถานภาพยุทธภัณฑ์ สภ.มหาราช**\n{self.DIVIDER}\n"
            report += f"📊 รวมทุกประเภท: **{grand_total}** รายการ | เบิกใช้: {grand_inuse} | คงคลัง: {grand_instock}\n\n"

            for cat, items in categories.items():
                cat_total = sum(i[1] for i in items)
                cat_inuse = sum(i[2] for i in items)
                cat_instock = sum(i[3] for i in items)
                stock_icon = "🔴" if cat_instock == 0 else "🟡" if cat_instock <= 2 else "🟢"
                report += f"{stock_icon} **{cat}** (รวม {cat_total} | คงคลัง {cat_instock})\n"
                for item, total, inuse, instock in items:
                    s_icon = "⚪" if instock == 0 else "▫️"
                    report += f"   {s_icon} {item}: {total} (ใช้ {inuse} / เหลือ {instock})\n"
                report += "\n"

            return report
        except Exception as e:
            return f"❌ ข้อผิดพลาดในการสรุปยุทธภัณฑ์: {e}"

    # ═══════════════════════════════════════════════════════════
    # 🔫 FIREARM REGISTRY MODULE
    # ═══════════════════════════════════════════════════════════

    def upsert_firearm_registry_bulk(self, bulk_data: List[List]):
        """Bulk Upsert for FirearmRegistry. Key = เลขทะเบียนโล่ (column index 4)."""
        if not self.firearm_registry_sheet: return 0
        try:
            all_rows = self.firearm_registry_sheet.get_all_values()
            existing_map = {}
            if len(all_rows) > 1:
                for i, row in enumerate(all_rows[1:], start=2):
                    if row and len(row) > 4 and row[4]:
                        key = self._normalize(row[4])  # Key = เลขทะเบียนโล่
                        existing_map[key] = (i, row)

            new_rows_f: List[Any] = []
            updated_shields_f: List[str] = []
            for row_data in bulk_data:
                key = self._normalize(row_data[4]) if len(row_data) > 4 else ""
                if key and key in existing_map:
                    idx, existing_row = existing_map[key]
                    updated = [new if new not in ["-", "", None] else old
                               for new, old in zip(row_data, existing_row)]
                    self.firearm_registry_sheet.update(values=[updated], range_name=f"A{idx}")
                    updated_shields_f.append(key)
                else:
                    new_rows_f.append(row_data)

            if new_rows_f:
                self.firearm_registry_sheet.append_rows(new_rows_f)

            return len(bulk_data)
        except Exception as e:
            logger.error(f"FirearmRegistry upsert error: {e}")
            return 0

    def append_firearm_registry(self, row_data: List):
        """Append a single firearm record."""
        if not self.firearm_registry_sheet: return False
        try:
            self.firearm_registry_sheet.append_row(row_data)
            return True
        except Exception as e:
            logger.error(f"FirearmRegistry append error: {e}")
            return False

    def get_firearm_registry_summary(self):
        """Strategic Report: บัญชียืมอาวุธปืนทางราชการ สภ.มหาราช."""
        if not self.firearm_registry_sheet: return "❌ ไม่พบฐานข้อมูลบัญชีอาวุธปืน"
        try:
            data = self.firearm_registry_sheet.get_all_values()
            if len(data) < 2: return "✅ ระบบยังไม่มีข้อมูลอาวุธปืนที่บันทึกไว้ครับ"

            total = len(data) - 1
            status_counts = {}  # Status -> count
            type_counts = {}    # Firearm type -> count
            borrowed_list = []  # Currently borrowed firearms
            in_stock_count = 0

            for r_raw4 in data[1:]:
                r4: List[Any] = cast(List[Any], r_raw4)
                if not any(r4): continue
                
                firearm_type = r4[1] if len(r4) > 1 else "-"
                status = r4[6] if len(r4) > 6 else "-"
                borrower = r4[7] if len(r4) > 7 else "-"
                
                # Count by type
                if firearm_type and firearm_type != "-":
                    type_counts[firearm_type] = type_counts.get(firearm_type, 0) + 1
                
                # Count by status
                if status and status != "-":
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                # Track borrowed items
                if status in ["ยืมออก", "เบิกใช้", "ยืม", "เบิก"]:
                    caliber = r4[2] if len(r4) > 2 else "-"
                    brand = r4[3] if len(r4) > 3 else "-"
                    shield_no = r4[4] if len(r4) > 4 else "-"
                    borrow_date = r4[8] if len(r4) > 8 else "-"
                    borrowed_list.append({
                        "type": firearm_type, "caliber": caliber, "brand": brand,
                        "shield": shield_no, "borrower": borrower, "date": borrow_date
                    })
                elif status in ["ในคลัง", "คงคลัง", "พร้อมใช้", "เก็บรักษา"]:
                    in_stock_count = int(in_stock_count) + 1

            report = f"🔫 **บัญชียืมอาวุธปืนทางราชการ สภ.มหาราช**\n{self.DIVIDER}\n"
            report += f"📊 รวมทั้งหมด: **{total}** กระบอก | ในคลัง: {in_stock_count} | ยืมออก: {len(borrowed_list)}\n\n"

            # By Type
            if type_counts:
                report += "📋 **แยกตามชนิดอาวุธปืน:**\n"
                for t, c in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
                    report += f"   ▫️ {t}: {c} กระบอก\n"
                report += "\n"

            # By Status
            if status_counts:
                report += "📦 **สถานะการเก็บรักษา:**\n"
                for s, c in status_counts.items():
                    s_icon = "🟢" if s in ["ในคลัง", "คงคลัง", "พร้อมใช้", "เก็บรักษา"] else "🔴" if s in ["ยืมออก", "เบิกใช้", "ยืม", "เบิก"] else "🟡"
                    report += f"   {s_icon} {s}: {c} กระบอก\n"
                report += "\n"

            # Borrowed List
            if borrowed_list:
                report += f"🔴 **รายการที่ยืมออก ({len(borrowed_list)} กระบอก):**\n"
                borrowed_typed: List[Any] = [borrowed_list[k] for k in range(min(15, len(borrowed_list)))]
                for i, b in enumerate(borrowed_typed, 1):
                    report += f"   {i}. {b['type']} {b['brand']} {b['caliber']} (โล่ {b['shield']})\n"
                    report += f"      👤 ผู้ยืม: {b['borrower']} | 📅 {b['date']}\n"
                if len(borrowed_list) > 15:
                    report += f"   ...และอีก {len(borrowed_list)-15} รายการ\n"
            else:
                report += "🟢 **ไม่มีอาวุธปืนที่ยืมออกในขณะนี้**\n"

            return report
        except Exception as e:
            return f"❌ ข้อผิดพลาดในการสรุปบัญชีอาวุธปืน: {e}"

    def append_order(self, row_data: List):
        if not self.orders_sheet: return False
        try:
            self.orders_sheet.append_row(row_data)
            return True
        except: return False

    def append_reminder(self, row_data: List):
        if not self.reminders_sheet: return False
        try:
            self.reminders_sheet.append_row(row_data)
            return True
        except: return False

    def get_due_reminders(self):
        """Finds reminders that are due now or soon. Robust against server timezones."""
        if not self.reminders_sheet: return []
        try:
            data = self.reminders_sheet.get_all_values()
            if len(data) < 2: return []
            
            due = []
            now = datetime.now()
            # Logging for debug (visible in console)
            current_time_str = now.strftime("%H:%M")
            logger.info(f"Checking reminders... Server Time: {current_time_str}")
            
            for i, r in enumerate(data[1:], start=2):
                if len(r) < 4: continue
                # Column Index: 0:Topic, 1:Content, 2:Reminder_Time, 3:Status
                if r[3] != "Active": continue
                
                time_val = r[2]
                match = re.search(r'(\d{1,2})[\.:](\d{2})', time_val)
                if match:
                    h, m = int(match.group(1)), int(match.group(2))
                    
                    # Check matching:
                    # 1. Direct match (for Local/Thai servers)
                    # 2. UTC+7 match (if server is UTC)
                    is_match = (now.hour == h and abs(now.minute - m) <= 5)
                    
                    # Alternative for UTC servers (Thai 00:30 is UTC 17:30)
                    utc_h = (h - 7) % 24
                    is_utc_match = (now.hour == utc_h and abs(now.minute - m) <= 5)
                    
                    if is_match or is_utc_match:
                        due.append((r[0], r[1], r[2], i))
            
            return due
        except Exception as e:
            logger.error(f"Error fetching due reminders: {e}")
            return []


    def mark_reminder_done(self, row_idx: int):
        """Updates status to 'Alerted' to prevent repeat notifications."""
        if not self.reminders_sheet: return
        try:
            self.reminders_sheet.update_cell(row_idx, 4, "Alerted")
        except Exception as e:
            logger.error(f"Error marking reminder done: {e}")
