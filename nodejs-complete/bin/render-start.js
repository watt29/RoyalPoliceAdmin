#!/usr/bin/env node

/**
 * Render.com Production Startup Script
 * สำหรับการเริ่มงานบน Render.com
 */

const fs = require('fs-extra');
const path = require('path');

console.log('🚀 Starting Smart Police Bot on Render.com...');
console.log('===============================================');

// Environment check
console.log(`📍 Environment: ${process.env.NODE_ENV || 'development'}`);
console.log(`🌍 Port: ${process.env.PORT || 3000}`);

// Check critical environment variables
const requiredEnvVars = [
  'TELEGRAM_BOT_TOKEN',
  'GOOGLE_SHEET_ID'
];

console.log('\n🔍 Checking environment variables...');
const missingVars = [];

requiredEnvVars.forEach(varName => {
  if (process.env[varName]) {
    console.log(`✅ ${varName} - OK`);
  } else {
    console.log(`❌ ${varName} - MISSING`);
    missingVars.push(varName);
  }
});

// Check Google Credentials (supports both formats)
if (process.env.GOOGLE_CREDENTIALS_BASE64) {
  console.log('✅ GOOGLE_CREDENTIALS_BASE64 - OK');
} else if (process.env.GOOGLE_CREDENTIALS) {
  console.log('✅ GOOGLE_CREDENTIALS - OK');
} else {
  console.log('❌ Google Credentials - MISSING (need GOOGLE_CREDENTIALS_BASE64 or GOOGLE_CREDENTIALS)');
  missingVars.push('GOOGLE_CREDENTIALS');
}

if (missingVars.length > 0) {
  console.error('\n❌ Missing required environment variables:', missingVars);
  console.error('Please set them in your Render dashboard');
  process.exit(1);
}

// Validate Google Credentials JSON
try {
  let credentials;

  if (process.env.GOOGLE_CREDENTIALS_BASE64) {
    const decoded = Buffer.from(process.env.GOOGLE_CREDENTIALS_BASE64, 'base64').toString();
    credentials = JSON.parse(decoded);
    console.log('✅ Google credentials (Base64) - Valid JSON');
  } else if (process.env.GOOGLE_CREDENTIALS) {
    credentials = JSON.parse(process.env.GOOGLE_CREDENTIALS);
    console.log('✅ Google credentials - Valid JSON');
  } else {
    throw new Error('No Google credentials found');
  }

  if (credentials.type !== 'service_account') {
    throw new Error('Invalid service account credentials');
  }
} catch (error) {
  console.error('❌ Google credentials - Invalid JSON:', error.message);
  process.exit(1);
}

// Create necessary directories
const directories = ['logs', 'temp', 'user-files', 'exports', 'backups'];

console.log('\n📁 Creating directories...');
directories.forEach(dir => {
  try {
    fs.ensureDirSync(dir);
    console.log(`✅ ${dir}/`);
  } catch (error) {
    console.error(`❌ Error creating ${dir}:`, error.message);
  }
});

// Prevent Render sleeping (free tier)
if (process.env.NODE_ENV === 'production') {
  console.log('\n⏰ Setting up keep-alive service...');

  const keepAliveInterval = 14 * 60 * 1000; // 14 minutes
  const appUrl = `https://${process.env.RENDER_SERVICE_NAME || 'smart-police-bot'}.onrender.com`;

  setInterval(async () => {
    try {
      const axios = require('axios');
      await axios.get(`${appUrl}/health`, { timeout: 30000 });
      console.log('💓 Keep-alive ping successful');
    } catch (error) {
      console.warn('⚠️ Keep-alive ping failed:', error.message);
    }
  }, keepAliveInterval);
}

// Optional quick test (non-blocking)
if (process.env.NODE_ENV === 'production') {
  console.log('\n🧪 Running production health check...');
  try {
    // Quick validation
    const hasGoogleCreds = process.env.GOOGLE_CREDENTIALS_BASE64 || process.env.GOOGLE_CREDENTIALS;
    if (process.env.TELEGRAM_BOT_TOKEN && hasGoogleCreds) {
      console.log('✅ Essential environment variables present');
    } else {
      console.log('⚠️ Some environment variables missing');
    }
  } catch (error) {
    console.warn('⚠️ Health check warning:', error.message);
  }
}

console.log('\n🤖 Starting Smart Police Bot...');
console.log('===============================================\n');

// Start the main application
require('../index.js');