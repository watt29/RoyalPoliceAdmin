"""
File Operations Handler for Telegram Bot
จัดการไฟล์ผ่าน Telegram: สร้าง แก้ไข ลบ
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class TelegramFileHandler:
    def __init__(self, base_path: str = "user-files"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

        # File type restrictions
        self.allowed_extensions = {
            '.txt', '.md', '.log', '.csv', '.json',
            '.pdf', '.docx', '.xlsx', '.jpg', '.png'
        }

        # Size limits
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.max_files_per_user = 100

    def get_user_directory(self, user_id: int) -> Path:
        """สร้าง/ได้รับโฟลเดอร์ของ user"""
        user_dir = self.base_path / f"user-{user_id}"
        user_dir.mkdir(exist_ok=True)
        return user_dir

    async def create_file(self, user_id: int, filename: str, content: str) -> Dict[str, Any]:
        """สร้างไฟล์ใหม่"""
        try:
            user_dir = self.get_user_directory(user_id)
            file_path = user_dir / filename

            # ตรวจสอบว่าไฟล์มีอยู่แล้วหรือไม่
            if file_path.exists():
                return {
                    "success": False,
                    "error": f"❌ ไฟล์ {filename} มีอยู่แล้ว"
                }

            # ตรวจสอบนามสกุลไฟล์
            if file_path.suffix.lower() not in self.allowed_extensions:
                return {
                    "success": False,
                    "error": f"❌ ไฟล์ประเภท {file_path.suffix} ไม่ได้รับอนุญาต"
                }

            # ตรวจสอบจำนวนไฟล์
            existing_files = list(user_dir.glob("*"))
            if len(existing_files) >= self.max_files_per_user:
                return {
                    "success": False,
                    "error": f"❌ เกินจำนวนไฟล์สูงสุด ({self.max_files_per_user})"
                }

            # เขียนไฟล์
            file_path.write_text(content, encoding='utf-8')

            # บันทึก metadata
            await self._save_file_metadata(user_id, filename, "created")

            return {
                "success": True,
                "message": f"✅ สร้างไฟล์ {filename} สำเร็จ",
                "file_path": str(file_path),
                "size": len(content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"❌ เกิดข้อผิดพลาด: {str(e)}"
            }

    async def edit_file(self, user_id: int, filename: str, content: str) -> Dict[str, Any]:
        """แก้ไขไฟล์ที่มีอยู่"""
        try:
            user_dir = self.get_user_directory(user_id)
            file_path = user_dir / filename

            # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"❌ ไม่พบไฟล์ {filename}"
                }

            # สำรองไฟล์เดิม
            backup_path = user_dir / f"{filename}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            original_content = file_path.read_text(encoding='utf-8')
            backup_path.write_text(original_content, encoding='utf-8')

            # แก้ไขไฟล์
            file_path.write_text(content, encoding='utf-8')

            # บันทึก metadata
            await self._save_file_metadata(user_id, filename, "edited")

            return {
                "success": True,
                "message": f"✅ แก้ไขไฟล์ {filename} สำเร็จ",
                "backup": str(backup_path),
                "size": len(content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"❌ เกิดข้อผิดพลาด: {str(e)}"
            }

    async def delete_file(self, user_id: int, filename: str) -> Dict[str, Any]:
        """ลบไฟล์"""
        try:
            user_dir = self.get_user_directory(user_id)
            file_path = user_dir / filename

            # ตรวจสอบว่าไฟล์มีอยู่หรือไม่
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"❌ ไม่พบไฟล์ {filename}"
                }

            # ย้ายไปถังขยะแทนการลบทันที
            trash_dir = user_dir / ".trash"
            trash_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            trash_path = trash_dir / f"{filename}.deleted.{timestamp}"

            file_path.rename(trash_path)

            # บันทึก metadata
            await self._save_file_metadata(user_id, filename, "deleted")

            return {
                "success": True,
                "message": f"✅ ลบไฟล์ {filename} สำเร็จ (ย้ายไปถังขยะ)",
                "trash_path": str(trash_path)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"❌ เกิดข้อผิดพลาด: {str(e)}"
            }

    async def list_files(self, user_id: int) -> Dict[str, Any]:
        """แสดงรายชื่อไฟล์ทั้งหมดของ user"""
        try:
            user_dir = self.get_user_directory(user_id)
            files = []

            for file_path in user_dir.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    stats = file_path.stat()
                    files.append({
                        "name": file_path.name,
                        "size": stats.st_size,
                        "modified": datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M'),
                        "type": file_path.suffix.lower()
                    })

            files.sort(key=lambda x: x["name"])

            return {
                "success": True,
                "files": files,
                "count": len(files),
                "message": f"📁 พบไฟล์ทั้งหมด {len(files)} ไฟล์"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"❌ เกิดข้อผิดพลาด: {str(e)}"
            }

    async def read_file(self, user_id: int, filename: str) -> Dict[str, Any]:
        """อ่านเนื้อหาไฟล์"""
        try:
            user_dir = self.get_user_directory(user_id)
            file_path = user_dir / filename

            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"❌ ไม่พบไฟล์ {filename}"
                }

            # ตรวจสอบขนาดไฟล์
            if file_path.stat().st_size > 1024 * 1024:  # 1MB
                return {
                    "success": False,
                    "error": f"❌ ไฟล์ {filename} ใหญ่เกินไป (>1MB)"
                }

            content = file_path.read_text(encoding='utf-8')

            return {
                "success": True,
                "filename": filename,
                "content": content,
                "size": len(content),
                "lines": content.count('\n') + 1
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"❌ เกิดข้อผิดพลาด: {str(e)}"
            }

    async def _save_file_metadata(self, user_id: int, filename: str, action: str):
        """บันทึก metadata การกระทำ"""
        try:
            user_dir = self.get_user_directory(user_id)
            metadata_file = user_dir / ".metadata.json"

            # อ่าน metadata เดิม
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
            else:
                metadata = {"history": []}

            # เพิ่มการกระทำใหม่
            metadata["history"].append({
                "filename": filename,
                "action": action,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            })

            # เก็บแค่ 100 รายการล่าสุด
            metadata["history"] = metadata["history"][-100:]

            # บันทึก
            metadata_file.write_text(json.dumps(metadata, indent=2))

        except Exception as e:
            print(f"Warning: Could not save metadata: {e}")

# Global instance
file_handler = TelegramFileHandler()

# API endpoints for main_api.py
async def handle_file_operation(operation: str, user_id: int, filename: str, content: str = "") -> Dict[str, Any]:
    """Main interface for file operations"""

    if operation == "create":
        return await file_handler.create_file(user_id, filename, content)
    elif operation == "edit":
        return await file_handler.edit_file(user_id, filename, content)
    elif operation == "delete":
        return await file_handler.delete_file(user_id, filename)
    elif operation == "read":
        return await file_handler.read_file(user_id, filename)
    elif operation == "list":
        return await file_handler.list_files(user_id)
    else:
        return {
            "success": False,
            "error": f"❌ การกระทำ '{operation}' ไม่ได้รับการสนับสนุน"
        }