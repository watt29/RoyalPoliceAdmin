from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import sys
import uvicorn
import asyncio
import httpx
from datetime import datetime

# เพิ่ม path เดิมเพื่อใช้ services เดิม
sys.path.append('..')
from services.sheets_service import GoogleSheetsService
from handlers.contact_handler import ContactHandler
from handlers.logic_utils import extract_data_with_ai
from config import Config

# Initialize FastAPI app
app = FastAPI(
    title="Smart Police Report API",
    description="Backend API สำหรับระบบรายงานตำรวจอัจฉริยะ",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
config = Config()
sheets_service = GoogleSheetsService(config)
contact_handler = ContactHandler(sheets_service)

# Telegram Bot API endpoint
BOT_API_URL = os.getenv('BOT_API_URL', 'http://localhost:3000')

# Pydantic models
class MessageRequest(BaseModel):
    message: str
    user_id: int
    chat_id: int
    user_info: Dict[str, Any]

class CallbackRequest(BaseModel):
    callback_data: str
    user_id: int
    chat_id: int
    message_id: int

class APIResponse(BaseModel):
    success: bool
    message: str
    keyboard: Optional[Dict] = None
    attachments: Optional[List[Dict]] = None
    error: Optional[str] = None
    edit_message: Optional[bool] = False

# In-memory session storage (ใช้ Redis ในการ deploy จริง)
user_sessions = {}

@app.on_event("startup")
async def startup_event():
    print("🐍 Python API Server เริ่มทำงาน...")
    print("🔗 เชื่อมต่อ Google Sheets...")

    # ทดสอบการเชื่อมต่อ
    try:
        test_data = sheets_service.get_sheet_data('Contacts', limit=1)
        print(f"✅ Google Sheets เชื่อมต่อสำเร็จ ({len(test_data)} records found)")
    except Exception as e:
        print(f"❌ Google Sheets เชื่อมต่อล้มเหลว: {e}")

@app.get("/")
async def root():
    return {
        "service": "Smart Police Report API",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/process-message", response_model=APIResponse)
async def process_message(request: MessageRequest):
    """
    ประมวลผลข้อความจากผู้ใช้และตอบกลับ
    """
    try:
        user_id = request.user_id
        message = request.message.strip()

        print(f"📨 Processing message from user {user_id}: {message[:50]}...")

        # ตรวจสอบประเภทของข้อความ
        intent = await detect_intent(message)

        if intent == "search":
            result = await handle_search_request(message, user_id)
        elif intent == "save":
            result = await handle_save_request(message, user_id)
        elif intent == "inquiry":
            result = await handle_inquiry_request(message, user_id)
        else:
            result = await handle_general_message(message, user_id)

        return result

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        return APIResponse(
            success=False,
            message="เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง",
            error=str(e)
        )

@app.post("/handle-callback", response_model=APIResponse)
async def handle_callback(request: CallbackRequest):
    """
    จัดการ callback จากปุ่มต่างๆ
    """
    try:
        callback_data = request.callback_data
        user_id = request.user_id

        print(f"🔘 Processing callback from user {user_id}: {callback_data}")

        if callback_data == "menu_save":
            return await show_save_menu(user_id)
        elif callback_data == "menu_search":
            return await show_search_menu(user_id)
        elif callback_data == "menu_report":
            return await show_report_menu(user_id)
        elif callback_data == "menu_settings":
            return await show_settings_menu(user_id)
        elif callback_data == "menu_help":
            return await show_help_menu(user_id)
        else:
            return APIResponse(
                success=True,
                message="คำสั่งไม่ถูกต้อง กรุณาเลือกจากเมนู",
                edit_message=True
            )

    except Exception as e:
        print(f"❌ Error handling callback: {e}")
        return APIResponse(
            success=False,
            message="เกิดข้อผิดพลาดในการประมวลผล",
            error=str(e)
        )

# Helper Functions

async def detect_intent(message: str) -> str:
    """
    ตรวจสอบเจตนาของข้อความ
    """
    message_lower = message.lower()

    # คำสำคัญสำหรับการค้นหา
    search_keywords = ["ค้นหา", "หา", "ดู", "เช็ค", "สอบถาม", "ตรวจสอบ"]

    # คำสำคัญสำหรับการบันทึก
    save_keywords = ["บันทึก", "เก็บ", "บันทึก", "เพิ่ม", "รายงาน"]

    if any(keyword in message_lower for keyword in search_keywords):
        return "search"
    elif any(keyword in message_lower for keyword in save_keywords):
        return "save"
    else:
        # ใช้ AI ตรวจสอบเจตนา
        return await detect_intent_with_ai(message)

async def detect_intent_with_ai(message: str) -> str:
    """
    ใช้ AI ตรวจสอบเจตนาของข้อความ
    """
    try:
        # ใช้ logic เดิมจาก contact_handler
        intent_result = contact_handler.detect_intent(message)
        return intent_result.get('intent', 'inquiry')
    except:
        return "inquiry"

async def handle_search_request(message: str, user_id: int) -> APIResponse:
    """
    จัดการคำขอค้นหาข้อมูล
    """
    try:
        # ใช้ search logic เดิม
        search_results = contact_handler.search_data(message)

        if search_results:
            response_text = "🔍 **ผลการค้นหา:**\n\n"
            for result in search_results[:5]:  # แสดงแค่ 5 รายการแรก
                response_text += f"• {result}\n"

            if len(search_results) > 5:
                response_text += f"\n_และอีก {len(search_results) - 5} รายการ_"
        else:
            response_text = "❌ ไม่พบข้อมูลที่ค้นหา กรุณาลองคำค้นหาอื่น"

        return APIResponse(
            success=True,
            message=response_text
        )

    except Exception as e:
        return APIResponse(
            success=False,
            message="เกิดข้อผิดพลาดในการค้นหา",
            error=str(e)
        )

async def handle_save_request(message: str, user_id: int) -> APIResponse:
    """
    จัดการคำขอบันทึกข้อมูล
    """
    try:
        # ใช้ save logic เดิม
        save_result = contact_handler.save_data(message, user_id)

        if save_result.get('success'):
            response_text = f"✅ **บันทึกข้อมูลสำเร็จ**\n\n{save_result.get('message', '')}"
        else:
            response_text = f"❌ **บันทึกข้อมูลล้มเหลว**\n\n{save_result.get('error', 'ไม่ทราบสาเหตุ')}"

        return APIResponse(
            success=save_result.get('success', False),
            message=response_text
        )

    except Exception as e:
        return APIResponse(
            success=False,
            message="เกิดข้อผิดพลาดในการบันทึกข้อมูล",
            error=str(e)
        )

async def handle_inquiry_request(message: str, user_id: int) -> APIResponse:
    """
    จัดการคำถามทั่วไป
    """
    try:
        # ใช้ AI ตอบคำถาม
        inquiry_result = contact_handler.handle_inquiry(message)

        return APIResponse(
            success=True,
            message=inquiry_result.get('message', 'ไม่สามารถตอบคำถามได้ในขณะนี้')
        )

    except Exception as e:
        return APIResponse(
            success=False,
            message="เกิดข้อผิดพลาดในการตอบคำถาม",
            error=str(e)
        )

async def handle_general_message(message: str, user_id: int) -> APIResponse:
    """
    จัดการข้อความทั่วไป
    """
    return APIResponse(
        success=True,
        message="ระบบไม่เข้าใจคำสั่ง กรุณาระบุให้ชัดเจนมากขึ้น หรือเลือกจากเมนูด้านล่าง",
        keyboard=create_main_keyboard()
    )

# Menu functions
async def show_save_menu(user_id: int) -> APIResponse:
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "👤 บุคลากร", "callback_data": "save_contact"},
                {"text": "🚗 ยานพาหนะ", "callback_data": "save_vehicle"}
            ],
            [
                {"text": "🔫 อาวุธปืน", "callback_data": "save_firearm"},
                {"text": "⚔️ อุปกรณ์", "callback_data": "save_equipment"}
            ],
            [
                {"text": "👮 การจับกุม", "callback_data": "save_arrest"},
                {"text": "📋 คำสั่ง", "callback_data": "save_order"}
            ],
            [
                {"text": "🔙 กลับเมนูหลัก", "callback_data": "back_main"}
            ]
        ]
    }

    return APIResponse(
        success=True,
        message="📝 **เลือกประเภทข้อมูลที่ต้องการบันทึก:**",
        keyboard=keyboard,
        edit_message=True
    )

async def show_search_menu(user_id: int) -> APIResponse:
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "👤 ค้นหาบุคลากร", "callback_data": "search_contact"},
                {"text": "🚗 ค้นหายานพาหนะ", "callback_data": "search_vehicle"}
            ],
            [
                {"text": "🔫 ค้นหาอาวุธปืน", "callback_data": "search_firearm"},
                {"text": "👮 ค้นหาการจับกุม", "callback_data": "search_arrest"}
            ],
            [
                {"text": "🔙 กลับเมนูหลัก", "callback_data": "back_main"}
            ]
        ]
    }

    return APIResponse(
        success=True,
        message="🔍 **เลือกประเภทข้อมูลที่ต้องการค้นหา:**",
        keyboard=keyboard,
        edit_message=True
    )

async def show_report_menu(user_id: int) -> APIResponse:
    return APIResponse(
        success=True,
        message="📊 **ฟีเจอร์รายงานกำลังพัฒนา**\nจะเปิดให้ใช้งานเร็วๆ นี้",
        edit_message=True
    )

async def show_settings_menu(user_id: int) -> APIResponse:
    return APIResponse(
        success=True,
        message="⚙️ **ฟีเจอร์การตั้งค่ากำลังพัฒนา**\nจะเปิดให้ใช้งานเร็วๆ นี้",
        edit_message=True
    )

async def show_help_menu(user_id: int) -> APIResponse:
    help_text = """
📚 **คู่มือการใช้งาน Smart Police Report Bot**

**💬 การส่งข้อความ:**
• พิมพ์ข้อความธรรมชาติเพื่อบันทึกข้อมูล
• ระบบจะแยกแยะประเภทข้อมูลอัตโนมัติ

**🔍 การค้นหา:**
• พิมพ์ "ค้นหา [ข้อมูลที่ต้องการ]"
• หรือใช้เมนูค้นหาแบบแยกประเภท

**📝 การบันทึก:**
• พิมพ์รายละเอียดข้อมูลตรงๆ
• ระบบจะสกัดข้อมูลและบันทึกลงฐานข้อมูล

**🆘 การขอความช่วยเหลือ:**
• พิมพ์ /start เพื่อกลับเมนูหลัก
• พิมพ์คำถามเพื่อขอคำแนะนำ
    """

    return APIResponse(
        success=True,
        message=help_text,
        edit_message=True
    )

def create_main_keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "📝 บันทึกข้อมูล", "callback_data": "menu_save"},
                {"text": "🔍 ค้นหาข้อมูล", "callback_data": "menu_search"}
            ],
            [
                {"text": "📊 สรุปรายงาน", "callback_data": "menu_report"},
                {"text": "⚙️ ตั้งค่า", "callback_data": "menu_settings"}
            ]
        ]
    }

# Background tasks
@app.post("/send-notification")
async def send_notification_to_bot(
    chat_id: int,
    message: str,
    options: Dict = None,
    background_tasks: BackgroundTasks = None
):
    """
    ส่งแจ้งเตือนผ่าน Telegram bot
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BOT_API_URL}/send-notification",
                json={
                    "chat_id": chat_id,
                    "message": message,
                    "options": options or {}
                }
            )
            return response.json()
    except Exception as e:
        print(f"Error sending notification: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.getenv('PYTHON_API_PORT', 8000))
    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )