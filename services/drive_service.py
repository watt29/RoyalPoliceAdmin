import logging
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import fitz  # PyMuPDF
import io

logger = logging.getLogger(__name__)

class DriveService:
    def __init__(self, credentials_path: str, root_folder_id: str):
        self.credentials_path = credentials_path
        self.root_folder_id = root_folder_id
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.service = None
        self.folders = {}

    def connect(self):
        """Connect to Google Drive API"""
        try:
            creds = Credentials.from_service_account_file(self.credentials_path, scopes=self.scopes)
            self.service = build('drive', 'v3', credentials=creds)
            self._initialize_folders()
            return True
        except Exception as e:
            logger.error(f"Drive connection error: {e}")
            return False

    def _initialize_folders(self):
        """Create or get category folders"""
        categories = ['เอกสาร', 'รูปภาพ', 'ข้อมูล', 'มัลติมีเดีย', 'อื่นๆ']
        for cat in categories:
            self.folders[cat] = self._get_or_create_folder(cat, self.root_folder_id)

    def _get_or_create_folder(self, folder_name: str, parent_id: str):
        try:
            query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.service.files().list(q=query, fields="files(id)").execute()
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            
            # Create if not found
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            file = self.service.files().create(body=file_metadata, fields='id').execute()
            return file.get('id')
        except Exception as e:
            logger.error(f"Folder error ({folder_name}): {e}")
            return parent_id

    def extract_text(self, keywords: str = ""):
        """Extract text from PDF/TXT files in Drive for AI context"""
        if not self.service: return ""
        
        context_text = []
        try:
            # Search for relevant PDF/TXT files
            query = f"'{self.root_folder_id}' in parents and (mimeType = 'application/pdf' or mimeType = 'text/plain') and trashed = false"
            results = self.service.files().list(q=query, fields="files(id, name, mimeType)").execute()
            files = results.get('files', [])

            for file in files:
                # Add logic to filter by keywords if needed
                file_id = file['id']
                mime_type = file['mimeType']
                
                if mime_type == 'application/pdf':
                    content = self.service.files().get_media(fileId=file_id).execute()
                    doc = fitz.open(stream=content, filetype="pdf")
                    text = ""
                    for page in doc:
                        text += page.get_text()
                    context_text.append(f"ไฟล์: {file['name']}\nเนื้อหา: {text[:2000]}") # Limit per file
                elif mime_type == 'text/plain':
                    content = self.service.files().get_media(fileId=file_id).execute().decode('utf-8')
                    context_text.append(f"ไฟล์: {file['name']}\nเนื้อหา: {content[:2000]}")

            return "\n\n".join(context_text)
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return ""
