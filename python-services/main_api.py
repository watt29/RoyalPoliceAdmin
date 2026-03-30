from fastapi import FastAPI, HTTPException, BackgroundTasks # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from pydantic import BaseModel # type: ignore
from typing import Optional, List, Dict, Any, cast
import os
import sys
import uvicorn # type: ignore
import asyncio
import httpx # type: ignore
from datetime import datetime

# เพิ่ม path เดิมเพื่อใช้ services เดิม
sys.path.append('.')
sys.path.append('..')

try:
    from services.sheets_service import SheetsService # type: ignore
    from config import Config # type: ignore
    from handlers.contact_handler import ContactHandler # type: ignore
    from handlers.order_handler import OrderHandler # type: ignore
    from handlers.vehicle_handler import VehicleHandler # type: ignore
except ImportError as e:
    print(f"Import warning: {e}")
    # Fallback for development
    SheetsService = None
    Config = None
    ContactHandler = None

# Initialize FastAPI app
app = FastAPI(
    title="Smart Police Report API",
    description="Backend API สำหรับระบบรายงานตำรวจอัจฉริยะ",
    version="2.0.0"
)

# CORS middleware for Render deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services (with error handling for Render)
config = None
sheets_service = None

try:
    if Config:
        # Note: Config in config.py is used as a class with static attributes
        sheets_service = SheetsService(Config.SERVICE_ACCOUNT_PATH, Config.GOOGLE_SHEET_ID) # type: ignore
        print("✅ SheetsService initialized with credentials and ID")
except Exception as e:
    print(f"⚠️ Services initialization warning: {e}")

# Telegram Bot API endpoint (will be set by Render environment)
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

# In-memory session storage (use Redis in production)
user_sessions = {}

@app.on_event("startup")
async def startup_event():
    print("🐍 Smart Police API starting on Render...")

    # Test Google Sheets connection
    if sheets_service:
        try:
            # Test with a simple operation
            print("🔗 Testing Google Sheets connection...")
            # You could add a simple test here
            print("✅ Google Sheets connection ready")
        except Exception as e:
            print(f"❌ Google Sheets connection failed: {e}")
    else:
        print("⚠️ Running without Google Sheets integration")

@app.get("/")
async def root():
    return {
        "service": "Smart Police Report API",
        "version": "2.0.0",
        "status": "running on Render",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv('PYTHON_ENV', 'development')
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "environment": os.getenv('PYTHON_ENV', 'development')
    }

    # Check services
    if sheets_service:
        status["google_sheets"] = "connected"
    else:
        status["google_sheets"] = "not_connected"

    return status

@app.post("/process-message", response_model=APIResponse)
async def process_message(request: MessageRequest):
    """
    ประมวลผลข้อความจากผู้ใช้และตอบกลับ
    """
    try:
        user_id = request.user_id
        message = request.message.strip()

        msg_preview = str(message)[:50] # type: ignore
        print(f"📨 Processing message from user {user_id}: {msg_preview}...")

        # ตรวจสอบประเภทของข้อความ
        intent = await detect_intent(message)

        if intent == "search":
            result = await handle_search_request(message, user_id)
        elif intent == "save":
            result = await handle_save_request(message, user_id)
        else:
            # Fallback to general processing if no specific intent is found
            # but still try to see if handlers can identify it (e.g. captures names, plates, etc)
            result = await handle_save_request(message, user_id)

        return result

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        return APIResponse( # type: ignore
            success=False, # type: ignore
            message="เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง", # type: ignore
            error=str(e) # type: ignore
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
            return APIResponse( # type: ignore
                success=True, # type: ignore
                message="คำสั่งไม่ถูกต้อง กรุณาเลือกจากเมนู", # type: ignore
                edit_message=True # type: ignore
            )

    except Exception as e:
        print(f"❌ Error handling callback: {e}")
        return APIResponse( # type: ignore
            success=False, # type: ignore
            message="เกิดข้อผิดพลาดในการประมวลผล", # type: ignore
            error=str(e) # type: ignore
        )

# Helper Functions

async def detect_intent(message: str) -> str:
    """ตรวจสอบเจตนาของข้อความ"""
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
        return "inquiry"

# 🌉 Mock Classes to Bridge Handlers with FastAPI
class MockMessage:
    def __init__(self, text=""):
        self.text = text
        self.responses = []
    async def reply_text(self, text, parse_mode=None, reply_markup=None):
        clean_text = text.replace("**", "").replace("__", "") # Simple clean
        self.responses.append(clean_text)
        return self # Return self for fluid edit_text
    async def edit_text(self, text, parse_mode=None, reply_markup=None):
        # In mock, edit_text just adds to responses or replaces last
        if self.responses: self.responses[-1] = text
        else: self.responses.append(text)
        return self

class MockUpdate:
    def __init__(self, text, user_id, chat_id):
        self.message = MockMessage(text)
        self.effective_user = type('User', (), {'id': user_id, 'first_name': 'User'}) # type: ignore
        self.effective_chat = type('Chat', (), {'id': chat_id}) # type: ignore

async def handle_save_request(message: str, user_id: int) -> APIResponse:
    """จัดการคำขอบันทึกข้อมูล โดยใช้ ContactHandler อัจฉริยะ (Stronger Version)"""
    try:
        if not sheets_service or not ContactHandler:
            return APIResponse(success=False, message="⚠️ บริการบันทึกข้อมูลไม่พร้อมใช้งาน (SheetsService/Handler missing)") # type: ignore

        # 1. Initialize Handler
        handler = ContactHandler(sheets_service) # type: ignore
        
        # 2. Create Mock Environment
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        update = MockUpdate(message, user_id, user_id) # Using user_id as chat_id
        
        # 3. Call The Real Processor (The "Strong Heart")
        # handle_text_save returns True if it handled/saved something
        success = await handler.handle_text_save(cast(Any, update), None, message, timestamp)
        
        # 4. Collect Responses
        responses = update.message.responses
        final_msg = "\n".join(responses) if responses else "บอทได้รับข้อมูลแล้ว แต่ไม่สามารถระบุหมวดหมู่ที่ชัดเจนได้"
        
        if success:
            return APIResponse(success=True, message=final_msg) # type: ignore
        else:
            return APIResponse(success=True, message="ไม่พบข้อมูลที่ต้องการบันทึก (เช่น ชื่อผู้ต้องหา, ทะเบียนรถ, หรือคำสั่ง) กรุณาลองตรวจสอบรูปแบบข้อความในคู่มือ /help") # type: ignore

    except Exception as e:
        print(f"❌ Error in robust save: {e}")
        return APIResponse(success=False, message="เกิดข้อผิดพลาดในการบันทึกข้อมูลทางเทคนิค", error=str(e)) # type: ignore

async def handle_search_request(message: str, user_id: int) -> APIResponse:
    """จัดการคำขอค้นหาข้อมูลอัจฉริยะ (Smart Search)"""
    try:
        if not sheets_service:
            return APIResponse(success=False, message="⚠️ บริการค้นหาไม่พร้อมใช้งาน") # type: ignore

        # Utilize sheets_service's search_all logic
        results_untouch = sheets_service.search_all(message)
        
        # results_untouch can be a string or a list
        if isinstance(results_untouch, str):
            return APIResponse(success=True, message=results_untouch) # type: ignore
            
        results = cast(List[Dict], results_untouch)
        if not results:
            return APIResponse(success=True, message=f"🔍 **ค้นหาสำหรับ:** {message}\n{sheets_service.DIVIDER}\n❌ ไม่พบข้อมูลที่เกี่ยวข้อง") # type: ignore

        response_text = f"🔍 **ผลการค้นหาสำหรับ:** {message}\n{sheets_service.DIVIDER}\n"
        for i, res in enumerate(results):
            if i >= 5: break
            target = res.get('target', 'Data')
            match = res.get('match', {})
            val = match.get('Name') or match.get('Detail') or match.get('Plate') or "ข้อมูล"
            response_text += f"{i+1}. [{target}] {val}\n"
        
        if len(results) > 5:
            response_text += f"\n...พบทั้งหมด {len(results)} รายการ (แสดง 5 อันดับแรก)"

        return APIResponse(success=True, message=response_text) # type: ignore

    except Exception as e:
        print(f"❌ Error in smart search: {e}")
        return APIResponse(success=False, message="เกิดข้อผิดพลาดในการค้นหา", error=str(e)) # type: ignore

async def handle_inquiry_request(message: str, user_id: int) -> APIResponse:
    """จัดการคำถามทั่วไป"""
    try:
        response_text = f"🤖 **ได้รับคำถาม:** {message}\n\nระบบ AI กำลังประมวลผล"

        return APIResponse( # type: ignore
            success=True, # type: ignore
            message=response_text # type: ignore
        )

    except Exception as e:
        return APIResponse( # type: ignore
            success=False, # type: ignore
            message="เกิดข้อผิดพลาดในการตอบคำถาม", # type: ignore
            error=str(e) # type: ignore
        )

async def handle_general_message(message: str, user_id: int) -> APIResponse:
    """จัดการข้อความทั่วไป"""
    return APIResponse( # type: ignore
        success=True, # type: ignore
        message="ระบบไม่เข้าใจคำสั่ง กรุณาระบุให้ชัดเจนมากขึ้น หรือเลือกจากเมนูด้านล่าง", # type: ignore
        keyboard=create_main_keyboard() # type: ignore
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
                {"text": "📋 คำสั่ง", "callback_data": "save_order"}
            ],
            [
                {"text": "🔙 กลับเมนูหลัก", "callback_data": "back_main"}
            ]
        ]
    }

    return APIResponse( # type: ignore
        success=True, # type: ignore
        message="📝 **เลือกประเภทข้อมูลที่ต้องการบันทึก:**", # type: ignore
        keyboard=keyboard, # type: ignore
        edit_message=True # type: ignore
    )

async def show_search_menu(user_id: int) -> APIResponse:
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "👤 ค้นหาบุคลากร", "callback_data": "search_contact"},
                {"text": "🚗 ค้นหายานพาหนะ", "callback_data": "search_vehicle"}
            ],
            [
                {"text": "🔫 ค้นหาอาวุธปืน", "callback_data": "search_firearm"}
            ],
            [
                {"text": "🔙 กลับเมนูหลัก", "callback_data": "back_main"}
            ]
        ]
    }

    return APIResponse( # type: ignore
        success=True, # type: ignore
        message="🔍 **เลือกประเภทข้อมูลที่ต้องการค้นหา:**", # type: ignore
        keyboard=keyboard, # type: ignore
        edit_message=True # type: ignore
    )

async def show_report_menu(user_id: int) -> APIResponse:
    return APIResponse( # type: ignore
        success=True, # type: ignore
        message="📊 **ฟีเจอร์รายงานกำลังพัฒนา**\nจะเปิดให้ใช้งานเร็วๆ นี้", # type: ignore
        edit_message=True # type: ignore
    )

async def show_settings_menu(user_id: int) -> APIResponse:
    return APIResponse( # type: ignore
        success=True, # type: ignore
        message="⚙️ **ฟีเจอร์การตั้งค่ากำลังพัฒนา**\nจะเปิดให้ใช้งานเร็วๆ นี้", # type: ignore
        edit_message=True # type: ignore
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

**🌐 Deployed on Render.com**
    """

    return APIResponse( # type: ignore
        success=True, # type: ignore
        message=help_text, # type: ignore
        edit_message=True # type: ignore
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

# Background tasks for notifications
async def send_notification_to_bot(
    chat_id: int,
    message: str,
    options: Optional[Dict] = None,
    background_tasks: Optional[BackgroundTasks] = None
):
    """ส่งแจ้งเตือนผ่าน Telegram bot"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BOT_API_URL}/send-notification",
                json={
                    "chat_id": chat_id,
                    "message": message,
                    "options": options or {}
                },
                timeout=30.0
            )
            return response.json()
    except Exception as e:
        print(f"Error sending notification: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Render uses PORT environment variable
    port = int(os.getenv('PORT', os.getenv('PYTHON_API_PORT', 8000)))

    # Determine if we're in production (Render) or development
    is_production = os.getenv('PYTHON_ENV') == 'production'

    print(f"🚀 Starting API on port {port} (production: {is_production})")

    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=port,
        reload=not is_production,  # No reload in production
        log_level="info" if is_production else "debug"
    )