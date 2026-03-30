/**
 * Google Services Integration Test
 * ทดสอบการเชื่อมต่อ Google Sheets + Google Drive
 */

require('dotenv').config();
const GoogleSheetsService = require('./services/GoogleSheetsService');
const GoogleDriveService = require('./services/GoogleDriveService');
const fs = require('fs-extra');

async function testGoogleServices() {
  console.log('🔍 Testing Google Services Integration...');
  console.log('============================================');

  const results = {
    sheets: { success: false, message: '' },
    drive: { success: false, message: '' },
    overall: { success: false, message: '' }
  };

  // Test Google Sheets
  console.log('\n📊 Testing Google Sheets Service...');
  try {
    const sheetsService = new GoogleSheetsService();

    // Wait for initialization
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Health check
    const sheetsHealth = await sheetsService.healthCheck();

    if (sheetsHealth.success) {
      console.log('✅ Google Sheets - Connected successfully');

      // Test basic operations
      const testData = {
        Name: 'Test User',
        Position: 'Test Position',
        Phone: '081-234-5678',
        Agency: 'Test Agency'
      };

      console.log('📝 Testing data write...');
      const writeResult = await sheetsService.appendData('Contacts', testData);

      if (writeResult.success) {
        console.log('✅ Data write - Success');

        console.log('🔍 Testing data search...');
        const searchResult = await sheetsService.searchAll('Test User');

        if (searchResult && searchResult.length > 0) {
          console.log('✅ Data search - Success');
          results.sheets = { success: true, message: 'All operations successful' };
        } else {
          results.sheets = { success: false, message: 'Search failed' };
        }
      } else {
        results.sheets = { success: false, message: `Write failed: ${writeResult.error}` };
      }
    } else {
      results.sheets = { success: false, message: `Connection failed: ${sheetsHealth.error}` };
    }

  } catch (error) {
    console.error('❌ Google Sheets Error:', error.message);
    results.sheets = { success: false, message: error.message };
  }

  // Test Google Drive
  console.log('\n📁 Testing Google Drive Service...');
  try {
    const driveService = new GoogleDriveService();

    // Wait for initialization
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Health check
    const driveHealth = await driveService.healthCheck();

    if (driveHealth.success) {
      console.log('✅ Google Drive - Connected successfully');
      console.log(`📂 Target Folder ID: ${driveHealth.folderId || 'Root'}`);

      // Test file operations
      console.log('📝 Testing file upload...');

      // Create a test file
      const testFilePath = './test-upload.txt';
      const testContent = `Smart Police Bot Test File\nCreated: ${new Date().toISOString()}\nThis is a test file for Google Drive integration.`;

      await fs.writeFile(testFilePath, testContent);

      const uploadResult = await driveService.uploadFile(
        testFilePath,
        `test-file-${Date.now()}.txt`,
        'text/plain'
      );

      if (uploadResult.success) {
        console.log('✅ File upload - Success');
        console.log(`📄 File ID: ${uploadResult.fileId}`);
        console.log(`🔗 View Link: ${uploadResult.webViewLink}`);

        // Test file listing
        console.log('📋 Testing file listing...');
        const listResult = await driveService.listFiles(5);

        if (listResult.success && listResult.files.length > 0) {
          console.log('✅ File listing - Success');
          console.log(`📊 Found ${listResult.count} files`);

          // Test file info
          console.log('ℹ️ Testing file info...');
          const infoResult = await driveService.getFileInfo(uploadResult.fileId);

          if (infoResult.success) {
            console.log('✅ File info - Success');
            results.drive = { success: true, message: 'All operations successful' };
          } else {
            results.drive = { success: false, message: 'File info failed' };
          }
        } else {
          results.drive = { success: false, message: 'File listing failed' };
        }

        // Clean up test file
        await fs.remove(testFilePath);

      } else {
        results.drive = { success: false, message: `Upload failed: ${uploadResult.error}` };
      }
    } else {
      results.drive = { success: false, message: `Connection failed: ${driveHealth.error}` };
    }

  } catch (error) {
    console.error('❌ Google Drive Error:', error.message);
    results.drive = { success: false, message: error.message };
  }

  // Overall results
  console.log('\n============================================');
  console.log('📊 Test Results Summary:');
  console.log(`📊 Google Sheets: ${results.sheets.success ? '✅ PASS' : '❌ FAIL'} - ${results.sheets.message}`);
  console.log(`📁 Google Drive: ${results.drive.success ? '✅ PASS' : '❌ FAIL'} - ${results.drive.message}`);

  const allSuccess = results.sheets.success && results.drive.success;
  console.log(`\n🎯 Overall: ${allSuccess ? '✅ ALL SYSTEMS GO!' : '❌ ISSUES DETECTED'}`);

  if (allSuccess) {
    console.log('\n🎉 Google Services Integration - READY!');
    console.log('🚀 Bot can now:');
    console.log('   📊 Read/Write to Google Sheets');
    console.log('   📁 Upload/Download files to Google Drive');
    console.log('   🔍 Search across both services');
    console.log('   💾 Backup and restore data');
  } else {
    console.log('\n⚠️ Some services failed. Please check:');
    console.log('   🔑 Service account credentials');
    console.log('   📋 Google Sheets ID and permissions');
    console.log('   📁 Google Drive folder ID and permissions');
    console.log('   🌐 Internet connection');
  }

  console.log('\n🔗 Service URLs:');
  console.log(`   📊 Google Sheets: https://docs.google.com/spreadsheets/d/${process.env.GOOGLE_SHEET_ID}`);
  console.log(`   📁 Google Drive: https://drive.google.com/drive/folders/${process.env.GOOGLE_DRIVE_FOLDER_ID}`);

  return allSuccess;
}

// Test specific sheet structure
async function testSheetStructure() {
  console.log('\n📋 Testing Sheet Structure...');

  try {
    const sheetsService = new GoogleSheetsService();
    await new Promise(resolve => setTimeout(resolve, 1000));

    const requiredSheets = ['Contacts', 'Vehicles', 'Orders'];

    for (const sheetName of requiredSheets) {
      console.log(`🔍 Checking sheet: ${sheetName}`);

      const data = await sheetsService.getSheetData(sheetName, 1);
      console.log(`✅ ${sheetName} - Accessible (${data.length} records)`);
    }

    console.log('✅ All required sheets are accessible');

  } catch (error) {
    console.error('❌ Sheet structure test failed:', error.message);
  }
}

// Run tests
if (require.main === module) {
  testGoogleServices()
    .then((success) => {
      if (success) {
        return testSheetStructure();
      }
    })
    .then(() => {
      console.log('\n🎯 Testing completed!');
      process.exit(0);
    })
    .catch((error) => {
      console.error('\n💥 Test failed:', error);
      process.exit(1);
    });
}

module.exports = { testGoogleServices, testSheetStructure };