/**
 * Google Drive Service - Node.js Implementation
 * บริการจัดการไฟล์บน Google Drive
 */

const { google } = require('googleapis');
const fs = require('fs-extra');
const path = require('path');

class GoogleDriveService {
  constructor() {
    this.auth = null;
    this.drive = null;
    this.folderId = process.env.GOOGLE_DRIVE_FOLDER_ID;

    this.initialize();
  }

  async initialize() {
    try {
      // Load credentials (same as GoogleSheetsService)
      const credentials = await this.loadCredentials();

      // Setup authentication
      this.auth = new google.auth.GoogleAuth({
        credentials: credentials,
        scopes: [
          'https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive.readonly'
        ]
      });

      // Get authenticated client
      const authClient = await this.auth.getClient();
      this.drive = google.drive({ version: 'v3', auth: authClient });

      console.log('✅ Google Drive service initialized');

    } catch (error) {
      console.error('❌ Failed to initialize Google Drive:', error);
      throw error;
    }
  }

  async loadCredentials() {
    try {
      // Try to load from environment variable first (for Render deployment)
      if (process.env.GOOGLE_CREDENTIALS) {
        console.log('✅ Using Google credentials from environment variable (Production)');
        return JSON.parse(process.env.GOOGLE_CREDENTIALS);
      }

      // Fallback for old environment variable name
      if (process.env.GOOGLE_CREDENTIALS_JSON) {
        console.log('✅ Using Google credentials from GOOGLE_CREDENTIALS_JSON');
        return JSON.parse(process.env.GOOGLE_CREDENTIALS_JSON);
      }

      // Try to load from file
      const credentialsPath = process.env.GOOGLE_CREDENTIALS_PATH || 'service_account.json';
      const fullPath = path.resolve(credentialsPath);
      if (await fs.pathExists(fullPath)) {
        console.log('✅ Using Google credentials from file:', credentialsPath);
        return await fs.readJson(fullPath);
      }

      // Try shared directory
      const sharedPath = path.resolve('../shared', credentialsPath);
      if (await fs.pathExists(sharedPath)) {
        return await fs.readJson(sharedPath);
      }

      throw new Error('Google credentials not found');

    } catch (error) {
      console.error('Error loading credentials:', error);
      throw error;
    }
  }

  async uploadFile(filePath, fileName, mimeType) {
    try {
      if (!this.drive) {
        throw new Error('Google Drive not initialized');
      }

      const fileMetadata = {
        name: fileName,
        parents: this.folderId ? [this.folderId] : undefined
      };

      const media = {
        mimeType: mimeType || 'application/octet-stream',
        body: fs.createReadStream(filePath)
      };

      console.log(`📤 Uploading ${fileName} to Google Drive...`);

      const file = await this.drive.files.create({
        requestBody: fileMetadata,
        media: media,
        fields: 'id,name,size,mimeType,createdTime,webViewLink,webContentLink'
      });

      console.log(`✅ File uploaded successfully: ${file.data.id}`);

      return {
        success: true,
        fileId: file.data.id,
        fileName: file.data.name,
        size: file.data.size,
        webViewLink: file.data.webViewLink,
        webContentLink: file.data.webContentLink,
        createdTime: file.data.createdTime
      };

    } catch (error) {
      console.error('❌ Error uploading file:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async uploadBuffer(buffer, fileName, mimeType) {
    try {
      if (!this.drive) {
        throw new Error('Google Drive not initialized');
      }

      const fileMetadata = {
        name: fileName,
        parents: this.folderId ? [this.folderId] : undefined
      };

      const { Readable } = require('stream');
      const bufferStream = new Readable();
      bufferStream.push(buffer);
      bufferStream.push(null);

      const media = {
        mimeType: mimeType || 'application/octet-stream',
        body: bufferStream
      };

      console.log(`📤 Uploading ${fileName} (buffer) to Google Drive...`);

      const file = await this.drive.files.create({
        requestBody: fileMetadata,
        media: media,
        fields: 'id,name,size,mimeType,createdTime,webViewLink,webContentLink'
      });

      console.log(`✅ Buffer uploaded successfully: ${file.data.id}`);

      return {
        success: true,
        fileId: file.data.id,
        fileName: file.data.name,
        size: file.data.size,
        webViewLink: file.data.webViewLink,
        webContentLink: file.data.webContentLink,
        createdTime: file.data.createdTime
      };

    } catch (error) {
      console.error('❌ Error uploading buffer:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async listFiles(maxResults = 20) {
    try {
      if (!this.drive) {
        throw new Error('Google Drive not initialized');
      }

      const query = this.folderId ? `'${this.folderId}' in parents` : undefined;

      const response = await this.drive.files.list({
        q: query,
        pageSize: maxResults,
        fields: 'nextPageToken, files(id, name, size, mimeType, createdTime, modifiedTime, webViewLink)',
        orderBy: 'modifiedTime desc'
      });

      const files = response.data.files || [];

      return {
        success: true,
        files: files.map(file => ({
          id: file.id,
          name: file.name,
          size: parseInt(file.size) || 0,
          mimeType: file.mimeType,
          createdTime: file.createdTime,
          modifiedTime: file.modifiedTime,
          webViewLink: file.webViewLink
        })),
        count: files.length,
        nextPageToken: response.data.nextPageToken
      };

    } catch (error) {
      console.error('❌ Error listing files:', error);
      return {
        success: false,
        error: error.message,
        files: [],
        count: 0
      };
    }
  }

  async downloadFile(fileId, outputPath) {
    try {
      if (!this.drive) {
        throw new Error('Google Drive not initialized');
      }

      console.log(`📥 Downloading file ${fileId}...`);

      const response = await this.drive.files.get({
        fileId: fileId,
        alt: 'media'
      }, { responseType: 'stream' });

      const writer = fs.createWriteStream(outputPath);
      response.data.pipe(writer);

      return new Promise((resolve, reject) => {
        writer.on('finish', () => {
          console.log(`✅ File downloaded to: ${outputPath}`);
          resolve({
            success: true,
            outputPath: outputPath
          });
        });

        writer.on('error', (error) => {
          console.error('❌ Error writing file:', error);
          reject({
            success: false,
            error: error.message
          });
        });
      });

    } catch (error) {
      console.error('❌ Error downloading file:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async deleteFile(fileId) {
    try {
      if (!this.drive) {
        throw new Error('Google Drive not initialized');
      }

      console.log(`🗑️ Deleting file ${fileId}...`);

      await this.drive.files.delete({
        fileId: fileId
      });

      console.log(`✅ File deleted successfully: ${fileId}`);

      return {
        success: true,
        message: 'File deleted successfully'
      };

    } catch (error) {
      console.error('❌ Error deleting file:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async getFileInfo(fileId) {
    try {
      if (!this.drive) {
        throw new Error('Google Drive not initialized');
      }

      const response = await this.drive.files.get({
        fileId: fileId,
        fields: 'id, name, size, mimeType, createdTime, modifiedTime, webViewLink, webContentLink, parents'
      });

      const file = response.data;

      return {
        success: true,
        file: {
          id: file.id,
          name: file.name,
          size: parseInt(file.size) || 0,
          mimeType: file.mimeType,
          createdTime: file.createdTime,
          modifiedTime: file.modifiedTime,
          webViewLink: file.webViewLink,
          webContentLink: file.webContentLink,
          parents: file.parents
        }
      };

    } catch (error) {
      console.error('❌ Error getting file info:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  async searchFiles(query, maxResults = 10) {
    try {
      if (!this.drive) {
        throw new Error('Google Drive not initialized');
      }

      const searchQuery = this.folderId
        ? `name contains '${query}' and '${this.folderId}' in parents`
        : `name contains '${query}'`;

      const response = await this.drive.files.list({
        q: searchQuery,
        pageSize: maxResults,
        fields: 'nextPageToken, files(id, name, size, mimeType, createdTime, modifiedTime, webViewLink)',
        orderBy: 'modifiedTime desc'
      });

      const files = response.data.files || [];

      return {
        success: true,
        files: files.map(file => ({
          id: file.id,
          name: file.name,
          size: parseInt(file.size) || 0,
          mimeType: file.mimeType,
          createdTime: file.createdTime,
          modifiedTime: file.modifiedTime,
          webViewLink: file.webViewLink
        })),
        count: files.length,
        query: query
      };

    } catch (error) {
      console.error('❌ Error searching files:', error);
      return {
        success: false,
        error: error.message,
        files: [],
        count: 0
      };
    }
  }

  async createFolder(folderName, parentFolderId) {
    try {
      if (!this.drive) {
        throw new Error('Google Drive not initialized');
      }

      const fileMetadata = {
        name: folderName,
        mimeType: 'application/vnd.google-apps.folder',
        parents: parentFolderId ? [parentFolderId] : (this.folderId ? [this.folderId] : undefined)
      };

      console.log(`📁 Creating folder: ${folderName}`);

      const folder = await this.drive.files.create({
        requestBody: fileMetadata,
        fields: 'id, name, webViewLink'
      });

      console.log(`✅ Folder created successfully: ${folder.data.id}`);

      return {
        success: true,
        folderId: folder.data.id,
        folderName: folder.data.name,
        webViewLink: folder.data.webViewLink
      };

    } catch (error) {
      console.error('❌ Error creating folder:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Health check method
  async healthCheck() {
    try {
      if (!this.drive) {
        throw new Error('Google Drive not initialized');
      }

      // Try to get about info
      await this.drive.about.get({ fields: 'user' });

      return {
        success: true,
        message: 'Google Drive connection OK',
        folderId: this.folderId
      };

    } catch (error) {
      console.error('Google Drive health check failed:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }

  // Utility method to get MIME type from file extension
  getMimeType(fileName) {
    const ext = path.extname(fileName).toLowerCase();
    const mimeTypes = {
      '.txt': 'text/plain',
      '.md': 'text/markdown',
      '.json': 'application/json',
      '.csv': 'text/csv',
      '.pdf': 'application/pdf',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.png': 'image/png',
      '.gif': 'image/gif',
      '.doc': 'application/msword',
      '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      '.xls': 'application/vnd.ms-excel',
      '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    };

    return mimeTypes[ext] || 'application/octet-stream';
  }

  // Format file size for display
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }
}

module.exports = GoogleDriveService;