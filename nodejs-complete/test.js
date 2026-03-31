/**
 * Simple Test Script for Smart Police Bot
 * ทดสอบการทำงานของระบบ
 */

const fs = require('fs-extra');
const path = require('path');

// Test configuration
const tests = [
  'ตรวจสอบไฟล์ package.json',
  'ตรวจสอบไฟล์ .env',
  'ตรวจสอบไฟล์ service_account.json',
  'ตรวจสอบ Node.js modules',
  'ทดสอบการเชื่อมต่อ Google Sheets',
  'ทดสอบ AI Processor',
  'ทดสอบ File Handler'
];

async function runTests() {
  console.log('🧪 Smart Police Bot v3.0 - System Test\n');
  console.log('===============================================\n');

  let passed = 0;
  let failed = 0;

  // Test 1: Check package.json
  try {
    const pkg = await fs.readJson('package.json');
    if (pkg.name && pkg.version && pkg.dependencies) {
      console.log('✅ package.json - OK');
      passed++;
    } else {
      console.log('❌ package.json - Invalid structure');
      failed++;
    }
  } catch (error) {
    console.log('❌ package.json - Not found');
    failed++;
  }

  // Test 2: Check .env
  try {
    const localEnv = await fs.pathExists('.env');
    const parentEnv = await fs.pathExists('../.env');
    if (localEnv || parentEnv || process.env.TELEGRAM_BOT_TOKEN) {
      console.log('✅ Environment variables/file - OK');
      passed++;
    } else {
      console.log('❌ Environment config - Missing');
      failed++;
    }
  } catch (error) {
    console.log('❌ Environment check - Error');
    failed++;
  }

  // Test 3: Check service_account.json
  try {
    let serviceAccount;
    if (await fs.pathExists('service_account.json')) {
      serviceAccount = await fs.readJson('service_account.json');
    } else if (await fs.pathExists('../service_account.json')) {
      serviceAccount = await fs.readJson('../service_account.json');
    } else if (process.env.GOOGLE_CREDENTIALS) {
      serviceAccount = JSON.parse(process.env.GOOGLE_CREDENTIALS);
    }

    if (serviceAccount && serviceAccount.type === 'service_account') {
      console.log('✅ service_account.json/config - OK');
      passed++;
    } else {
      console.log('❌ service_account.json - Not found');
      failed++;
    }
  } catch (error) {
    console.log('❌ service_account.json - Error');
    failed++;
  }

  // Test 4: Check node_modules
  try {
    if (await fs.pathExists('node_modules')) {
      const requiredModules = [
        'node-telegram-bot-api',
        'googleapis',
        'express',
        'winston',
        'moment',
        'fs-extra'
      ];

      let modulesPassed = 0;
      for (const module of requiredModules) {
        if (await fs.pathExists(path.join('node_modules', module))) {
          modulesPassed++;
        }
      }

      if (modulesPassed === requiredModules.length) {
        console.log('✅ Node.js modules - OK');
        passed++;
      } else {
        console.log(`❌ Node.js modules - Missing ${requiredModules.length - modulesPassed} modules`);
        failed++;
      }
    } else {
      console.log('❌ Node.js modules - Run npm install');
      failed++;
    }
  } catch (error) {
    console.log('❌ Node.js modules - Error checking');
    failed++;
  }

  // Test 5: Test Google Sheets Service
  try {
    const GoogleSheetsService = require('./services/GoogleSheetsService');
    const sheetsService = new GoogleSheetsService();
    console.log('✅ Google Sheets Service - OK');
    passed++;
  } catch (error) {
    console.log('❌ Google Sheets Service - Import error');
    failed++;
  }

  // Test 6: Test AI Processor
  try {
    const AIProcessor = require('./services/AIProcessor');
    const aiProcessor = new AIProcessor();
    const testResult = await aiProcessor.detectIntent('นาย สมชาย โทร 081-234-5678');
    if (testResult && testResult.type) {
      console.log('✅ AI Processor - OK');
      passed++;
    } else {
      console.log('❌ AI Processor - Detection failed');
      failed++;
    }
  } catch (error) {
    console.log('❌ AI Processor - Error:', error.message);
    failed++;
  }

  // Test 7: Test File Handler
  try {
    const FileHandler = require('./handlers/FileHandler');
    const fileHandler = new FileHandler();
    const validation = fileHandler.validateFilename('test.txt');
    if (validation.valid) {
      console.log('✅ File Handler - OK');
      passed++;
    } else {
      console.log('❌ File Handler - Validation failed');
      failed++;
    }
  } catch (error) {
    console.log('❌ File Handler - Error:', error.message);
    failed++;
  }

  // Summary
  console.log('\n===============================================');
  console.log('📊 Test Results Summary:');
  console.log(`✅ Passed: ${passed}`);
  console.log(`❌ Failed: ${failed}`);
  console.log(`📈 Success Rate: ${((passed / tests.length) * 100).toFixed(1)}%`);

  if (failed === 0) {
    console.log('\n🎉 All tests passed! ระบบพร้อมใช้งาน');
    console.log('🚀 Run: npm start or node index.js');
  } else {
    console.log('\n⚠️  Some tests failed. กรุณาตรวจสอบการตั้งค่า');
    console.log('📚 ดูวิธีแก้ไขใน README.md');
  }

  console.log('\n🔗 Health Check: http://localhost:3000/health');
}

// Run tests
if (require.main === module) {
  runTests().catch(console.error);
}

module.exports = { runTests };