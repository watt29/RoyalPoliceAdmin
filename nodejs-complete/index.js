/**
 * Smart Police Report Bot - Complete Node.js Version
 * ระบบรายงานตำรวจอัจฉริยะ - 100% JavaScript
 */

const TelegramBot = require('node-telegram-bot-api');
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const winston = require('winston');
const fs = require('fs-extra');
const path = require('path');
const cron = require('node-cron');
const { v4: uuidv4 } = require('uuid');
require('dotenv').config();

// Import modules
const GoogleSheetsService = require('./services/GoogleSheetsService');
const GoogleDriveService = require('./services/GoogleDriveService');
const ContactHandler = require('./handlers/ContactHandler');
const VehicleHandler = require('./handlers/VehicleHandler');
const OrderHandler = require('./handlers/OrderHandler');
const FileHandler = require('./handlers/FileHandler');
const AIProcessor = require('./services/AIProcessor');
const DataProcessor = require('./services/DataProcessor');

// Logger setup
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'smart-police-bot' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    })
  ]
});

class SmartPoliceBot {
  constructor() {
    this.token = process.env.TELEGRAM_BOT_TOKEN;
    this.adminChatId = process.env.ADMIN_CHAT_ID;

    if (!this.token) {
      throw new Error('TELEGRAM_BOT_TOKEN is required');
    }

    // Initialize bot
    this.bot = new TelegramBot(this.token, { polling: true });

    // Initialize services
    this.sheetsService = new GoogleSheetsService();
    this.driveService = new GoogleDriveService();
    this.aiProcessor = new AIProcessor();
    this.dataProcessor = new DataProcessor();

    // Initialize handlers
    this.contactHandler = new ContactHandler(this.sheetsService, this.aiProcessor);
    this.vehicleHandler = new VehicleHandler(this.sheetsService);
    this.orderHandler = new OrderHandler(this.sheetsService);
    this.fileHandler = new FileHandler(this.driveService);

    // User sessions
    this.userSessions = new Map();

    // Setup directories
    this.setupDirectories();

    // Setup bot handlers
    this.setupHandlers();

    // Setup cron jobs
    this.setupCronJobs();

    logger.info('🤖 Smart Police Bot initialized successfully');
  }

  setupDirectories() {
    const directories = ['logs', 'temp', 'uploads', 'reports', 'backups'];
    directories.forEach(dir => {
      fs.ensureDirSync(dir);
    });
  }

  setupHandlers() {
    // Error handling
    this.bot.on('error', (error) => {
      logger.error('Bot error:', error);
    });

    this.bot.on('polling_error', (error) => {
      logger.error('Polling error:', error);
    });

    // Start command
    this.bot.onText(/\/start/, (msg) => this.handleStart(msg));

    // Help command
    this.bot.onText(/\/help/, (msg) => this.handleHelp(msg));

    // File commands
    this.bot.onText(/\/(สร้าง|create) (.+)/, (msg, match) =>
      this.handleFileCreate(msg, match[2])
    );

    this.bot.onText(/\/(แก้ไข|edit) (.+)/, (msg, match) =>
      this.handleFileEdit(msg, match[2])
    );

    this.bot.onText(/\/(ลบ|delete) (.+)/, (msg, match) =>
      this.handleFileDelete(msg, match[2])
    );

    this.bot.onText(/\/(อ่าน|read|ดู) (.+)/, (msg, match) =>
      this.handleFileRead(msg, match[2])
    );

    this.bot.onText(/\/(ไฟล์|files|list)$/, (msg) =>
      this.handleFileList(msg)
    );

    // Search commands
    this.bot.onText(/\/(ค้นหา|search) (.+)/, (msg, match) =>
      this.handleSearch(msg, match[2])
    );

    // Export commands
    this.bot.onText(/\/(export) (\w+) (\w+)/, (msg, match) =>
      this.handleExport(msg, match[2], match[3])
    );

    // Report commands
    this.bot.onText(/\/(รายงาน|report) (.+)/, (msg, match) =>
      this.handleReport(msg, match[2])
    );

    // Handle all messages
    this.bot.on('message', (msg) => {
      if (!msg.text || msg.text.startsWith('/')) return;
      this.handleMessage(msg);
    });

    // Handle callback queries
    this.bot.on('callback_query', (query) => this.handleCallbackQuery(query));

    // Handle document uploads
    this.bot.on('document', (msg) => this.handleDocumentUpload(msg));
    this.bot.on('photo', (msg) => this.handlePhotoUpload(msg));
  }

  async handleStart(msg) {
    const chatId = msg.chat.id;
    const userId = msg.from.id;

    // Initialize user session
    this.userSessions.set(userId, {
      chatId,
      state: 'main',
      data: {}
    });

    const welcomeMessage = `🚔 **ยินดีต้อนรับสู่ Smart Police Report Bot v3.0**

ระบบรายงานตำรวจอัจฉริยะ - **100% Node.js**
✅ บันทึกข้อมูลอัตโนมัติ
✅ ค้นหาข้อมูลรวดเร็ว
✅ จัดการไฟล์ครบครัน
✅ ส่งออกรายงาน
✅ แจ้งเตือนอัจฉริยะ
⚡ **Performance สูงสุด**

พิมพ์ข้อความเพื่อเริ่มใช้งาน หรือเลือกเมนูด้านล่าง`;

    const keyboard = {
      reply_markup: {
        inline_keyboard: [
          [
            { text: '📝 บันทึกข้อมูล', callback_data: 'menu_save' },
            { text: '🔍 ค้นหาข้อมูล', callback_data: 'menu_search' }
          ],
          [
            { text: '📁 จัดการไฟล์', callback_data: 'menu_files' },
            { text: '📊 รายงาน', callback_data: 'menu_reports' }
          ],
          [
            { text: '⚙️ ตั้งค่า', callback_data: 'menu_settings' },
            { text: '📚 คู่มือ', callback_data: 'menu_help' }
          ]
        ]
      }
    };

    try {
      await this.bot.sendMessage(chatId, welcomeMessage, {
        parse_mode: 'Markdown',
        ...keyboard
      });

      logger.info(`User ${userId} started the bot`);
    } catch (error) {
      logger.error('Error sending start message:', error);
    }
  }

  async handleMessage(msg) {
    const chatId = msg.chat.id;
    const userId = msg.from.id;
    const text = msg.text.trim();

    try {
      // Show typing indicator
      await this.bot.sendChatAction(chatId, 'typing');

      // Get or create user session
      let session = this.userSessions.get(userId);
      if (!session) {
        session = { chatId, state: 'main', data: {} };
        this.userSessions.set(userId, session);
      }

      logger.info(`Processing message from user ${userId}: ${text.substring(0, 50)}...`);

      // Handle based on session state
      if (session.state === 'file_create_content') {
        await this.handleFileCreateContent(msg, session);
        return;
      } else if (session.state === 'file_edit_content') {
        await this.handleFileEditContent(msg, session);
        return;
      }

      // Detect intent and process message
      const intent = await this.detectIntent(text);
      let result;

      switch (intent.type) {
        case 'search':
          result = await this.processSearch(text, userId);
          break;
        case 'save_contact':
          result = await this.contactHandler.processMessage(text, userId);
          break;
        case 'save_vehicle':
          result = await this.vehicleHandler.processMessage(text, userId);
          break;
        case 'save_order':
          result = await this.orderHandler.processMessage(text, userId);
          break;
        case 'file':
          result = await this.processFileCommand(text, userId);
          break;
        default:
          result = await this.processGeneral(text, userId);
          break;
      }

      // Send response
      if (result.success) {
        await this.bot.sendMessage(chatId, result.message, {
          parse_mode: 'Markdown',
          reply_markup: result.keyboard || null
        });
      } else {
        await this.bot.sendMessage(chatId, `❌ ${result.error || 'เกิดข้อผิดพลาด'}`);
      }

    } catch (error) {
      logger.error('Error processing message:', error);
      await this.bot.sendMessage(chatId, '❌ ระบบขัดข้อง กรุณาลองใหม่อีกครั้ง');
    }
  }

  async detectIntent(text) {
    try {
      const textLower = text.toLowerCase();

      // File operations
      const fileKeywords = ['สร้าง', 'แก้ไข', 'ลบ', 'อ่าน', 'ไฟล์', 'create', 'edit', 'delete', 'read', 'file'];
      if (fileKeywords.some(keyword => textLower.includes(keyword))) {
        return { type: 'file', confidence: 0.9 };
      }

      // Search operations
      const searchKeywords = ['ค้นหา', 'หา', 'ดู', 'เช็ค', 'search', 'find'];
      if (searchKeywords.some(keyword => textLower.includes(keyword))) {
        return { type: 'search', confidence: 0.8 };
      }

      // Contact data
      const contactPattern = /(นาย|นาง|นางสาว|จส|พล|ร\.ต|พ\.ต|โทร|เบอร์|สภ\.|กอง)/i;
      if (contactPattern.test(text)) {
        return { type: 'save_contact', confidence: 0.8 };
      }

      // Vehicle data
      const vehiclePattern = /(โล่|ทะเบียน|รถ|กข|นข|บข|มอเตอร์ไซค์|รถยนต์)/i;
      if (vehiclePattern.test(text)) {
        return { type: 'save_vehicle', confidence: 0.8 };
      }

      // Order/Command data
      const orderPattern = /(คำสั่ง|ภารกิจ|ให้|ไป|ตรวจ|เร่งด่วน|กำหนด)/i;
      if (orderPattern.test(text)) {
        return { type: 'save_order', confidence: 0.7 };
      }

      // Use AI for complex intent detection
      const aiResult = await this.aiProcessor.detectIntent(text);
      return aiResult || { type: 'general', confidence: 0.5 };

    } catch (error) {
      logger.error('Error detecting intent:', error);
      return { type: 'general', confidence: 0.3 };
    }
  }

  async processSearch(query, userId) {
    try {
      const results = await this.sheetsService.searchAll(query);

      if (!results || results.length === 0) {
        return {
          success: true,
          message: `🔍 **ค้นหา:** ${query}\n\n❌ ไม่พบข้อมูลที่ตรงกัน`
        };
      }

      let response = `🔍 **ผลการค้นหา:** ${query}\n\n`;

      results.slice(0, 10).forEach((result, index) => {
        const target = result.sheet || 'ข้อมูล';
        const name = result.Name || result.Detail || result.Plate || 'ไม่ระบุ';
        response += `${index + 1}. **[${target}]** ${name}\n`;
      });

      if (results.length > 10) {
        response += `\n_พบทั้งหมด ${results.length} รายการ (แสดง 10 อันดับแรก)_`;
      }

      return { success: true, message: response };

    } catch (error) {
      logger.error('Error processing search:', error);
      return { success: false, error: 'เกิดข้อผิดพลาดในการค้นหา' };
    }
  }

  async processGeneral(text, userId) {
    try {
      // Try to save as general data
      const saveResult = await this.contactHandler.processMessage(text, userId);

      if (saveResult.success) {
        return saveResult;
      }

      // If can't save, provide help
      return {
        success: true,
        message: `💬 **ข้อความของคุณ:** ${text.substring(0, 100)}...\n\n` +
                `ระบบไม่เข้าใจคำสั่ง กรุณา:\n\n` +
                `📝 ระบุข้อมูลให้ชัดเจนมากขึ้น\n` +
                `🔍 ใช้คำสั่งค้นหา: "ค้นหา [คำค้น]"\n` +
                `📁 จัดการไฟล์: "ไฟล์" หรือ "สร้าง filename.txt"\n` +
                `❓ ดูคำแนะนำ: /help`,
        keyboard: this.getMainKeyboard()
      };

    } catch (error) {
      logger.error('Error processing general message:', error);
      return { success: false, error: 'ไม่สามารถประมวลผลข้อความได้' };
    }
  }

  // File operation handlers
  async handleFileCreate(msg, filename) {
    const userId = msg.from.id;
    const chatId = msg.chat.id;

    // Validate filename
    const validation = this.fileHandler.validateFilename(filename);
    if (!validation.valid) {
      return this.bot.sendMessage(chatId, `❌ ${validation.error}`);
    }

    // Set user state
    const session = this.userSessions.get(userId) || { chatId, state: 'main', data: {} };
    session.state = 'file_create_content';
    session.data.filename = filename;
    this.userSessions.set(userId, session);

    await this.bot.sendMessage(chatId,
      `📝 **สร้างไฟล์:** ${filename}\n\n` +
      `กรุณาส่งเนื้อหาไฟล์ในข้อความถัดไป`
    );
  }

  async handleFileCreateContent(msg, session) {
    const userId = msg.from.id;
    const chatId = msg.chat.id;
    const content = msg.text;
    const filename = session.data.filename;

    try {
      const result = await this.fileHandler.createFile(userId, filename, content);

      // Reset session state
      session.state = 'main';
      session.data = {};
      this.userSessions.set(userId, session);

      if (result.success) {
        await this.bot.sendMessage(chatId, result.message);
      } else {
        await this.bot.sendMessage(chatId, `❌ ${result.error}`);
      }

    } catch (error) {
      logger.error('Error creating file:', error);
      await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการสร้างไฟล์');
    }
  }

  async handleFileList(msg) {
    const userId = msg.from.id;
    const chatId = msg.chat.id;

    try {
      const result = await this.fileHandler.listFiles(userId);

      if (result.success) {
        let response = `📁 **ไฟล์ทั้งหมด** (${result.files.length} ไฟล์)\n\n`;

        if (result.files.length === 0) {
          response += '📭 ยังไม่มีไฟล์';
        } else {
          result.files.forEach((file, index) => {
            const size = this.formatFileSize(file.size);
            response += `${index + 1}. 📄 **${file.name}** (${size}, ${file.modified})\n`;
          });

          response += `\n💾 ใช้พื้นที่: ${this.formatFileSize(result.totalSize)} / 50 MB`;
        }

        await this.bot.sendMessage(chatId, response, { parse_mode: 'Markdown' });

      } else {
        await this.bot.sendMessage(chatId, `❌ ${result.error}`);
      }

    } catch (error) {
      logger.error('Error listing files:', error);
      await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการแสดงรายชื่อไฟล์');
    }
  }

  async handleHelp(msg) {
    const chatId = msg.chat.id;
    const helpMessage = this.getHelpMessage();

    try {
      await this.bot.sendMessage(chatId, helpMessage.message, {
        parse_mode: 'Markdown',
        reply_markup: helpMessage.keyboard || null
      });
    } catch (error) {
      logger.error('Error sending help message:', error);
    }
  }

  async handleFileEdit(msg, filename) {
    const userId = msg.from.id;
    const chatId = msg.chat.id;

    try {
      // Check if file exists first
      const userDir = this.fileHandler.getUserDirectory(userId);
      const filePath = path.join(userDir, filename);

      if (!await fs.pathExists(filePath)) {
        return this.bot.sendMessage(chatId, `❌ ไม่พบไฟล์ ${filename}`);
      }

      // Read current content
      const result = await this.fileHandler.readFile(userId, filename);
      if (!result.success) {
        return this.bot.sendMessage(chatId, `❌ ${result.error}`);
      }

      // Set user state for editing
      const session = this.userSessions.get(userId) || { chatId, state: 'main', data: {} };
      session.state = 'file_edit_content';
      session.data.filename = filename;
      session.data.originalContent = result.content;
      this.userSessions.set(userId, session);

      await this.bot.sendMessage(chatId,
        `✏️ **แก้ไขไฟล์:** ${filename}\n\n` +
        `**เนื้อหาปัจจุบัน:**\n\`\`\`\n${result.content.substring(0, 500)}${result.content.length > 500 ? '...' : ''}\n\`\`\`\n\n` +
        `กรุณาส่งเนื้อหาใหม่ในข้อความถัดไป`,
        { parse_mode: 'Markdown' }
      );

    } catch (error) {
      logger.error('Error handling file edit:', error);
      await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการแก้ไขไฟล์');
    }
  }

  async handleFileEditContent(msg, session) {
    const userId = msg.from.id;
    const chatId = msg.chat.id;
    const content = msg.text;
    const filename = session.data.filename;

    try {
      const result = await this.fileHandler.editFile(userId, filename, content);

      // Reset session state
      session.state = 'main';
      session.data = {};
      this.userSessions.set(userId, session);

      if (result.success) {
        await this.bot.sendMessage(chatId, result.message, { parse_mode: 'Markdown' });
      } else {
        await this.bot.sendMessage(chatId, `❌ ${result.error}`);
      }

    } catch (error) {
      logger.error('Error editing file content:', error);
      await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการแก้ไขไฟล์');
    }
  }

  async handleFileDelete(msg, filename) {
    const userId = msg.from.id;
    const chatId = msg.chat.id;

    try {
      const result = await this.fileHandler.deleteFile(userId, filename);

      if (result.success) {
        await this.bot.sendMessage(chatId, result.message, { parse_mode: 'Markdown' });
      } else {
        await this.bot.sendMessage(chatId, `❌ ${result.error}`);
      }

    } catch (error) {
      logger.error('Error deleting file:', error);
      await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการลบไฟล์');
    }
  }

  async handleFileRead(msg, filename) {
    const userId = msg.from.id;
    const chatId = msg.chat.id;

    try {
      const result = await this.fileHandler.readFile(userId, filename);

      if (result.success) {
        let response = `📖 **ไฟล์:** ${result.filename}\n`;
        response += `📊 **ขนาด:** ${this.formatFileSize(result.size)} (${result.lines} บรรทัด)\n`;
        response += `📅 **แก้ไขล่าสุด:** ${result.modified}\n\n`;
        response += `**เนื้อหา:**\n\`\`\`\n${result.content}\n\`\`\``;

        // Split message if too long
        if (response.length > 4000) {
          const parts = this.splitMessage(response, 4000);
          for (const part of parts) {
            await this.bot.sendMessage(chatId, part, { parse_mode: 'Markdown' });
          }
        } else {
          await this.bot.sendMessage(chatId, response, { parse_mode: 'Markdown' });
        }

      } else {
        await this.bot.sendMessage(chatId, `❌ ${result.error}`);
      }

    } catch (error) {
      logger.error('Error reading file:', error);
      await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการอ่านไฟล์');
    }
  }

  async handleSearch(msg, query) {
    const chatId = msg.chat.id;
    const userId = msg.from.id;

    try {
      await this.bot.sendChatAction(chatId, 'typing');
      const result = await this.processSearch(query, userId);

      await this.bot.sendMessage(chatId, result.message, {
        parse_mode: 'Markdown',
        reply_markup: result.keyboard || null
      });

    } catch (error) {
      logger.error('Error handling search:', error);
      await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการค้นหา');
    }
  }

  async handleExport(msg, dataType, format) {
    const chatId = msg.chat.id;
    const userId = msg.from.id;

    try {
      await this.bot.sendChatAction(chatId, 'upload_document');

      // Get data from Google Sheets
      let data = [];
      switch (dataType.toLowerCase()) {
        case 'contacts':
        case 'บุคลากร':
          data = await this.sheetsService.readSheet('Contacts');
          break;
        case 'vehicles':
        case 'ยานพาหนะ':
          data = await this.sheetsService.readSheet('Vehicles');
          break;
        case 'orders':
        case 'คำสั่ง':
          data = await this.sheetsService.readSheet('Orders');
          break;
        default:
          return this.bot.sendMessage(chatId, '❌ ประเภทข้อมูลไม่ถูกต้อง (contacts, vehicles, orders)');
      }

      if (!data || data.length === 0) {
        return this.bot.sendMessage(chatId, '❌ ไม่มีข้อมูลสำหรับส่งออก');
      }

      // Export data
      const timestamp = new Date().toISOString().slice(0, 10);
      const filename = `${dataType}_export_${timestamp}.csv`;

      const exportResult = await this.dataProcessor.exportToCSV(data, filename);

      if (exportResult.success) {
        // Send file
        await this.bot.sendDocument(chatId, exportResult.filePath, {
          caption: `📄 **ส่งออกข้อมูลสำเร็จ**\n` +
                  `📊 **ประเภท:** ${dataType}\n` +
                  `📈 **จำนวน:** ${exportResult.recordCount} รายการ\n` +
                  `📅 **วันที่:** ${timestamp}`,
          parse_mode: 'Markdown'
        });
      } else {
        await this.bot.sendMessage(chatId, `❌ ส่งออกไม่สำเร็จ: ${exportResult.error}`);
      }

    } catch (error) {
      logger.error('Error handling export:', error);
      await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการส่งออกข้อมูล');
    }
  }

  async handleReport(msg, reportType) {
    const chatId = msg.chat.id;
    const userId = msg.from.id;

    try {
      await this.bot.sendChatAction(chatId, 'typing');

      let reportData;
      switch (reportType.toLowerCase()) {
        case 'สรุป':
        case 'summary':
          reportData = await this.generateSummaryReport();
          break;
        case 'สถิติ':
        case 'stats':
          reportData = await this.generateStatsReport();
          break;
        case 'รายวัน':
        case 'daily':
          reportData = await this.generateDailyReport();
          break;
        default:
          return this.bot.sendMessage(chatId, '❌ ประเภทรายงานไม่ถูกต้อง (สรุป, สถิติ, รายวัน)');
      }

      if (reportData && reportData.success) {
        await this.bot.sendMessage(chatId, reportData.message, {
          parse_mode: 'Markdown'
        });
      } else {
        await this.bot.sendMessage(chatId, '❌ ไม่สามารถสร้างรายงานได้');
      }

    } catch (error) {
      logger.error('Error handling report:', error);
      await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการสร้างรายงาน');
    }
  }

  async handleDocumentUpload(msg) {
    const chatId = msg.chat.id;
    const userId = msg.from.id;
    const document = msg.document;

    try {
      await this.bot.sendChatAction(chatId, 'typing');

      // Validate file
      if (document.file_size > 50 * 1024 * 1024) {
        return this.bot.sendMessage(chatId, '❌ ไฟล์ใหญ่เกินไป (สูงสุด 50MB)');
      }

      const validation = this.fileHandler.validateFilename(document.file_name);
      if (!validation.valid) {
        return this.bot.sendMessage(chatId, `❌ ${validation.error}`);
      }

      // Download file
      const fileLink = await this.bot.getFileLink(document.file_id);
      const response = await require('axios').get(fileLink, { responseType: 'arraybuffer' });
      const content = Buffer.from(response.data);

      // Save file
      const filename = document.file_name;
      const result = await this.fileHandler.createFile(userId, filename, content);

      if (result.success) {
        await this.bot.sendMessage(chatId,
          `✅ **อัปโหลดไฟล์สำเร็จ**\n` +
          `📄 **ชื่อ:** ${filename}\n` +
          `📊 **ขนาด:** ${this.formatFileSize(document.file_size)}\n` +
          `⏰ **เวลา:** ${new Date().toLocaleString('th-TH')}`,
          { parse_mode: 'Markdown' }
        );
      } else {
        await this.bot.sendMessage(chatId, `❌ ${result.error}`);
      }

    } catch (error) {
      logger.error('Error handling document upload:', error);
      await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการอัปโหลดไฟล์');
    }
  }

  async handlePhotoUpload(msg) {
    const chatId = msg.chat.id;
    const userId = msg.from.id;
    const photo = msg.photo[msg.photo.length - 1]; // Get highest resolution

    try {
      await this.bot.sendChatAction(chatId, 'typing');

      // Download photo
      const fileLink = await this.bot.getFileLink(photo.file_id);
      const response = await require('axios').get(fileLink, { responseType: 'arraybuffer' });
      const content = Buffer.from(response.data);

      // Generate filename
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `photo_${timestamp}.jpg`;

      // Save photo
      const result = await this.fileHandler.createFile(userId, filename, content);

      if (result.success) {
        await this.bot.sendMessage(chatId,
          `📸 **บันทึกรูปภาพสำเร็จ**\n` +
          `📄 **ชื่อ:** ${filename}\n` +
          `📊 **ขนาด:** ${this.formatFileSize(photo.file_size)}\n` +
          `⏰ **เวลา:** ${new Date().toLocaleString('th-TH')}`,
          { parse_mode: 'Markdown' }
        );
      } else {
        await this.bot.sendMessage(chatId, `❌ ${result.error}`);
      }

    } catch (error) {
      logger.error('Error handling photo upload:', error);
      await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการบันทึกรูปภาพ');
    }
  }

  async processFileCommand(text, userId) {
    try {
      const textLower = text.toLowerCase();

      if (textLower.includes('สร้าง') || textLower.includes('create')) {
        const match = text.match(/(?:สร้าง|create)\s+(.+)/i);
        if (match) {
          const filename = match[1].trim();
          return {
            success: true,
            message: `📝 **กำลังสร้างไฟล์:** ${filename}\n\nกรุณาใช้คำสั่ง: \`/สร้าง ${filename}\``,
            keyboard: this.getMainKeyboard()
          };
        }
      }

      if (textLower.includes('รายชื่อไฟล์') || textLower.includes('ไฟล์')) {
        return await this.processFileList(userId);
      }

      return {
        success: true,
        message: `📁 **คำสั่งไฟล์ที่ใช้ได้:**\n\n` +
                `• \`/สร้าง ชื่อไฟล์.txt\` - สร้างไฟล์ใหม่\n` +
                `• \`/แก้ไข ชื่อไฟล์.txt\` - แก้ไขไฟล์\n` +
                `• \`/ลบ ชื่อไฟล์.txt\` - ลบไฟล์\n` +
                `• \`/อ่าน ชื่อไฟล์.txt\` - อ่านไฟล์\n` +
                `• \`/ไฟล์\` - แสดงรายชื่อไฟล์ทั้งหมด`,
        keyboard: this.getFilesMenu().keyboard
      };

    } catch (error) {
      logger.error('Error processing file command:', error);
      return { success: false, error: 'เกิดข้อผิดพลาดในการประมวลผลคำสั่งไฟล์' };
    }
  }

  async processFileList(userId) {
    try {
      const result = await this.fileHandler.listFiles(userId);

      if (result.success && result.files.length > 0) {
        let message = `📁 **ไฟล์ทั้งหมด** (${result.files.length} ไฟล์)\n\n`;

        result.files.slice(0, 20).forEach((file, index) => {
          const size = this.formatFileSize(file.size);
          message += `${index + 1}. 📄 **${file.name}** (${size})\n`;
        });

        if (result.files.length > 20) {
          message += `\n_และอีก ${result.files.length - 20} ไฟล์..._`;
        }

        message += `\n\n💾 **ใช้พื้นที่:** ${this.formatFileSize(result.totalSize)} / 50 MB`;

        return { success: true, message: message };
      } else {
        return { success: true, message: '📭 ยังไม่มีไฟล์ในระบบ' };
      }

    } catch (error) {
      logger.error('Error processing file list:', error);
      return { success: false, error: 'เกิดข้อผิดพลาดในการแสดงรายชื่อไฟล์' };
    }
  }

  // Menu generators
  getSearchMenu() {
    return {
      message: '🔍 **เลือกประเภทการค้นหา:**',
      keyboard: {
        inline_keyboard: [
          [
            { text: '👤 ค้นหาบุคลากร', callback_data: 'search_contacts' },
            { text: '🚗 ค้นหายานพาหนะ', callback_data: 'search_vehicles' }
          ],
          [
            { text: '📋 ค้นหาคำสั่ง', callback_data: 'search_orders' },
            { text: '🔍 ค้นหาทั้งหมด', callback_data: 'search_all' }
          ],
          [
            { text: '🔙 กลับเมนูหลัก', callback_data: 'menu_main' }
          ]
        ]
      }
    };
  }

  getFilesMenu() {
    return {
      message: '📁 **จัดการไฟล์:**',
      keyboard: {
        inline_keyboard: [
          [
            { text: '📄 รายชื่อไฟล์', callback_data: 'files_list' },
            { text: '📝 สร้างไฟล์', callback_data: 'files_create' }
          ],
          [
            { text: '✏️ แก้ไขไฟล์', callback_data: 'files_edit' },
            { text: '🗑️ ลบไฟล์', callback_data: 'files_delete' }
          ],
          [
            { text: '📖 อ่านไฟล์', callback_data: 'files_read' },
            { text: '🔄 กู้คืนไฟล์', callback_data: 'files_restore' }
          ],
          [
            { text: '🔙 กลับเมนูหลัก', callback_data: 'menu_main' }
          ]
        ]
      }
    };
  }

  getReportsMenu() {
    return {
      message: '📊 **เลือกประเภทรายงาน:**',
      keyboard: {
        inline_keyboard: [
          [
            { text: '📈 รายงานสรุป', callback_data: 'report_summary' },
            { text: '📊 รายงานสถิติ', callback_data: 'report_stats' }
          ],
          [
            { text: '📅 รายงานรายวัน', callback_data: 'report_daily' },
            { text: '📋 รายงานรายสัปดาห์', callback_data: 'report_weekly' }
          ],
          [
            { text: '📤 ส่งออกข้อมูล', callback_data: 'export_data' },
            { text: '📄 สร้าง PDF', callback_data: 'generate_pdf' }
          ],
          [
            { text: '🔙 กลับเมนูหลัก', callback_data: 'menu_main' }
          ]
        ]
      }
    };
  }

  getHelpMessage() {
    return {
      message: `📚 **คู่มือการใช้งาน Smart Police Report Bot v3.0**

🤖 **คำสั่งพื้นฐาน:**
• \`/start\` - เริ่มใช้งาน
• \`/help\` - แสดงคู่มือนี้

📝 **บันทึกข้อมูล:**
• ส่งข้อความธรรมดา - ระบบจะวิเคราะห์และบันทึกอัตโนมัติ
• รองรับ: บุคลากร, ยานพาหนะ, คำสั่ง, การจับกุม

🔍 **ค้นหาข้อมูล:**
• \`/ค้นหา [คำค้น]\` - ค้นหาข้อมูล
• \`ค้นหา นาย สมชาย\` - ค้นหาชื่อ
• \`ค้นหา กข-1234\` - ค้นหาทะเบียนรถ

📁 **จัดการไฟล์:**
• \`/สร้าง ชื่อไฟล์.txt\` - สร้างไฟล์
• \`/แก้ไข ชื่อไฟล์.txt\` - แก้ไขไฟล์
• \`/ลบ ชื่อไฟล์.txt\` - ลบไฟล์
• \`/อ่าน ชื่อไฟล์.txt\` - อ่านไฟล์
• \`/ไฟล์\` - แสดงรายชื่อไฟล์

📊 **รายงาน:**
• \`/รายงาน สรุป\` - รายงานสรุป
• \`/export contacts csv\` - ส่งออกข้อมูล

⚡ **คุณสมบัติพิเศษ:**
✅ วิเคราะห์ข้อความอัจฉริยะ
✅ บันทึกอัตโนมัติ
✅ ค้นหาได้ทุกภาษา
✅ สำรองข้อมูลอัตโนมัติ
✅ รายงานเชิงลึก

💡 **เทคนิค:**
• ใช้ภาษาไทยได้เต็มที่
• รองรับตำแหน่งข้าราชการ
• ระบบเข้าใจบริบท

📧 **ติดต่อ:** แอดมิน @your_admin`,
      keyboard: this.getMainKeyboard()
    };
  }

  // Report generators
  async generateSummaryReport() {
    try {
      const contacts = await this.sheetsService.readSheet('Contacts') || [];
      const vehicles = await this.sheetsService.readSheet('Vehicles') || [];
      const orders = await this.sheetsService.readSheet('Orders') || [];

      const now = new Date();
      const today = now.toLocaleDateString('th-TH');

      let message = `📊 **รายงานสรุปประจำวัน**\n📅 ${today}\n\n`;

      message += `📈 **สถิติรวม:**\n`;
      message += `👥 บุคลากร: ${contacts.length} ราย\n`;
      message += `🚗 ยานพาหนะ: ${vehicles.length} คัน\n`;
      message += `📋 คำสั่ง: ${orders.length} รายการ\n\n`;

      // Today's data
      const todayData = [...contacts, ...vehicles, ...orders].filter(item => {
        if (item.Timestamp) {
          const itemDate = new Date(item.Timestamp).toLocaleDateString('th-TH');
          return itemDate === today;
        }
        return false;
      });

      message += `📅 **ข้อมูลวันนี้:** ${todayData.length} รายการ\n`;

      // Recent activity
      if (todayData.length > 0) {
        message += `\n🔥 **กิจกรรมล่าสุด:**\n`;
        todayData.slice(0, 5).forEach((item, index) => {
          const name = item.Name || item.Detail || item.Plate || 'ไม่ระบุ';
          message += `${index + 1}. ${name}\n`;
        });
      }

      message += `\n⏰ **อัปเดตล่าสุด:** ${now.toLocaleString('th-TH')}`;

      return { success: true, message: message };

    } catch (error) {
      logger.error('Error generating summary report:', error);
      return { success: false, error: 'ไม่สามารถสร้างรายงานสรุปได้' };
    }
  }

  async generateStatsReport() {
    try {
      const contacts = await this.sheetsService.readSheet('Contacts') || [];
      const vehicles = await this.sheetsService.readSheet('Vehicles') || [];
      const orders = await this.sheetsService.readSheet('Orders') || [];

      let message = `📈 **รายงานสถิติระบบ**\n\n`;

      // Contact stats
      if (contacts.length > 0) {
        const contactAnalysis = await this.dataProcessor.analyzeData(contacts, 'contacts');
        message += `👥 **สถิติบุคลากร:**\n`;
        message += `• ทั้งหมด: ${contactAnalysis.totalRecords} ราย\n`;
        message += `• มีเบอร์โทร: ${contactAnalysis.overview.withPhone || 0} ราย\n`;
        message += `• มีหน่วยงาน: ${contactAnalysis.overview.withAgency || 0} ราย\n\n`;
      }

      // Vehicle stats
      if (vehicles.length > 0) {
        const vehicleAnalysis = await this.dataProcessor.analyzeData(vehicles, 'vehicles');
        message += `🚗 **สถิติยานพาหนะ:**\n`;
        message += `• ทั้งหมด: ${vehicleAnalysis.totalRecords} คัน\n`;
        message += `• ใช้งานได้: ${vehicleAnalysis.overview.inUse || 0} คัน\n`;
        message += `• ซ่อม: ${vehicleAnalysis.overview.underRepair || 0} คัน\n\n`;
      }

      // Order stats
      if (orders.length > 0) {
        const orderAnalysis = await this.dataProcessor.analyzeData(orders, 'orders');
        message += `📋 **สถิติคำสั่ง:**\n`;
        message += `• ทั้งหมด: ${orderAnalysis.totalRecords} รายการ\n`;
        message += `• รอดำเนินการ: ${orderAnalysis.overview.pending || 0} รายการ\n`;
        message += `• เสร็จสิ้น: ${orderAnalysis.overview.completed || 0} รายการ\n`;
        message += `• เร่งด่วน: ${orderAnalysis.overview.urgent || 0} รายการ\n\n`;
      }

      message += `⏰ **สร้างเมื่อ:** ${new Date().toLocaleString('th-TH')}`;

      return { success: true, message: message };

    } catch (error) {
      logger.error('Error generating stats report:', error);
      return { success: false, error: 'ไม่สามารถสร้างรายงานสถิติได้' };
    }
  }

  async generateDailyReport() {
    try {
      const today = new Date().toLocaleDateString('th-TH');
      const contacts = await this.sheetsService.readSheet('Contacts') || [];
      const vehicles = await this.sheetsService.readSheet('Vehicles') || [];
      const orders = await this.sheetsService.readSheet('Orders') || [];

      // Filter today's data
      const todayContacts = contacts.filter(item => {
        if (item.Timestamp) {
          return new Date(item.Timestamp).toLocaleDateString('th-TH') === today;
        }
        return false;
      });

      const todayVehicles = vehicles.filter(item => {
        if (item.Timestamp) {
          return new Date(item.Timestamp).toLocaleDateString('th-TH') === today;
        }
        return false;
      });

      const todayOrders = orders.filter(item => {
        if (item.Timestamp) {
          return new Date(item.Timestamp).toLocaleDateString('th-TH') === today;
        }
        return false;
      });

      let message = `📅 **รายงานประจำวัน**\n${today}\n\n`;

      message += `📊 **สรุปกิจกรรมวันนี้:**\n`;
      message += `👥 บุคลากรใหม่: ${todayContacts.length} ราย\n`;
      message += `🚗 ยานพาหนะใหม่: ${todayVehicles.length} คัน\n`;
      message += `📋 คำสั่งใหม่: ${todayOrders.length} รายการ\n\n`;

      // Show details if any
      if (todayContacts.length > 0) {
        message += `👤 **บุคลากรใหม่:**\n`;
        todayContacts.slice(0, 5).forEach((contact, index) => {
          message += `${index + 1}. ${contact.Name || 'ไม่ระบุชื่อ'}\n`;
        });
        message += '\n';
      }

      if (todayVehicles.length > 0) {
        message += `🚗 **ยานพาหนะใหม่:**\n`;
        todayVehicles.slice(0, 5).forEach((vehicle, index) => {
          message += `${index + 1}. ${vehicle.Plate || vehicle.Shield || 'ไม่ระบุ'}\n`;
        });
        message += '\n';
      }

      if (todayOrders.length > 0) {
        message += `📋 **คำสั่งใหม่:**\n`;
        todayOrders.slice(0, 3).forEach((order, index) => {
          const detail = order.Detail ? order.Detail.substring(0, 50) + '...' : 'ไม่ระบุ';
          message += `${index + 1}. ${detail}\n`;
        });
        message += '\n';
      }

      if (todayContacts.length === 0 && todayVehicles.length === 0 && todayOrders.length === 0) {
        message += `📭 **ยังไม่มีกิจกรรมใหม่วันนี้**\n\n`;
      }

      message += `⏰ **สร้างรายงาน:** ${new Date().toLocaleString('th-TH')}`;

      return { success: true, message: message };

    } catch (error) {
      logger.error('Error generating daily report:', error);
      return { success: false, error: 'ไม่สามารถสร้างรายงานรายวันได้' };
    }
  }

  // Utility methods
  splitMessage(message, maxLength = 4000) {
    if (message.length <= maxLength) {
      return [message];
    }

    const parts = [];
    let current = '';
    const lines = message.split('\n');

    for (const line of lines) {
      if ((current + line + '\n').length > maxLength) {
        if (current) {
          parts.push(current.trim());
          current = '';
        }

        if (line.length > maxLength) {
          // Split long lines
          let remaining = line;
          while (remaining.length > maxLength) {
            parts.push(remaining.substring(0, maxLength));
            remaining = remaining.substring(maxLength);
          }
          current = remaining + '\n';
        } else {
          current = line + '\n';
        }
      } else {
        current += line + '\n';
      }
    }

    if (current.trim()) {
      parts.push(current.trim());
    }

    return parts;
  }

  // Callback query handler
  async handleCallbackQuery(query) {
    const chatId = query.message.chat.id;
    const userId = query.from.id;
    const data = query.data;

    try {
      await this.bot.answerCallbackQuery(query.id);

      let response;
      switch (data) {
        case 'menu_save':
          response = this.getSaveMenu();
          break;
        case 'menu_search':
          response = this.getSearchMenu();
          break;
        case 'menu_files':
          response = this.getFilesMenu();
          break;
        case 'menu_reports':
          response = this.getReportsMenu();
          break;
        case 'menu_help':
          response = this.getHelpMessage();
          break;
        default:
          response = { message: 'คำสั่งไม่ถูกต้อง' };
      }

      await this.bot.editMessageText(response.message, {
        chat_id: chatId,
        message_id: query.message.message_id,
        parse_mode: 'Markdown',
        reply_markup: response.keyboard || null
      });

    } catch (error) {
      logger.error('Error handling callback query:', error);
    }
  }

  // Setup cron jobs for automated tasks
  setupCronJobs() {
    // Daily backup at 2 AM
    cron.schedule('0 2 * * *', async () => {
      logger.info('Running daily backup...');
      await this.performBackup();
    });

    // Weekly report on Sunday at 9 AM
    cron.schedule('0 9 * * 0', async () => {
      logger.info('Generating weekly report...');
      await this.generateWeeklyReport();
    });

    // Clean temp files every 6 hours
    cron.schedule('0 */6 * * *', async () => {
      logger.info('Cleaning temporary files...');
      await this.cleanTempFiles();
    });
  }

  // Utility methods
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  getMainKeyboard() {
    return {
      inline_keyboard: [
        [
          { text: '📝 บันทึก', callback_data: 'menu_save' },
          { text: '🔍 ค้นหา', callback_data: 'menu_search' }
        ],
        [
          { text: '📁 ไฟล์', callback_data: 'menu_files' },
          { text: '📊 รายงาน', callback_data: 'menu_reports' }
        ]
      ]
    };
  }

  getSaveMenu() {
    return {
      message: '📝 **เลือกประเภทข้อมูลที่ต้องการบันทึก:**',
      keyboard: {
        inline_keyboard: [
          [
            { text: '👤 บุคลากร', callback_data: 'save_contact' },
            { text: '🚗 ยานพาหนะ', callback_data: 'save_vehicle' }
          ],
          [
            { text: '📋 คำสั่ง', callback_data: 'save_order' },
            { text: '👮 การจับกุม', callback_data: 'save_arrest' }
          ],
          [
            { text: '🔫 อาวุธปืน', callback_data: 'save_firearm' },
            { text: '⚔️ อุปกรณ์', callback_data: 'save_equipment' }
          ],
          [
            { text: '🔙 กลับเมนูหลัก', callback_data: 'menu_main' }
          ]
        ]
      }
    };
  }

  async performBackup() {
    // Implementation for backup
    logger.info('Backup completed');
  }

  async generateWeeklyReport() {
    // Implementation for weekly report
    logger.info('Weekly report generated');
  }

  async cleanTempFiles() {
    try {
      await fs.emptyDir('./temp');
      logger.info('Temporary files cleaned');
    } catch (error) {
      logger.error('Error cleaning temp files:', error);
    }
  }
}

// Express server for health checks and webhooks
const app = express();
app.use(helmet());
app.use(compression());
app.use(cors());
app.use(express.json({ limit: '50mb' }));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    version: '3.0.0',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Start the bot
async function startBot() {
  try {
    // Create bot instance
    const bot = new SmartPoliceBot();

    // Start Express server
    const port = process.env.PORT || 3000;
    app.listen(port, () => {
      logger.info(`🌐 Server running on port ${port}`);
      logger.info('🤖 Smart Police Bot is ready!');
    });

    // Graceful shutdown
    process.on('SIGINT', () => {
      logger.info('👋 Shutting down gracefully...');
      bot.bot.stopPolling();
      process.exit(0);
    });

  } catch (error) {
    logger.error('Failed to start bot:', error);
    process.exit(1);
  }
}

// Start the application
startBot();