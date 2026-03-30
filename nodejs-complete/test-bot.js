/**
 * Telegram Bot Connection Test
 * ทดสอบการเชื่อมต่อกับ Telegram Bot
 */

require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');

async function testBotConnection() {
  console.log('🤖 Testing Telegram Bot Connection...');
  console.log('=========================================');

  const token = process.env.TELEGRAM_BOT_TOKEN;
  const botUsername = process.env.BOT_USERNAME || 'police_ddb_bot';

  if (!token) {
    console.error('❌ TELEGRAM_BOT_TOKEN not found in .env file');
    process.exit(1);
  }

  console.log(`📱 Bot Token: ${token.substring(0, 20)}...`);
  console.log(`🤖 Bot Username: @${botUsername}`);

  try {
    // Create bot instance (without polling for testing)
    const bot = new TelegramBot(token, { polling: false });

    console.log('\n🔍 Getting bot info...');

    // Get bot information
    const botInfo = await bot.getMe();

    console.log('\n✅ Bot Connection Successful!');
    console.log('📊 Bot Information:');
    console.log(`   ID: ${botInfo.id}`);
    console.log(`   Name: ${botInfo.first_name}`);
    console.log(`   Username: @${botInfo.username}`);
    console.log(`   Can Join Groups: ${botInfo.can_join_groups}`);
    console.log(`   Can Read Group Messages: ${botInfo.can_read_all_group_messages}`);
    console.log(`   Supports Inline: ${botInfo.supports_inline_queries}`);

    console.log('\n🔗 Bot Links:');
    console.log(`   Direct Message: https://t.me/${botInfo.username}`);
    console.log(`   Add to Group: https://t.me/${botInfo.username}?startgroup=start`);

    console.log('\n📋 Next Steps:');
    console.log('1. ส่งข้อความ /start ไปที่บอท');
    console.log('2. รันระบบด้วย: npm start');
    console.log('3. ทดสอบการทำงานของระบบ');

    console.log('\n🎉 Bot พร้อมใช้งาน!');

  } catch (error) {
    console.error('\n❌ Bot Connection Failed!');

    if (error.code === 'ETELEGRAM') {
      console.error('📛 Telegram API Error:', error.response?.body?.description || error.message);

      if (error.response?.statusCode === 401) {
        console.error('🔑 Invalid bot token. Please check your TELEGRAM_BOT_TOKEN');
      } else if (error.response?.statusCode === 404) {
        console.error('🤖 Bot not found. Token may be incorrect');
      }
    } else {
      console.error('🌐 Network Error:', error.message);
    }

    console.log('\n🛠️ Troubleshooting:');
    console.log('1. ตรวจสอบ TELEGRAM_BOT_TOKEN ในไฟล์ .env');
    console.log('2. ตรวจสอบการเชื่อมต่อ internet');
    console.log('3. ตรวจสอบว่าบอทยังใช้งานได้อยู่');

    process.exit(1);
  }
}

// Test webhook info (optional)
async function testWebhookInfo() {
  try {
    const bot = new TelegramBot(process.env.TELEGRAM_BOT_TOKEN, { polling: false });
    const webhookInfo = await bot.getWebHookInfo();

    console.log('\n📡 Webhook Information:');
    console.log(`   URL: ${webhookInfo.url || 'Not set (using polling)'}`);
    console.log(`   Has Custom Certificate: ${webhookInfo.has_custom_certificate}`);
    console.log(`   Pending Updates: ${webhookInfo.pending_update_count}`);

    if (webhookInfo.last_error_date) {
      console.log(`   Last Error: ${new Date(webhookInfo.last_error_date * 1000)}`);
      console.log(`   Last Error Message: ${webhookInfo.last_error_message}`);
    }

  } catch (error) {
    console.warn('⚠️ Could not get webhook info:', error.message);
  }
}

// Run tests
if (require.main === module) {
  testBotConnection()
    .then(() => testWebhookInfo())
    .catch(console.error);
}

module.exports = { testBotConnection };