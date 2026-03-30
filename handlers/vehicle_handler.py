import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.sheets_service import SheetsService

logger = logging.getLogger(__name__)

class VehicleHandler:
    DIVIDER = "━━━━━━━━━━━━━━━━━━"

    def __init__(self, sheets_service: SheetsService):
        self.sheets = sheets_service

    async def search_vehicles(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """Professionalized vehicle search"""
        if not self.sheets.vehicles_sheet:
            await update.message.reply_text("❌ Error: Vehicle database not connected.")
            return

        # Let SheetsService handle the heavy lifting for consistency
        res = self.sheets.search_all(query)
        if "No records" in res:
            await update.message.reply_text(f"🔍 No vehicle found matching: **{query}**", parse_mode='Markdown')
        else:
            await update.message.reply_text(res, parse_mode='Markdown')
