import logging
import os
import re
from datetime import datetime
from typing import List, Dict, Any, cast
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton # type: ignore
from telegram.ext import ( # type: ignore
    Application, CommandHandler, MessageHandler, filters, 
    ContextTypes
)

from config import Config # type: ignore
from services.sheets_service import SheetsService # type: ignore

from handlers.contact_handler import ContactHandler # type: ignore

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartPoliceBot:
    def __init__(self):
        self.config: Config = Config()
        self.sheets: SheetsService = SheetsService(self.config.GOOGLE_CREDENTIALS_PATH, self.config.GOOGLE_SHEET_ID)
        self.contact_handler: ContactHandler = ContactHandler(self.sheets)

    def _get_main_menu(self):
        keyboard = [
            [KeyboardButton("🔎 ค้นหาด่วน"), KeyboardButton("📅 ภารกิจวันนี้")],
            [KeyboardButton("📅 ภารกิจพรุ่งนี้"), KeyboardButton("📊 รายงานสรุป")],
            [KeyboardButton("✍️ บันทึกงาน"), KeyboardButton("❓ ช่วยเหลือ")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    def _get_summary_menu(self):
        keyboard = [
            [KeyboardButton("🚗 ยานพาหนะ"), KeyboardButton("🛡️ ยุทธภัณฑ์")],
            [KeyboardButton("💰 งบประมาณ"), KeyboardButton("🔫 บัญชีปืน")],
            [KeyboardButton("🔙 กลับเมนูหลัก")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    def _get_save_menu(self):
        # 🚀 Dynamic Generation: สร้างเมนูอัตโนมัติจากโครงสร้างชีทที่กำหนดไว้
        raw_profiles: Any = getattr(self.sheets, 'SHEET_PROFILES', {})
        profiles: Dict[str, Any] = cast(Dict[str, Any], raw_profiles) if isinstance(raw_profiles, dict) else {}
        keyboard: List[List[KeyboardButton]] = []
        temp_row: List[KeyboardButton] = []
        
        icons = {"Orders": "📝", "Contacts": "👥", "Vehicles": "🚗", "Equipment": "🛡️", "Arrests": "📑", "FirearmRegistry": "🔫"}
        
        # Use a list of keys to avoid the .items() issues if it persists
        profile_keys = list(profiles.keys())
        for sheet_name in profile_keys:
            profile = profiles[sheet_name]
            icon = icons.get(sheet_name, "📁")
            display = profile.get("display_name", sheet_name)
            temp_row.append(KeyboardButton(f"{icon} บันทึก{display}"))
            if len(temp_row) == 2:
                keyboard.append(temp_row)
                temp_row = []
        
        if temp_row: keyboard.append(temp_row)
        keyboard.append([KeyboardButton("🔙 กลับเมนูหลัก")])
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_name = update.effective_user.first_name
        welcome_text = (
            f"👮 **ระบบเลขาธุรการอัจฉริยะ (Virtual Admin Assistant)**\n"
            f"สวัสดีครับคุณ {user_name} ผมพร้อมช่วยงานธุรการแล้วครับ\n\n"
            f"✅ **เลือกเมนูที่ต้องการใช้งานด้านล่างนี้ได้เลยครับ:**"
        )
        await update.message.reply_text(welcome_text, reply_markup=self._get_main_menu(), parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Intelligent Engine: Identifies Intent (Save, Ask, Search, or Menu)"""
        text = update.message.text.strip()
        logger.info(f"Incoming message from {update.effective_user.first_name}: {text}")
        
        try:
            # --- 🛠️ 1. Menu Navigation & Sub-Menus ---
            if text == "📊 รายงานสรุป":
                await update.message.reply_text("📈 **เลือกรายงานที่ต้องการสรุป:**", reply_markup=self._get_summary_menu())
                return
            if text == "🔙 กลับเมนูหลัก":
                context.user_data.pop('save_mode', None)
                await update.message.reply_text("🏠 **กลับสู่เมนูหลัก:**", reply_markup=self._get_main_menu())
                return
            if text == "✍️ บันทึกงาน":
                msg = (
                    "📋 **วิธีการบันทึกข้อมูลแบบอัจฉริยะ:**\n"
                    "1. **บันทึกปกติ:** พิมพ์ 'จด [ชื่อ/รายละเอียด]' เช่น `จด พ.ต.อ.ขาว 081-xxxx` \n"
                    "2. **บันทึกการจับกุม/ประชุม:** ส่งข้อความรายงานการจับกุม หรือสรุปการประชุมมาได้เลย ระบบจะแยกชื่อผู้ต้องหาและรายละเอียดให้อัตโนมัติ (Arrest/Meeting Detection)\n"
                    "3. **บันทึกบัญชีปืน:** ส่งข้อมูลเลขโล่ ยี่ห้อปืน และคนเบิกยืมมาได้เลยครับ\n"
                    "4. **บันทึกตาราง:** ก๊อปปี้ตารางจาก Excel หรือ Markdown มาวางได้เลย\n\n"
                    "👇 **หรือเลือกชีทที่ต้องการบันทึกโดยตรง:**"
                )
                await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=self._get_save_menu())
                return
            
            if text == "❓ ช่วยเหลือ":
                await update.message.reply_text("👮 **บอทเลขาธุรการ:** ถ้าต้องการหาข้อมูลให้พิมพ์สิ่งที่ต้องการหามาได้เลยครับ หรือกดปุ่มเมนูเพื่อดูสรุปยอดต่างๆ")
                return
            
            # --- 💾 Save to Specific Sheets (Dynamic Mode Switch) ---
            raw_profiles: Any = getattr(self.sheets, 'SHEET_PROFILES', {})
            sheet_profiles: Dict[str, Any] = cast(Dict[str, Any], raw_profiles) if isinstance(raw_profiles, dict) else {}
            profile_keys_search = list(sheet_profiles.keys())
            for sheet_name in profile_keys_search:
                profile = sheet_profiles[sheet_name]
                display = profile.get("display_name", sheet_name)
                if f"บันทึก{display}" in text:
                    context.user_data['save_mode'] = sheet_name
                    await update.message.reply_text(
                        f"✍️ **โหมดบันทึก{display}:**\n"
                        f"หน้าที่: {profile.get('duty')}\n"
                        f"ส่งรายละเอียดที่ต้องการบันทึกมาได้เลยครับ"
                    )
                    return
            if "ค้นหา" in text:
                await update.message.reply_text("🔎 **โหมดค้นหา:** พิมพ์ชื่อ, ทะเบียนรถ, เลขโล่ หรือคำค้นหาที่ต้องการได้เลยครับ")
                return
            # 🟢 2. Summaries & Reports (Missions)
            text_norm = text.replace(" ", "")
            if any(k in text for k in ["ภารกิจวันนี้", "งานวันนี้"]) or text_norm == "ภารกิจวันนี้":
                await update.message.reply_chat_action("typing")
                summary = self.sheets.get_today_summary()
                await update.message.reply_text(summary, parse_mode='Markdown')
                return

            if any(k in text for k in ["ภารกิจพรุ่งนี้", "งานพรุ่งนี้"]) or text_norm == "ภารกิจพรุ่งนี้":
                await update.message.reply_chat_action("typing")
                summary = self.sheets.get_tomorrow_summary()
                await update.message.reply_text(summary, parse_mode='Markdown')
                return

            # Special Case: 'ภารกิจ [คำค้นหา]' -> Search specifically for missions/orders
            if text.startswith("ภารกิจ") and len(text) > 6:
                await update.message.reply_chat_action("typing")
                results = self.sheets.search_all(text)
                await update.message.reply_text(results, parse_mode='Markdown')
                return
            
            # --- 📈 3. Summary Reports ---
            if text == "🚗 ยานพาหนะ" or "สรุปรถ" in text:
                await update.message.reply_chat_action("typing")
                report = self.sheets.get_vehicle_summary()
                await update.message.reply_text(report, parse_mode='Markdown', reply_markup=self._get_summary_menu())
                return
            if text == "🛡️ ยุทธภัณฑ์" or "สรุปยุทธภัณฑ์" in text:
                await update.message.reply_chat_action("typing")
                report = self.sheets.get_equipment_summary()
                await update.message.reply_text(report, parse_mode='Markdown', reply_markup=self._get_summary_menu())
                return
            if text == "💰 งบประมาณ" or "สรุปงบ" in text:
                await update.message.reply_chat_action("typing")
                report = self.sheets.get_budget_summary()
                await update.message.reply_text(report, parse_mode='Markdown', reply_markup=self._get_summary_menu())
                return
            if text == "🔫 บัญชีปืน" or "สรุปปืน" in text:
                await update.message.reply_chat_action("typing")
                report = self.sheets.get_firearm_registry_summary()
                await update.message.reply_text(report, parse_mode='Markdown', reply_markup=self._get_summary_menu())
                return

            # 🟢 4. Auto-Save based on Mode or Keywords (Using Code Parser)
            save_keywords = ['จด', 'บันทึก', 'เก็บ', 'save', 'add', 'แจ้งเตือน', 'เตือน', 'นัดหมาย', 'จับกุม', 'อาวุธปืน', 'ยืมปืน', 'เบิกปืน', 'คืนปืน']
            is_bulk = (text.count('\n') > 2 or '|' in text)
            
            current_mode = context.user_data.get('save_mode')
            if current_mode or any(k in text[:10] for k in save_keywords) or is_bulk:
                # Now calls handle_text_save (non-AI deterministic parser)
                await self.contact_handler.handle_text_save(update, context, force_mode=current_mode)
                return

            # 🟢 3. Status/Summary Commands
            if any(k in text for k in ["เช็คเบิก", "สถานะเบิกจ่าย", "เบิกถึง", "จ่ายถึง", "ถึงไหน"]):
                await update.message.reply_chat_action("typing")
                report = self.sheets.get_expenditure_status()
                await update.message.reply_text(report, parse_mode='Markdown')
                return

            # 🟢 4. Ask Command (Now strictly search-based, no AI)
            if any(text.lower().startswith(k) for k in ["ถาม", "ask", "how", "ช่วยบอก"]):
                query = re.sub(r'^(ถาม|ask|ช่วยบอก)\s*', '', text, flags=re.IGNORECASE).strip()
                await update.message.reply_chat_action("typing")
                response = self.sheets.search_all(query)
                await update.message.reply_text(f"📝 **ผลการค้นหา:**\n{response}", parse_mode='Markdown')
                return

            # 🔍 5. Global Search
            await update.message.reply_chat_action("typing")
            results = self.sheets.search_all(text)
            logger.info(f"Search results for '{text}': {len(results)} chars")
            # 🛡️ Deliver with Markdown for the new Form format
            await update.message.reply_text(results, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in handle_message: {e}", exc_info=True)
            await update.message.reply_text(f"❌ **เกิดข้อผิดพลาด:** {str(e)}\nกรุณาลองใหม่อีกครั้งครับ")

    async def _show_help(self, update: Update):
        help_msg = (
            "🛡️ **System Guide**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🔍 **Search:** Just type any name/word.\n"
            "📞 **Save:** Type `จดชื่อ [Detail]` to record.\n"
            "🤖 **Ask:** Type `ถาม [Question]` for help.\n"
            "━━━━━━━━━━━━━━━━━━"
        )
        await update.message.reply_text(help_msg, parse_mode='Markdown')

    async def check_reminders(self, context: ContextTypes.DEFAULT_TYPE):
        """Background Task: Proactively sends notifications for due reminders."""
        try:
            # Fetch reminders that need to be alerted
            reminders = self.sheets.get_due_reminders()
            if not reminders: return

            for r in reminders:
                topic, content, time_str, row_idx = r
                logger.info(f"🔔 Due Reminder Found: {topic} at {time_str}")
                msg = (f"⏰ **[แจ้งเตือนนัดหมาย]**\n"
                       f"━━━━━━━━━━━━━━━━━━\n"
                       f"📌 **หัวข้อ:** {topic}\n"
                       f"📝 **รายละเอียด:** {content}\n"
                       f"⏳ **เวลา:** {time_str}\n"
                       f"━━━━━━━━━━━━━━━━━━")
                
                await context.bot.send_message(
                    chat_id=self.config.ADMIN_CHAT_ID, 
                    text=msg, 
                    parse_mode='Markdown'
                )
                # Mark as 'Alerted' or 'Done' in sheet to prevent duplicate alerts
                self.sheets.mark_reminder_done(row_idx)
                logger.info(f"Proactive alert sent for: {topic}")
                
        except Exception as e:
            logger.error(f"Reminder Job Error: {e}")

    def run(self):
        try:
            if not self.sheets.connect():
                logger.error("🛑 Could not connect to Google Sheets. Please check your internet or credentials.")
                return
            
            app = Application.builder().token(self.config.TELEGRAM_BOT_TOKEN).build()
            
            # 🕒 Job Queue for Auto-Notifications
            job_queue = app.job_queue
            job_queue.run_repeating(self.check_reminders, interval=60, first=10)
            
            app.add_handler(CommandHandler("start", self.start))
            app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            logger.info("Smart Police Professional System (with Auto-Alerts) is Online.")
            app.run_polling()
        except Exception as e:
            logger.error(f"Startup crash: {e}")

if __name__ == "__main__":
    bot = SmartPoliceBot()
    bot.run()
