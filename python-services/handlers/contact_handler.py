import logging
import re
import os
import sys
from telegram import Update, Message # type: ignore
from telegram.ext import ContextTypes # type: ignore
from services.sheets_service import SheetsService # type: ignore

from datetime import datetime
from typing import List, Dict, Optional, Any, cast, Union

# Import Smart Recorder Skill Logic
try:
    from .logic_utils import SmartParserUtils, LogicUtils # type: ignore
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from logic_utils import SmartParserUtils, LogicUtils # type: ignore

logger = logging.getLogger(__name__)

class ContactHandler:
    DIVIDER = "━━━━━━━━━━━━━━━━━━"

    def __init__(self, sheets_service: SheetsService):
        self.sheets = sheets_service
        self.profiles = getattr(sheets_service, 'SHEET_PROFILES', {})

    async def handle_text_save(self, update: Update, context: ContextTypes.DEFAULT_TYPE, force_mode: Optional[str] = None):
        """Main Handler: Orchestrates specialized sub-parsers."""
        if not update.message or not update.message.text:
            return

        text = update.message.text.strip()
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        # 🧠 DECISION PARSER 2.0: Scoring-based Intent Detection
        scores = {
            "arrests": 0,
            "firearm": 0,
            "orders": 0,
            "table": 0,
            "expenditure": 0
        }
        
        # A. Key-based Scoring (Professional Police Keywords Expansion 2.0)
        
        # 🟢 Arrests & Incidents - Catch Criminal Case context
        arrest_keywords = ["จับกุม", "ผู้ต้องหา", "ของกลาง", "ข้อหา", "สภ.", "พงส.", "ร้อยเวร", 
                           "พิกัด", "ชุดจับกุม", "ศาล", "หมายจับ", "คดี", "ดำเนินคดี", "ศจก.", "คดีที่",
                           "ว.20", "เหตุ 100", "เหตุ 111", "เหตุ 200", "ลักทรัพย์", "ทำร้ายร่างกาย"]
        if any(k in text for k in arrest_keywords): scores["arrests"] += 130
        
        # 🔫 Firearm & Equipment context
        firearm_keywords = ["บัญชีอาวุธ", "คลังอาวุธ", "ปืน", "ทะเบียนโล่", "ลูกกระสุน", "กระสุน", "ขนาด", 
                            "ยี่ห้อ", "เบิก", "ยืม", "ปืนสั้น", "ปืนยาว", "เอ็ม16", "M16", "HK", "SIG", "Glock", "อาวุธ"]
        if any(k in text for k in firearm_keywords): scores["firearm"] += 120
        
        # 🗓️ Orders & Missions context
        mission_keywords = ["ประชุม", "นัดหมาย", "กิจกรรม", "ภารกิจ", "ตรวจราชการ", "ว.0", "ว.5", "กำชับ", "สั่งการ", 
                            "ภารกิจเร่งด่วน", "ประชุมเพลิง", "งานศพ", "รับนโยบาย", "ลงพื้นที่", "ปล่อยแถว", 
                            "ว.4", "ว.35", "ว.36", "ว.43", "ตรวจสอบ", "ตั้งด่าน"]
        if any(k in text for k in mission_keywords): scores["orders"] += 100
        
        # 🕒 Time & Relative context
        time_keywords = ["พรุ่งนี้", "วันนี้เวลา", "กำหนดเวลา", "มะรืน", "สัปดาห์หน้า", "เดือนหน้า", "เลื่อนเป็น", "ยกเลิก", "ว.24"]
        if any(k in text for k in time_keywords): scores["orders"] += 50
        
        # 🎖️ Commander & Ranks context (Mapping Ranks to Orders/Personnel)
        police_ranks = ["พล.ต.อ.", "พล.ต.ท.", "พล.ต.ต.", "พ.ต.อ.", "พ.ต.ท.", "พ.ต.ต.", "ร.ต.อ.", "ร.ต.โท", "ร.ต.ต.", 
                        "ด.ต.", "จ.ส.ต.", "ส.ต.อ.", "ส.ต.ท.", "ส.ต.ต.", "นรต.", "ผบ.ตร.", "ผบช.", "ผบก.", 
                        "สมชาย", "แจ้งธรรมมา", "ผกก", "ผู้กำกับ", "รองผกก", "ผู้การ", "นาย"]
        if any(k in text for k in police_ranks): 
            scores["orders"] += 70
            
        # 📊 Table/Personnel context
        if "|" in text: scores["table"] += 120
        if "\t" in text or re.search(r"\s{2,}", text): scores["table"] += 60
        
        # ☕ Expenditure & Finances context
        finance_keywords = ["น้ำมัน", "ไฟฟ้า", "ประปา", "อินเทอร์เน็ต", "เน็ต", "งบประมาณ", "บจ.", "พัสดุ", "เบิกจ่าย", "การประเมิน", "ว.13"]
        if any(k in text for k in finance_keywords) and any(m in text for m in ["มกราคม", "ม.ค.", "ประเมิน", "ปี"]):
            scores["expenditure"] += 150

        # B. Execution Priority
        best_intent = max(scores, key=lambda k: scores[k])
        if scores[best_intent] < 40 and not (text.startswith("จด") or text.startswith("บันทึก")):
             # 🔵 Fallback: No saving intent detected, treat as Search
             loading_msg = await update.message.reply_text("⏳ **กำลังค้นหาข้อมูล...**")
             response = self.sheets.search_all(text) # type: ignore
             await loading_msg.edit_text(response, parse_mode='Markdown')
             return

        # C. Intent Dispatcher (Arrests removed)
        
        if best_intent == "firearm" and scores["firearm"] >= 100:
            if await self._detect_firearm_registry(update, context, text, timestamp): return
            
        if best_intent == "orders" or text.startswith(("จด", "บันทึก")):
            # High priority for Orders if date/time exists
            if await self._detect_meeting_order(update, context, text, timestamp): return
            if await self._parse_expenditure_and_memo(update, context, text, timestamp): return
            
        if best_intent == "table" and scores["table"] >= 50:
            if await self._parse_universal_table(update, context, text, timestamp): return
            if await self._parse_tsv_equipment(update, context, text, timestamp): return

        if best_intent == "expenditure" and scores["expenditure"] >= 100:
            if await self._parse_expenditure_and_memo(update, context, text, timestamp): return
        
        # Final Fallback: If score was high but all parsers failed
        # 🚀 SMART FALLBACK: If it doesn't look like an explicit save command (no prefix), try searching
        if not text.startswith(("จด", "บันทึก")):
             loading_msg = await update.message.reply_text("⏳ **ไม่พบรูปแบบการบันทึก กำลังลองค้นหาให้แทนครับ...**")
             response = self.sheets.search_all(text) # type: ignore
             if response and "ไม่พบข้อมูล" not in response:
                 await loading_msg.edit_text(response, parse_mode='Markdown')
                 return
             else:
                 await loading_msg.delete()

        await update.message.reply_text("❌ **บอทไม่เข้าใจรูปแบบการบันทึก:** กรุณาพิมพ์ให้ชัดเจน หรือใช้รูปแบบ 'จด [ข้อความ]' ครับ")

    # ══════════════════════════════════════════════════════════════════════════════
    # INTERNALS: MODULAR PARSERS
    # ══════════════════════════════════════════════════════════════════════════════

    # (Arrests functionality removed as requested)

        return False

    async def _detect_firearm_registry(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, timestamp: str) -> bool:
        """🔫 1.2 Firearm Registry Detection."""
        if not any(k in text for k in ["บัญชีอาวุธ", "คลังอาวุธ", "อาวุธปืน", "ทะเบียนโล่", "ปืนสั้น", "ปืนยาว"]):
            return False

        lines = [l.strip() for l in text.split('\n') if l.strip()]
        bulk, col_map = [], {}
        header_found, seq = False, 0
        
        for line in lines:
            if '---' in line or '|' not in line: continue
            parts = [p.strip() for p in line.split('|')]
            if line.startswith('|') and line.endswith('|'): parts = parts[1:-1] # type: ignore
            elif line.startswith('|'): parts = parts[1:] # type: ignore
            elif line.endswith('|'): parts = parts[:-1] # type: ignore
            parts = [p.strip() for p in parts]
            if not parts: continue
            
            if not header_found:
                for idx, p in enumerate(parts):
                    p = p.lower()
                    if any(k in p for k in ["ลำดับ", "ที่"]): col_map['seq'] = idx # type: ignore
                    elif any(k in p for k in ["ชนิด", "ประเภท"]): col_map['type'] = idx # type: ignore
                    elif "ขนาด" in p: col_map['caliber'] = idx # type: ignore
                    elif any(k in p for k in ["ยี่ห้อ", "รุ่น"]): col_map['brand'] = idx # type: ignore
                    elif any(k in p for k in ["โล่", "ทะเบียน"]): col_map['shield'] = idx # type: ignore
                    elif any(k in p for k in ["สถานะ", "คลัง"]): col_map['status'] = idx # type: ignore
                    elif any(k in p for k in ["ผู้ยืม", "ผู้เบิก"]): col_map['borrower'] = idx # type: ignore
                    elif "ยืม" in p: col_map['borrow_date'] = idx # type: ignore
                    elif "คืน" in p: col_map['return_date'] = idx # type: ignore
                    elif "หมายเหตุ" in p: col_map['note'] = idx # type: ignore
                if 'shield' in col_map or 'type' in col_map: header_found = True # type: ignore
                continue
            
            if len(parts) >= 3:
                bulk.append([
                    parts[col_map['seq']] if 'seq' in col_map else str(seq + 1), # type: ignore
                    parts[col_map['type']] if 'type' in col_map else "-", # type: ignore
                    parts[col_map['caliber']] if 'caliber' in col_map else "-", # type: ignore
                    parts[col_map['brand']] if 'brand' in col_map else "-", # type: ignore
                    parts[col_map['shield']] if 'shield' in col_map else "-", # type: ignore
                    "-", # date_recv
                    parts[col_map['status']] if 'status' in col_map else "-", # type: ignore
                    parts[col_map['borrower']] if 'borrower' in col_map else "-", # type: ignore
                    parts[col_map['borrow_date']] if 'borrow_date' in col_map else "-", # type: ignore
                    parts[col_map['return_date']] if 'return_date' in col_map else "-", # type: ignore
                    "-", # purpose
                    parts[col_map['note']] if 'note' in col_map else "-", # type: ignore
                    timestamp
                ])
                seq += 1 # type: ignore

        if bulk:
            loading = await update.message.reply_text("⏳ ตรวจพบข้อมูลอาวุธปืน... กำลังขึ้นทะเบียนพัสดุ")
            success = self.sheets.upsert_firearm_registry_bulk(bulk)
            
            msg = (f"✅ **ขึ้นทะเบียนพัสดุปืนสำเร็จ!** 🔫\n"
                   f"{self.DIVIDER}\n"
                   f"🛡️ **จำนวน:** {success} กระบอก\n"
                   f"📁 อัปเดตข้อมูลลงชีท **FirearmRegistry** ให้แล้วครับ")
            await loading.edit_text(msg, parse_mode='Markdown')
            return True
        return False

    async def _detect_meeting_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, timestamp: str) -> bool:
        """🗓️ 1.3 Meeting/Order Detection logic."""
        keywords = ["ประชุม", "ตรวจราชการ", "นัดหมาย", "กิจกรรม", "จิตอาสา", "ภารกิจ"]
        if not (any(k in text for k in keywords) and any(k in text for k in ["วันที่", "พรุ่งนี้", "เวลา"])):
            return False

        topic = "ประชุม/นัดหมาย"
        for k in keywords:
            if k in text:
                m = re.search(fr'{k}\s*(.*?)\s*(?:ที่|ณ|วันที่|เวลา|$)', text, re.DOTALL)
                if m and m.group(1).strip(): topic = f"{k} {m.group(1).strip()}"
                else: topic = k
                break

        loc_m = re.search(r'(?:ที่|ณ)\s*(.*?)\s*(?:วันที่|เวลา|$)', text)
        loc = loc_m.group(1).strip() if loc_m else "-"
        date_v = "พรุ่งนี้" if "พรุ่งนี้" in text else "-"
        if date_v == "-":
            d_m = re.search(r'วันที่\s*([๑-๙0-9\s]+[^\s]+)', text)
            date_v = d_m.group(1).strip() if d_m else "-"
        
        t_m = re.search(r'เวลา\s*([\d\.\sน]+)', text)
        time_v = t_m.group(1).strip() if t_m else "-"
        
        row = [f"{topic} ณ {loc}", loc, f"{date_v} ({time_v})", "Pending", "High", "Auto-Detect", timestamp] # type: ignore
        try:
            if self.sheets.orders_sheet: # type: ignore
                self.sheets.orders_sheet.append_row(row) # type: ignore
            
            msg = (f"🗓️ **บันทึกภารกิจ/นัดหมายสำเร็จ!**\n"
                   f"{self.DIVIDER}\n"
                   f"📌 **เรื่อง:** {topic}\n"
                   f"📍 **สถานที่:** {loc}\n"
                   f"📅 **เวลา:** {date_v} {time_v}\n"
                   f"{self.DIVIDER}\n"
                   f"📁 บันทึกลงในชีท **Orders** ให้เรียบร้อยครับ")
            await update.message.reply_text(msg, parse_mode='Markdown')
            return True
        except Exception:
            return False

    async def _parse_universal_table(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, timestamp: str) -> bool:
        """📊 1.4 Universal Table Parser (Markdown/TSV)."""
        if '|' not in text: return False
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        bulk, col_map, target = [], {}, "Contacts"
        
        header_found = False
        for line in lines:
            if '|' not in line or '---' in line: continue
            parts = [p.strip() for p in line.split('|')]
            if line.startswith('|') and line.endswith('|'): parts = parts[1:-1] # type: ignore
            elif line.startswith('|'): parts = parts[1:] # type: ignore
            elif line.endswith('|'): parts = parts[:-1] # type: ignore
            if not parts: continue
            
            if not header_found:
                for idx, p in enumerate(parts):
                    p = p.lower()
                    if any(k in p for k in ["ชื่อ", "ยศ"]): col_map['name'] = idx # type: ignore
                    elif "ตำแหน่ง" in p: col_map['pos'] = idx # type: ignore
                    elif "โทร" in p: col_map['phone'] = idx # type: ignore
                    elif "สังกัด" in p: col_map['agency'] = idx # type: ignore
                    elif "ที่ม" in p: col_map['date'] = idx # type: ignore # Shift/Month support
                if 'name' in col_map: header_found = True; continue # type: ignore
            
            if header_found and len(parts) >= 2:
                name = parts[col_map['name']] if 'name' in col_map and col_map['name'] < len(parts) else "-" # type: ignore
                if not name or name == "-": continue
                bulk.append([name, 
                    parts[col_map['pos']] if 'pos' in col_map and col_map['pos'] < len(parts) else "-", # type: ignore
                    "-",
                    parts[col_map['phone']] if 'phone' in col_map and col_map['phone'] < len(parts) else "-", # type: ignore
                    parts[col_map['agency']] if 'agency' in col_map and col_map['agency'] < len(parts) else "-", # type: ignore
                    "-", "-", "-", "-", "-", timestamp])

        if bulk:
            loading = await update.message.reply_text("⏳ ตรวจพบข้อมูลรายชื่อบุคลากร... กำลังตรวจสอบความถูกต้อง")
            s = self.sheets.upsert_contacts_bulk(bulk)
            
            msg = (f"✅ **อัปเกรดฐานข้อมูลบุคลากรสำเร็จ!** 👥\n"
                   f"{self.DIVIDER}\n"
                   f"📊 **จำนวน:** {s} รายการ\n"
                   f"📁 บันทึกข้อมูลลงชีท **Contacts** เป็นที่เรียบร้อยครับ")
            await loading.edit_text(msg, parse_mode='Markdown')
            return True
        return False

    async def _parse_tsv_equipment(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, timestamp: str) -> bool:
        """🛡️ 1.5 TSV Equipment Parser."""
        if '\t' not in text and not re.search(r'\s{2,}', text): return False
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        bulk, h_map, h_found = [], {}, False
        cat = "ยุทธภัณฑ์"
        for line in lines:
            parts = [p.strip() for p in line.split('\t')] if '\t' in line else [p.strip() for p in re.split(r'\s{2,}', line) if p.strip()]
            if not h_found:
                for idx, p in enumerate(parts):
                    if any(k in p for k in ["รายการ", "ยุทธภัณฑ์"]): h_map['item'] = idx # type: ignore
                    elif "จำนวน" in p: h_map['total'] = idx # type: ignore
                if 'item' in h_map: h_found = True; continue # type: ignore
            if h_found and len(parts) >= 2:
                item = parts[h_map['item']] if 'item' in h_map else "-" # type: ignore
                if not item or "รวม" in item: continue
                val = parts[h_map['total']] if 'total' in h_map and h_map['total'] < len(parts) else "0" # type: ignore
                bulk.append([cat, item, val, "0", val, "-", timestamp])
        if bulk:
            s = self.sheets.upsert_equipment_bulk(bulk)
            await update.message.reply_text(f"✅ บันทึกยุทธภัณฑ์สำเร็จ {s} รายการ")
            return True
        return False

    async def _parse_expenditure_and_memo(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, timestamp: str) -> bool:
        """☕ 1.6 Expenditure and Natural Memo (Stronger Version)."""
        # Dictionary of keywords to full sheet item names
        kw_exp = {
            "น้ำมัน": "ค่าน้ำมันเชื้อเพลิง",
            "ไฟฟ้า": "ค่าไฟฟ้า (สถานีตำรวจ)",
            "ประปา": "ค่าน้ำประปา",
            "อินเทอร์เน็ต": "ค่าบริการอินเทอร์เน็ต",
            "เน็ต": "ค่าบริการอินเทอร์เน็ต",
            "โทรศัพท์": "ค่าโทรศัพท์",
            "เบี้ยเลี้ยง": "งบประมาณเบี้ยเลี้ยง",
            "OT": "งบประมาณ OT",
            "โอที": "งบประมาณ OT"
        }
        
        # 1. Detect Expenditure Updates
        for k, full in kw_exp.items():
            if k in text:
                # Check for month/year keywords to confirm it's a status update
                month_keywords = ["มกราคม", "ม.ค.", "กุมภาพันธ์", "ก.พ.", "มีนาคม", "มี.ค.", "เมษายน", "เม.ย.", 
                                  "พฤษภาคม", "พ.ค.", "มิถุนายน", "มิ.ย.", "กรกฎาคม", "ก.ค.", "สิงหาคม", "ส.ค.", 
                                  "กันยายน", "ก.ย.", "ตุลาคม", "ต.ค.", "พฤศจิกายน", "พ.ย.", "ธันวาคม", "ธ.ค."]
                if any(m in text for m in month_keywords) or "ปี" in text or "ประเมิน" in text:
                    # Extract the value/status (text after the keyword)
                    status_val = text.replace(k, "").replace("จด", "").replace("บันทึก", "").strip()
                    if not status_val: status_val = "อัปเดต"
                    
                    self.sheets.upsert_expenditure_bulk([[full, status_val, "-"]])
                    await update.message.reply_text(f"✅ **อัปเดตสถานะงบประมาณสำเร็จ**\n━━━━━━━━━━━━━━━━━━\n📊 **รายการ:** {full}\n📝 **สถานะล่าสุด:** {status_val}\n📁 ลงชีท ExpenditureStatus เรียบร้อยครับ", parse_mode='Markdown')
                    return True
        
        # 2. Natural Memo Logging (Handles "จด ..." or "บันทึก ...")
        for k in ["จด", "บันทึก", "เพิ่มข้อความ", "เก็บ"]:
            if text.startswith(k) and len(text) > (len(k) + 1):
                memo = text[len(k):].strip() # type: ignore
                # If there's a ":" or "-" at the start after the command, remove it
                memo = re.sub(r'^[:\-\s]+', '', memo)
                
                if memo:
                    # Default row for Orders/Memo sheet
                    # Columns: [Detail, Commander, Deadline, Status, Urgency, Note, Timestamp]
                    row = [memo, "-", "-", "Pending", "Normal", "Auto-Memo", timestamp]
                    if self.sheets.orders_sheet:
                        self.sheets.orders_sheet.append_row(row)
                        await update.message.reply_text(f"📝 **บันทึกโน้ตด่วนสำเร็จ!**\n━━━━━━━━━━━━━━━━━━\n📌 **เรื่อง:** {memo}\n📁 ลงชีท Orders เรียบร้อยแล้วครับ", parse_mode='Markdown')
                        return True
        return False

    # (Strategic Arrest Parser removed)

    async def _show_help(self, update: Update):
        help_msg = ("🛡️ **System Guide**\n"
                    "━━━━━━━━━━━━━━━━━━\n"
                    "🔍 **Search:** ทะเบียน/ชื่อ\n"
                    "📞 **Save:** พิมพ์ 'จด [ข้อความ]'\n"
                    "🤖 **Ask:** ระบบวิเคราะห์จับกุมและตารางอัตโนมัติ")
        await update.message.reply_text(help_msg, parse_mode='Markdown')
