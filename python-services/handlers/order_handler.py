import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.sheets_service import SheetsService
from datetime import datetime

logger = logging.getLogger(__name__)

class OrderHandler:
    def __init__(self, sheets_service: SheetsService):
        self.sheets = sheets_service

    async def save_order(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save a new order from conversation"""
        detail = context.user_data.get('order_detail')
        commander = context.user_data.get('order_commander')
        deadline = update.message.text
        
        if not self.sheets.orders_sheet:
            await update.message.reply_text("❌ เชื่อมต่อ Database ไม่ได้")
            return
            
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        # Detail, Commander, Deadline, Status, Urgency, Note, Timestamp
        row = [detail, commander, deadline, "รอดำเนินการ", "ปกติ", "-", timestamp]
        
        try:
            self.sheets.orders_sheet.append_row(row)
            await update.message.reply_text(
                f"✅ **บันทึกข้อสั่งการเรียบร้อย!**\n\n"
                f"📋 รายละเอียด: {detail}\n"
                f"👮 ผู้สั่ง: {commander}\n"
                f"📅 กำหนดส่ง: {deadline}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Save order error: {e}")
            await update.message.reply_text("❌ เกิดข้อผิดพลาดในการบันทึก")
