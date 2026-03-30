const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
require('dotenv').config({ path: '../shared/.env' });

class SmartPoliceBot {
    constructor() {
        this.token = process.env.TELEGRAM_BOT_TOKEN;
        this.bot = new TelegramBot(this.token, { polling: true });
        this.pythonApiUrl = process.env.PYTHON_API_URL || 'http://localhost:8000';

        this.setupHandlers();
        console.log('🤖 Smart Police Bot เริ่มทำงานแล้ว...');
    }

    setupHandlers() {
        // /start command
        this.bot.onText(/\/start/, async (msg) => {
            await this.handleStart(msg);
        });

        // Handle all messages
        this.bot.on('message', async (msg) => {
            if (msg.text && !msg.text.startsWith('/')) {
                await this.handleMessage(msg);
            }
        });

        // Handle callback queries (inline keyboard buttons)
        this.bot.on('callback_query', async (query) => {
            await this.handleCallbackQuery(query);
        });

        // Error handling
        this.bot.on('error', (error) => {
            console.error('Bot Error:', error);
        });
    }

    async handleStart(msg) {
        const chatId = msg.chat.id;
        const welcomeMessage = `
🚔 **ยินดีต้อนรับสู่ Smart Police Report Bot**

ระบบรายงานตำรวจอัจฉริยะ
✅ บันทึกข้อมูลอัตโนมัติ
✅ ค้นหาข้อมูลรวดเร็ว
✅ แจ้งเตือนอัจฉริยะ

พิมพ์ข้อความเพื่อเริ่มใช้งาน หรือเลือกเมนูด้านล่าง
        `;

        const keyboard = {
            reply_markup: {
                inline_keyboard: [
                    [
                        { text: '📝 บันทึกข้อมูล', callback_data: 'menu_save' },
                        { text: '🔍 ค้นหาข้อมูล', callback_data: 'menu_search' }
                    ],
                    [
                        { text: '📊 สรุปรายงาน', callback_data: 'menu_report' },
                        { text: '⚙️ ตั้งค่า', callback_data: 'menu_settings' }
                    ],
                    [
                        { text: '📚 คู่มือการใช้งาน', callback_data: 'menu_help' }
                    ]
                ]
            }
        };

        await this.bot.sendMessage(chatId, welcomeMessage, {
            parse_mode: 'Markdown',
            ...keyboard
        });
    }

    async handleMessage(msg) {
        const chatId = msg.chat.id;
        const text = msg.text;
        const userId = msg.from.id;

        try {
            // แสดง typing indicator
            await this.bot.sendChatAction(chatId, 'typing');

            // ส่งข้อความไป Python API เพื่อประมวลผล
            const response = await axios.post(`${this.pythonApiUrl}/process-message`, {
                message: text,
                user_id: userId,
                chat_id: chatId,
                user_info: {
                    first_name: msg.from.first_name,
                    last_name: msg.from.last_name,
                    username: msg.from.username
                }
            });

            const result = response.data;

            // ส่งผลลัพธ์กลับไปยังผู้ใช้
            if (result.success) {
                await this.bot.sendMessage(chatId, result.message, {
                    parse_mode: 'Markdown',
                    reply_markup: result.keyboard || null
                });

                // ถ้ามี attachments (files, images)
                if (result.attachments) {
                    for (const attachment of result.attachments) {
                        if (attachment.type === 'document') {
                            await this.bot.sendDocument(chatId, attachment.url);
                        } else if (attachment.type === 'photo') {
                            await this.bot.sendPhoto(chatId, attachment.url);
                        }
                    }
                }
            } else {
                await this.bot.sendMessage(chatId, `❌ เกิดข้อผิดพลาด: ${result.error}`);
            }

        } catch (error) {
            console.error('Error processing message:', error);
            await this.bot.sendMessage(chatId, '❌ ระบบขัดข้อง กรุณาลองใหม่อีกครั้ง');
        }
    }

    async handleCallbackQuery(query) {
        const chatId = query.message.chat.id;
        const data = query.data;
        const messageId = query.message.message_id;

        try {
            // Answer callback query เพื่อลบ loading indicator
            await this.bot.answerCallbackQuery(query.id);

            // ส่งคำสั่งไป Python API
            const response = await axios.post(`${this.pythonApiUrl}/handle-callback`, {
                callback_data: data,
                user_id: query.from.id,
                chat_id: chatId,
                message_id: messageId
            });

            const result = response.data;

            if (result.success) {
                if (result.edit_message) {
                    // แก้ไขข้อความเดิม
                    await this.bot.editMessageText(result.message, {
                        chat_id: chatId,
                        message_id: messageId,
                        parse_mode: 'Markdown',
                        reply_markup: result.keyboard || null
                    });
                } else {
                    // ส่งข้อความใหม่
                    await this.bot.sendMessage(chatId, result.message, {
                        parse_mode: 'Markdown',
                        reply_markup: result.keyboard || null
                    });
                }
            }

        } catch (error) {
            console.error('Error handling callback query:', error);
            await this.bot.sendMessage(chatId, '❌ เกิดข้อผิดพลาดในการประมวลผล');
        }
    }

    // Method สำหรับส่งแจ้งเตือนจาก Python
    async sendNotification(chatId, message, options = {}) {
        try {
            await this.bot.sendMessage(chatId, message, {
                parse_mode: 'Markdown',
                ...options
            });
            return true;
        } catch (error) {
            console.error('Error sending notification:', error);
            return false;
        }
    }
}

// สร้าง Express server สำหรับรับ webhooks จาก Python
const express = require('express');
const app = express();
app.use(express.json());

let botInstance;

// Endpoint สำหรับ Python ส่งแจ้งเตือน
app.post('/send-notification', async (req, res) => {
    try {
        const { chat_id, message, options } = req.body;
        const success = await botInstance.sendNotification(chat_id, message, options);
        res.json({ success });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// เริ่มต้น bot และ server
async function start() {
    try {
        // สร้าง bot instance
        botInstance = new SmartPoliceBot();

        // เริ่ม Express server
        const port = process.env.BOT_SERVER_PORT || 3000;
        app.listen(port, () => {
            console.log(`🌐 Bot API Server running on port ${port}`);
        });

    } catch (error) {
        console.error('Failed to start bot:', error);
        process.exit(1);
    }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('🛑 Shutting down bot...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('🛑 Shutting down bot...');
    process.exit(0);
});

start();