# เพิ่ม Code นี้ใน python-services/main_api.py

# Import file handler
from file_handler import handle_file_operation

# Pydantic model สำหรับ file operations
class FileOperationRequest(BaseModel):
    operation: str  # create, edit, delete, read, list
    filename: Optional[str] = None
    content: Optional[str] = ""
    user_id: int

@app.post("/file-operation", response_model=APIResponse)
async def handle_file_request(request: FileOperationRequest):
    """
    จัดการคำขอเกี่ยวกับไฟล์ผ่าน Telegram
    """
    try:
        result = await handle_file_operation(
            operation=request.operation,
            user_id=request.user_id,
            filename=request.filename or "",
            content=request.content or ""
        )

        if result["success"]:
            return APIResponse(
                success=True,
                message=result["message"]
            )
        else:
            return APIResponse(
                success=False,
                message=result["error"]
            )

    except Exception as e:
        print(f"❌ Error in file operation: {e}")
        return APIResponse(
            success=False,
            message="เกิดข้อผิดพลาดในการจัดการไฟล์",
            error=str(e)
        )

# เพิ่มการตรวจสอบ file commands ใน detect_intent
async def detect_intent(message: str) -> str:
    """ตรวจสอบเจตนาของข้อความ (รวม file operations)"""
    message_lower = message.lower()

    # คำสำคัญสำหรับไฟล์
    file_keywords = ["สร้าง", "แก้ไข", "ลบ", "อ่าน", "ไฟล์", "/create", "/edit", "/delete", "/read", "/list"]

    # คำสำคัญสำหรับการค้นหา
    search_keywords = ["ค้นหา", "หา", "ดู", "เช็ค", "สอบถาม", "ตรวจสอบ"]

    # คำสำคัญสำหรับการบันทึก
    save_keywords = ["บันทึก", "เก็บ", "เพิ่ม", "รายงาน"]

    if any(keyword in message_lower for keyword in file_keywords):
        return "file"
    elif any(keyword in message_lower for keyword in search_keywords):
        return "search"
    elif any(keyword in message_lower for keyword in save_keywords):
        return "save"
    else:
        return "inquiry"

# เพิ่มใน process_message function
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

        if intent == "file":
            result = await handle_file_command(message, user_id)
        elif intent == "search":
            result = await handle_search_request(message, user_id)
        elif intent == "save":
            result = await handle_save_request(message, user_id)
        else:
            result = await handle_save_request(message, user_id)  # fallback

        return result

    except Exception as e:
        print(f"❌ Error processing message: {e}")
        return APIResponse(
            success=False,
            message="เกิดข้อผิดพลาดในการประมวลผล กรุณาลองใหม่อีกครั้ง",
            error=str(e)
        )

# ฟังก์ชันใหม่สำหรับจัดการ file commands
async def handle_file_command(message: str, user_id: int) -> APIResponse:
    """จัดการคำสั่งเกี่ยวกับไฟล์"""
    try:
        message_lower = message.lower().strip()

        # Parse file commands
        if message_lower.startswith(('สร้าง ', '/create ')):
            # สร้างไฟล์ใหม่
            parts = message.split(' ', 1)
            if len(parts) < 2:
                return APIResponse(success=False, message="❌ กรุณาระบุชื่อไฟล์: สร้าง filename.txt")

            filename = parts[1].strip()
            return APIResponse(
                success=True,
                message=f"📝 กรุณาส่งเนื้อหาไฟล์ {filename} ในข้อความถัดไป"
            )

        elif message_lower.startswith(('แก้ไข ', '/edit ')):
            # แก้ไขไฟล์
            parts = message.split(' ', 1)
            if len(parts) < 2:
                return APIResponse(success=False, message="❌ กรุณาระบุชื่อไฟล์: แก้ไข filename.txt")

            filename = parts[1].strip()
            result = await handle_file_operation("read", user_id, filename)

            if result["success"]:
                return APIResponse(
                    success=True,
                    message=f"📄 เนื้อหาปัจจุบันของ {filename}:\n\n{result['content']}\n\n📝 ส่งเนื้อหาใหม่เพื่อแก้ไข"
                )
            else:
                return APIResponse(success=False, message=result["error"])

        elif message_lower.startswith(('ลบ ', '/delete ')):
            # ลบไฟล์
            parts = message.split(' ', 1)
            if len(parts) < 2:
                return APIResponse(success=False, message="❌ กรุณาระบุชื่อไฟล์: ลบ filename.txt")

            filename = parts[1].strip()
            result = await handle_file_operation("delete", user_id, filename)

            return APIResponse(
                success=result["success"],
                message=result["message"] if result["success"] else result["error"]
            )

        elif message_lower.startswith(('อ่าน ', '/read ', 'ดู ')):
            # อ่านไฟล์
            parts = message.split(' ', 1)
            if len(parts) < 2:
                return APIResponse(success=False, message="❌ กรุณาระบุชื่อไฟล์: อ่าน filename.txt")

            filename = parts[1].strip()
            result = await handle_file_operation("read", user_id, filename)

            if result["success"]:
                content = result["content"]
                if len(content) > 4000:  # Telegram message limit
                    content = content[:4000] + "\n\n... (ตัดทอนเนื่องจากยาวเกินไป)"

                return APIResponse(
                    success=True,
                    message=f"📄 **{filename}** ({result['lines']} บรรทัด, {result['size']} ตัวอักษร)\n\n```\n{content}\n```"
                )
            else:
                return APIResponse(success=False, message=result["error"])

        elif message_lower in ['ไฟล์', '/list', 'รายชื่อ']:
            # แสดงรายชื่อไฟล์
            result = await handle_file_operation("list", user_id, "")

            if result["success"]:
                files = result["files"]
                if not files:
                    return APIResponse(success=True, message="📁 ไม่มีไฟล์")

                file_list = "📁 **ไฟล์ทั้งหมด:**\n"
                for i, file_info in enumerate(files, 1):
                    size_str = format_file_size(file_info["size"])
                    file_list += f"{i}. 📄 {file_info['name']} ({size_str}, {file_info['modified']})\n"

                return APIResponse(success=True, message=file_list)
            else:
                return APIResponse(success=False, message=result["error"])

        else:
            # คำสั่งไฟล์ที่ไม่รู้จัก
            return APIResponse(
                success=True,
                message="📁 **คำสั่งไฟล์ที่ใช้ได้:**\n\n"
                       "📝 `สร้าง filename.txt` - สร้างไฟล์ใหม่\n"
                       "✏️ `แก้ไข filename.txt` - แก้ไขไฟล์\n"
                       "🗑️ `ลบ filename.txt` - ลบไฟล์\n"
                       "📄 `อ่าน filename.txt` - อ่านไฟล์\n"
                       "📁 `ไฟล์` - แสดงรายชื่อไฟล์ทั้งหมด"
            )

    except Exception as e:
        print(f"❌ Error handling file command: {e}")
        return APIResponse(
            success=False,
            message="เกิดข้อผิดพลาดในการจัดการไฟล์",
            error=str(e)
        )

def format_file_size(size_bytes: int) -> str:
    """แปลงขนาดไฟล์เป็นรูปแบบที่อ่านง่าย"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"