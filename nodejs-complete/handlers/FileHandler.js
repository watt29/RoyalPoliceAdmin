/**
 * File Handler - Node.js Implementation
 * จัดการไฟล์ผ่าน Telegram Bot ด้วย JavaScript
 */

const fs = require('fs-extra');
const path = require('path');
const moment = require('moment');
const { v4: uuidv4 } = require('uuid');

class FileHandler {
  constructor() {
    this.basePath = path.join(process.cwd(), 'user-files');
    this.tempPath = path.join(process.cwd(), 'temp');

    // File type restrictions
    this.allowedExtensions = new Set([
      '.txt', '.md', '.log', '.csv', '.json',
      '.pdf', '.docx', '.xlsx', '.jpg', '.png', '.gif'
    ]);

    this.blockedExtensions = new Set([
      '.exe', '.bat', '.sh', '.py', '.js', '.php', '.asp'
    ]);

    // Size limits
    this.maxFileSize = 50 * 1024 * 1024; // 50MB
    this.maxFilesPerUser = 100;
    this.maxTextFileSize = 1024 * 1024; // 1MB for text files

    // Initialize directories
    this.initializeDirectories();
  }

  async initializeDirectories() {
    try {
      await fs.ensureDir(this.basePath);
      await fs.ensureDir(this.tempPath);
      console.log('📁 File handler directories initialized');
    } catch (error) {
      console.error('Error initializing directories:', error);
    }
  }

  getUserDirectory(userId) {
    return path.join(this.basePath, `user-${userId}`);
  }

  async ensureUserDirectory(userId) {
    const userDir = this.getUserDirectory(userId);
    await fs.ensureDir(userDir);
    await fs.ensureDir(path.join(userDir, '.trash'));
    await fs.ensureDir(path.join(userDir, '.backup'));
    return userDir;
  }

  validateFilename(filename) {
    try {
      if (!filename || filename.trim().length === 0) {
        return { valid: false, error: 'ชื่อไฟล์ไม่ถูกต้อง' };
      }

      // Clean filename
      filename = filename.trim();

      // Check for dangerous characters
      if (/[<>:"|?*\\]/.test(filename)) {
        return { valid: false, error: 'ชื่อไฟล์มีอักขระที่ไม่อนุญาต' };
      }

      // Check extension
      const ext = path.extname(filename).toLowerCase();

      if (this.blockedExtensions.has(ext)) {
        return { valid: false, error: `ไฟล์ประเภท ${ext} ไม่อนุญาต (เพื่อความปลอดภัย)` };
      }

      if (ext && !this.allowedExtensions.has(ext)) {
        return { valid: false, error: `ไฟล์ประเภท ${ext} ไม่รองรับ` };
      }

      // Check length
      if (filename.length > 100) {
        return { valid: false, error: 'ชื่อไฟล์ยาวเกินไป (สูงสุด 100 ตัวอักษร)' };
      }

      return { valid: true };

    } catch (error) {
      console.error('Error validating filename:', error);
      return { valid: false, error: 'ไม่สามารถตรวจสอบชื่อไฟล์ได้' };
    }
  }

  async createFile(userId, filename, content) {
    try {
      // Validate filename
      const validation = this.validateFilename(filename);
      if (!validation.valid) {
        return { success: false, error: validation.error };
      }

      // Ensure user directory
      const userDir = await this.ensureUserDirectory(userId);
      const filePath = path.join(userDir, filename);

      // Check if file already exists
      if (await fs.pathExists(filePath)) {
        return {
          success: false,
          error: `❌ ไฟล์ ${filename} มีอยู่แล้ว`
        };
      }

      // Check content size
      if (content.length > this.maxFileSize) {
        return {
          success: false,
          error: `❌ เนื้อหาไฟล์ใหญ่เกินไป (สูงสุด ${this.formatFileSize(this.maxFileSize)})`
        };
      }

      // Check total files count
      const existingFiles = await this.getUserFiles(userId);
      if (existingFiles.length >= this.maxFilesPerUser) {
        return {
          success: false,
          error: `❌ เกินจำนวนไฟล์สูงสุด (${this.maxFilesPerUser} ไฟล์)`
        };
      }

      // Create file
      await fs.writeFile(filePath, content, 'utf8');

      // Save metadata
      await this.saveFileMetadata(userId, filename, 'created');

      const stats = await fs.stat(filePath);

      return {
        success: true,
        message: `✅ **สร้างไฟล์สำเร็จ**\n📄 **ชื่อ:** ${filename}\n📊 **ขนาด:** ${this.formatFileSize(stats.size)}\n⏰ **เวลา:** ${moment().format('DD/MM/YYYY HH:mm')}`,
        filePath: filePath,
        size: stats.size
      };

    } catch (error) {
      console.error('Error creating file:', error);
      return {
        success: false,
        error: `❌ เกิดข้อผิดพลาด: ${error.message}`
      };
    }
  }

  async editFile(userId, filename, content) {
    try {
      const userDir = this.getUserDirectory(userId);
      const filePath = path.join(userDir, filename);

      // Check if file exists
      if (!await fs.pathExists(filePath)) {
        return {
          success: false,
          error: `❌ ไม่พบไฟล์ ${filename}`
        };
      }

      // Check content size
      if (content.length > this.maxFileSize) {
        return {
          success: false,
          error: `❌ เนื้อหาไฟล์ใหญ่เกินไป (สูงสุด ${this.formatFileSize(this.maxFileSize)})`
        };
      }

      // Create backup
      const backupDir = path.join(userDir, '.backup');
      const timestamp = moment().format('YYYYMMDD_HHmmss');
      const backupPath = path.join(backupDir, `${filename}.backup.${timestamp}`);

      await fs.copy(filePath, backupPath);

      // Update file
      await fs.writeFile(filePath, content, 'utf8');

      // Save metadata
      await this.saveFileMetadata(userId, filename, 'edited');

      const stats = await fs.stat(filePath);

      return {
        success: true,
        message: `✅ **แก้ไขไฟล์สำเร็จ**\n📄 **ชื่อ:** ${filename}\n📊 **ขนาด:** ${this.formatFileSize(stats.size)}\n💾 **สำรอง:** ${path.basename(backupPath)}\n⏰ **เวลา:** ${moment().format('DD/MM/YYYY HH:mm')}`,
        backupPath: backupPath,
        size: stats.size
      };

    } catch (error) {
      console.error('Error editing file:', error);
      return {
        success: false,
        error: `❌ เกิดข้อผิดพลาด: ${error.message}`
      };
    }
  }

  async deleteFile(userId, filename) {
    try {
      const userDir = this.getUserDirectory(userId);
      const filePath = path.join(userDir, filename);

      // Check if file exists
      if (!await fs.pathExists(filePath)) {
        return {
          success: false,
          error: `❌ ไม่พบไฟล์ ${filename}`
        };
      }

      // Move to trash instead of permanent delete
      const trashDir = path.join(userDir, '.trash');
      const timestamp = moment().format('YYYYMMDD_HHmmss');
      const trashPath = path.join(trashDir, `${filename}.deleted.${timestamp}`);

      await fs.move(filePath, trashPath);

      // Save metadata
      await this.saveFileMetadata(userId, filename, 'deleted');

      return {
        success: true,
        message: `✅ **ลบไฟล์สำเร็จ**\n📄 **ชื่อ:** ${filename}\n🗑️ **ย้ายไปถังขยะ**\n⏰ **เวลา:** ${moment().format('DD/MM/YYYY HH:mm')}\n\n💡 _ใช้คำสั่ง "กู้คืน ${filename}" เพื่อกู้คืนไฟล์_`,
        trashPath: trashPath
      };

    } catch (error) {
      console.error('Error deleting file:', error);
      return {
        success: false,
        error: `❌ เกิดข้อผิดพลาด: ${error.message}`
      };
    }
  }

  async readFile(userId, filename) {
    try {
      const userDir = this.getUserDirectory(userId);
      const filePath = path.join(userDir, filename);

      // Check if file exists
      if (!await fs.pathExists(filePath)) {
        return {
          success: false,
          error: `❌ ไม่พบไฟล์ ${filename}`
        };
      }

      const stats = await fs.stat(filePath);

      // Check if file is too large to read
      if (stats.size > this.maxTextFileSize) {
        return {
          success: false,
          error: `❌ ไฟล์ ${filename} ใหญ่เกินไป (สูงสุด ${this.formatFileSize(this.maxTextFileSize)} สำหรับการอ่าน)`
        };
      }

      // Check file extension
      const ext = path.extname(filename).toLowerCase();
      if (!['.txt', '.md', '.log', '.csv', '.json'].includes(ext)) {
        return {
          success: false,
          error: `❌ ไม่สามารถอ่านไฟล์ประเภท ${ext} ได้`
        };
      }

      const content = await fs.readFile(filePath, 'utf8');
      const lines = content.split('\n').length;

      return {
        success: true,
        filename: filename,
        content: content,
        size: stats.size,
        lines: lines,
        modified: moment(stats.mtime).format('DD/MM/YYYY HH:mm')
      };

    } catch (error) {
      console.error('Error reading file:', error);
      return {
        success: false,
        error: `❌ เกิดข้อผิดพลาด: ${error.message}`
      };
    }
  }

  async listFiles(userId) {
    try {
      const userDir = this.getUserDirectory(userId);

      // Ensure directory exists
      if (!await fs.pathExists(userDir)) {
        return {
          success: true,
          files: [],
          totalSize: 0,
          message: '📁 ยังไม่มีไฟล์'
        };
      }

      const files = [];
      let totalSize = 0;

      const items = await fs.readdir(userDir);

      for (const item of items) {
        const itemPath = path.join(userDir, item);
        const stats = await fs.stat(itemPath);

        // Skip directories and hidden files
        if (stats.isFile() && !item.startsWith('.')) {
          files.push({
            name: item,
            size: stats.size,
            modified: moment(stats.mtime).format('DD/MM/YYYY HH:mm'),
            type: path.extname(item).toLowerCase()
          });
          totalSize += stats.size;
        }
      }

      // Sort by modification time (newest first)
      files.sort((a, b) => moment(b.modified, 'DD/MM/YYYY HH:mm').diff(moment(a.modified, 'DD/MM/YYYY HH:mm')));

      return {
        success: true,
        files: files,
        totalSize: totalSize,
        count: files.length
      };

    } catch (error) {
      console.error('Error listing files:', error);
      return {
        success: false,
        error: `❌ เกิดข้อผิดพลาด: ${error.message}`
      };
    }
  }

  async restoreFile(userId, filename) {
    try {
      const userDir = this.getUserDirectory(userId);
      const trashDir = path.join(userDir, '.trash');

      // Find the deleted file
      const trashItems = await fs.readdir(trashDir);
      const deletedFile = trashItems.find(item => item.startsWith(`${filename}.deleted.`));

      if (!deletedFile) {
        return {
          success: false,
          error: `❌ ไม่พบไฟล์ ${filename} ในถังขยะ`
        };
      }

      const trashPath = path.join(trashDir, deletedFile);
      const restorePath = path.join(userDir, filename);

      // Check if file already exists
      if (await fs.pathExists(restorePath)) {
        return {
          success: false,
          error: `❌ ไฟล์ ${filename} มีอยู่แล้ว ไม่สามารถกู้คืนได้`
        };
      }

      // Restore file
      await fs.move(trashPath, restorePath);

      // Save metadata
      await this.saveFileMetadata(userId, filename, 'restored');

      return {
        success: true,
        message: `✅ **กู้คืนไฟล์สำเร็จ**\n📄 **ชื่อ:** ${filename}\n⏰ **เวลา:** ${moment().format('DD/MM/YYYY HH:mm')}`
      };

    } catch (error) {
      console.error('Error restoring file:', error);
      return {
        success: false,
        error: `❌ เกิดข้อผิดพลาด: ${error.message}`
      };
    }
  }

  async saveFileMetadata(userId, filename, action) {
    try {
      const userDir = this.getUserDirectory(userId);
      const metadataPath = path.join(userDir, '.metadata.json');

      let metadata = { history: [] };

      // Load existing metadata
      if (await fs.pathExists(metadataPath)) {
        metadata = await fs.readJson(metadataPath);
      }

      // Add new entry
      metadata.history.push({
        filename: filename,
        action: action,
        timestamp: moment().toISOString(),
        userId: userId
      });

      // Keep only last 100 entries
      metadata.history = metadata.history.slice(-100);

      // Save metadata
      await fs.writeJson(metadataPath, metadata, { spaces: 2 });

    } catch (error) {
      console.warn('Could not save file metadata:', error);
    }
  }

  async getUserFiles(userId) {
    try {
      const result = await this.listFiles(userId);
      return result.success ? result.files : [];
    } catch (error) {
      console.error('Error getting user files:', error);
      return [];
    }
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  // Clean up old files and temporary data
  async cleanup() {
    try {
      // Clean temp directory
      await fs.emptyDir(this.tempPath);

      // Clean old backup files (older than 30 days)
      const cutoffDate = moment().subtract(30, 'days');

      const userDirs = await fs.readdir(this.basePath);
      for (const userDir of userDirs) {
        const backupDir = path.join(this.basePath, userDir, '.backup');
        if (await fs.pathExists(backupDir)) {
          const backupFiles = await fs.readdir(backupDir);
          for (const backupFile of backupFiles) {
            const backupPath = path.join(backupDir, backupFile);
            const stats = await fs.stat(backupPath);
            if (moment(stats.mtime).isBefore(cutoffDate)) {
              await fs.remove(backupPath);
            }
          }
        }
      }

      console.log('🧹 File cleanup completed');

    } catch (error) {
      console.error('Error during file cleanup:', error);
    }
  }
}

module.exports = FileHandler;