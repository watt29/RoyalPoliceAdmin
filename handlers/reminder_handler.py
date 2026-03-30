import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.sheets_service import SheetsService
from datetime import datetime

logger = logging.getLogger(__name__)

class ReminderHandler:
    def __init__(self, sheets_service: SheetsService):
        self.sheets = sheets_service

    async def save_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save a new reminder from conversation"""
        topic = context.user_data.get('reminder_topic')
        content = context.user_data.get('reminder_content')
        remind_time = update.message.text
        
        if not self.sheets.reminders_sheet:
            await update.message.reply_text("❌ เชื่อมต่อ Database ไม่ได้")
            return
            
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        # Topic, Content, Reminder_Time, Status, Created_At
        row = [topic, content, remind_time, "รอดำเนินการ", timestamp]
        
        try:
            self.sheets.reminders_sheet.append_row(row)
            await update.message.reply_text(
                f"⏰ **ตั้งเวลาเรียบร้อย!**\n\n"
                f"📌 หัวข้อ: {topic}\n"
                f"📅 เวลา: {remind_time}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Save reminder error: {e}")
            await update.message.reply_text("❌ เกิดข้อผิดพลาดในการบันทึก")
